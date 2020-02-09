import logging
from typing import Dict

import grpc

from needlestack.apis import collections_pb2
from needlestack.apis import servicers_pb2
from needlestack.apis import servicers_pb2_grpc
from needlestack.apis import serializers
from needlestack.collections.collection import Collection
from needlestack.collections.shard import Shard
from needlestack.cluster_managers import ClusterManager
from needlestack.servicers.settings import BaseConfig
from needlestack.utilities.rpc import unhandled_exception_rpc


logger = logging.getLogger("needlestack")


class SearcherServicer(servicers_pb2_grpc.SearcherServicer):
    """A gRPC servicer to perform kNN queries on in-memory index structures"""

    collections: Dict[str, Collection]
    collection_protos: Dict[str, collections_pb2.Collection]

    def __init__(self, config: BaseConfig, cluster_manager: ClusterManager):
        self.config = config
        self.cluster_manager = cluster_manager
        self.collections = {}
        self.collection_protos = {}
        self.cluster_manager.register_searcher()
        self.load_collections()

    @unhandled_exception_rpc(servicers_pb2.SearchResponse)
    def Search(self, request, context):
        X = serializers.proto_to_ndarray(request.vector)
        k = request.count
        collection = self.get_collection(request.collection_name)

        if len(X.shape) == 1:
            X = X.reshape(1, -1)

        if collection.dimension == X.shape[1]:
            results = collection.query(X, k, request.shard_names)
            items = [item for i, item in enumerate(results) if i < k]
            return servicers_pb2.SearchResponse(items=items)
        else:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(
                f"Collection {collection.name} expected matrix shaped ({collection.dimension}), got {X.shape}"
            )
            return servicers_pb2.SearchResponse()

    @unhandled_exception_rpc(servicers_pb2.RetrieveResponse)
    def Retrieve(self, request, context):
        collection = self.get_collection(request.collection_name)
        item = collection.retrieve(request.id, request.shard_names)
        if item is not None:
            return servicers_pb2.RetrieveResponse(item=item)
        else:
            return servicers_pb2.RetrieveResponse()

    @unhandled_exception_rpc(collections_pb2.CollectionsLoadResponse)
    def CollectionsLoad(self, request, context):
        self.load_collections()
        return collections_pb2.CollectionsLoadResponse()

    def get_collection(self, name: str) -> Collection:
        return self.collections[name]

    def load_collections(self):
        """Load collections from Zookeeper configs

        There are 4 states to handle for each collection:
            - A new collection needs to be loaded
            - An existing collection needs to be dropped
            - An existing collection added/dropped shards
            - No changes
        """
        collection_protos = self.cluster_manager.list_local_collections(
            include_state=False
        )
        current_collections = {name for name in self.collection_protos.keys()}
        new_collections = {proto.name for proto in collection_protos}
        for proto in collection_protos:
            if proto.name in current_collections:
                self._modify_collection(proto)
            else:
                self._add_collection(proto)
        for name in current_collections:
            if name not in new_collections:
                self._drop_collection(name)
        for collection in self.collections.values():
            if collection.update_available():
                logger.debug(f"Update collection {collection.name}")
                self.cluster_manager.set_local_state(
                    collections_pb2.Replica.BOOTING, collection.name
                )
                collection.load()
                self.cluster_manager.set_local_state(
                    collections_pb2.Replica.ACTIVE, collection.name
                )
        self.collection_protos = {proto.name: proto for proto in collection_protos}

    def _add_collection(self, proto: collections_pb2.Collection):
        logger.debug(f"Add collection {proto.name}")
        collection = Collection.from_proto(proto)
        self.cluster_manager.set_local_state(
            collections_pb2.Replica.BOOTING, collection.name
        )
        self.collections[collection.name] = collection
        collection.load()
        self.cluster_manager.set_local_state(
            collections_pb2.Replica.ACTIVE, collection.name
        )

    def _drop_collection(self, name: str):
        logger.debug(f"Drop collection {name}")
        del self.collections[name]

    def _modify_collection(self, proto: collections_pb2.Collection):
        old_proto = self.collection_protos[proto.name]
        if old_proto.SerializeToString() != proto.SerializeToString():
            collection = self.get_collection(proto.name)
            collection.merge_proto(proto)

            old_shards = {shard.name: shard for shard in old_proto.shards}
            new_shards = {shard.name: shard for shard in proto.shards}

            for name, new_shard in new_shards.items():
                if name not in old_shards:
                    logger.debug(f"Add collection shard {proto.name}/{name}")
                    self.cluster_manager.set_local_state(
                        collections_pb2.Replica.BOOTING, collection.name, name
                    )
                    collection.add_shard(Shard.from_proto(new_shard))
                elif (
                    new_shard.SerializeToString()
                    != old_shards[name].SerializeToString()
                ):
                    logger.debug(f"Update collection shard {proto.name}/{name}")
                    self.cluster_manager.set_local_state(
                        collections_pb2.Replica.BOOTING, collection.name, name
                    )
                    collection.drop_shard(name)
                    collection.add_shard(Shard.from_proto(new_shard))

            for name in old_shards.keys():
                if name not in new_shards:
                    logger.debug(f"Drop collection shard {proto.name}/{name}")
                    collection.drop_shard(name)

            collection.load()
            self.cluster_manager.set_local_state(
                collections_pb2.Replica.ACTIVE, collection.name, name
            )
