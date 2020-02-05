=====
Usage
=====

Cluster
-------

The first thing to do is start a Needlestack cluster.
This involves running the ``Merger`` and ``Searcher``
gRPC servicers.

1. Create a ``BaseConfig`` for your service

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

2. Create Python scripts to run the gRPC services. Choose either a or b.

   a) Run ``Merger`` and ``Searcher`` on separate nodes

    .. code-block:: python

        from needlestack.servicers import factory

        def main():
            config = MyNeedlestackConfig()
            server = factory.create_server(config)
            zk = factory.create_zookeeper_cluster_manager(config)
            factory.get_merger_servicer(server, zk)
            factory.serve(server)

    .. code-block:: python

        from needlestack.servicers import factory

        def main():
            config = MyNeedlestackConfig()
            server = factory.create_server(config)
            zk = factory.create_zookeeper_cluster_manager(config)
            factory.get_searcher_servicer(server, zk)
            factory.serve(server)

   b) Run ``Merger`` and ``Searcher`` on same node

    .. code-block:: python

        from needlestack.servicers import factory

        def main():
            config = MyNeedlestackConfig()
            server = factory.create_server(config)
            zk = factory.create_zookeeper_cluster_manager(config)
            factory.get_merger_servicer(server, zk)
            factory.get_searcher_servicer(server, zk)
            factory.serve(server)

3. Run the Python scripts on nodes. Check that a node is up
with the following requests.

.. code-block:: python

    from grpc_health.v1 import health_pb2
    from needlestack.apis import clients

    hostname = "localhost:50051"
    stub = clients.get_health_stub(hostname)
    stub.Check(health_pb2.HealthCheckRequest(service="merger"))


Configuration
-------------

When the Needlestack cluster is up, configure it via a gRPC request
to any ``Merger``. This will determine how to split the shards across
available ``Searchers``, then send gRPC requests to each ``Searcher``
to load specific ``Shards`` to memory.

.. code-block:: python

    from needlestack.apis import clients
    from needlestack.apis import collections_pb2

    # Create a list of collections_pb2.Collection objects
    # that specific collections, shards, and their data sources
    # collections = [...]

    hostname = "localhost:50051"
    stub = clients.get_merger_stub(hostname)
    request = collections_pb2.CollectionConfigurationRequest(collections=collections)
    response = stub.CollectionConfiguration(request)


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

In a production environment, some load balancing should be implemented to assure
requests are split up across nodes.
