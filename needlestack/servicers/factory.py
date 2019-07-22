import os
import logging
import time
from concurrent import futures

import grpc
from grpc._server import _Server

from needlestack.apis import health_pb2_grpc
from needlestack.apis import servicers_pb2_grpc
from needlestack.servicers.health import HealthServicer
from needlestack.servicers.merger import MergerServicer
from needlestack.servicers.searcher import SearcherServicer
from needlestack.servicers.settings import BaseConfig
from needlestack.servicers.logging import configure_logger
from needlestack.cluster_managers.zookeeper import ZookeeperClusterManager

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

logger = logging.getLogger("needlestack")


def create_server(config: BaseConfig) -> _Server:
    """Create a gRPC server app with a health servicer.

    Args:
        config: Config with settings on how to setup the server
    """
    configure_logger(config)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=config.MAX_WORKERS))
    server.add_insecure_port(f"[::]:{config.SERVICER_PORT}")
    health_pb2_grpc.add_HealthServicer_to_server(HealthServicer(), server)
    return server


def create_zookeeper_client(config: BaseConfig) -> ZookeeperClusterManager:
    """Create a Zookeeper client for cluster managment.

    Args:
        config: Config with settings on how to set up a Zookeeper client
    """
    return ZookeeperClusterManager(
        config.CLUSTER_NAME, config.HOSTPORT, config.ZOOKEEPER_HOSTS
    )


def get_merger_servicer(server: _Server, zk: ZookeeperClusterManager) -> MergerServicer:
    """"""
    servicer = MergerServicer(zk)
    servicers_pb2_grpc.add_MergerServicer_to_server(servicer, server)
    return servicer


def get_searcher_servicer(
    server: _Server, zk: ZookeeperClusterManager
) -> SearcherServicer:
    servicer = SearcherServicer(zk)
    servicers_pb2_grpc.add_SearcherServicer_to_server(servicer, server)
    return servicer


def serve(server: _Server):
    server.start()
    logger.warning(f"Started gRPC server on {os.getpid()}")
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        logger.warning(f"Stopped gRPC server on {os.getpid()}")
        server.stop(0)
