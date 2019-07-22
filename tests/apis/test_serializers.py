import pytest
import numpy as np

from needlestack.apis import serializers
from needlestack.apis import tensors_pb2


def test_ndarray_to_proto_numpy():
    X = np.array([1, 2, 3], dtype="float32")
    proto = serializers.ndarray_to_proto(X)
    assert proto.shape == [3]
    assert proto.dtype == tensors_pb2.NDArray.FLOAT32
    assert proto.numpy_content == X.tobytes()

    proto = serializers.ndarray_to_proto(X, dtype="float64")
    assert proto.dtype == tensors_pb2.NDArray.FLOAT64


def test_ndarray_to_proto_list():
    X = [1, 2, 3]
    proto = serializers.ndarray_to_proto(X, dtype="int8", shape=(3,))
    assert proto.shape == [3]
    assert proto.dtype == tensors_pb2.NDArray.INT8
    assert proto.numpy_content is not None


@pytest.mark.parametrize(
    "X",
    [
        np.array([1991, 11, 21], dtype="int32"),
        np.array([1998, 11, 21], dtype="int64"),
        np.array([2002, 12, 13], dtype="float32"),
        np.array([2017, 3, 3], dtype="float64"),
    ],
)
def test_proto_to_ndarray_numpy(X):
    proto = serializers.ndarray_to_proto(X)
    X_prime = serializers.proto_to_ndarray(proto)
    assert np.array_equal(X, X_prime)


@pytest.mark.parametrize(
    "value,shape,dtype",
    [
        ([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], (2, 3), "float32"),
        ([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], (3, 2), "float64"),
        ([1, 2, 3, 4, 5, 6], (1, 6), "int32"),
        ([1, 2, 3, 4, 5, 6], (6, 1), "int64"),
    ],
)
def test_proto_to_ndarray(value, shape, dtype):
    if dtype == "float32":
        proto = tensors_pb2.NDArray(
            float_val=value, dtype=tensors_pb2.NDArray.FLOAT32, shape=shape
        )
    elif dtype == "float64":
        proto = tensors_pb2.NDArray(
            double_val=value, dtype=tensors_pb2.NDArray.FLOAT64, shape=shape
        )
    elif dtype == "int32":
        proto = tensors_pb2.NDArray(
            int_val=value, dtype=tensors_pb2.NDArray.INT32, shape=shape
        )
    elif dtype == "int64":
        proto = tensors_pb2.NDArray(
            long_val=value, dtype=tensors_pb2.NDArray.INT64, shape=shape
        )

    X = np.array(value, dtype=dtype).reshape(shape)
    X_prime = serializers.proto_to_ndarray(proto)
    assert np.array_equal(X, X_prime)


@pytest.mark.parametrize(
    "proto,error",
    [
        (
            tensors_pb2.NDArray(int_val=[1, 2, 3], dtype=tensors_pb2.NDArray.INT8),
            "Missing attribute shape",
        ),
        (tensors_pb2.NDArray(shape=[5]), "Missing value attribute"),
    ],
)
def test_proto_to_ndarray_missing_info(proto, error):
    with pytest.raises(ValueError) as excinfo:
        serializers.proto_to_ndarray(proto)
        assert "Missing attribute shape" in str(excinfo.value)


@pytest.mark.parametrize(
    "X,dtype,shape,error",
    [
        ("unsupported_input", None, None, "Unsupported NDArray"),
        (np.array([1], dtype="complex64"), None, None, "dtype not yet supported"),
        (np.array([1]), "bad_dtype", None, "dtype not supported"),
        ([1, 2, 3, 4], None, None, "Serializing list needs dtype"),
        ([1, 2, 3, 4], "int8", None, "Serializing list needs shape"),
        ([1, 2, 3, 4], "int8", (100,), "Shape mismatch"),
    ],
)
def test_ndarray_to_proto_unsupported_input(X, dtype, shape, error):
    with pytest.raises(ValueError) as excinfo:
        serializers.ndarray_to_proto(X, dtype=dtype, shape=shape)
        assert error in str(excinfo.value)


def test_metadata_list_to_proto():
    i = 100
    ids = [str(i) for i in range(i)]
    fields_list = [(i, float(i)) for i in range(i)]
    fieldtypes = ("int", "float")
    fieldnames = ("my_int", "my_float")
    protos = serializers.metadata_list_to_proto(
        ids, fields_list, fieldtypes, fieldnames
    )
    assert len(protos) == i


@pytest.mark.parametrize(
    "id,fields,fieldtypes,fieldnames",
    [
        ("my_id", ("field1"), None, None),
        ("my_id", ("field1", 1), ("string", "int"), ("meta1", "meta2")),
    ],
)
def test_metadata_to_proto(id, fields, fieldtypes, fieldnames):
    proto = serializers.metadata_to_proto(id, fields, fieldtypes, fieldnames)
    assert proto.id == id
    assert len(proto.fields) == len(fields)


@pytest.mark.parametrize(
    "field,fieldtype,fieldname",
    [
        ("my_value", "string", "my_field"),
        ("my_value", None, None),
        (3.14, "double", None),
        (3.14, None, "my_pi"),
        (2.718, "float", "my_euler"),
        (2.718, None, None),
        (1984, "long", None),
        (1984, None, None),
        (1991, "int", None),
        (1991, None, None),
        (True, "bool", "my_bool"),
        (False, None, None),
    ],
)
def test_metadata_field_to_proto(field, fieldtype, fieldname):
    proto = serializers.metadata_field_to_proto(field, fieldtype, fieldname)
    assert proto.name == (fieldname or "")
    val_type = proto.WhichOneof("value")
    if isinstance(field, (int, float)):
        assert abs(getattr(proto, val_type) - field) < 1e-4
    else:
        assert getattr(proto, val_type) == field


@pytest.mark.parametrize(
    "field,fieldtype,fieldname", [(object(), None, None), (object(), "string", None)]
)
def test_metadata_field_to_proto_not_serializable(field, fieldtype, fieldname):
    with pytest.raises(ValueError) as excinfo:
        serializers.metadata_field_to_proto(field, fieldtype, fieldname)
        assert "not serializable" in str(excinfo.value)
