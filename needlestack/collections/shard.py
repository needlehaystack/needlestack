from typing import List

import numpy as np

from needlestack.apis import indices_pb2
from needlestack.apis import collections_pb2
from needlestack.indices import BaseIndex


class Shard(object):

    """A logical shard containing a index to perform kNN search.

    Attributes:
        name: Name of shard
        weight: Weight of shard
        index: BaseIndex for kNN queries
        enable_id_to_vector: Enable retrieving vector from id
    """

    name: str
    weight: float
    index: BaseIndex
    enable_id_to_vector: bool = False

    @classmethod
    def from_proto(cls, proto: collections_pb2.Shard) -> "Shard":
        shard = cls()
        shard.populate_from_proto(proto)
        return shard

    def populate_from_proto(self, proto: collections_pb2.Shard):
        self.name = proto.name
        self.weight = proto.weight
        self.index = BaseIndex.from_proto(proto.index)

    def load(self):
        self.index.enable_id_to_vector = self.enable_id_to_vector
        self.index.load()

    def update_available(self) -> bool:
        return self.index.update_available()

    def set_vectors(self, X: np.ndarray, metadatas: List[indices_pb2.Metadata]):
        return self.index.set_vectors(X, metadatas)

    def add_vectors(self, X: np.ndarray, metadatas: List[indices_pb2.Metadata]):
        return self.index.add_vectors(X, metadatas)

    def query(self, X: np.ndarray, k: int) -> List[indices_pb2.SearchResultItem]:
        return self.index.query(X, k)[0]

    def retrieve(self, id: str) -> indices_pb2.RetrievalResultItem:
        return self.index.retrieve(id)
