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


- Free software: MIT license
- Documentation: https://needlestack.readthedocs.io.


Features
--------

- gRPC server for kNN vector search
- Shard vectors over multiple nodes
- Replicate shard over multiple nodes
- Retrieve vectors by ID


Caveats
-------
These are some limitations of the current alpha builds

- Vectors must be sharded and indexed before loading to Needlestack
- To reload updated vectors, all ``MergerServicer`` and ``SearcherServicer`` nodes must be restarted
- Vectors must be saved locally to disk for Needlestack to load them
- Only kNN library supported currently is `Faiss <https://github.com/facebookresearch/faiss/>`_


Next Steps
----------
These are valuable features to make Needlestack usable in production

- Endpoint to index vectors in realtime
- Update vectors from pre-built data sources without restarting the cluster
- Allow vectors to be loaded from data sources like S3 or GCS
- Add support for other kNN libraries
