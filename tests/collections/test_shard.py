import pytest
import numpy as np

from needlestack.apis import indices_pb2


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
    for item in results:
        if item.WhichOneof("distance") in ("float32", "float16"):
            assert item.float_distance >= 0.0
        else:
            assert item.double_distance >= 0.0
        assert isinstance(item.metadata, indices_pb2.Metadata)


@pytest.mark.parametrize("id", ["test_index-0", "doesnt exists"])
def test_retrieve(shard_3d, id):
    shard_3d.enable_id_to_vector = True
    shard_3d.load()
    item = shard_3d.retrieve(id)
    # index = shard_3d.index._get_index_by_id(id)
    assert isinstance(item, indices_pb2.RetrievalResultItem)
