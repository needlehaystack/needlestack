import logging
import signal
from copy import deepcopy
from typing import List, Optional

import kazoo
from kazoo.client import KazooClient, KazooState
from kazoo.recipe.cache import TreeCache
from kazoo.retry import KazooRetry

from needlestack.apis import collections_pb2
from needlestack.cluster_managers import ClusterManager


logger = logging.getLogger("needlestack")


class ZookeeperClusterManager(ClusterManager):

    """
    A cluster manager that manages one cluster's state and configurations
    with a Zookeeper ensemble via kazoo.

    Below is the structure of the znodes:
        /needlestack
            /<CLUSTER_NAME_1>
                /live_nodes
                    /<HOSTPORT_1>
                    /<HOSTPORT_2>
                    /<HOSTPORT_3>
                    /<HOSTPORT_4>
                    ...
                /collections
                    /<COLLECTION_NAME_1>
                        /shards
                            /<SHARD_NAME_1>
                                /replicas
                                    /<HOSTPORT_2>
                                    /<HOSTPORT_4>
                            /<SHARD_NAME_2>
                                /replicas
                                    /<HOSTPORT_1>
                                    /<HOSTPORT_3>
                    /<COLLECTION_NAME_2>
                        ...
    """

    cluster_name: str
    hostport: str
    zk: KazooClient
    cache: TreeCache

    def __init__(
        self, cluster_name: str, hostport: str, hosts: List[str], zookeeper_root: str
    ):
        self.cluster_name = cluster_name
        self.hostport = hostport
        self.zookeeper_root = zookeeper_root
        self.zk = KazooClient(hosts=hosts)
        self.zk.add_listener(self.zk_listener)
        self.cache = TreeCache(self.zk, self.base_znode)

    @property
    def base_znode(self):
        return f"{self.zookeeper_root}/{self.cluster_name}"

    @property
    def live_nodes_znode(self):
        return f"{self.base_znode}/live_nodes"

    @property
    def this_node_znode(self):
        return f"{self.base_znode}/live_nodes/{self.hostport}"

    @property
    def collections_znode(self):
        return f"{self.base_znode}/collections"

    def collection_znode(self, collection_name: str) -> str:
        return f"{self.collections_znode}/{collection_name}"

    def shard_znode(self, collection_name: str, shard_name: str = None) -> str:
        znode = f"{self.collections_znode}/{collection_name}/shards"
        if shard_name:
            znode += "/" + shard_name
        return znode

    def replica_znode(
        self, collection_name: str, shard_name: str, hostport: str = None
    ) -> str:
        shard_znode = self.shard_znode(collection_name, shard_name)
        znode = f"{shard_znode}/replicas"
        if hostport:
            znode += "/" + hostport
        return znode

    def startup(self):
        self.zk.start()
        self.cache.start()
        signal.signal(signal.SIGINT, self.signal_listener)
        signal.signal(signal.SIGTERM, self.signal_listener)
        self.zk.ensure_path(self.live_nodes_znode)
        self.zk.ensure_path(self.collections_znode)

    def shutdown(self):
        self.cache.close()
        self.zk.stop()
        self.zk.close()

    def cleanup(self):
        logger.info(f"Removing ZNodes via cleanup")
        transaction = self.zk.transaction()

        for collection in self.list_local_collections():
            for shard in collection.shards:
                for replica in shard.replicas:
                    znode = self.replica_znode(
                        collection.name, shard.name, replica.hostport
                    )
                    transaction.delete(znode)

        self.commit_transaction(transaction)

    def register_merger(self):
        pass

    def register_searcher(self):
        try:
            retrier = KazooRetry(max_tries=5, delay=1, backoff=2, max_delay=20)
            retrier(self.zk.create, self.this_node_znode, ephemeral=True, makepath=True)
            logger.info(f"Created ephemeral ZNode {self.this_node_znode}")
        except kazoo.retry.RetryFailedError:
            logger.error(
                f"Max retries reached for creating ephemeral ZNode {self.this_node_znode}"
            )
        except kazoo.retry.InterruptedError:
            logger.error(
                f"Retries interrupted for creating ephemeral ZNode {self.this_node_znode}"
            )

    def set_state(self, state, collection_name=None, shard_name=None, hostport=None):
        transaction = self.zk.transaction()

        collections = [collection_name] if collection_name else None
        for collection in self._list_collections(
            collections, hostport=hostport, load_replica=True
        ):
            logger.info(
                f"Set {collection.name}/shards ZNodes to {collections_pb2.Replica.State.Name(state)}"
            )
            for shard in collection.shards:
                for replica in shard.replicas:
                    znode = self.replica_znode(
                        collection.name, shard.name, replica.node.hostport
                    )
                    replica.state = state
                    transaction.set_data(znode, replica.SerializeToString())

        return self.commit_transaction(transaction)

    def set_local_state(self, state, collection_name=None, shard_name=None):
        return self.set_state(state, collection_name, shard_name, self.hostport)

    def signal_listener(self, signum, frame):
        self.shutdown()

    def zk_listener(self, state):
        if state == KazooState.LOST:
            logger.warn("Connection to Zookeeper lost")
        elif state == KazooState.SUSPENDED:
            logger.warn("Connection to Zookeeper disconnected")
        else:
            logger.info("Connection to Zookeeper established")

    def add_collections(self, collections):
        """Configure a list of collections into Zookeeper
        """
        transaction = self.zk.transaction()

        for collection in collections:
            collection_copy = deepcopy(collection)
            collection_copy.ClearField("shards")
            collection_znode = self.collection_znode(collection.name)
            transaction.create(collection_znode, collection_copy.SerializeToString())
            transaction.create(self.shard_znode(collection.name))
            for shard in collection.shards:
                shard_copy = deepcopy(shard)
                shard_copy.ClearField("replicas")
                shard_znode = self.shard_znode(collection.name, shard.name)
                transaction.create(shard_znode, shard_copy.SerializeToString())
                transaction.create(self.replica_znode(collection.name, shard.name))
                for replica in shard.replicas:
                    replica_copy = deepcopy(replica)
                    replica_copy.state = collections_pb2.Replica.BOOTING
                    replica_znode = self.replica_znode(
                        collection.name, shard.name, replica.node.hostport
                    )
                    transaction.create(replica_znode, replica_copy.SerializeToString())

        if self.commit_transaction(transaction):
            return collections
        else:
            return []

    def delete_collections(self, collection_names):
        transaction = self.zk.transaction()

        for collection_name in collection_names:
            shards_znode = self.shard_znode(collection_name)
            for shard_name in self.zk.get_children(shards_znode):
                replicas_znode = self.replica_znode(collection_name, shard_name)
                for replica_name in self.zk.get_children(replicas_znode):
                    replica_znode = self.replica_znode(
                        collection_name, shard_name, replica_name
                    )
                    transaction.delete(replica_znode)
                transaction.delete(replicas_znode)
                transaction.delete(self.shard_znode(collection_name, shard_name))
            transaction.delete(shards_znode)
            transaction.delete(self.collection_znode(collection_name))

        if self.commit_transaction(transaction):
            return collection_names
        else:
            return []

    def list_nodes(self):
        live_nodes = self.zk.get_children(self.live_nodes_znode)
        nodes = [collections_pb2.Node(hostport=node) for node in live_nodes]
        return nodes

    def list_collections(self, collection_names=None, include_state=True):
        return self._list_collections(collection_names, load_replica=include_state)

    def list_local_collections(self, include_state=True):
        return self._list_collections(
            hostport=self.hostport, load_replica=include_state
        )

    def _list_collections(
        self,
        collection_names: Optional[List[str]] = None,
        hostport: Optional[str] = None,
        load_replica: Optional[bool] = True,
    ) -> List[collections_pb2.Collection]:
        collections = []

        collection_names = collection_names or self.zk.get_children(
            self.collections_znode
        )
        for collection_name in collection_names:

            shards = []
            shards_znode = self.shard_znode(collection_name)
            for shard_name in self.zk.get_children(shards_znode):

                replicas = []
                replicas_znode = self.replica_znode(collection_name, shard_name)
                for replica_hostport in self.zk.get_children(replicas_znode):
                    if hostport == replica_hostport or hostport is None:
                        replica_znode = self.replica_znode(
                            collection_name, shard_name, replica_hostport
                        )
                        if load_replica:
                            replica_data, _ = self.zk.get(replica_znode)
                            replica_proto = collections_pb2.Replica.FromString(
                                replica_data
                            )
                        else:
                            replica_proto = collections_pb2.Replica()
                        replicas.append(replica_proto)

                if replicas:
                    shard_znode = self.shard_znode(collection_name, shard_name)
                    shard_data, _ = self.zk.get(shard_znode)
                    shard_proto = collections_pb2.Shard.FromString(shard_data)
                    shard_proto.replicas.extend(replicas)
                    shards.append(shard_proto)

            if shards:
                collection_znode = self.collection_znode(collection_name)
                collection_data, _ = self.zk.get(collection_znode)
                collection_proto = collections_pb2.Collection.FromString(
                    collection_data
                )
                collection_proto.shards.extend(shards)
                collections.append(collection_proto)

        return collections

    def get_searchers(self, collection_name, shard_names=None):
        if not shard_names:
            shards_znode = self.shard_znode(collection_name)
            shard_names = self.cache.get_children(shards_znode, [])

        shard_hostports = []
        for shard_name in shard_names:
            hostports = self._get_searchers_for_shard(
                collection_name, shard_name, active=True
            )
            if hostports:
                shard_hostports.append((shard_name, hostports))
            else:
                logger.error(
                    f"No active Searcher node for {collection_name}/{shard_name}."
                )

        return shard_hostports

    def _get_searchers_for_shard(
        self, collection_name: str, shard_name: str, active: bool = True
    ) -> List[str]:
        replicas_znode = self.replica_znode(collection_name, shard_name)
        hostports = self.cache.get_children(replicas_znode, [])

        if active:
            active_hostports = []
            for hostport in hostports:
                replica_znode = self.replica_znode(
                    collection_name, shard_name, hostport
                )
                node = self.cache.get_data(replica_znode)
                if node:
                    replica = collections_pb2.Replica.FromString(node.data)
                    if replica.state == collections_pb2.Replica.ACTIVE:
                        active_hostports.append(hostport)
            hostports = active_hostports

        return hostports

    def commit_transaction(self, transaction: kazoo.client.TransactionRequest) -> bool:
        """Commit a transaction and log the first exception after rollbacks"""
        for result, operation in zip(transaction.commit(), transaction.operations):
            if isinstance(result, kazoo.exceptions.RolledBackError):
                continue
            elif isinstance(result, Exception):
                logger.error(
                    f"{result.__class__.__name__} in Kazoo transaction: {operation}"
                )
                return False
        return True
