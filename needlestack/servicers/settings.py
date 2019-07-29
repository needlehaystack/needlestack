import socket
from typing import List, Optional


class BaseConfig(object):
    """Base configuration for gRPC services

    Attributes:
        DEBUG: Attach a stream handler to console for logger
        LOG_LEVEL: Level for logger
        LOG_FORMAT_DATE: Format string for date
        DEBUG_LOG_FORMAT: Format string for debug logger
        FILE_LOG_FORMAT: Format string for file logger
        LOG_FILE: Filepath to log file
        LOG_FILE_MAX_BYTES: Max byte size for log file
        LOG_FILE_BACKUPS: Number of log files to keep in rotation
        MAX_WORKERS: Number of worker threads per gRPC server
        HOSTNAME: Hostname of node
        SERVICER_PORT: Port of gRPC server
        CLUSTER_NAME: Name for Needlestack cluster
        HOSTPORT: Hostport to gRPC server
        ZOOKEEPER_HOSTS: List of Zookeeper host for cluster manager
    """

    DEBUG = False

    LOG_LEVEL = "WARNING"

    LOG_FORMAT_DATE = "%Y-%m-%d %H:%M:%S"
    DEBUG_LOG_FORMAT = (
        "%(asctime)s [%(name)s] [%(threadName)-10s] [%(levelname)s] - %(message)s"
    )
    FILE_LOG_FORMAT = "%(asctime)s [%(name)s] [%(thread)d] [%(process)d] [%(levelname)s] - %(message)s"

    LOG_FILE: Optional[str] = None
    LOG_FILE_MAX_BYTES: int
    LOG_FILE_BACKUPS: int

    MAX_WORKERS: int
    HOSTNAME: str
    SERVICER_PORT: int

    CLUSTER_NAME: str
    HOSTPORT: str

    ZOOKEEPER_HOSTS: List[str]


class LocalDockerConfig(BaseConfig):
    """Configs for local development environment"""

    DEBUG = True

    LOG_LEVEL = "DEBUG"

    LOG_FILE = "/var/log/needlestack.log"
    LOG_FILE_MAX_BYTES = 1 * 1024 ** 2  # 1 MB
    LOG_FILE_BACKUPS = 10

    MAX_WORKERS = 10
    HOSTNAME = socket.gethostname()
    SERVICER_PORT = 50051

    CLUSTER_NAME = "my_needlstack"
    HOSTPORT = f"{HOSTNAME}:{SERVICER_PORT}"

    ZOOKEEPER_HOSTS = ["zoo1:2181", "zoo2:2181", "zoo3:2181"]


class TestDockerConfig(BaseConfig):
    """Configs for local test environment"""

    DEBUG = True

    LOG_LEVEL = "DEBUG"

    LOG_FILE = "/tmp/needlestack.log"
    LOG_FILE_MAX_BYTES = 1 * 1024 ** 2  # 1 MB
    LOG_FILE_BACKUPS = 2

    MAX_WORKERS = 4
    HOSTNAME = socket.gethostname()
    SERVICER_PORT = 50051

    CLUSTER_NAME = "test_needlstack"
    HOSTPORT = f"{HOSTNAME}:{SERVICER_PORT}"

    ZOOKEEPER_HOSTS = ["zoo1:2181", "zoo2:2181", "zoo3:2181"]
