import os
from contextlib import contextmanager

from needlestack.data_sources import DataSource


class LocalDataSource(DataSource):
    """Data source that lives locally on disk as a file

    Attributes:
        filename: Filename on disk
    """

    filename: str

    @property
    def last_modified(self):
        """Last time a data source was modified"""
        return os.path.getmtime(self.filename)

    def populate_from_proto(self, proto):
        self.filename = proto.filename

    @contextmanager
    def local_filename(self):
        yield self.filename

    @contextmanager
    def get_content(self, mode: str = "rb"):
        with open(self.filename, mode) as f:
            yield f
