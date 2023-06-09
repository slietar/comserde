import builtins
import collections
import sys
import types
import typing
import warnings
from dataclasses import dataclass
from types import UnionType
from typing import IO, Any, Optional

from .primitive import EncodingFormat as PrimitiveEncodingFormat
from .primitive import deserialize as primitive_deserialize
from .primitive import serialize as primitive_serialize
from .types import Serializable


EncodingFormat = PrimitiveEncodingFormat | UnionType | type | type[int]

@dataclass
class SerializationFormat:
  type: EncodingFormat


def serialize(value: Any, /, file: IO[bytes], encoding: EncodingFormat):
  match encoding:
    case Serializable():
      encoding.__serialize__(value, file)
    case builtins.str():
      primitive_serialize(value, file, encoding)

    case builtins.bool:
      primitive_serialize(value, file, 'bool')
    case builtins.bytearray | builtins.bytes:
      primitive_serialize(bytes(value), file, 'bytes')
    case builtins.complex:
      primitive_serialize(value.real, file, 'f32')
      primitive_serialize(value.imag, file, 'f32')
    case builtins.float:
      primitive_serialize(value, file, 'f32')
    case builtins.int:
      primitive_serialize(value, file, 'v8')
    case builtins.str:
      primitive_serialize(value, file, 'utf-8')

    case builtins.type() if (pathlib := sys.modules.get('pathlib')) and issubclass(encoding, pathlib.PurePath):
      return primitive_serialize(str(value), file, 'utf-8')

    case typing.Any:
      serialize(value, file, 'object')
    case types.EllipsisType | types.NoneType:
      pass
    case types.GenericAlias(__args__=(item_type,), __origin__=(builtins.list | builtins.set)):
      primitive_serialize(len(value), file, 'v8')

      for item in value:
        serialize(item, file, item_type)
    case types.GenericAlias(__args__=(item_type,), __origin__=collections.deque):
      serialize(value.maxlen, file, Optional[int])
      serialize(value, file, builtins.list[item_type])
    case typing._AnnotatedAlias(__args__=(default_type,), __metadata__=metadata_entries): # type: ignore
      for entry in metadata_entries:
        if isinstance(entry, SerializationFormat):
          serialize(value, file, entry.type)
          return

      serialize(value, file, default_type)
    case typing._LiteralGenericAlias(__args__=variants): # type: ignore
      if len(variants) > 1:
        primitive_serialize(variants.index(value), file, 'v8')
    case types.UnionType(__args__=variants) | typing._UnionGenericAlias(__args__=variants): # type: ignore
      for variant_index, variant_type in enumerate(variants):
        match variant_type:
          case typing._AnnotatedAlias(__args__=(inner_type,)) | inner_type if isinstance(value, inner_type): # type: ignore
            primitive_serialize(variant_index, file, 'v8')
            serialize(value, file, variant_type)
            break
      else:
        raise ValueError("No matching enumeration found")

    case _:
      warnings.warn(f"Implicitly pickling object of type '{type(value)}' with format '{encoding}'", stacklevel=2)
      primitive_serialize(value, file, 'pickle')


def deserialize(file: IO[bytes], encoding: EncodingFormat) -> Any:
  match encoding:
    case Serializable():
      return encoding.__deserialize__(file)
    case builtins.str():
      return primitive_deserialize(file, encoding)

    case builtins.bytearray:
      return bytearray(primitive_deserialize(file, 'bytes'))
    case builtins.bytes:
      return primitive_deserialize(file, 'bytes')
    case builtins.complex:
      return complex(primitive_deserialize(file, 'f32'), primitive_deserialize(file, 'f32'))
    case builtins.float:
      return primitive_deserialize(file, 'f32')
    case builtins.int:
      return primitive_deserialize(file, 'v8')
    case builtins.str:
      return primitive_deserialize(file, 'utf-8')

    case builtins.type() if (pathlib := sys.modules.get('pathlib')) and issubclass(encoding, pathlib.PurePath):
      return encoding(primitive_deserialize(file, 'utf-8'))

    case typing.Any:
      return deserialize(file, 'object')
    case types.EllipsisType:
      return Ellipsis
    case types.NoneType:
      return None
    case types.GenericAlias(__args__=(item_type,), __origin__=builtins.list):
      return [deserialize(file, item_type) for _ in range(primitive_deserialize(file, 'v8'))]
    case types.GenericAlias(__args__=(item_type,), __origin__=builtins.set):
      return {deserialize(file, item_type) for _ in range(primitive_deserialize(file, 'v8'))}
    case types.GenericAlias(__args__=(item_type,), __origin__=collections.deque):
      maxlen = deserialize(file, Optional[int])
      return collections.deque(deserialize(file, builtins.list[item_type]), maxlen=maxlen)
    case typing._AnnotatedAlias(__args__=(default_type,), __metadata__=metadata_entries): # type: ignore
      for entry in metadata_entries:
        if isinstance(entry, SerializationFormat):
          return deserialize(file, entry.type)

      return deserialize(file, default_type)
    case typing._LiteralGenericAlias(__args__=variants): # type: ignore
      return variants[primitive_deserialize(file, 'v8')] if len(variants) > 1 else variants[0]
    case types.UnionType(__args__=variants) | typing._UnionGenericAlias(__args__=variants): # type: ignore
      variant_index = primitive_deserialize(file, 'v8')
      return deserialize(file, variants[variant_index])

    case _:
      return primitive_deserialize(file, 'pickle')


__all__ = [
  'EncodingFormat',
  'SerializationFormat',
  'deserialize',
  'serialize'
]
