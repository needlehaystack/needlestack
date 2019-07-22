import logging
import random
import heapq
from typing import List, Tuple, Dict

import grpc

from needlestack.apis import clients
from needlestack.apis import collections_pb2
from needlestack.apis import servicers_pb2
from needlestack.apis import servicers_pb2_grpc
from needlestack.balancers import balance
from needlestack.balancers import greedy
from needlestack.cluster_managers import ClusterManager
from needlestack.servicers.decorators import unhandled_exception_rpc

logger = logging.getLogger("needlestack")


class MergerServicer(servicers_pb2_grpc.MergerServicer):
    """A gRPC servicer to accept external requests, use searcher nodes, and
    merge results together."""

    def __init__(self, cluster_manager: ClusterManager):
        self.cluster_manager = cluster_manager

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
        for shard, host in shard_to_host.items():
            host_to_shards[host] = host_to_shards.get(host, [])
            host_to_shards[host].append(shard)

        return list(host_to_shards.items())

    @unhandled_exception_rpc(servicers_pb2.SearchResponse)
    def Search(self, request, context):

        hostports_shards = self.get_searcher_hostports(
            request.collection_name, list(request.shard_names)
        )

        futures = []
        for hostport, shard_names in hostports_shards:
            stub = clients.get_searcher_stub(hostport)
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
            headers = subsearch_results[0].headers
            return servicers_pb2.SearchResponse(items=items, headers=headers)
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
            stub = clients.get_searcher_stub(hostport)
            subrequest = servicers_pb2.RetrieveRequest(
                id=request.id,
                collection_name=request.collection_name,
                shard_names=shard_names,
            )
            future = stub.Retrieve.future(subrequest)
            futures.append(future)

        for future in futures:
            result = future.result()
            if result.id != "":
                return result

        context.set_code(grpc.StatusCode.NOT_FOUND)
        context.set_details("ID not found in collection")
        return servicers_pb2.RetrieveResponse()

    @unhandled_exception_rpc(collections_pb2.CollectionConfigurationResponse)
    def CollectionConfiguration(self, request, context):
        collections = request.collections
        nodes = self.cluster_manager.get_live_nodes()
        balance(collections, nodes, greedy.solver)

        if not request.noop:
            self.cluster_manager.register_collections(collections)

            futures = []
            for node in nodes:
                stub = clients.get_searcher_stub(node.hostport)
                subrequest = collections_pb2.CollectionLoadRequest()
                future = stub.CollectionLoad.future(subrequest)
                futures.append((node.hostport, future))

            for hostport, future in futures:
                try:
                    future.result()
                except grpc.RpcError as e:
                    logger.error(f"Searcher {hostport} failed to load collections: {e}")

        return collections_pb2.CollectionConfigurationResponse(collections=collections)

    @unhandled_exception_rpc(collections_pb2.CollectionsResponse)
    def GetCollections(self, request, context):
        collection_names = list(request.names)
        collections = self.cluster_manager.get_collections(collection_names)
        return collections_pb2.CollectionsResponse(collections=collections)
