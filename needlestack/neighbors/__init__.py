from typing import List, Tuple, Dict

import numpy as np

from needlestack.apis import neighbors_pb2


class SpatialIndex(object):
    """Base class for spatial index implementations. Defines interfaces
    for populating data and performing kNN queries."""

    @staticmethod
    def from_proto(proto: neighbors_pb2.SpatialIndex) -> "SpatialIndex":
        """Factory method to construct the correct implementation of a SpatialIndex
        from a protobuf.

        Args:
            proto: Protobuf defining how to load data for the index
        """
        index = proto.WhichOneof("index")
        if index == "faiss_index":
            from needlestack.neighbors.faiss_indices import FaissIndex

            spatial_index = FaissIndex()
            spatial_index.populate_from_proto(proto.faiss_index)
        else:
            raise ValueError("No valid index found from protobuf")

        return spatial_index

    @property
    def dimension(self) -> int:
        """Spatial dimensions for the vector space"""
        raise NotImplementedError()

    @property
    def count(self) -> int:
        """Number of vectors in the vector space"""
        raise NotImplementedError()

    def populate_from_proto(self, proto):
        """Populate SpatialIndex from protobuf defining data source

        Args:
            proto: Protobuf with data on how to populate a particular
                SpatialIndex implementation
        """
        raise NotImplementedError()

    def populate(self, data: Dict):
        """Populate SpatialIndex from dictionary

        Args:
            data: Dictionary of key, value pairs for attributes
        """
        raise NotImplementedError()

    def serialize(self):
        """Serialize the current index to a protobuf"""
        raise NotImplementedError()

    def load(self):
        """Load data into memory"""
        raise NotImplementedError()

    def _get_metadata_by_index(self, i: int) -> neighbors_pb2.Metadata:
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
    ) -> Tuple[np.ndarray, neighbors_pb2.Metadata]:
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

    def query(
        self, X: np.ndarray, k: int
    ) -> List[List[Tuple[float, neighbors_pb2.Metadata]]]:
        """Returns a list of list of knn query results.
        Each result is a tuple of (distance, metadata) pairs.

        Args:
            X: Matrix of vectors to perform kNN search for
            k: Number of neighbors
        """
        dists, idxs = self.knn_search(X, k)
        batches = []
        for dist, idx in zip(dists, idxs):
            results = [(d, self._get_metadata_by_index(i)) for d, i in zip(dist, idx)]
            batches.append(results)
        return batches
