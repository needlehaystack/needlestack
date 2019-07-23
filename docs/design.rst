======
Design
======

This is an overall of Needlestack from a high level.

Vector Space
------------

The vector spaces are logically organized into object classes.

Collection
~~~~~~~~~~

A ``Collection`` represents a set of vectors within in a vector space.
``Collections`` partition its vectors into ``Shards``.

Shard
~~~~~

A ``Shard`` represents some parition of vectors from a ``Collection``.
They contain an ``Index`` which perform the actual kNN search logic.

Index
~~~~~

An ``Index`` implements kNN search for a set of vectors. Implementions could include
brute force, KD trees, voronoi tessellations, and more.


Application
-----------

There are three main components to run the live distributed gRPC service.
They all work together to perform map-reduce-like queries.

Cluster Manager
~~~~~~~~~~~~~~~

The ``ClusterManager`` stores the state of all ``Searcher`` nodes
in a Needlestack cluster. The default backend for the ``ClusterManager``
is `Zookeeper <https://zookeeper.apache.org/>`_, but it can easily be
swapped out for other key-value stores.

The information availabe from the ``ClusterManager`` is:

- All live ``Searcher`` nodes in a Needlestack cluster
- All ``Collections`` and their ``Shards``
- Which ``Searcher`` nodes host a given ``Shard``
- Status of a ``Searcher`` node (``ACTIVE``, ``DOWN``, ``BOOTING``)

Merger gRPC Service
~~~~~~~~~~~~~~~~~~~

The ``Merger`` is a microservice that Needlestack clients interface with.
Search, retrieval, and configuration requests are handled here via gRPC.

If handling a search requests for a ``Collection``, a ``Merger`` node will use
a ``ClusterManager`` to determine which ``Searcher`` nodes host ``Shards``
of that ``Collection``. The ``Merger`` sends concurrent requests to relevant
``Searcher`` nodes to perform a kNN search on those ``Shards``. The
``Merger`` node waits for all requests to finish, then merges the results together.

Searcher gRPC Service
~~~~~~~~~~~~~~~~~~~~~

The ``Searcher`` is a micorservice that host ``Shards`` of ``Collections``.
In a multi-node Needlestack cluster, each ``Searcher`` node might host only
a subset of all ``Shards``.

A ``Searcher`` node will register itself with the ``ClusterManager`` upon startup.
This allows the Needlestack cluster to know about all ``Searcher`` nodes potentially
hosting ``Shards``.

A ``Merger`` node can request a ``Searcher`` node to perform a kNN search
over a set of ``Shards`` hosted on that ``Searcher``.
