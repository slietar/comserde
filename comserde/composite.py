import builtins
import collections
import types
import typing
import warnings
from types import UnionType
from typing import Any, Optional

from . import primitive
from .decoder import Decoder
from .types import Serializable


EncodingFormat = primitive.EncodingFormat | UnionType | type | type[int]

class SerializationEncoding:
  def __init__(self, type: EncodingFormat, /):
    self.type = type

def serialize(value: Any, /, encoding: EncodingFormat) -> bytes:
  match encoding:
    case Serializable():
      return value.__serialize__()
    case builtins.str():
      return primitive.serialize(value, encoding)

    case builtins.bool:
      return primitive.serialize(value, 'bool')
    case builtins.bytearray | builtins.bytes:
      return primitive.serialize(bytes(value), 'bytes')
    case builtins.complex:
      return primitive.serialize(value.real, 'f32') + primitive.serialize(value.imag, 'f32')
    case builtins.float:
      return primitive.serialize(value, 'f32')
    case builtins.int:
      return primitive.serialize(value, 'v8')
    case builtins.str:
      return primitive.serialize(value, 'utf-8')

    case types.EllipsisType | types.NoneType:
      return bytes()
    case types.GenericAlias(__args__=(item_type,), __origin__=(builtins.list | builtins.set)):
      return primitive.serialize(len(value), 'v8') + bytes().join(serialize(item, item_type) for item in value)
    case types.GenericAlias(__args__=(item_type,), __origin__=collections.deque):
      return serialize(value.maxlen, Optional[int]) + serialize(value, builtins.list[item_type])
    case typing._AnnotatedAlias(__args__=(default_type,), __metadata__=metadata_entries): # type: ignore
      for entry in metadata_entries:
        if isinstance(entry, SerializationEncoding):
          return serialize(value, entry.type)

      return serialize(value, default_type)
    case typing._LiteralGenericAlias(__args__=variants): # type: ignore
      return primitive.serialize(variants.index(value), 'v8') if len(variants) > 1 else bytes()
    case types.UnionType(__args__=variants) | typing._UnionGenericAlias(__args__=variants): # type: ignore
      for variant_index, variant_type in enumerate(variants):
        match variant_type:
          case typing._AnnotatedAlias(__args__=(inner_type,)) | inner_type if isinstance(value, inner_type): # type: ignore
            return primitive.serialize(variant_index, 'v8') + serialize(value, variant_type)

      raise ValueError("No matching enumeration found")

    case _:
      warnings.warn(f"Implicitly pickling object of type '{encoding}'")
      return primitive.serialize(value, 'pickle')


def deserialize(decoder: Decoder, type: EncodingFormat) -> Any:
  match type:
    case Serializable():
      return type.__deserialize__(decoder)
    case builtins.str():
      return primitive.deserialize(decoder, type)

    case builtins.bytearray:
      return bytearray(primitive.deserialize(decoder, 'bytes'))
    case builtins.bytes:
      return primitive.deserialize(decoder, 'bytes')
    case builtins.complex:
      return complex(primitive.deserialize(decoder, 'f32'), primitive.deserialize(decoder, 'f32'))
    case builtins.float:
      return primitive.deserialize(decoder, 'f32')
    case builtins.int:
      return primitive.deserialize(decoder, 'v8')
    case builtins.str:
      return primitive.deserialize(decoder, 'utf-8')

    case types.EllipsisType:
      return Ellipsis
    case types.NoneType:
      return None
    case types.GenericAlias(__args__=(item_type,), __origin__=builtins.list):
      return [deserialize(decoder, item_type) for _ in range(primitive.deserialize(decoder, 'v8'))]
    case types.GenericAlias(__args__=(item_type,), __origin__=builtins.set):
      return {deserialize(decoder, item_type) for _ in range(primitive.deserialize(decoder, 'v8'))}
    case types.GenericAlias(__args__=(item_type,), __origin__=collections.deque):
      maxlen = deserialize(decoder, Optional[int])
      return collections.deque(deserialize(decoder, builtins.list[item_type]), maxlen=maxlen)
    case typing._AnnotatedAlias(__args__=(default_type,), __metadata__=metadata_entries): # type: ignore
      for entry in metadata_entries:
        if isinstance(entry, SerializationEncoding):
          return deserialize(decoder, entry.type)

      return deserialize(decoder, default_type)
    case typing._LiteralGenericAlias(__args__=variants): # type: ignore
      return variants[primitive.deserialize(decoder, 'v8')] if len(variants) > 1 else variants[0]
    case types.UnionType(__args__=variants) | typing._UnionGenericAlias(__args__=variants): # type: ignore
      variant_index = primitive.deserialize(decoder, 'v8')
      return deserialize(decoder, variants[variant_index])

    case _:
      return primitive.deserialize(decoder, 'pickle')
