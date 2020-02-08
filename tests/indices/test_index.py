import pytest

from needlestack.apis import indices_pb2
from needlestack.indices import BaseIndex


def test_no_datasource(tmpdir):
    proto = indices_pb2.BaseIndex()
    with pytest.raises(ValueError) as excinfo:
        BaseIndex.from_proto(proto)
        assert "No valid index found" in str(excinfo.value)
