.. highlight:: shell

============
Contributing
============

Contributions are welcomed and greatly appreciated!
These can be done through submitting Github issues, fixing bugs, or implementing features.
Please read through these guidelines to assure a smooth process.


1. Github Issue Tracking
------------------------

All bugs and feature requests should be submitted through Github's
issue tracking.

1.1 Review Open Issues
~~~~~~~~~~~~~~~~~~~~~~

Check if the bug or feature is has already been submitted. The bugfix
or feature could already be in active development

1.2 Create New Issue
~~~~~~~~~~~~~~~~~~~~

If the bug or feature is not already reported, please open an issue at
https://github.com/needlehaystack/needlestack/issues. Follow the templates
and provide the information requested in the templates.


2. Pick an Open Issue
---------------------

Whether it's an existing issue or one you opened yourself, pick an issue
to implement.

2.1 Fix Bugs
~~~~~~~~~~~~

Look through issues tagged with ``bug`` and ``help wanted``.

2.2 Implement Features
~~~~~~~~~~~~~~~~~~~~~~

Look through issues tagged with ``enhancement`` and ``help wanted``.


3. Start Development
--------------------

Follow these steps for local development on any machine of your choice
with Docker and Docker-Compose

1. Fork the ``needlestack`` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_username/needlestack.git

3. Build the Docker images::

    $ docker-compose build

4. Create a branch for local development. Branch names should be prefixed with
   the type of fix. Run one of the following commands::

    $ git checkout -b bug/name-for-bugfix
    $ git checkout -b feature/name-for-feature
    $ git checkout -b docs/name-for-docs-added

5. Implement changes.

6. Check that your code changes pass ``black``, ``pytest``, ``flake8``, and ``mypy``.
   Note that ``black`` will autoformat all files inplace::

    $ docker-compose run --rm test

7. Run the live gRPC service on `localhost:50051` for any additional testing::

    $ docker-compose up merger-grpc searcher-grpc1 searcher-grpc2 searcher-grpc3

8. Add documentation for new functionality and rebuild docs::

    $ docker-compose run --rm docs

9. Remove containers after development::

    $ docker-compose down

10. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin branch-type/branch-name

11. Submit a pull request through the GitHub website.


4. Submit Pull Request
----------------------

Follow these guidelines when submitting pull requests.

1. Include tests for the new feature or covering the bug.
2. Write documentation and docstrings for any new functionality.
3. Check that the pull request is passing test
   https://travis-ci.org/needlehaystack/needlestack/pull_requests


5. Deploying
------------

A note for maintainers for deploying to PyPi. Bump the package version and tag
the commit. Pushing new tags to GitHub will kick off a Travis CI pipeline to test
and deploy the package to PyPi.

.. code-block:: shell

    $ bumpversion patch # major||minor||patch
    $ git push
    $ git push --tags
