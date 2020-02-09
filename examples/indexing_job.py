import os
from typing import Tuple, List

import faiss
import numpy as np
from google.protobuf import text_format

from needlestack.apis import data_sources_pb2, indices_pb2, collections_pb2, serializers, indexing
from needlestack.indices.faiss_indices import FaissIndex


script_dir = os.path.dirname(os.path.realpath(__file__))
app_dir = os.path.dirname(script_dir)
data_dir = os.path.join(app_dir, "data")


def generate_shard_data(
    id_prefix: str,
    dimension: int = 64,
    count: int = 1000,
    seed: int = 42
) -> Tuple[np.ndarray, List[indices_pb2.Metadata]]:
    """Create random vector and metadatas for a shard"""
    np.random.seed(seed)
    X = np.random.random((count, dimension)).astype("float32")

    ids = [f"{id_prefix}-{i}" for i in range(count)]
    fields_list = [(i, i % 2 == 0) for i in range(count)]
    fieldtypes = ("int", "bool")
    fieldnames = ("int_id", "is_even")
    metadatas = serializers.metadata_list_to_proto(
        ids, fields_list, fieldtypes, fieldnames
    )

    return X, metadatas


def create_index(X: np.ndarray) -> faiss.Index:
    """Creates a brute-force flat faiss index"""
    index = faiss.IndexFlatL2(X.shape[1])
    index.add(X)
    return index


def create_shard_proto(collection_name: str, name: str) -> collections_pb2.Shard:
    """Creates a shard protobuf that points to a local data source file"""
    return collections_pb2.Shard(
        name=name,
        index=indices_pb2.BaseIndex(
            faiss_index=indices_pb2.FaissIndex(
                data_source=data_sources_pb2.DataSource(
                    local_data_source=data_sources_pb2.LocalDataSource(
                        filename=get_shard_filename(collection_name, name)
                    )
                )
            )
        )
    )


def create_collection_proto(name: str, shards: List[collections_pb2.Shard], replication_factor: int) -> collections_pb2.Collection:
    """Creates a collection protobuf which a list of shards protobufs"""
    return collections_pb2.Collection(
        name=name,
        replication_factor=replication_factor,
        enable_id_to_vector=True,
        shards=shards
    )


def get_shard_filename(collection: str, shard: str) -> str:
    """Filename format for a shard"""
    return os.path.join(data_dir, f"{collection}__{shard}.pb")


def get_collection_filename(collection: str) -> str:
    """Filename format for a collection"""
    return os.path.join(data_dir, f"{collection}_data_source.pbtxt")


def main():
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)

    # Some test collections and shards to loop over
    collections = [
        ("collection_1", ["shard_1a", "shard_1b"]),
        ("collection_2", ["shard_2a", "shard_2b", "shard_2c"]),
    ]

    seed = 1
    for collection, shards in collections:
        for shard in shards:
            X, metadatas = generate_shard_data(shard, seed=seed)
            index = create_index(X)
            faiss_index = indexing.create_faiss_index_shard(index, metadatas)

            # Serialize the shard object to disk
            faiss_index_proto = faiss_index.serialize()
            with open(get_shard_filename(collection, shard), "wb") as f:
                f.write(faiss_index_proto.SerializeToString())

            seed += 1

        # Create a collection proto with the shard protos that point to the
        # local data sources that were just generated
        collection_proto = create_collection_proto(
            collection,
            [create_shard_proto(collection, shard) for shard in shards],
            2
        )

        # Write those collection proto to disk to use later
        with open(get_collection_filename(collection), "w") as f:
            f.write(text_format.MessageToString(collection_proto))


if __name__ == "__main__":
    main()
