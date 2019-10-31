import logging

from needlestack.servicers import factory
from needlestack.servicers.settings import LocalDockerConfig

logging.getLogger("kazoo").setLevel("WARN")


def main():
    config = LocalDockerConfig()
    server = factory.create_server(config)
    zk = factory.create_zookeeper_cluster_manager(config)
    servicer = factory.get_searcher_servicer(server, zk)
    factory.serve(server)


if __name__ == "__main__":
    main()
