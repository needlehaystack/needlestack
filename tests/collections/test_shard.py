import pytest
import numpy as np

from needlestack.apis import neighbors_pb2


@pytest.mark.parametrize(
    "X,k",
    [
        (np.array([[1, 1, 1]]), 1),
        (np.array([[1, 1, 1]]), 5),
        (np.array([[1, 1, 1]]), 1000000),
    ],
)
def test_query(shard_3d, X, k):
    shard_3d.load()
    results = shard_3d.query(X, k)
    assert isinstance(results, list)
    assert len(results) == min(k, shard_3d.index.count)
    for dist, metadata in results:
        assert dist > 0.0
        assert isinstance(metadata, neighbors_pb2.Metadata)


@pytest.mark.parametrize("id", ["test_index-0", "doesnt exists"])
def test_get_vector_and_metadata(shard_3d, id):
    shard_3d.enable_id_to_vector = True
    shard_3d.load()
    vector, metadata = shard_3d.get_vector_and_metadata(id)
    index = shard_3d.index._get_index_by_id(id)
    if index is None:
        assert vector is None
        assert metadata is None
    else:
        assert isinstance(vector, np.ndarray)
        assert isinstance(metadata, neighbors_pb2.Metadata)
