import faiss
import pytest
import numpy as np

from needlestack.apis import collections_pb2
from needlestack.apis import data_sources_pb2
from needlestack.apis import neighbors_pb2
from needlestack.apis import serializers
from needlestack.collections.collection import Collection
from needlestack.collections.shard import Shard
from needlestack.neighbors import SpatialIndex
from needlestack.neighbors.faiss_indices import FaissIndex


@pytest.fixture
def faiss_index_4d(tmpdir):
    proto = gen_random_faiss_index_proto(tmpdir, dimension=4, size=10)
    yield SpatialIndex.from_proto(proto)


@pytest.fixture
def shard_3d(tmpdir):
    proto = collections_pb2.Shard(
        name="shard_1",
        weight=20.0,
        index=gen_random_faiss_index_proto(tmpdir, dimension=3, size=10),
    )
    yield Shard.from_proto(proto)


@pytest.fixture
def collection_2shards_2d(tmpdir):
    proto = collections_pb2.Collection(
        name="test_name",
        replication_factor=1,
        enable_id_to_vector=True,
        shards=[
            collections_pb2.Shard(
                name="shard_1",
                weight=20.0,
                index=gen_random_faiss_index_proto(
                    tmpdir, dimension=2, size=20, name="shard_1"
                ),
            ),
            collections_pb2.Shard(
                name="shard_2",
                weight=25.0,
                index=gen_random_faiss_index_proto(
                    tmpdir, dimension=2, size=25, name="shard_2"
                ),
            ),
        ],
    )
    yield Collection.from_proto(proto)


def gen_random_faiss_index_proto(tmpdir, dimension, size, name="test_index", seed=42):
    np.random.seed(seed)

    X = np.random.rand(size, dimension).astype("float32")
    index = faiss.IndexFlatL2(dimension)
    index.add(X)

    ids = [f"{name}-{i}" for i in range(size)]
    fields_list = [(i, float(i)) for i in range(size)]
    fieldtypes = ("int", "float")
    fieldnames = ("id_as_int", "id_as_float")
    metadatas = serializers.metadata_list_to_proto(
        ids, fields_list, fieldtypes, fieldnames
    )

    faiss_index = FaissIndex()
    faiss_index.populate({"index": index, "metadatas": metadatas})
    proto = faiss_index.serialize()

    data_filename = str(tmpdir.join(f"{name}.pb"))
    with open(data_filename, "wb") as f:
        f.write(proto.SerializeToString())

    return neighbors_pb2.SpatialIndex(
        faiss_index=neighbors_pb2.FaissIndex(
            data_source=data_sources_pb2.DataSource(
                local_data_source=data_sources_pb2.LocalDataSource(
                    filename=data_filename
                )
            )
        )
    )
