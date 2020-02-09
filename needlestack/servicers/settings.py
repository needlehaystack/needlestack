import socket
from typing import List, Optional

import grpc


class BaseConfig(object):
    """Base configuration for gRPC services

    Attributes:
        DEBUG: Attach a stream handler to console for logger
        DEBUG_LOG_FORMAT: Format string for debug logger
        LOG_LEVEL: Level for logger
        LOG_FORMAT_DATE: Format string for date
        LOG_FILE: Filepath to log file
        LOG_FILE_BACKUPS: Number of log files to keep in rotation
        LOG_FILE_LOG_FORMAT: Format string for file logger
        LOG_FILE_MAX_BYTES: Max byte size for log file
        MAX_WORKERS: Number of worker threads per gRPC server
        HOSTNAME: Hostname of node
        SERVICER_PORT: Port of gRPC server
        SERVICER_SSL_PRIVATE_KEY_FILE: SSL private key file
        SERVICER_SSL_CERT_CHAIN_FILE: SSL certificate chain file
        CLUSTER_NAME: Name for Needlestack cluster
        ZOOKEEPER_HOSTS: List of Zookeeper host for cluster manager
        hostport: Hostport to gRPC server
        use_ssl: Should SSL be used
        ssl_server_credentials: gRPC SSL server credentials
    """

    DEBUG = False
    DEBUG_LOG_FORMAT = (
        "%(asctime)s [%(name)s] [%(threadName)-10s] [%(levelname)s] - %(message)s"
    )

    LOG_LEVEL = "WARNING"
    LOG_FORMAT_DATE = "%Y-%m-%d %H:%M:%S"

    LOG_FILE: Optional[str] = None
    LOG_FILE_BACKUPS: int
    LOG_FILE_LOG_FORMAT = "%(asctime)s [%(name)s] [%(thread)d] [%(process)d] [%(levelname)s] - %(message)s"
    LOG_FILE_MAX_BYTES: int

    MAX_WORKERS: int
    HOSTNAME: str
    SERVICER_PORT: int
    SERVICER_SSL_PRIVATE_KEY_FILE: Optional[str] = None
    SERVICER_SSL_CERT_CHAIN_FILE: Optional[str] = None

    CLUSTER_NAME: str
    HOSTPORT: str

    ZOOKEEPER_ROOT = "/needlestack"
    ZOOKEEPER_HOSTS: List[str]

    @property
    def hostport(self):
        return f"{self.HOSTNAME}:{self.SERVICER_PORT}"

    @property
    def use_ssl(self):
        return (
            self.SERVICER_SSL_PRIVATE_KEY_FILE is not None
            and self.SERVICER_SSL_CERT_CHAIN_FILE is not None
        )

    @property
    def ssl_server_credentials(self):
        if self.use_ssl:
            with open(self.SERVICER_SSL_PRIVATE_KEY_FILE, "rb") as f:
                private_key = f.read()
            with open(self.SERVICER_SSL_CERT_CHAIN_FILE, "rb") as f:
                certificate_chain = f.read()
            return grpc.ssl_server_credentials([(private_key, certificate_chain)])
        else:
            return None


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

    CLUSTER_NAME = "my_needlestack"

    ZOOKEEPER_HOSTS = ["zoo1:2181", "zoo2:2181", "zoo3:2181"]


class TestDockerConfig(BaseConfig):
    """Configs for local test environment"""

    DEBUG = True

    LOG_LEVEL = "DEBUG"

    LOG_FILE = "/tmp/needlestack.log"
    LOG_FILE_MAX_BYTES = 1 * 1024 ** 2  # 1 MB
    LOG_FILE_BACKUPS = 2

    MAX_WORKERS = 4
    HOSTNAME = "localhost"
    SERVICER_PORT = 50051

    CLUSTER_NAME = "test_needlestack"

    ZOOKEEPER_HOSTS = ["zoo1:2181", "zoo2:2181", "zoo3:2181"]
