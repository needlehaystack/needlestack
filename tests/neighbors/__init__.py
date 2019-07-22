import pytest

from needlestack.apis import neighbors_pb2
from needlestack.neighbors import SpatialIndex


def test_no_datasource(tmpdir):
    proto = neighbors_pb2.SpatialIndex()
    with pytest.raises(ValueError) as excinfo:
        SpatialIndex.from_proto(proto)
        assert "No valid index found" in str(excinfo.value)
