import os

import grpc
from google.protobuf import text_format
from grpc_health.v1 import health_pb2
from grpc_health.v1 import health_pb2_grpc

from needlestack.apis import collections_pb2
from needlestack.apis import servicers_pb2_grpc

from examples.configs import LocalDockerConfig, LocalDockerSSLConfig


USE_SSL = False

script_dir = os.path.dirname(os.path.realpath(__file__))
app_dir = os.path.dirname(script_dir)
data_dir = os.path.join(app_dir, "data")


def main():
    hostname = "merger-grpc:50051"

    if USE_SSL:
        config = LocalDockerSSLConfig()
        channel = grpc.secure_channel(hostname, config.ssl_channel_credentials)
    else:
        channel = grpc.insecure_channel(hostname)

    print("Doing health check")
    health_stub = health_pb2_grpc.HealthStub(channel)
    response = health_stub.Check(health_pb2.HealthCheckRequest(service="Merger"))
    print(response)

    # Grabs the collections protobubs from the files that indexing_job.py wrote to ./data
    collections_files = ["collection_1_data_source.pbtxt", "collection_2_data_source.pbtxt"]
    collections = []
    for file in collections_files:
        with open(os.path.join(data_dir, file), "r") as f:
            collection = text_format.Parse(f.read(), collections_pb2.Collection())
            collections.append(collection)

    print("Adding collections to cluster")
    stub = servicers_pb2_grpc.MergerStub(channel)
    response = stub.CollectionsAdd(collections_pb2.CollectionsAddRequest(collections=collections))
    print(response)


if __name__ == "__main__":
    main()
