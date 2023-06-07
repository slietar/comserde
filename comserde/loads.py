from typing import Any, Optional

from .composite import EncodingFormat, deserialize, serialize
from .decoder import Decoder


def dumps(value: Any, /, encoding: Optional[EncodingFormat] = None):
  """
  Serialize an object into compact binary data.

  The output data structure is an implementation detail, therefore the data should only be consumed by `loads()` from this package.

  Parameters
    value: The object to serialize.
    encoding: The encoding to use. Defaults to `type(value)`.

  Returns
    Compact binary data which corresponds to `value`.
  """

  return serialize(value, encoding or type(value))


def loads(data: bytes, /, encoding: EncodingFormat):
  """
  Deserialize compact binary data into an object.

  The input data structure is an implementation detail, therefore the data should have been produced by `loads()` from this package.

  Parameters
    data: The data to deserialize.
    encoding: The encoding used to serialize the data.

  Returns
    An object which corresponds to `data`.

  Raises
    DeserializationError: If `data` is corrupted or `encoding` is incorrect.
  """

  return deserialize(Decoder(data), encoding)


__all__ = [
  'dumps',
  'loads'
]
