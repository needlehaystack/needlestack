import os

from needlestack.servicers.settings import BaseConfig


class LocalDockerConfig(BaseConfig):
    """Configs for local development environment"""

    DEBUG = True

    LOG_LEVEL = "DEBUG"

    LOG_FILE = "/app/data/needlestack.log"
    LOG_FILE_MAX_BYTES = 1 * 1024 ** 2  # 1 MB
    LOG_FILE_BACKUPS = 10

    MAX_WORKERS = 10
    HOSTNAME = os.getenv("CONTAINER_NAME")
    SERVICER_PORT = 50051

    CLUSTER_NAME = "my_needlestack"

    ZOOKEEPER_HOSTS = ["zoo1:2181", "zoo2:2181", "zoo3:2181"]


class LocalDockerSSLConfig(LocalDockerConfig):

    MUTUAL_TLS = True
    SSL_CA_CERT_CHAIN_FILE = "/app/data/credentials/ca.crt"
    SSL_SERVER_PRIVATE_KEY_FILE = "/app/data/credentials/server.key"
    SSL_SERVER_CERT_CHAIN_FILE = "/app/data/credentials/server.crt"
    SSL_CLIENT_PRIVATE_KEY_FILE = "/app/data/credentials/client.key"
    SSL_CLIENT_CERT_CHAIN_FILE = "/app/data/credentials/client.crt"
