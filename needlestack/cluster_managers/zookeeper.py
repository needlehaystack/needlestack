import os
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

    ACTIVE = b"ACTIVE"
    DOWN = b"DOWN"
    BOOTING = b"BOOTING"

    cluster_name: str
    hostport: str
    zk: KazooClient
    cache: TreeCache

    def __init__(self, cluster_name: str, hostport: str, hosts: List[str]):
        self.cluster_name = cluster_name
        self.hostport = hostport
        self.zk = KazooClient(hosts=hosts)
        self.zk.add_listener(self.listener)
        self.zk.start()
        self.cache = TreeCache(self.zk, self.base_znode)
        self.cache.start()
        signal.signal(signal.SIGINT, self.signal_listener)
        signal.signal(signal.SIGTERM, self.signal_listener)

    @property
    def base_znode(self):
        return f"/needlestack/{self.cluster_name}"

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
        for i in range(3):
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
        for znode in self.local_replicas():
            self.zk.set(znode, self.ACTIVE)
            logger.info(f"Set ZNode {znode} active")

    def down(self):
        for znode in self.local_replicas():
            self.zk.set(znode, self.DOWN)
            logger.info(f"Set ZNode {znode} down")

    def clean(self):
        logger.info(f"Removing ZNodes via clean")
        for znode in self.local_replicas():
            self.zk.delete(znode)
            logger.info(f"Removed ZNode {znode}")

    def register_collections(self, collections: List[collections_pb2.Collection]):
        """Configure a list of collections into Zookeeper

        TODO: Make operations in a transaction.
        """
        self.zk.delete(self.collections_znode, recursive=True)

        for collection in collections:
            for shard in collection.shards:
                for replica in shard.replicas:
                    replica_znode = self.replica_znode(
                        collection.name, shard.name, replica.hostport
                    )
                    self.zk.ensure_path(replica_znode)
                    self.zk.set(replica_znode, self.BOOTING)
                    logger.info(f"Created ZNode {replica_znode}")

        for collection in collections:
            collection_proto = deepcopy(collection)
            collection_proto.ClearField("shards")
            collection_znode = self.collection_znode(collection.name)
            self.zk.set(collection_znode, collection_proto.SerializeToString())
            for shard in collection.shards:
                shard_proto = deepcopy(shard)
                shard_proto.ClearField("replicas")
                shard_znode = self.shard_znode(collection.name, shard.name)
                self.zk.set(shard_znode, shard_proto.SerializeToString())

    def get_collections_to_load(self):
        collections = {}
        for znode in self.local_replicas():
            shard_znode = os.path.dirname(os.path.dirname(znode))
            collection_znode = os.path.dirname(os.path.dirname(shard_znode))
            shard_node = self.zk.get(shard_znode)
            collection_node = self.zk.get(collection_znode)

            collection = collections_pb2.Collection.FromString(collection_node[0])
            shard = collections_pb2.Shard.FromString(shard_node[0])

            collections[collection.name] = collections.get(collection.name, collection)
            collections[collection.name].shards.extend([shard])

        return list(collections.values())

    def get_searchers(self, collection_name, shard_names=None):
        if not shard_names:
            shards_znode = self.shard_znode(collection_name)
            shard_names = self.cache.get_children(shards_znode, [])

        shard_hostports = []
        for shard_name in shard_names:
            hostports = self.get_searchers_for_shard_name(
                collection_name, shard_name, active=True
            )
            if hostports:
                shard_hostports.append((shard_name, hostports))
            else:
                logger.error(f"{collection_name}/{shard_name} no active host.")

        return shard_hostports

    def get_searchers_for_shard_name(
        self, collection_name: str, shard_name: str, active: bool = True
    ):
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

    def get_live_nodes(self):
        live_nodes = self.zk.get_children(self.live_nodes_znode)
        nodes = [collections_pb2.Node(hostport=node) for node in live_nodes]
        return nodes

    def get_collections(self, collection_names):
        collections = []

        collection_names = collection_names or self.cache.get_children(
            self.collections_znode, []
        )
        for collection_name in collection_names:
            collection_znode = self.collection_znode(collection_name)
            collection_node = self.cache.get_data(collection_znode)
            collection = collections_pb2.Collection.FromString(collection_node.data)

            shards = []
            shards_znode = self.shard_znode(collection_name)
            for shard_name in self.cache.get_children(shards_znode, []):
                shard_znode = self.shard_znode(collection_name, shard_name)
                shard_node = self.cache.get_data(shard_znode)
                shard_proto = collections_pb2.Shard.FromString(shard_node.data)

                replicas_znode = self.replica_znode(collection_name, shard_name)
                hostports = self.cache.get_children(replicas_znode, [])
                replicas = [
                    collections_pb2.Node(hostport=hostport) for hostport in hostports
                ]
                shard_proto.replicas.extend(replicas)

                shards.append(shard_proto)

            collection.shards.extend(shards)
            collections.append(collection)

        return collections

    def local_replicas(self, cached: bool = False) -> List[str]:
        if cached:
            client = self.cache
        elif self.zk.exists(self.collections_znode):
            client = self.zk
        else:
            return []

        replicas = []
        for collection_name in client.get_children(self.collections_znode):
            shards_znode = self.shard_znode(collection_name)
            for shard_name in client.get_children(shards_znode):
                replicas_znode = self.replica_znode(collection_name, shard_name)
                for hostport in client.get_children(replicas_znode):
                    if hostport == self.hostport:
                        replica_znode = self.replica_znode(
                            collection_name, shard_name, hostport
                        )
                        replicas.append(replica_znode)
        return replicas

    def listener(self, state):
        if state == KazooState.LOST:
            logger.warn("Connection to Zookeeper lost")
        elif state == KazooState.SUSPENDED:
            logger.warn("Connection to Zookeeper disconnected")
        else:
            logger.info("Connection to Zookeeper established")

    def close(self):
        self.cache.close()
        self.zk.stop()
        self.zk.close()

    def signal_listener(self, signum, frame):
        self.down()
        self.close()
