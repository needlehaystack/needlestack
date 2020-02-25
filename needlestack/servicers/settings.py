from typing import List, Optional

import grpc
from grpc import ServerCredentials, ChannelCredentials


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
        MUTUAL_TLS: Require server and client to authenticate each other the CA
        SSL_CA_CERT_CHAIN: Certificate authority certificate chain bytes
        SSL_CA_CERT_CHAIN_FILE: Certificate authority certificate chain file
        SSL_SERVER_PRIVATE_KEY: Server private key bytes
        SSL_SERVER_PRIVATE_KEY_FILE: Server private key file
        SSL_SERVER_CERT_CHAIN: Server certificate chain bytes
        SSL_SERVER_CERT_CHAIN_FILE: Server certificate chain file
        SSL_CLIENT_PRIVATE_KEY: Client private key bytes
        SSL_CLIENT_PRIVATE_KEY_FILE: Client private key file
        SSL_CLIENT_CERT_CHAIN: Client certificate chain bytes
        SSL_CLIENT_CERT_CHAIN_FILE: Client certificate chain file
        CLUSTER_NAME: Name for Needlestack cluster
        ZOOKEEPER_ROOT: Root path on Zookeeper
        ZOOKEEPER_HOSTS: List of Zookeeper host for cluster manager
        hostport: Hostport to gRPC server
        use_mutual_tls: Should server and clients be authenticated
        use_server_ssl: Should server be authenticated
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

    MUTUAL_TLS: bool = False
    SSL_CA_CERT_CHAIN: Optional[bytes] = None
    SSL_CA_CERT_CHAIN_FILE: Optional[str] = None
    SSL_SERVER_PRIVATE_KEY: Optional[bytes] = None
    SSL_SERVER_PRIVATE_KEY_FILE: Optional[str] = None
    SSL_SERVER_CERT_CHAIN: Optional[bytes] = None
    SSL_SERVER_CERT_CHAIN_FILE: Optional[str] = None
    SSL_CLIENT_PRIVATE_KEY: Optional[bytes] = None
    SSL_CLIENT_PRIVATE_KEY_FILE: Optional[str] = None
    SSL_CLIENT_CERT_CHAIN: Optional[bytes] = None
    SSL_CLIENT_CERT_CHAIN_FILE: Optional[str] = None

    CLUSTER_NAME: str

    ZOOKEEPER_ROOT = "/needlestack"
    ZOOKEEPER_HOSTS: List[str]

    @property
    def hostport(self) -> str:
        return f"{self.HOSTNAME}:{self.SERVICER_PORT}"

    @property
    def use_mutual_tls(self) -> bool:
        return self.MUTUAL_TLS

    @property
    def use_server_ssl(self) -> bool:
        return (
            self.SSL_SERVER_PRIVATE_KEY is not None
            or self.SSL_SERVER_PRIVATE_KEY_FILE is not None
        ) and (
            self.SSL_SERVER_CERT_CHAIN is not None
            or self.SSL_SERVER_CERT_CHAIN_FILE is not None
        )

    @property
    def use_channel_ssl(self):
        return (
            self.SSL_CA_CERT_CHAIN is not None
            or self.SSL_CA_CERT_CHAIN_FILE is not None
        )

    @property
    def ca_certificate(self) -> Optional[bytes]:
        return self._get_credential("SSL_CA_CERT_CHAIN")

    @property
    def server_private_key(self) -> Optional[bytes]:
        return self._get_credential("SSL_SERVER_PRIVATE_KEY")

    @property
    def server_certificate(self) -> Optional[bytes]:
        return self._get_credential("SSL_SERVER_CERT_CHAIN")

    @property
    def channel_private_key(self) -> Optional[bytes]:
        return self._get_credential("SSL_CLIENT_PRIVATE_KEY")

    @property
    def channel_certificate(self) -> Optional[bytes]:
        return self._get_credential("SSL_CLIENT_CERT_CHAIN")

    @property
    def ssl_server_credentials(self) -> Optional[ServerCredentials]:
        if self.use_server_ssl:
            pairs = [(self.server_private_key, self.server_certificate)]
            ca_certificate = self.ca_certificate if self.use_mutual_tls else None
            return grpc.ssl_server_credentials(
                private_key_certificate_chain_pairs=pairs,
                root_certificates=ca_certificate,
            )
        else:
            return None

    @property
    def ssl_channel_credentials(self) -> Optional[ChannelCredentials]:
        if self.use_channel_ssl:
            return grpc.ssl_channel_credentials(
                root_certificates=self.ca_certificate,
                private_key=self.channel_private_key,
                certificate_chain=self.channel_certificate,
            )
        else:
            return None

    def _get_credential(self, name: str) -> Optional[bytes]:
        data = getattr(self, name, None)
        filename = getattr(self, f"{name}_FILE", None)
        if data:
            return data
        elif filename:
            with open(filename, "rb") as f:
                return f.read()
        else:
            return None


class TestConfig(BaseConfig):
    """Configs for local test environment"""

    DEBUG = True

    LOG_LEVEL = "DEBUG"

    LOG_FILE = "/tmp/needlestack.log"
    LOG_FILE_MAX_BYTES = 1 * 1024 ** 2  # 1 MB
    LOG_FILE_BACKUPS = 2

    MAX_WORKERS = 2
    HOSTNAME = "localhost"
    SERVICER_PORT = 50051

    CLUSTER_NAME = "test_needlestack"

    ZOOKEEPER_HOSTS = ["zoo1:2181", "zoo2:2181", "zoo3:2181"]
