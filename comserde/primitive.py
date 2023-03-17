import json
import pickle
import struct
from typing import Any, Literal, overload

from . import vlq
from .decoder import Decoder, DecodingError
from .error import DeserializationError


EncodingFormat = Literal[
  'bool',

  'u8', 'u16', 'u32', 'u64',
  'i8', 'i16', 'i32', 'i64',
  'v8', 'v16', 'v32', 'v64',
  'f32', 'f64',

  'bytes', 'nt-bytes',
  'utf-8', 'utf-16',

  'json',
  'pickle',
  'void'
]

def serialize(value: Any, /, encoding: EncodingFormat) -> bytes:
  match encoding:
    case 'bool':
      return struct.pack('?', value)

    case 'u8':
      return struct.pack('<B', value)
    case 'u16':
      return struct.pack('<H', value)
    case 'u32':
      return struct.pack('<I', value)
    case 'u64':
      return struct.pack('<Q', value)
    case 'i8':
      return struct.pack('<b', value)
    case 'i16':
      return struct.pack('<h', value)
    case 'i32':
      return struct.pack('<i', value)
    case 'i64':
      return struct.pack('<q', value)
    case 'v8' | 'v16' | 'v32' | 'v64':
      return vlq.encode(value)
    case 'f32':
      return struct.pack('<f', value)
    case 'f64':
      return struct.pack('<d', value)

    case 'bytes':
      return vlq.encode(len(value)) + value
    case 'nt-bytes':
      return value + b"\x00"
    case 'utf-8' | 'utf-16':
      return serialize(value.encode(encoding), 'bytes')

    case 'json':
      return serialize(json.dumps(value), 'utf-8')
    case 'pickle':
      return serialize(pickle.dumps(value), 'bytes')
    case 'void':
      return bytes()

    case _:
      raise ValueError("Invalid encoding")


@overload
def deserialize(decoder: Decoder, encoding: Literal['bytes']) -> bytes:
  ...

@overload
def deserialize(decoder: Decoder, encoding: Literal['f32', 'f64']) -> float:
  ...

@overload
def deserialize(decoder: Decoder, encoding: EncodingFormat) -> Any:
  ...

def deserialize(decoder: Decoder, encoding: EncodingFormat) -> Any:
  try:
    match encoding:
      case 'bool':
        return decoder.read_struct('?')[0]
      case 'u8':
        return decoder.read_struct('<B')[0]
      case 'u16':
        return decoder.read_struct('<H')[0]
      case 'u32':
        return decoder.read_struct('<I')[0]
      case 'u64':
        return decoder.read_struct('<Q')[0]
      case 'i8':
        return decoder.read_struct('<b')[0]
      case 'i16':
        return decoder.read_struct('<h')[0]
      case 'i32':
        return decoder.read_struct('<i')[0]
      case 'i64':
        return decoder.read_struct('<q')[0]
      case 'v8' | 'v16' | 'v32' | 'v64':
        return decoder.read_vlq()
      case 'f32':
        return decoder.read_struct('<f')[0]
      case 'f64':
        return decoder.read_struct('<d')[0]

      case 'bytes':
        length = decoder.read_vlq()
        return decoder.read_bytes(length)
      case 'nt-bytes':
        return decoder.read_nt_bytes()
      case 'utf-8' | 'utf-16':
        return deserialize(decoder, 'bytes').decode(encoding)

      case 'json':
        return json.loads(deserialize(decoder, 'utf-8'))
      case 'pickle':
        return pickle.loads(deserialize(decoder, 'bytes'))
      case 'void':
        return ()

      case _:
        raise ValueError("Invalid encoding")
  except (DecodingError, struct.error) as e:
    raise DeserializationError from e


def get_encoding_for_int_range(max_value: int, /, *, signed: bool = False) -> EncodingFormat:
  """
  Returns the appropriate encoding for an integer ranging from 0 to a fixed value.

  Parameters
    max_value: The maximum encoded integer, excluded.
    signed: Whether the encoded integer can be negative.
  """

  assert not signed

  for encoding, limit in [
    ('u8', 1 << 8),
    ('u16', 1 << 16),
    ('u32', 1 << 32),
    ('u64', 1 << 64)
  ]:
    if max_value <= limit:
      return encoding

  return 'v64'
