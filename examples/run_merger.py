import logging

from grpc_health.v1 import health_pb2, health_pb2_grpc
from grpc_health.v1.health import HealthServicer

from needlestack.apis import servicers_pb2_grpc
from needlestack.servicers import factory
from needlestack.servicers.merger import MergerServicer

from examples import configs

logging.getLogger("kazoo").setLevel("WARN")


def main():
    config = configs.LocalDockerConfig()

    server = factory.create_server(config)
    manager = factory.create_zookeeper_cluster_manager(config)
    manager.startup()

    servicers_pb2_grpc.add_MergerServicer_to_server(MergerServicer(config, manager), server)

    health = HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health, server)
    health.set("Merger", health_pb2.HealthCheckResponse.SERVING)

    factory.serve(server)


if __name__ == "__main__":
    main()
