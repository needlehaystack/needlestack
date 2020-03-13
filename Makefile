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

gen-ssl-certs:
	mkdir -p data/credentials
	cd data/credentials && \
		openssl req -x509 -sha256 -newkey rsa:4096 -keyout ca.key -out ca.crt -days 356 -nodes -subj '/CN=My Cert Authority' && \
		openssl req -new -newkey rsa:4096 -keyout server.key -out server.csr -nodes -subj '/CN=needlestack' -config ../../examples/openssl.conf && \
		openssl x509 -req -sha256 -days 365 -in server.csr -CA ca.crt -CAkey ca.key -set_serial 01 -out server.crt -extensions v3_req -extfile ../../examples/openssl.conf && \
		openssl req -new -newkey rsa:4096 -keyout client.key -out client.csr -nodes -subj '/CN=My Client' && \
		openssl x509 -req -sha256 -days 365 -in client.csr -CA ca.crt -CAkey ca.key -set_serial 02 -out client.crt

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
	rm -f my.log

clean-proto:
	find . -name '*_pb2.py' -delete
	find . -name '*_pb2.pyi' -delete
	find . -name '*_pb2_grpc.py' -delete

test-all: compile-proto-test auto-format lint test test-typing

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
