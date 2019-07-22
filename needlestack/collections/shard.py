from typing import Tuple, List

import numpy as np

from needlestack.apis import neighbors_pb2
from needlestack.apis import collections_pb2
from needlestack.neighbors import SpatialIndex


class Shard(object):

    """A logical shard containing a index to perform kNN search.

    Attributes:
        name: Name of shard
        weight: Weight of shard
        index: SpatialIndex for kNN queries
        enable_id_to_vector: Enable retrieving vector from id
    """

    name: str
    weight: float
    index: SpatialIndex
    enable_id_to_vector: bool = False

    @classmethod
    def from_proto(cls, proto: collections_pb2.Shard) -> "Shard":
        shard = cls()
        shard.populate_from_proto(proto)
        return shard

    def populate_from_proto(self, proto: collections_pb2.Shard):
        self.name = proto.name
        self.weight = proto.weight
        self.index = SpatialIndex.from_proto(proto.index)

    def load(self):
        self.index.enable_id_to_vector = self.enable_id_to_vector
        self.index.load()

    def query(
        self, X: np.ndarray, k: int
    ) -> List[Tuple[float, neighbors_pb2.Metadata]]:
        return self.index.query(X, k)[0]

    def get_vector_and_metadata(
        self, id: str
    ) -> Tuple[np.ndarray, neighbors_pb2.Metadata]:
        return self.index.get_vector_and_metadata(id)
