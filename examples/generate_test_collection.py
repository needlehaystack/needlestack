import os

import faiss
import numpy as np

from needlestack.apis import data_sources_pb2, neighbors_pb2, collections_pb2, serializers
from needlestack.neighbors.faiss_indices import FaissIndex


def create_test_data_with_proto(noop=True):

    script_dir = os.path.dirname(os.path.realpath(__file__))
    app_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(app_dir, "data")

    np.random.seed(42)
    d = 64  # dimension
    nb = 100  # database size
    collections = [
        ("collection_1", ["shard_1a", "shard_1b"]),
        ("collection_2", ["shard_2a", "shard_2b", "shard_2c"]),
    ]

    collection_protos = []

    for collection_name, shards in collections:
        shard_protos = []

        for shard_name in shards:
            proto_filename = os.path.join(data_dir, f"{collection_name}__{shard_name}.pb")
            if not noop:
                os.makedirs(data_dir, exist_ok=True)

                xb = np.random.random((nb, d)).astype("float32")
                index = faiss.IndexFlatL2(d)
                index.add(xb)

                ids = [f"{shard_name}-{i}" for i in range(nb)]
                fields_list = [(i, float(i)) for i in range(nb)]
                fieldtypes = ("int", "float")
                fieldnames = ("id_as_int", "id_as_float")
                metadatas = serializers.metadata_list_to_proto(
                    ids, fields_list, fieldtypes, fieldnames
                )

                faiss_index = FaissIndex()
                faiss_index.populate({
                    "index": index,
                    "metadatas": metadatas,
                })
                index_proto = faiss_index.serialize()

                with open(proto_filename, "wb") as f:
                    f.write(index_proto.SerializeToString())

            shard_proto = collections_pb2.Shard(
                name=shard_name,
                index=neighbors_pb2.SpatialIndex(
                    faiss_index=neighbors_pb2.FaissIndex(
                        data_source=data_sources_pb2.DataSource(
                            local_data_source=data_sources_pb2.LocalDataSource(
                                filename=proto_filename
                            )
                        )
                    )
                )
            )

            shard_protos.append(shard_proto)

        collection_proto = collections_pb2.Collection(
            name=collection_name,
            replication_factor=2,
            enable_id_to_vector=True,
            shards=shard_protos
        )
        collection_protos.append(collection_proto)

    return collection_protos
