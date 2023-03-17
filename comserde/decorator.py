import dataclasses
from typing import Any, Optional, TypeVar

from . import composite
from .decoder import Decoder


T = TypeVar('T')

def serializable(target: type[T] | dict[str, composite.EncodingFormat], /) -> type[T]:
  if type(target) == dict:
    return lambda cls: process_cls(cls, target) # type: ignore
  else:
    return process_cls(target, None)

def process_cls(cls, raw_fields: Optional[dict[str, composite.EncodingFormat]], /):
  if raw_fields is None:
    assert dataclasses.is_dataclass(cls)
    fields: dict[str, composite.EncodingFormat] = cls.__dict__.get('__annotations__', dict())
  else:
    fields = raw_fields

  class new_cls(cls):
    def __serialize__(self):
      output = bytes()

      for field_name, field_type in fields.items():
        field_value = getattr(self, field_name)
        output += composite.serialize(field_value, field_type)

      return output

    @classmethod
    def __deserialize__(cls, decoder: Decoder):
      field_values = dict[str, Any]()

      for field_name, field_type in fields.items():
        field_values[field_name] = composite.deserialize(decoder, field_type)

      obj = cls.__new__(cls)

      if hasattr(obj, '__deserialize_init__'):
        obj.__deserialize_init__(**field_values)
      else:
        for field_name, field_value in field_values.items():
          setattr(obj, field_name, field_value)

      return obj


  new_cls.__name__ = cls.__name__
  new_cls.__qualname__ = cls.__qualname__

  return new_cls
