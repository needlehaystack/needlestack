import logging
import signal
import time
from copy import deepcopy
from typing import List

from kazoo.exceptions import NodeExistsError
from kazoo.client import KazooClient, KazooState
from kazoo.recipe.cache import TreeCache

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

    ACTIVE = collections_pb2.Node.State.ACTIVE
    DOWN = collections_pb2.Node.State.DOWN
    BOOTING = collections_pb2.Node.State.BOOTING
    RECOVERING = collections_pb2.Node.State.RECOVERING

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
        self.zk.start()
        self.cache = TreeCache(self.zk, self.base_znode)
        self.cache.start()
        signal.signal(signal.SIGINT, self.signal_listener)
        signal.signal(signal.SIGTERM, self.signal_listener)

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

    def up(self):
        for i in range(5):
            try:
                self.zk.create(self.this_node_znode, ephemeral=True, makepath=True)
                logger.info(f"Created ephemeral ZNode {self.this_node_znode}")
                return
            except NodeExistsError:
                logger.warn(
                    f"Ephemeral ZNode {self.this_node_znode} already exists, waiting 5 seconds."
                )
                time.sleep(5)
        logger.error(f"Could not created ephemeral ZNode {self.this_node_znode}")

    def active(self):
        for znode in self._list_local_replica_znodes():
            self.zk.set(znode, self.ACTIVE)
            logger.info(f"Set ZNode {znode} active")

    def down(self):
        for znode in self._list_local_replica_znodes():
            self.zk.set(znode, self.DOWN)
            logger.info(f"Set ZNode {znode} down")

    def clean(self):
        logger.info(f"Removing ZNodes via clean")
        for znode in self._list_local_replica_znodes():
            self.zk.delete(znode)
            logger.info(f"Removed ZNode {znode}")

    def close(self):
        self.cache.close()
        self.zk.stop()
        self.zk.close()

    def signal_listener(self, signum, frame):
        self.down()
        self.close()

    def zk_listener(self, state):
        if state == KazooState.LOST:
            logger.warn("Connection to Zookeeper lost")
        elif state == KazooState.SUSPENDED:
            logger.warn("Connection to Zookeeper disconnected")
        else:
            logger.info("Connection to Zookeeper established")

    def add_collections(self, collections):
        """Configure a list of collections into Zookeeper

        TODO: Make operations in a transaction.
        """
        transaction = self.zk.transaction()

        for collection in collections:
            collection_copy = deepcopy(collection)
            collection_copy.ClearField("shards")
            collection_znode = self.collection_znode(collection.name)
            transaction.create(collection_znode, collection_copy.SerializeToString())
            for shard in collection.shards:
                shard_copy = deepcopy(shard)
                shard_copy.ClearField("replicas")
                shard_znode = self.shard_znode(collection.name, shard.name)
                transaction.create(shard_znode, shard_copy.SerializeToString())
                for replica in shard.replicas:
                    replica_znode = self.replica_znode(
                        collection.name, shard.name, replica.hostport
                    )
                    transaction.create(replica_znode, self.BOOTING)

        results = transaction.commit()
        logger.info(results)
        return collections

    def delete_collections(self, collection_names):
        for collection_name in collection_names:
            collection_znode = self.collection_znode(collection_name)
            self.zk.delete(collection_znode, recursive=True)
        return collection_names

    def list_nodes(self):
        live_nodes = self.zk.get_children(self.live_nodes_znode)
        nodes = [collections_pb2.Node(hostport=node) for node in live_nodes]
        return nodes

    def list_collections(self, collection_names=None):
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
                for hostport in self.zk.get_children(replicas_znode):
                    replica_znode = self.replica_znode(
                        collection_name, shard_name, hostport
                    )
                    state, _ = self.zk.get(replica_znode)
                    node_proto = collections_pb2.Node(hostport=hostport, state=state)
                    replicas.append(node_proto)

                shard_znode = self.shard_znode(collection_name, shard_name)
                shard_data, _ = self.zk.get(shard_znode)
                shard_proto = collections_pb2.Shard.FromString(shard_data)
                shard_proto.replicas.extend(replicas)
                shards.append(shard_proto)

            collection_znode = self.collection_znode(collection_name)
            collection_data, _ = self.zk.get(collection_znode)
            collection_proto = collections_pb2.Collection.FromString(collection_data)
            collection_proto.shards.extend(shards)
            collections.append(collection_proto)

        return collections

    def list_local_collections(self):
        collections = []

        for collection_name in self.zk.get_children(self.collections_znode):

            shards = []
            shards_znode = self.shard_znode(collection_name)
            for shard_name in self.zk.get_children(shards_znode):

                replicas = []
                replicas_znode = self.replica_znode(collection_name, shard_name)
                for hostport in self.zk.get_children(replicas_znode):
                    if hostport == self.hostport:
                        replica_znode = self.replica_znode(
                            collection_name, shard_name, hostport
                        )
                        state, _ = self.zk.get(replica_znode)
                        node_proto = collections_pb2.Node(
                            hostport=hostport, state=state
                        )
                        replicas.append(node_proto)

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
                if node and node.data == self.ACTIVE:
                    active_hostports.append(hostport)
            hostports = active_hostports

        return hostports

    def _list_local_replica_znodes(self):
        znodes = []
        for collection in self.list_local_collections():
            for shard in collection.shards:
                for replica in shard.replicas:
                    znode = self.replica_znode(
                        collection.name, shard.name, replica.hostport
                    )
                    znodes.append(znode)
        return znodes
