from typing import Any, Optional

from . import composite
from .decoder import Decoder
from .decorator import serializable
from .decoder import Decoder
from .error import DeserializationError
from .types import Deserializable, Serializable


def dumps(value: Any, /, encoding: Optional[composite.EncodingFormat] = None):
  """
  Serializes an object into compact binary data.

  The output data structure is an implementation detail, therefore the data should only be consumed by `loads()` from this package.

  Parameters
    value: The object to serialize.
    encoding: The encoding to use. Defaults to `type(value)`.

  Returns
    Compact binary data which corresponds to `value`.
  """

  return composite.serialize(value, encoding or type(value))

def loads(data: bytes, /, encoding: composite.EncodingFormat):
  """
  Deserializes compact binary data into an object.

  The input data structure is an implementation detail, therefore the data should have been produced by `loads()` from this package.

  Parameters
    data: The data to deserialize.
    encoding: The encoding used to serialize the data.

  Returns
    An object which corresponds to `data`.

  Raises
    DeserializationError If `data` is corrupted or `encoding` is incorrect.
  """

  return composite.deserialize(Decoder(data), encoding)


__all__ = [
  'Decoder',
  'Deserializable',
  'Serializable',
  'dumps',
  'loads',
  'serializable'
]
