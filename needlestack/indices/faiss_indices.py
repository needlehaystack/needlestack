import tempfile
from typing import List, Dict

import faiss
import numpy as np

from needlestack.apis import indices_pb2
from needlestack.data_sources import DataSource
from needlestack.indices import BaseIndex
from needlestack.exceptions import UnsupportedIndexOperationException


class FaissIndex(BaseIndex):

    """Implementation of a BaseIndex using Faiss's index classes

    Attributes:
        index: Faiss index object
        metadatas: List of metadata for items in index
        data_source: Data source to load index
        id2index: Dictionary from metadata id to index in Faiss index
        enable_id_to_vector: Enable retrieving vector from id
    """

    index: faiss.Index
    metadatas: List[indices_pb2.Metadata]
    data_source: DataSource
    id2index: Dict[str, int]
    enable_id_to_vector: bool = False

    @property
    def dimension(self):
        return self.index.d

    @property
    def count(self):
        return self.index.ntotal

    def populate_from_proto(self, proto: indices_pb2.FaissIndex):
        self.data_source = DataSource.from_proto(proto.data_source)

    def populate(self, data):
        self.index = data.get("index")
        self.metadatas = data.get("metadatas")
        self.modified_time = data.get("modified_time")

    def serialize(self):
        with tempfile.NamedTemporaryFile() as f:
            faiss.write_index(self.index, f.name)
            index_binary = f.read()

        return indices_pb2.FaissIndex(
            index_binary=index_binary, metadatas=self.metadatas
        )

    def _load(self):
        with self.data_source.get_content() as content:
            proto = indices_pb2.FaissIndex.FromString(content.read())

        with tempfile.NamedTemporaryFile() as f:
            f.write(proto.index_binary)
            f.seek(0)
            proto.ClearField("index_binary")
            faiss_index = faiss.read_index(f.name)

        self.populate(
            {
                "index": faiss_index,
                "metadatas": proto.metadatas,
                "modified_time": self.data_source.last_modified,
            }
        )

        self._set_id_to_vector(self.enable_id_to_vector)

    def update_available(self):
        if self.modified_time is None:
            return True
        elif self.modified_time < self.data_source.last_modified:
            return True
        else:
            return False

    def _set_id_to_vector(self, enable: bool):
        if enable:
            self.id2index = {
                metadata.id: i for i, metadata in enumerate(self.metadatas)
            }
            self.enable_id_to_vector = True
        else:
            self.id2index = {}
            self.enable_id_to_vector = False

    def _get_metadata_by_index(self, i):
        return self.metadatas[i]

    def _get_vector_by_index(self, i):
        start = self.index.d * i
        end = self.index.d * (i + 1)
        data = [self.index.xb.at(i) for i in range(start, end)]
        return np.array(data).astype("float32")

    def _get_index_by_id(self, id):
        if self.enable_id_to_vector:
            return self.id2index.get(id)
        else:
            raise UnsupportedIndexOperationException(
                "Index does not have enable_id_to_vector"
            )

    def knn_search(self, X, k):
        """Faiss only supports float32 at version 1.5.0"""
        if X.dtype != "float32":
            X = X.astype("float32")
        k = min(k, self.index.ntotal)
        return self.index.search(X, k)
