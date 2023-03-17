from typing import Any, Optional

from . import composite
from .decoder import Decoder
from .decorator import serializable
from .decoder import Decoder
from .types import Deserializable, Serializable


def dumps(value: Any, /, encoding: Optional[composite.EncodingFormat] = None):
  return composite.serialize(value, encoding or type(value))

def loads(data: bytes, /, encoding: composite.EncodingFormat):
  return composite.deserialize(Decoder(data), encoding)


__all__ = [
  'Decoder',
  'Deserializable',
  'Serializable',
  'dumps',
  'loads',
  'serializable'
]
