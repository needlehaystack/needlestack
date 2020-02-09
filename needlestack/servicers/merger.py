import logging
import random
import heapq
from typing import List, Tuple, Dict

import grpc

from needlestack.apis import clients
from needlestack.apis import collections_pb2
from needlestack.apis import servicers_pb2
from needlestack.apis import servicers_pb2_grpc
from needlestack.balancers import calculate_add
from needlestack.balancers.greedy import GreedyAlgorithm
from needlestack.cluster_managers import ClusterManager
from needlestack.servicers.settings import BaseConfig
from needlestack.utilities.rpc import unhandled_exception_rpc

logger = logging.getLogger("needlestack")


class MergerServicer(servicers_pb2_grpc.MergerServicer):
    """A gRPC servicer to accept external requests, use searcher nodes, and
    merge results together."""

    def __init__(self, config: BaseConfig, cluster_manager: ClusterManager):
        self.config = config
        self.cluster_manager = cluster_manager
        self.cluster_manager.register_merger()

    @unhandled_exception_rpc(servicers_pb2.SearchResponse)
    def Search(self, request, context):

        hostports_shards = self.get_searcher_hostports(
            request.collection_name, list(request.shard_names)
        )

        futures = []
        for hostport, shard_names in hostports_shards:
            stub = clients.get_searcher_stub(
                hostport, self.config.SERVICER_SSL_CERT_CHAIN_FILE
            )
            subrequest = servicers_pb2.SearchRequest(
                vector=request.vector,
                count=request.count,
                collection_name=request.collection_name,
                shard_names=shard_names,
            )
            future = stub.Search.future(subrequest)
            futures.append(future)

        subsearch_results = [future.result() for future in futures]

        num_subsearch = len(subsearch_results)
        if num_subsearch > 1:
            item_batches = [result.items for result in subsearch_results]
            merged_item_batches = heapq.merge(
                *item_batches, key=lambda x: x.float_distance or x.double_distance
            )
            items = [
                item for i, item in enumerate(merged_item_batches) if i < request.count
            ]
            return servicers_pb2.SearchResponse(items=items)
        elif num_subsearch == 1:
            return subsearch_results[0]
        else:
            context.set_code(grpc.StatusCode.UNKNOWN)
            context.set_details("Empty responses from Search")
            return servicers_pb2.SearchResponse()

    @unhandled_exception_rpc(servicers_pb2.RetrieveResponse)
    def Retrieve(self, request, context):
        hostports_shards = self.get_searcher_hostports(
            request.collection_name, list(request.shard_names)
        )

        futures = []
        for hostport, shard_names in hostports_shards:
            stub = clients.get_searcher_stub(
                hostport, self.config.SERVICER_SSL_CERT_CHAIN_FILE
            )
            subrequest = servicers_pb2.RetrieveRequest(
                id=request.id,
                collection_name=request.collection_name,
                shard_names=shard_names,
            )
            future = stub.Retrieve.future(subrequest)
            futures.append(future)

        for future in futures:
            result = future.result()
            if result.item.metadata.id:
                return result

        context.set_code(grpc.StatusCode.NOT_FOUND)
        context.set_details("ID not found in collection")
        return servicers_pb2.RetrieveResponse()

    @unhandled_exception_rpc(collections_pb2.CollectionsAddResponse)
    def CollectionsAdd(self, request, context):
        new_collections = request.collections
        current_collections = self.cluster_manager.list_collections()

        new_names = {c.name for c in new_collections}
        current_names = {c.name for c in current_collections}
        if new_names & current_names:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details(
                f"Collections {new_names & current_names} already exists. No new collections added."
            )
            return collections_pb2.CollectionsAddResponse(success=False)

        nodes = self.cluster_manager.list_nodes()
        algorithm = GreedyAlgorithm()
        collections_to_add = calculate_add(
            nodes, current_collections, new_collections, algorithm
        )
        success = True

        if not request.noop:
            self.cluster_manager.add_collections(collections_to_add)
            success = self.collections_load()

        return collections_pb2.CollectionsAddResponse(
            collections=collections_to_add, success=success
        )

    @unhandled_exception_rpc(collections_pb2.CollectionsDeleteResponse)
    def CollectionsDelete(self, request, context):
        collection_names = request.names
        success = True

        new_names = set(collection_names)
        current_names = {
            collection.name for collection in self.cluster_manager.list_collections()
        }
        if not new_names <= current_names:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(
                f"Collections {new_names - current_names} do not exists"
            )
            return collections_pb2.CollectionsDeleteResponse()

        if not request.noop:
            self.cluster_manager.delete_collections(collection_names)
            success = self.collections_load()

        return collections_pb2.CollectionsDeleteResponse(
            names=collection_names, success=success
        )

    @unhandled_exception_rpc(collections_pb2.CollectionsLoadResponse)
    def CollectionsLoad(self, request, context):
        success = self.collections_load()
        return collections_pb2.CollectionsLoadResponse(success=success)

    @unhandled_exception_rpc(collections_pb2.CollectionsListResponse)
    def CollectionsList(self, request, context):
        collection_names = list(request.names)
        collections = self.cluster_manager.list_collections(collection_names)
        return collections_pb2.CollectionsListResponse(collections=collections)

    def collections_load(self) -> bool:
        success = True
        futures = []
        nodes = self.cluster_manager.list_nodes()
        for node in nodes:
            stub = clients.get_searcher_stub(
                node.hostport, self.config.SERVICER_SSL_CERT_CHAIN_FILE
            )
            subrequest = collections_pb2.CollectionsLoadRequest()
            future = stub.CollectionsLoad.future(subrequest)
            futures.append((node.hostport, future))

        for hostport, future in futures:
            try:
                result = future.result()
                success = success and result.success
            except grpc.RpcError as e:
                success = False
                logger.error(f"Searcher {hostport} failed CollectionsLoadRequest: {e}")

        return success

    def get_searcher_hostports(
        self, collection_name: str, shard_names: List[str] = None
    ) -> List[Tuple[str, List[str]]]:
        shard_hostports = self.cluster_manager.get_searchers(
            collection_name, shard_names
        )

        shard_to_host = {}
        for shard_name, hostports in shard_hostports:
            shard_to_host[shard_name] = random.choice(hostports)

        host_to_shards: Dict[str, List] = {}
        for shard_name, hostport in shard_to_host.items():
            host_to_shards[hostport] = host_to_shards.get(hostport, [])
            host_to_shards[hostport].append(shard_name)

        return list(host_to_shards.items())
