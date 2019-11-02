import logging

from needlestack.servicers import factory
from needlestack.servicers.settings import LocalDockerConfig

logging.getLogger("kazoo").setLevel("WARN")


def main():
    config = LocalDockerConfig()
    server = factory.create_server(config)
    manager = factory.create_zookeeper_cluster_manager(config)
    manager.startup()
    servicer = factory.get_merger_servicer(server, manager)
    factory.serve(server)


if __name__ == "__main__":
    main()
