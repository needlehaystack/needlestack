import numpy as np

from needlestack.apis import servicers_pb2
from needlestack.apis import neighbors_pb2
from needlestack.apis import serializers


def create_result_item(
    dist: np.ndarray, metadata: neighbors_pb2.Metadata
) -> servicers_pb2.SearchResultItem:
    if dist.dtype == "float32" or dist.dtype == "float16":
        return servicers_pb2.SearchResultItem(
            id=metadata.id, float_distance=dist, metadata=metadata
        )
    else:
        return servicers_pb2.SearchResultItem(
            id=metadata.id, double_distance=dist, metadata=metadata
        )


def create_retrieval_item(
    vector: np.ndarray, metadata: neighbors_pb2.Metadata
) -> servicers_pb2.RetrieveResponse:
    vector_proto = serializers.ndarray_to_proto(vector)
    return servicers_pb2.RetrieveResponse(
        id=metadata.id, vector=vector_proto, metadata=metadata
    )
