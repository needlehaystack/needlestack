from needlestack.apis import data_sources_pb2
from needlestack.data_sources import DataSource


def test_local_data_source(tmpdir):
    filename = str(tmpdir.join("myfile.txt"))
    value = b"winter is coming"
    with open(filename, "wb") as f:
        f.write(value)

    proto = data_sources_pb2.DataSource(
        local_data_source=data_sources_pb2.LocalDataSource(filename=filename)
    )
    data_source = DataSource.from_proto(proto)

    with data_source.local_filename() as local_filename:
        assert local_filename == filename

    with data_source.get_content() as data:
        assert data.read() == value
