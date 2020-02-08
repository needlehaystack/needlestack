from typing import List, TYPE_CHECKING

from needlestack.apis import indices_pb2
from needlestack.indices import BaseIndex


"""Developers could choose to use a different index implementation,
so only import packages when needed so developers don't need to
install packages they won't use"""
if TYPE_CHECKING:
    import faiss


def create_faiss_index_shard(
    faiss_index: "faiss.Index", metadatas: List[indices_pb2.Metadata]
) -> BaseIndex:
    """A simple function to that takes a faiss index object and metadata for vectors to create a serializable
    FaissIndex object. It would have been nice to be able to pass in vectors and metadatas, but creating a faiss
    index requires developers make decisions about hyper-parameters that would be difficult to automate.
    """
    from needlestack.indices.faiss_indices import FaissIndex

    index = FaissIndex()
    index.populate({"index": faiss_index, "metadatas": metadatas})

    return index
