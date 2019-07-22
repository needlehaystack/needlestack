import pytest

from needlestack.apis import data_sources_pb2
from needlestack.data_sources import DataSource


def test_no_datasource(tmpdir):
    proto = data_sources_pb2.DataSource()
    with pytest.raises(ValueError) as excinfo:
        DataSource.from_proto(proto)
        assert "No valid data source found" in str(excinfo.value)
