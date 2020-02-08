from needlestack.apis import data_sources_pb2
from needlestack.data_sources import DataSource
from needlestack.data_sources import gcs


def test_create_client(gcs_storage_client):
    assert gcs.create_client() is not None
    assert gcs.create_client("credentials.json") is not None


def test_get_client(gcs_storage_client):
    client_1 = gcs.get_client()
    client_2 = gcs.get_client()
    assert client_1 == client_2


def test_gcs_data_source(gcs_storage_client):
    proto = data_sources_pb2.DataSource(
        gcs_data_source=data_sources_pb2.GcsDataSource(
            bucket_name="my_bucket", blob_name="my_blob"
        )
    )
    data_source = DataSource.from_proto(proto)

    assert isinstance(data_source.last_modified, float)

    with data_source.local_filename() as f:
        assert isinstance(f, str)

    with data_source.get_content() as content:
        assert isinstance(content, bytes)
