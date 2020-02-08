=====
Usage
=====

Here are some instructions on how to run the service.

Cluster
-------

The first thing to do is start a Needlestack cluster.
This involves running the ``Merger`` and ``Searcher``
gRPC servicers.

Create BaseConfig
~~~~~~~~~~~~~~~~~

See :ref:`needlestack.servicers.settings module` for available
settings fields.

.. code-block:: python

    from needlestack.servicers.settings import BaseConfig

    class MyNeedlestackConfig(BaseConfig):
        LOG_LEVEL = "WARNING"
        LOG_FILE = "/var/log/needlestack.log"
        LOG_FILE_MAX_BYTES = 10 * 1024 ** 2
        LOG_FILE_BACKUPS = 10

        MAX_WORKERS = 10
        HOSTNAME = socket.gethostname()
        SERVICER_PORT = 50051

        CLUSTER_NAME = "my_cluster"
        ZOOKEEPER_HOSTS = [
            "zoo1:2181",
            "zoo2:2181",
            "zoo3:2181"
        ]

Service Script
~~~~~~~~~~~~~~
Create Python scripts to run the gRPC services. Choose either `Separate Nodes` or `Same Nodes`.

Separate Nodes
^^^^^^^^^^^^^^
Run ``Merger`` and ``Searcher`` on separate nodes

.. code-block:: python

    from grpc_health.v1 import health_pb2, health_pb2_grpc
    from grpc_health.v1.health import HealthServicer

    from needlestack.apis import servicers_pb2_grpc
    from needlestack.servicers import factory
    from needlestack.servicers.merger import MergerServicer

    def main():
        config = MyNeedlestackConfig()
        server = factory.create_server(config)
        manager = factory.create_zookeeper_cluster_manager(config)
        manager.startup()
        servicers_pb2_grpc.add_MergerServicer_to_server(MergerServicer(config, manager), server)
        health = HealthServicer()
        health_pb2_grpc.add_HealthServicer_to_server(health, server)
        health.set("Merger", health_pb2.HealthCheckResponse.SERVING)
        factory.serve(server)

.. code-block:: python

    from grpc_health.v1 import health_pb2, health_pb2_grpc
    from grpc_health.v1.health import HealthServicer

    from needlestack.apis import servicers_pb2_grpc
    from needlestack.servicers import factory
    from needlestack.servicers.searcher import SearcherServicer

    def main():
        config = MyNeedlestackConfig()
        server = factory.create_server(config)
        manager = factory.create_zookeeper_cluster_manager(config)
        manager.startup()
        servicers_pb2_grpc.add_SearcherServicer_to_server(SearcherServicer(config, manager), server)
        health = HealthServicer()
        health_pb2_grpc.add_HealthServicer_to_server(health, server)
        health.set("Searcher", health_pb2.HealthCheckResponse.SERVING)
        factory.serve(server)

Same Nodes
^^^^^^^^^^
Run ``Merger`` and ``Searcher`` on same node

.. code-block:: python

    from grpc_health.v1 import health_pb2, health_pb2_grpc
    from grpc_health.v1.health import HealthServicer

    from needlestack.apis import servicers_pb2_grpc
    from needlestack.servicers import factory
    from needlestack.servicers.merger import MergerServicer
    from needlestack.servicers.searcher import SearcherServicer

    def main():
        config = MyNeedlestackConfig()
        server = factory.create_server(config)
        manager = factory.create_zookeeper_cluster_manager(config)
        manager.startup()
        servicers_pb2_grpc.add_MergerServicer_to_server(MergerServicer(config, manager), server)
        servicers_pb2_grpc.add_SearcherServicer_to_server(SearcherServicer(config, manager), server)
        health = HealthServicer()
        health_pb2_grpc.add_HealthServicer_to_server(health, server)
        health.set("Merger", health_pb2.HealthCheckResponse.SERVING)
        health.set("Searcher", health_pb2.HealthCheckResponse.SERVING)
        factory.serve(server)

Health Checks
~~~~~~~~~~~~~
Check that a node is up with the following requests.

.. code-block:: python

    from grpc_health.v1 import health_pb2
    from needlestack.apis import clients

    hostname = "localhost:50051"
    stub = clients.get_health_stub(hostname)
    stub.Check(health_pb2.HealthCheckRequest(service="Merger"))
    stub.Check(health_pb2.HealthCheckRequest(service="Searcher"))


Configuration
-------------

When the Needlestack cluster is up, configure it via a gRPC request
to any ``Merger``. This will determine how to split the shards across
available ``Searchers``, then send gRPC requests to each ``Searcher``
to load specific ``Shards`` to memory.

Adding Collections
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from needlestack.apis import clients
    from needlestack.apis import collections_pb2

    # Create a list of collections_pb2.Collection objects
    # that specifies collections, shards, and their data sources
    # collections = [...]

    hostname = "localhost:50051"
    stub = clients.get_merger_stub(hostname)
    request = collections_pb2.CollectionsAddRequest(collections=collections)
    response = stub.CollectionConfiguration(request)

Deleting Collections
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    request = collections_pb2.CollectionsDeleteRequest(
        names=["my_collection_name", "another_collection_name"]
    )
    response = stub.CollectionsDelete(request)

Reloading Collections
~~~~~~~~~~~~~~~~~~~~~
If any data sources have changes, this will load the new changes on all searchers.

.. code-block:: python

    response = stub.CollectionsLoad(collections_pb2.CollectionsLoadRequest())



Query
-----

Search queries should be issued to any ``Merger`` node. These request should contain
the vector, count, collection name, and optionally a list of specific shards to in
that collection to search. If a list of shards is not provided, the search occurs over
all shards.

.. code-block:: python

    from needlestack.apis import serializers
    from needlestack.apis import clients

    hostname = "localhost:50051"
    stub = clients.get_merger_stub(hostname)
    # X = some vector as a numpy array
    # k = number of k neighbors
    vector = serializers.ndarray_to_proto(X)
    request = servicers_pb2.SearchRequest(vector=vector, count=k, collection_name="my_collection")
    response = stub.Search(request)

In a production environment, load balance queries across mergers to distribute network traffic.
