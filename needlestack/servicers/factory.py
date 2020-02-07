import os
import logging
import time
from concurrent import futures

import grpc
from grpc._server import _Server

from needlestack.servicers.settings import BaseConfig
from needlestack.servicers.logging import configure_logger
from needlestack.cluster_managers.manager import ClusterManager

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

logger = logging.getLogger("needlestack")


def create_server(config: BaseConfig) -> _Server:
    """Create a gRPC server app with a health servicer.

    Args:
        config: Config with settings on how to setup the server
    """
    configure_logger(config)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=config.MAX_WORKERS))
    if config.use_ssl:
        server.add_secure_port(
            f"[::]:{config.SERVICER_PORT}", config.ssl_server_credentials
        )
    else:
        server.add_insecure_port(f"[::]:{config.SERVICER_PORT}")
    return server


def create_zookeeper_cluster_manager(config: BaseConfig) -> ClusterManager:
    """Create a Zookeeper client for cluster managment.

    Args:
        config: Config with settings on how to set up a Zookeeper client
    """
    from needlestack.cluster_managers.zookeeper import ZookeeperClusterManager

    return ZookeeperClusterManager(
        config.CLUSTER_NAME,
        config.hostport,
        config.ZOOKEEPER_HOSTS,
        config.ZOOKEEPER_ROOT,
    )


def serve(server: _Server):
    server.start()
    logger.info(f"Started gRPC server on {os.getpid()}")
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        logger.info(f"Stopped gRPC server on {os.getpid()}")
        server.stop(0)
