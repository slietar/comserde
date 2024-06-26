import json
import pickle
import struct
from typing import IO, Any, Literal, overload

from .decoding import DecodingError, read_bytes, read_nt_bytes, read_struct
from .error import DeserializationError
from .vlq import (read_vlq, read_vlq_signed, read_vlq_sized, write_vlq,
                  write_vlq_signed, write_vlq_sized)


EncodingFormat = Literal[
  'bool',

  'u8', 'u16', 'u32', 'u64',
  'i8', 'i16', 'i32', 'i64',
  'v8', 'v16', 'v32', 'v64',
  'w8', 'w16', 'w32', 'w64',
  'f32', 'f64',

  'bytes', 'nt-bytes',
  'utf-8', 'utf-16',

  'json',
  'object',
  'pickle',
  'void'
]

def serialize(value: Any, /, file: IO[bytes], encoding: EncodingFormat):
  match encoding:
    case 'bool':
      file.write(struct.pack('?', value))

    case 'u8':
      file.write(struct.pack('<B', value))
    case 'u16':
      file.write(struct.pack('<H', value))
    case 'u32':
      file.write(struct.pack('<I', value))
    case 'u64':
      file.write(struct.pack('<Q', value))
    case 'i8':
      file.write(struct.pack('<b', value))
    case 'i16':
      file.write(struct.pack('<h', value))
    case 'i32':
      file.write(struct.pack('<i', value))
    case 'i64':
      file.write(struct.pack('<q', value))
    case 'v8' | 'v16' | 'v32' | 'v64':
      write_vlq(value, file)
    case 'v8':
      write_vlq_sized(value, file)
    case 'v16':
      write_vlq_sized(value, file, fixed_size=1)
    case 'v32':
      write_vlq_sized(value, file, fixed_size=2)
    case 'v64':
      write_vlq_sized(value, file, fixed_size=3)
    case 'w8':
      write_vlq_signed(value, file)
    case 'w16':
      write_vlq_signed(value, file, fixed_size=1)
    case 'w32':
      write_vlq_signed(value, file, fixed_size=2)
    case 'w64':
      write_vlq_signed(value, file, fixed_size=3)
    case 'f32':
      file.write(struct.pack('<f', value))
    case 'f64':
      file.write(struct.pack('<d', value))

    case 'bytes':
      write_vlq(len(value), file)
      file.write(value)
    case 'nt-bytes':
      file.write(value)
      file.write(b"\x00")
    case 'utf-8' | 'utf-16':
      serialize(value.encode(encoding), file, 'bytes')

    case 'json':
      serialize(json.dumps(value), file, 'utf-8')
    case 'object':
      from .composite import serialize as composite_serialize

      serialize(type(value).__module__, file, 'utf-8')
      serialize(type(value).__qualname__, file, 'utf-8')

      composite_serialize(value, file, type(value))
    case 'pickle':
      serialize(pickle.dumps(value), file, 'bytes')
    case 'void':
      pass

    case _:
      raise ValueError("Invalid encoding")


@overload
def deserialize(file: IO[bytes], encoding: Literal['bytes']) -> bytes:
  ...

@overload
def deserialize(file: IO[bytes], encoding: Literal['f32', 'f64']) -> float:
  ...

@overload
def deserialize(file: IO[bytes], encoding: EncodingFormat) -> Any:
  ...

def deserialize(file: IO[bytes], encoding: EncodingFormat) -> Any:
  try:
    match encoding:
      case 'bool':
        return read_struct('?', file)[0]
      case 'u8':
        return read_struct('<B', file)[0]
      case 'u16':
        return read_struct('<H', file)[0]
      case 'u32':
        return read_struct('<I', file)[0]
      case 'u64':
        return read_struct('<Q', file)[0]
      case 'i8':
        return read_struct('<b', file)[0]
      case 'i16':
        return read_struct('<h', file)[0]
      case 'i32':
        return read_struct('<i', file)[0]
      case 'i64':
        return read_struct('<q', file)[0]
      case 'v8':
        return read_vlq_sized(file)
      case 'v16':
        return read_vlq_sized(file, fixed_size=1)
      case 'v32':
        return read_vlq_sized(file, fixed_size=2)
      case 'v64':
        return read_vlq_sized(file, fixed_size=3)
      case 'w8':
        return read_vlq_signed(file)
      case 'w16':
        return read_vlq_signed(file, fixed_size=1)
      case 'w32':
        return read_vlq_signed(file, fixed_size=2)
      case 'w64':
        return read_vlq_signed(file, fixed_size=3)
      case 'f32':
        return read_struct('<f', file)[0]
      case 'f64':
        return read_struct('<d', file)[0]

      case 'bytes':
        length = read_vlq(file)
        return read_bytes(length, file)
      case 'nt-bytes':
        return read_nt_bytes(file)
      case 'utf-8' | 'utf-16':
        return deserialize(file, 'bytes').decode(encoding)

      case 'json':
        return json.loads(deserialize(file, 'utf-8'))
      case 'object':
        from importlib import import_module

        from .composite import deserialize as composite_deserialize

        module_name = deserialize(file, 'utf-8')
        qualname = deserialize(file, 'utf-8')

        obj = import_module(module_name)

        for part in qualname.split('.'):
          obj = getattr(obj, part)

        assert isinstance(obj, type)

        return composite_deserialize(file, obj)
      case 'pickle':
        return pickle.loads(deserialize(file, 'bytes'))
      case 'void':
        return ()

      case _:
        raise ValueError("Invalid encoding")
  except (DecodingError, EOFError, UnicodeDecodeError, struct.error) as e:
    raise DeserializationError from e


def get_encoding_for_int_range(max_value: int, /, *, signed: bool = False) -> EncodingFormat:
  """
  Return the appropriate encoding for an integer ranging from 0 to a fixed value.

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
