from types import GeneratorType

import pytest
import numpy as np

from needlestack.apis import neighbors_pb2


@pytest.mark.parametrize(
    "X,k",
    [(np.array([[1, 1]]), 1), (np.array([[1, 1]]), 5), (np.array([[1, 1]]), 1000000)],
)
def test_query(collection_2shards_2d, X, k):
    collection_2shards_2d.load()
    results = collection_2shards_2d.query(X, k, collection_2shards_2d.shards.keys())
    assert isinstance(results, GeneratorType)
    for dist, metadata in results:
        assert dist > 0.0
        assert isinstance(metadata, neighbors_pb2.Metadata)


@pytest.mark.parametrize("id", ["shard_1-0", "doesnt exists"])
def test_get_vector_and_metadata(collection_2shards_2d, id):
    collection_2shards_2d.load()
    vector, metadata = collection_2shards_2d.get_vector_and_metadata(
        id, collection_2shards_2d.shards.keys()
    )
    assert vector is None or isinstance(vector, np.ndarray)
    assert metadata is None or isinstance(metadata, neighbors_pb2.Metadata)
