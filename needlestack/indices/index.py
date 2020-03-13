from typing import List, Tuple, Dict, Union

import numpy as np

from needlestack.apis import indices_pb2
from needlestack.apis import serializers
from needlestack.exceptions import DeserializationError


class BaseIndex(object):
    """Base class for index implementations. Defines interfaces
    for populating data and performing kNN queries."""

    modified_time: Union[float, None] = None

    @staticmethod
    def from_proto(proto: indices_pb2.BaseIndex) -> "BaseIndex":
        """Factory method to construct the correct implementation of a BaseIndex
        from a protobuf. Specific index types are imported in this function
        so their dependent packages do not need to be installed

        Args:
            proto: Protobuf defining how to load data for the index
        """
        index_type = proto.WhichOneof("index")
        if index_type == "faiss_index":
            from needlestack.indices.faiss_indices import FaissIndex

            index = FaissIndex()
            index.populate_from_proto(proto.faiss_index)
        else:
            raise DeserializationError("No valid index found from protobuf")

        return index

    @property
    def dimension(self) -> int:
        """Spatial dimensions for the vector space"""
        raise NotImplementedError()

    @property
    def count(self) -> int:
        """Number of vectors in the vector space"""
        raise NotImplementedError()

    def populate_from_proto(self, proto):
        """Populate BaseIndex from protobuf defining data source

        Args:
            proto: Protobuf with data on how to populate a particular
                BaseIndex implementation
        """
        raise NotImplementedError()

    def populate(self, data: Dict):
        """Populate BaseIndex from dictionary

        Args:
            data: Dictionary of key, value pairs for attributes
        """
        raise NotImplementedError()

    def serialize(self):
        """Serialize the current index to a protobuf"""
        raise NotImplementedError()

    def load(self):
        """Load data into memory"""
        if self.update_available():
            self._load()

    def _load(self):
        """Load data into memory"""
        raise NotImplementedError()

    def update_available(self):
        """Data source has an update available"""
        raise NotImplementedError()

    def set_vectors(self, X: np.ndarray, metadatas: List[indices_pb2.Metadata]):
        """Set the vectors for this index"""
        raise NotImplementedError()

    def add_vectors(self, X: np.ndarray, metadatas: List[indices_pb2.Metadata]):
        """Add the vectors to existing index"""
        raise NotImplementedError()

    def _get_metadata_by_index(self, i: int) -> indices_pb2.Metadata:
        raise NotImplementedError()

    def _get_vector_by_index(self, i: int) -> np.ndarray:
        raise NotImplementedError()

    def _get_index_by_id(self, id: str) -> int:
        raise NotImplementedError()

    def knn_search(self, X: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        """Returns an array of distances and index ids

        Args:
            X: Matrix of vectors to perform kNN search
            k: Number of neighbors
        """
        raise NotImplementedError()

    def get_vector_and_metadata(
        self, id: str
    ) -> Tuple[np.ndarray, indices_pb2.Metadata]:
        """Returns the vector and metadata for a particular item id

        Args:
            id: ID within metadata
        """
        i = self._get_index_by_id(id)
        if i is not None:
            vector = self._get_vector_by_index(i)
            metadata = self._get_metadata_by_index(i)
            return vector, metadata
        else:
            return None, None

    def retrieve(self, id: str) -> indices_pb2.RetrievalResultItem:
        vector, metadata = self.get_vector_and_metadata(id)
        vector_proto = None if vector is None else serializers.ndarray_to_proto(vector)
        return indices_pb2.RetrievalResultItem(vector=vector_proto, metadata=metadata)

    def query(self, X: np.ndarray, k: int) -> List[List[indices_pb2.SearchResultItem]]:
        """Returns a list of list of knn query results.
        Each result is a tuple of (distance, metadata) pairs.

        Args:
            X: Matrix of vectors to perform kNN search for
            k: Number of neighbors
        """
        dists, idxs = self.knn_search(X, k)
        batches = []
        for dist, idx in zip(dists, idxs):
            if dists.dtype == "float32" or dists.dtype == "float16":
                results = [
                    indices_pb2.SearchResultItem(
                        float_distance=d, metadata=self._get_metadata_by_index(i)
                    )
                    for d, i in zip(dist, idx)
                ]
            else:
                results = [
                    indices_pb2.SearchResultItem(
                        double_distance=d, metadata=self._get_metadata_by_index(i)
                    )
                    for d, i in zip(dist, idx)
                ]
            batches.append(results)
        return batches
