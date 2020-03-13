============
Contributing
============

Contributions are welcomed and greatly appreciated!
These can be done through submitting GitHub issues, fixing bugs, implementing features,
and documentation. Needlestack follows the GitFlow branching model.


1. GitHub Issue Tracking
------------------------

All bugs and feature requests should be submitted through GitHub's
issue tracking.

1.1 Review Open Issues
~~~~~~~~~~~~~~~~~~~~~~

Check if the bug or feature has already been submitted. The bug-fix
or feature could already be in active development.

1.2 Create New Issue
~~~~~~~~~~~~~~~~~~~~

If the bug or feature is not already reported, please open an issue at
https://github.com/needlehaystack/needlestack/issues. Follow the templates
and provide the information requested.


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

4. Create a branch for local development::

    $ git flow feature start NAME_OF_FEATURE

5. Implement changes.

6. Check that your code changes pass ``black``, ``pytest``, ``flake8``, and ``mypy``.
   Note that ``black`` will auto-format all files in-place::

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
    $ git flow feature publish NAME_OF_FEATURE

11. Submit a pull request through the GitHub website.
    The base should be ``needlehaystack/needlestack`` and ``develop``.


4. Submit Pull Request
----------------------

Follow these guidelines when submitting pull requests.

1. Include tests for the new feature or covering the bug.
2. Write documentation and docstrings for any new functionality.
3. Check that the pull request is passing test
   https://travis-ci.org/needlehaystack/needlestack/pull_requests


5. Deploying
------------

A note for maintainers deploying to PyPi.

Minor & Minor Changes
~~~~~~~~~~~~~~~~~~~~~

1. Create a release branch and publish it::

    $ git flow release start <version>
    $ git flow publish <version>

2. Fix bugs, if any::
    $ git add .
    $ git commit -m "bug fix message"

3. Start a release candidate and push to build::

    $ bumpversion [major|minor] --tag
    $ git push
    $ git push --tags

4. If another release candidate is needed::

    $ bumpversion candidate --tag
    $ git push
    $ git push --tags

5. When ready for PyPi bump the release, merge, and push::

    $ bumpversion release
    $ git push
    $ git flow release finish <version>
    $ git push
    $ git push --tags

Hotfix
~~~~~~

1. Start the hotfix::

    $ git flow hotfix start <version>

2. Makes changes and bump the version::

    $ git add .
    $ git commit -m "hotfix message"
    $ bumpversion patch --no-commit
    $ bumpversion release --allow-dirty

3. Finish the hotfix::

    $ git flow hotfix finish <version>
    $ git push
    $ git push --tags
