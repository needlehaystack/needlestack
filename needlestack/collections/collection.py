import heapq
from typing import List, Tuple, Dict, Iterable, Union

import numpy as np

from needlestack.apis import neighbors_pb2
from needlestack.apis import collections_pb2
from needlestack.collections.shard import Shard


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

        shards = [Shard.from_proto(shard_proto) for shard_proto in proto.shards]
        self.shards = {shard.name: shard for shard in shards}
        for shard in self.shards.values():
            shard.enable_id_to_vector = self.enable_id_to_vector

    def load(self):
        for shard in self.shards.values():
            shard.load()
        self.validate()

    def validate(self):
        shard_dimensions = {shard.index.dimension for shard in self.shards.values()}
        if len(shard_dimensions) > 1:
            raise Exception(
                f"All shards in {self.name} Collection do not match dimensions"
            )
        self.dimension = shard_dimensions.pop()

    def query(
        self, X: np.ndarray, k: int, shard_names: List[str]
    ) -> Iterable[Tuple[float, neighbors_pb2.Metadata]]:
        shard_results = [
            self.shards[shard_name].query(X, k) for shard_name in shard_names
        ]
        return heapq.merge(*shard_results, key=lambda x: x[0])

    def get_vector_and_metadata(
        self, id: str, shard_names: List[str]
    ) -> Union[Tuple[np.ndarray, neighbors_pb2.Metadata], Tuple[None, None]]:
        for shard_name in shard_names:
            vector, metadata = self.shards[shard_name].get_vector_and_metadata(id)
            if vector is not None:
                return vector, metadata
        return None, None
