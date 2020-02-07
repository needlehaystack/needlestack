import heapq
from typing import List, Dict, Iterable, Optional

import numpy as np

from needlestack.apis import indices_pb2
from needlestack.apis import collections_pb2
from needlestack.collections.shard import Shard
from needlestack.exceptions import DimensionMismatchException


class Collection(object):

    """A logical collection made of shards where kNN queries can be performed.

    Attributes:
        name: Name of collection
        shards: Dictionary of shard names to shards
        replication_factor: Number of replicas per shard in the cluster
        enable_id_to_vector: Enable retrieving vector from id
        dimension: Dimensionality of the vectors
    """

    name: str
    shards: Dict[str, Shard]
    replication_factor: int
    enable_id_to_vector: bool
    dimension: int

    @classmethod
    def from_proto(cls, proto: collections_pb2.Collection) -> "Collection":
        collection = cls()
        collection.populate_from_proto(proto)
        return collection

    def populate_from_proto(self, proto: collections_pb2.Collection):
        self.name = proto.name
        self.replication_factor = proto.replication_factor
        self.enable_id_to_vector = proto.enable_id_to_vector
        self.shards = {}

        shards = [Shard.from_proto(shard_proto) for shard_proto in proto.shards]
        for shard in shards:
            shard.enable_id_to_vector = self.enable_id_to_vector
            self.add_shard(shard)

    def merge_proto(self, proto):
        self.replication_factor = proto.replication_factor
        self.enable_id_to_vector = proto.enable_id_to_vector

    def load(self):
        for shard in self.shards.values():
            shard.enable_id_to_vector = self.enable_id_to_vector
            shard.load()
        self.validate()

    def update_available(self) -> bool:
        for shard in self.shards.values():
            if shard.update_available():
                return True
        return False

    def validate(self):
        shard_dimensions = {shard.index.dimension for shard in self.shards.values()}
        if len(shard_dimensions) > 1:
            raise DimensionMismatchException(
                f"All shards in {self.name} Collection do not match dimensions"
            )
        self.dimension = shard_dimensions.pop()

    def add_shard(self, shard: Shard):
        self.shards[shard.name] = shard

    def drop_shard(self, name: str):
        del self.shards[name]

    def query(
        self, X: np.ndarray, k: int, shard_names: List[str]
    ) -> Iterable[indices_pb2.SearchResultItem]:
        shard_results = [
            self.shards[shard_name].query(X, k) for shard_name in shard_names
        ]
        return heapq.merge(
            *shard_results, key=lambda x: x.float_distance or x.double_distance
        )

    def retrieve(
        self, id: str, shard_names: List[str]
    ) -> Optional[indices_pb2.RetrievalResultItem]:
        for shard_name in shard_names:
            retrieval_item = self.shards[shard_name].retrieve(id)
            if retrieval_item is not None:
                return retrieval_item
        return None
