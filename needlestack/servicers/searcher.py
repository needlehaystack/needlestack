import logging
from typing import Dict

import grpc

from needlestack.apis import collections_pb2
from needlestack.apis import servicers_pb2
from needlestack.apis import servicers_pb2_grpc
from needlestack.apis import serializers
from needlestack.servicers import protos
from needlestack.collections.collection import Collection
from needlestack.cluster_managers import ClusterManager
from needlestack.servicers.decorators import unhandled_exception_rpc


logger = logging.getLogger("needlestack")


class SearcherServicer(servicers_pb2_grpc.SearcherServicer):
    """A gRPC servicer to perform kNN queries on in-memory index structures"""

    collections: Dict[str, Collection]

    def __init__(self, cluster_manager: ClusterManager):
        self.cluster_manager = cluster_manager
        self.collections = {}
        self.cluster_manager.up()
        self.load_collections()

    def get_collection(self, name: str) -> Collection:
        return self.collections[name]

    def load_collections(self):
        collection_protos = self.cluster_manager.get_collections_to_load()
        for proto in collection_protos:
            collection = Collection.from_proto(proto)
            self.collections[collection.name] = collection
            collection.load()

        self.cluster_manager.active()

    @unhandled_exception_rpc(servicers_pb2.SearchResponse)
    def Search(self, request, context):
        X = serializers.proto_to_ndarray(request.vector)
        k = request.count
        collection = self.get_collection(request.collection_name)

        if len(X.shape) == 1:
            X = X.reshape(1, -1)

        if collection.dimension == X.shape[1]:
            results = collection.query(X, k, request.shard_names)
            items = [
                protos.create_result_item(dist, metadata)
                for i, (dist, metadata) in enumerate(results)
                if i < k
            ]
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
        vector, metadata = collection.get_vector_and_metadata(
            request.id, request.shard_names
        )
        if vector is not None:
            return protos.create_retrieval_item(vector, metadata)
        else:
            return servicers_pb2.RetrieveResponse()

    @unhandled_exception_rpc(collections_pb2.CollectionLoadResponse)
    def CollectionLoad(self, request, context):
        self.load_collections()
        return collections_pb2.CollectionLoadResponse()
