======
Design
======

Needlestack allows users to index their vector spaces and
search them in real-time. Below are some of the vocabulary and
design decisions.

Vector Spaces
-------------

Vector spaces are coordinate systems in which a set of vectors exists.
Each vector space may represent something different about the vectors
they contain.

Collection
~~~~~~~~~~

A ``Collection`` represents a particular vector space and it's set of vectors.
``Collections`` partition its vectors into one or more ``Shards``. Performing
a kNN search on a ``Collection`` will perform a kNN search on each ``Shard``,
then merge the results together. User's can also specify which ``Shards`` to
perform a kNN search on, ignoring those not specified.

Shard
~~~~~

A ``Shard`` represents a partition of vectors in a ``Collection``.
All ``Shards`` in a ``Collection`` exists in the same vector space.
Each ``Shard`` can perform a kNN search over its partition of vectors.
Each ``Shard`` contains a ``SpatialIndex`` which implements how kNN searches
are performed.

Spatial Index
~~~~~~~~~~~~~

A ``SpatialIndex`` implements how vectors are stored and searched.
This is achieved using kNN indices from third party packages
like ``faiss`` and ``scikit-learn``. A particular ``SpatialIndex``
might use an algorithm like brute-force, kd-tree, voronoi tessellations,
or more. Metadata about each vector is also stored in the ``SpatialIndex``.
Metadata for a vector includes a string id and optional primitive values.


Services 
--------

There are three main components to run a live Needlestack cluster:

- ``ClusterManager`` maintains the state of all worker nodes in a cluster
- ``Merger`` splits and distributes task over multiple worker nodes and merges results
- ``Searcher`` runs on worker nodes to perform task

If you're from the map-reduce world, think of these as resource manager,
reducer, and mapper respectively.

Cluster Manager
~~~~~~~~~~~~~~~

The ``ClusterManager`` maintains the cluster state in a key-value store.
This key-value store should be accessible by every node in the Needlestack
cluster. The default key-value store is
`Zookeeper <https://zookeeper.apache.org/>`_.

The information available from the ``ClusterManager`` is:

- All live ``Searcher`` nodes in a Needlestack cluster
- All ``Collections`` and their ``Shards``
- Which ``Shards`` are hosted on which ``Searchers``
- The status of any given ``Shard`` on a ``Searcher`` (``ACTIVE``, ``DOWN``, ``BOOTING``)

Merger gRPC Service
~~~~~~~~~~~~~~~~~~~

The ``Merger`` is a microservice that Needlestack clients interface with.
Clients can make search, retrieval, and configuration requests through
gRPC. On requests, it will retrieve the cluster state from the ``ClusterManager``
and determine which ``Searcher`` nodes will fulfill a task. It sends tasks to
each ``Searcher``, waits for responses, then merges the results together.

ex. On a search requests for a ``Collection``, a ``Merger`` node will
get the cluster state from the ``ClusterManager`` and determine which ``Searcher``
nodes host ``Shards`` in that ``Collection``. The ``Merger`` sends concurrent
requests to relevant ``Searcher`` nodes to perform kNN searchers on those ``Shards``.
It waits for all concurrent requests to complete, then merges the results together.
The client gets a list of search results from the ``Merger``, as if all vectors in
the collection were hosted on it.

Searcher gRPC Service
~~~~~~~~~~~~~~~~~~~~~

The ``Searcher`` is a microservice that hosts the ``Shards``. It is responsible
for the compute heavy task of doing kNN searches. In a multi-node Needlestack
cluster, each ``Searcher`` node might only host a subset of all ``Shards``.

A ``Searcher`` node will register itself with the ``ClusterManager`` on startup.
It will be visible to the rest of the Needlestack cluster and is available to
host ``Shards``.

A ``Merger`` node can send a ``Searcher`` tasks as a gRPC requests. The task could
be something like performing a kNN search over a specific set of ``Shards``
hosted on that node.
