from types import GeneratorType

import pytest
import numpy as np

from needlestack.apis import indices_pb2


@pytest.mark.parametrize(
    "X,k",
    [(np.array([[1, 1]]), 1), (np.array([[1, 1]]), 5), (np.array([[1, 1]]), 1000000)],
)
def test_query(collection_2shards_2d, X, k):
    collection_2shards_2d.load()
    results = collection_2shards_2d.query(X, k, collection_2shards_2d.shards.keys())
    assert isinstance(results, GeneratorType)
    for item in results:
        if item.WhichOneof("distance") in ("float32", "float16"):
            assert item.float_distance >= 0.0
        else:
            assert item.double_distance >= 0.0
        assert isinstance(item.metadata, indices_pb2.Metadata)


@pytest.mark.parametrize("id", ["shard_1-0", "doesnt exists"])
def test_retrieve(collection_2shards_2d, id):
    collection_2shards_2d.load()
    item = collection_2shards_2d.retrieve(id, collection_2shards_2d.shards.keys())
    assert isinstance(item, indices_pb2.RetrievalResultItem)
