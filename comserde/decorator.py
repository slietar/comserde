import dataclasses
import functools
import operator
from abc import ABC
from typing import Any, Optional, TypeVar

from . import composite
from .decoder import Decoder
from .types import Serializable


T = TypeVar('T')

def serializable(target: type[T] | dict[str, composite.EncodingFormat], /) -> type[T]:
  """
  Adds serialization and deserialization capabilities to a class.

  Parameters
    target: A dictionary describing the encoding of each attribute of an instance of this class. Only valid when used on a regular class (as opposed to a `dataclasses.dataclass`).
  """

  if type(target) == dict:
    return lambda cls: process_cls(cls, target) # type: ignore
  else:
    return process_cls(target, None) # type: ignore

def process_cls(target, raw_fields: Optional[dict[str, composite.EncodingFormat]], /):
  if raw_fields is None:
    assert dataclasses.is_dataclass(target)
    fields: dict[str, composite.EncodingFormat] = target.__dict__.get('__annotations__', dict())
  else:
    fields = raw_fields

  def serialize(self):
    output = bytes()

    for field_name, field_type in fields.items():
      field_value = getattr(self, field_name)
      output += composite.serialize(field_value, field_type)

    return output

  @classmethod
  def deserialize(cls, decoder: Decoder):
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

  target.__deserialize__ = deserialize
  target.__serialize__ = serialize

  return target


def union_serializable(target: type[T]) -> type[T]:
  @functools.cache
  def get_encoding():
    return functools.reduce(operator.or_, target.__subclasses__())

  if not issubclass(target, ABC):
    raise ValueError("Target class must be an abstract base class")

  def serialize(self):
    assert isinstance(target, Serializable)

    if type(self).__serialize__ is target.__serialize__:
      raise ValueError(f"Instance of '{type(self).__name__}' is not serializable")

    return composite.serialize(self, get_encoding())

  @staticmethod
  def deserialize(decoder: Decoder):
    return composite.deserialize(decoder, get_encoding())

  target.__deserialize__ = deserialize # type: ignore
  target.__serialize__ = serialize # type: ignore

  return target
