from contextlib import contextmanager

from needlestack.apis import data_sources_pb2
from needlestack.exceptions import DeserializationError


class DataSource(object):
    """Base class for data source implementations. Defines interfaces
    for populating access data."""

    @staticmethod
    def from_proto(proto: data_sources_pb2.DataSource) -> "DataSource":
        """Factory method to construct the correct implementation of a DataSource
        from a protobuf.

        Args:
            proto: Protobuf defining how to access data
        """
        data_source: DataSource
        source = proto.WhichOneof("source")
        if source == "local_data_source":
            from needlestack.data_sources.local import LocalDataSource

            data_source = LocalDataSource()
            data_source.populate_from_proto(proto.local_data_source)
        elif source == "gcs_data_source":
            from needlestack.data_sources.gcs import GcsDataSource

            data_source = GcsDataSource()
            data_source.populate_from_proto(proto.gcs_data_source)
        else:
            raise DeserializationError("No valid data source found from protobuf")

        return data_source

    @property
    def last_modified(self) -> float:
        """Last time a data source was modified"""
        raise NotImplementedError()

    def populate_from_proto(self, proto: data_sources_pb2.DataSource):
        """Populate DataSource from protobuf defining the data source

        Args:
            proto: Protobuf to populate fields for DataSource implementation
        """
        raise NotImplementedError()

    @contextmanager
    def local_filename(self):
        """Yield a local filename to access the data as file"""
        raise NotImplementedError()

    @contextmanager
    def get_content(self, mode: str):
        """Yield raw data from the data source"""
        raise NotImplementedError()
