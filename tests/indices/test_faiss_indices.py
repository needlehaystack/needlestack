import pytest
import numpy as np

from needlestack.apis import indices_pb2


def test_load(faiss_index_4d):
    assert not hasattr(faiss_index_4d, "index")
    assert not hasattr(faiss_index_4d, "metadatas")
    faiss_index_4d.load()
    assert hasattr(faiss_index_4d, "index")
    assert hasattr(faiss_index_4d, "metadatas")


@pytest.mark.parametrize(
    "X,k",
    [
        (np.array([[1, 1, 1, 1]]), 1),
        (np.array([[1, 1, 1, 1]]), 5),
        (np.array([[1, 1, 1, 1]]), 1000000),
    ],
)
def test_query(faiss_index_4d, X, k):
    faiss_index_4d.load()
    results = faiss_index_4d.query(X, k)

    for result in results:
        for item in result:
            assert isinstance(item, indices_pb2.SearchResultItem)


@pytest.mark.parametrize(
    "X,k",
    [
        (np.array([[1, 1, 1, 1]]), 1),
        (np.array([[1, 1, 1, 1]]), 5),
        (np.array([[1, 1, 1, 1]]), 1000000),
    ],
)
def test_knn_search(faiss_index_4d, X, k):
    faiss_index_4d.load()
    dists, idxs = faiss_index_4d.knn_search(X, k)

    assert dists.shape[1] == dists.shape[1] == min(k, faiss_index_4d.count)


@pytest.mark.parametrize(
    "X,k",
    [
        (np.array([[1]]), 5),
        (np.array([[1, 1]]), 5),
        (np.array([[1, 1, 1, 1, 1, 1]]), 5),
    ],
)
def test_knn_search_bad_shape(faiss_index_4d, X, k):
    faiss_index_4d.load()
    with pytest.raises(Exception):
        faiss_index_4d.knn_search(X, k)


@pytest.mark.parametrize("index", [0, 1, 2, 3])
def test_retrieve(faiss_index_4d, index):
    faiss_index_4d.enable_id_to_vector = True
    faiss_index_4d.load()

    id = faiss_index_4d._get_metadata_by_index(index).id
    item = faiss_index_4d.retrieve(id)
    assert len(item.ListFields()) != 0


@pytest.mark.parametrize("id", ["doesnt", "exists"])
def test_retrieve_none(faiss_index_4d, id):
    faiss_index_4d.enable_id_to_vector = True
    faiss_index_4d.load()

    item = faiss_index_4d.retrieve(id)
    assert len(item.ListFields()) == 0


def test_get_vector_by_index(faiss_index_4d):
    faiss_index_4d.load()
    X = faiss_index_4d._get_vector_by_index(0)
    assert type(X) == np.ndarray
    assert X.shape == (4,)


@pytest.mark.parametrize("index", [0, 1, 2, 3])
def test_get_metadata_by_index(faiss_index_4d, index):
    faiss_index_4d.enable_id_to_vector = True
    faiss_index_4d.load()

    id = faiss_index_4d._get_metadata_by_index(index).id
    faiss_index_4d._get_index_by_id(id) == index


def test_get_index_by_id_not_enabled(faiss_index_4d):
    faiss_index_4d.load()

    with pytest.raises(ValueError) as excinfo:
        faiss_index_4d._get_index_by_id(99999999)
        assert "Index does not have enable_id_to_vector" == str(excinfo.value)
