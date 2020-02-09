import tempfile
from contextlib import contextmanager
from typing import Optional

from google.cloud import storage

from needlestack.data_sources import DataSource
from needlestack.utilities.multiton import multiton_pattern


class GcsDataSource(DataSource):
    """Data source that lives locally on disk as a file.

    Attributes:
        bucket_name: Google Cloud Storage bucket name
        blob_name: Blob name in bucket
        project_name: Google Cloud Platform project name
        credentials_file: JSON credentials file for GCP. If not provided,
            the google.cloud package will try to get the credentials implicitly
    """

    bucket_name: str
    blob_name: str
    project_name: str
    credentials_file: str

    @property
    def blob(self) -> storage.Blob:
        client = get_client(self.credentials_file)
        bucket = client.get_bucket(self.bucket_name)
        return bucket.get_blob(self.blob_name)

    @property
    def last_modified(self):
        timestamp = self.blob.updated
        if timestamp is not None:
            return timestamp.timestamp()
        else:
            return None

    def populate_from_proto(self, proto):
        self.bucket_name = proto.bucket_name
        self.blob_name = proto.blob_name
        self.project_name = proto.project_name
        self.credentials_file = proto.credentials_file

    @contextmanager
    def local_filename(self):
        with tempfile.NamedTemporaryFile() as f:
            self.blob.download_to_file(f)
            yield f.name

    @contextmanager
    def get_content(self, mode: str = "rb"):
        yield self.blob.download_as_string()


def create_client(credentials_file: Optional[str] = None) -> storage.Client:
    if credentials_file:
        return storage.Client.from_service_account_json(credentials_file)
    else:
        return storage.Client()


get_client = multiton_pattern(create_client)
