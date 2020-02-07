from itertools import repeat
from typing import Any, Tuple, Optional, List, Union

import numpy as np

from needlestack.apis import tensors_pb2
from needlestack.apis import indices_pb2
from needlestack.exceptions import SerializationError, DeserializationError


TYPE_TO_ENUM = {
    "float16": tensors_pb2.NDArray.FLOAT16,
    "float32": tensors_pb2.NDArray.FLOAT32,
    "float64": tensors_pb2.NDArray.FLOAT64,
    "int8": tensors_pb2.NDArray.INT8,
    "int16": tensors_pb2.NDArray.INT16,
    "int32": tensors_pb2.NDArray.INT32,
    "int64": tensors_pb2.NDArray.INT64,
}

ENUM_TO_TYPE = {v: k for k, v in TYPE_TO_ENUM.items()}


def ndarray_to_proto(
    X: Any, dtype: Optional[str] = None, shape: Optional[Tuple] = None
) -> tensors_pb2.NDArray:
    """Transforms a Python n-dimension array into a protobuf

    Args:
        X: ND Array
        dtype: Explicit datatype for number
        shape: Explicit shape for nd array
    """
    proto = tensors_pb2.NDArray()

    if isinstance(X, list):
        if dtype is None:
            raise SerializationError("Serializing list needs dtype")
        if shape is None:
            raise SerializationError("Serializing list needs shape")
        X = np.array(X, dtype=dtype)
        if X.shape != shape:
            raise SerializationError("Shape mismatch")

    if isinstance(X, np.ndarray):
        if dtype and X.dtype.name != dtype:
            if dtype in TYPE_TO_ENUM:
                X = X.astype(dtype)
            else:
                raise SerializationError(f"{dtype} dtype not supported")
        dtype_enum = TYPE_TO_ENUM.get(X.dtype.name)
        if dtype_enum is None:
            raise SerializationError(f"{X.dtype.name} dtype not yet supported")
        proto.dtype = dtype_enum
        proto.shape.extend(X.shape)
        proto.numpy_content = X.tobytes()
        return proto
    else:
        raise SerializationError("Unsupported NDArray")


def proto_to_ndarray(proto: tensors_pb2.NDArray) -> np.ndarray:
    """Transform a protobuf into a numpy array

    Args:
        proto: Protobuf for nd array
    """
    dtype = ENUM_TO_TYPE.get(proto.dtype)

    if not proto.shape:
        raise DeserializationError("Missing attribute shape to convert to ndarray")

    if proto.numpy_content and dtype:
        return np.frombuffer(proto.numpy_content, dtype=dtype).reshape(*proto.shape)
    elif proto.float_val:
        dtype = dtype or "float32"
        return np.array(proto.float_val, dtype=dtype).reshape(*proto.shape)
    elif proto.double_val:
        dtype = dtype or "float64"
        return np.array(proto.double_val, dtype=dtype).reshape(*proto.shape)
    elif proto.int_val:
        dtype = dtype or "int32"
        return np.array(proto.int_val, dtype=dtype).reshape(*proto.shape)
    elif proto.long_val:
        dtype = dtype or "int64"
        return np.array(proto.long_val, dtype=dtype).reshape(*proto.shape)
    else:
        raise DeserializationError("Missing value attribute to convert to ndarray")


def metadata_list_to_proto(
    ids: List[str],
    fields_list: List[Tuple],
    fieldtypes: Optional[Tuple[str]] = None,
    fieldnames: Optional[Tuple[str]] = None,
) -> List[indices_pb2.Metadata]:
    """Serialize a set of items with metadata fields

    Args:
        ids: List of ids for items
        fields_list: List of tuple of field values
        fieldtypes: Optional tuple of types for values
        fieldname: Optional tuple of names for values
    """
    return [
        metadata_to_proto(id, fields, fieldtypes, fieldnames)
        for id, fields in zip(ids, fields_list)
    ]


def metadata_to_proto(
    id: str,
    fields: Tuple,
    fieldtypes: Optional[Tuple[str]] = None,
    fieldnames: Optional[Tuple[str]] = None,
) -> indices_pb2.Metadata:
    """Serialize a set of metadata fields for some item.
    Skips over None fields

    Args:
        id: ID for item
        fields: Tuple of primative python values
        fieldtypes: Optional tuple of types for values
        fieldnames: Optional tuple of names for values
    """
    _fieldtypes = fieldtypes or repeat(None, len(fields))
    _fieldnames = fieldnames or repeat(None, len(fields))
    metadata_fields = [
        metadata_field_to_proto(field, fieldtype, fieldname)
        for field, fieldtype, fieldname in zip(fields, _fieldtypes, _fieldnames)
        if field is not None
    ]
    return indices_pb2.Metadata(id=id, fields=metadata_fields)


TYPE_TO_FIELD_TYPE = {str: "string", float: "double", int: "long", bool: "bool"}


def metadata_field_to_proto(
    field: Union[str, int, float, bool],
    fieldtype: Optional[str] = None,
    fieldname: Optional[str] = None,
) -> indices_pb2.MetadataField:
    """Serialize some python value to a metadata field proto

    Args:
        field: Primative python value
        fieldtype: Explicit type to serialize the field
        fieldname: Optional name for this metadata field
    """
    proto = indices_pb2.MetadataField(name=fieldname)

    fieldtype = fieldtype if fieldtype else TYPE_TO_FIELD_TYPE.get(type(field))
    if fieldtype is None:
        raise SerializationError(f"Fieldtype {type(field)} not serializable.")

    if fieldtype == "string" and isinstance(field, str):
        proto.string_val = field
    elif fieldtype == "double" and isinstance(field, float):
        proto.double_val = field
    elif fieldtype == "float" and isinstance(field, float):
        proto.float_val = field
    elif fieldtype == "long" and isinstance(field, int):
        proto.long_val = field
    elif fieldtype == "int" and isinstance(field, int):
        proto.int_val = field
    elif fieldtype == "bool" and isinstance(field, bool):
        proto.bool_val = field
    else:
        raise SerializationError(
            f"Fieldtype {fieldtype} and primative {type(field)} not serializable."
        )

    return proto
