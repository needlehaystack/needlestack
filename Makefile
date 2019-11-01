install: clean compile-proto
	python setup.py install

dist: clean compile-proto
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

compile-proto:
	python -m grpc_tools.protoc \
		-I. \
		--python_out=. \
		--grpc_python_out=. \
		./needlestack/apis/*.proto

compile-proto-test:
	python -m grpc_tools.protoc \
		-I. \
		--python_out=. \
		--mypy_out=. \
		--grpc_python_out=. \
		./needlestack/apis/*.proto

clean: clean-build clean-pyc clean-test clean-proto

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -f .coverage
	rm -fr htmlcov/

clean-proto:
	find . -name '*_pb2.py' -delete
	find . -name '*_pb2.pyi' -delete
	find . -name '*_pb2_grpc.py' -delete

test-all: compile-proto-test auto-format test lint test-typing

auto-format:
	black needlestack tests

test:
	pytest

lint:
	flake8 needlestack tests

test-typing:
	python3 -m mypy needlestack

sphinx-docs: compile-proto clean-docs
	sphinx-apidoc -o docs/ needlestack
	$(MAKE) -C docs html

clean-docs:
	rm -f docs/needlestack.rst
	rm -f docs/needlestack.*.rst
	rm -f docs/modules.rst
	$(MAKE) -C docs clean
