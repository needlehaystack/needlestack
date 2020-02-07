===========
Needlestack
===========

.. image:: https://img.shields.io/pypi/v/needlestack.svg
        :target: https://pypi.python.org/pypi/needlestack

.. image:: https://img.shields.io/travis/needlehaystack/needlestack.svg
        :target: https://travis-ci.org/needlehaystack/needlestack

.. image:: https://coveralls.io/repos/github/needlehaystack/needlestack/badge.svg?branch=master
        :target: https://coveralls.io/github/needlehaystack/needlestack?branch=master

.. image:: https://readthedocs.org/projects/needlestack/badge/?version=latest
        :target: https://needlestack.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status



Needlestack is a distributed vector search microservice.


- Free software: Apache License 2.0
- Documentation: https://needlestack.readthedocs.io.


Features
--------

- gRPC server for kNN vector search
- Shard vectors over multiple nodes
- Replicate shard over multiple nodes
- Retrieve vectors by ID


Limitations
-----------
The current beta builds have limitations that make them difficult to use in production.
These should be addressed in future builds.

Caveats
~~~~~~~

- Vectors must be manually sharded, indexed, and serialized to disk as protobufs
- Only kNN library currently supported is `Faiss <https://github.com/facebookresearch/faiss/>`_


Quickstart
----------
Get started with the examples in this repo!

Start Docker containers running Needlestack services.
This runs the ``examples/run_merger.py`` and ``examples/run_searcher.py``
in containers.

.. code-block:: bash

    docker-compose up merger-grpc searcher-grpc1 searcher-grpc2 searcher-grpc3

Create local index data and send to the Needlestack services.
This runs ``examples/indexing_job.py`` to create dummy data,
then runs ``examples/add_collections.py`` to send them to the Needlestack service.

.. code-block:: bash

    docker-compose run --rm make-test-data

Access the gRPC endpoints at ``localhost:50051``
