from pathlib import Path
from unittest import mock
from datetime import datetime

import faiss
import pytest
import numpy as np
from google.cloud import storage

from needlestack.apis import collections_pb2
from needlestack.apis import data_sources_pb2
from needlestack.apis import indices_pb2
from needlestack.apis import serializers
from needlestack.collections.collection import Collection
from needlestack.collections.shard import Shard
from needlestack.indices import BaseIndex
from needlestack.indices.faiss_indices import FaissIndex
from needlestack.servicers.settings import BaseConfig


@pytest.fixture
def ssl_key_path(tmpdir):
    return Path("tests/credentials/key.pem")


@pytest.fixture
def ssl_cert_path(tmpdir):
    return Path("tests/credentials/cert.pem")


@pytest.fixture
def faiss_index_4d(tmpdir):
    X, metadatas = gen_random_vectors_and_metadatas(
        dimension=4, size=10, dtype="float32"
    )
    proto = gen_faiss_index_proto(tmpdir, X, metadatas)
    yield BaseIndex.from_proto(proto)


@pytest.fixture
def shard_3d(tmpdir):
    X, metadatas = gen_random_vectors_and_metadatas(
        dimension=3, size=10, dtype="float32"
    )
    index = gen_faiss_index_proto(tmpdir, X, metadatas)

    proto = collections_pb2.Shard(name="shard_1", weight=20.0, index=index,)
    yield Shard.from_proto(proto)


@pytest.fixture
def collection_2shards_2d(tmpdir):
    X, metadatas = gen_random_vectors_and_metadatas(
        dimension=2, size=20, dtype="float32", id_prefix="shard_1"
    )
    index_proto_shard_1 = gen_faiss_index_proto(tmpdir, X, metadatas, "shard_1")

    X, metadatas = gen_random_vectors_and_metadatas(
        dimension=2, size=25, dtype="float32", id_prefix="shard_2"
    )
    index_proto_shard_2 = gen_faiss_index_proto(tmpdir, X, metadatas, "shard_2")

    proto = collections_pb2.Collection(
        name="test_name",
        replication_factor=1,
        enable_id_to_vector=True,
        shards=[
            collections_pb2.Shard(
                name="shard_1", weight=20.0, index=index_proto_shard_1
            ),
            collections_pb2.Shard(
                name="shard_2", weight=25.0, index=index_proto_shard_2
            ),
        ],
    )
    yield Collection.from_proto(proto)


@pytest.fixture
def test_servicer_config(ssl_key_path, ssl_cert_path):
    class TestConfig(BaseConfig):
        LOG_FILE = "/tmp/needlestack.log"
        LOG_FILE_MAX_BYTES = 1024
        LOG_FILE_BACKUPS = 2
        MAX_WORKERS = 1
        HOSTNAME = "localhost"
        SERVICER_PORT = 50051
        SERVICER_SSL_PRIVATE_KEY_FILE = ssl_key_path
        SERVICER_SSL_CERT_CHAIN_FILE = ssl_cert_path
        CLUSTER_NAME = "test_needlestack"
        ZOOKEEPER_HOSTS = ["zoo1:2181", "zoo2:2181", "zoo3:2181"]

    return TestConfig()


@pytest.fixture
def gcs_blob():
    def download_to_file(f):
        f.write(b"")

    def download_as_string():
        return b""

    blob = mock.Mock(spec=storage.Blob)
    blob.updated = datetime.now()
    blob.download_to_file = mock.Mock(side_effect=download_to_file)
    blob.download_as_string = mock.Mock(side_effect=download_as_string)
    yield blob


@pytest.fixture
def gcs_bucket(gcs_blob):
    def get_blob(*args):
        return gcs_blob

    bucket = mock.Mock(spec=storage.Bucket)
    bucket.get_blob = mock.Mock(side_effect=get_blob)
    yield bucket


@pytest.fixture
def gcs_storage_client(monkeypatch, gcs_bucket):
    def get_bucket(*args):
        return gcs_bucket

    client = mock.Mock(spec=storage.Client)
    client.get_bucket = mock.Mock(side_effect=get_bucket)
    client_cls = mock.Mock(return_value=client)
    client_cls.from_service_account_json = mock.Mock(side_effect=get_bucket)
    monkeypatch.setattr(storage, "Client", client_cls)
    yield client


def gen_random_vectors_and_metadatas(dimension, size, dtype, id_prefix="id", seed=42):
    np.random.seed(seed)
    X = np.random.rand(size, dimension).astype(dtype)

    ids = [f"{id_prefix}-{i}" for i in range(size)]
    fields_list = [(i, i % 2 == 0) for i in range(size)]
    fieldtypes = ("int", "bool")
    fieldnames = ("int_id", "is_even")
    metadatas = serializers.metadata_list_to_proto(
        ids, fields_list, fieldtypes, fieldnames
    )

    return X, metadatas


def gen_faiss_index_proto(tmpdir, X, metadatas, name="test_index"):
    index = faiss.IndexFlatL2(X.shape[1])
    index.add(X)

    faiss_index = FaissIndex()
    faiss_index.populate({"index": index, "metadatas": metadatas})
    proto = faiss_index.serialize()

    filename = str(tmpdir.join(f"{name}.pb"))
    with open(filename, "wb") as f:
        f.write(proto.SerializeToString())

    return indices_pb2.BaseIndex(
        faiss_index=indices_pb2.FaissIndex(
            data_source=data_sources_pb2.DataSource(
                local_data_source=data_sources_pb2.LocalDataSource(filename=filename)
            )
        )
    )
