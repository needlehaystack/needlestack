from unittest.mock import MagicMock

import pytest
from google.protobuf.message import Message

from needlestack.utilities import rpc


def test_unhandled_exception_rpc():
    @rpc.unhandled_exception_rpc(Message)
    def do_nothing(self, request, context):
        return Message()

    assert isinstance(do_nothing(MagicMock(), Message(), MagicMock()), Message)


def test_unhandled_exception_rpc_exception():
    expection_text = "some exception thrown"

    @rpc.unhandled_exception_rpc(Message)
    def raise_exception(self, request, context):
        raise Exception(expection_text)

    with pytest.raises(Exception) as excinfo:
        raise_exception(MagicMock(), Message(), MagicMock())
        assert expection_text == str(excinfo.value)
