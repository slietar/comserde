from io import BytesIO
from typing import IO, Any, Optional

from .composite import EncodingFormat, deserialize, serialize
from .error import DeserializationEOFError, DeserializationError


def dump(value: Any, /, file: IO[bytes], encoding: Optional[EncodingFormat] = None):
  serialize(value, file, encoding or type(value))

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

  file = BytesIO()
  dump(value, file, encoding)

  return file.getvalue()


def load(file: IO[bytes], encoding: EncodingFormat):
  current_pos = file.tell()

  try:
    return deserialize(file, encoding)
  except DeserializationError as e:
    if file.tell() == current_pos:
      raise DeserializationEOFError from e

    raise

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
    DeserializationEOFError: If `data` is empty.
  """

  return deserialize(BytesIO(data), encoding)


__all__ = [
  'dump',
  'dumps',
  'load',
  'loads'
]
