import dataclasses
import functools
import operator
from abc import ABC
from enum import Enum, Flag
from typing import IO, Any, Optional, TypeVar

from .composite import EncodingFormat, deserialize, serialize
from .primitive import get_encoding_for_int_range
from .types import Serializable


T = TypeVar('T')

def serializable(target: type[T] | dict[str, EncodingFormat], /) -> type[T]:
  """
  Add serialization and deserialization capabilities to a class.

  Parameters
    target: A dictionary describing the encoding of each attribute of an instance of this class. Only valid when used on a regular class (as opposed to a `dataclasses.dataclass`).
  """

  match target:
    case dict():
      return lambda cls: class_serializable(cls, target) # type: ignore
    case _ if issubclass(target, Flag):
      return flag_serializable(target)
    case _ if issubclass(target, Enum):
      return enum_serializable(target)
    case _ if dataclasses.is_dataclass(target):
      return class_serializable(target, None) # type: ignore
    case _:
      raise ValueError("Invalid decoration")


def enum_serializable(target: type[Enum]):
  variants = list(target)
  encoding = get_encoding_for_int_range(len(variants))

  def _serialize(self, file: IO[bytes]):
    serialize(variants.index(self), file, encoding)

  @staticmethod
  def _deserialize(file: IO[bytes]):
    return variants[deserialize(file, encoding)]

  target.__deserialize__ = _deserialize # type: ignore
  target.__serialize__ = _serialize # type: ignore

  return target


def flag_serializable(target: type[Flag]):
  variants = list(target)
  encoding = get_encoding_for_int_range(2 ** len(variants))

  def _serialize(self, file: IO[bytes]):
    serialize(sum([2 ** index for index, variant in enumerate(variants) if variant in self]), file, encoding)

  @staticmethod
  def _deserialize(file: IO[bytes]):
    value = deserialize(file, encoding)
    return functools.reduce(operator.or_, [variant for index, variant in enumerate(variants) if (value & (2 ** index)) > 0])

  target.__deserialize__ = _deserialize # type: ignore
  target.__serialize__ = _serialize # type: ignore

  return target

def class_serializable(target, raw_fields: Optional[dict[str, EncodingFormat]], /):
  if (raw_fields is None):
    fields: dict[str, EncodingFormat] = target.__dict__.get('__annotations__', dict())
  else:
    fields = raw_fields

  def _serialize(self, file: IO[bytes]):
    for field_name, field_type in fields.items():
      field_value = getattr(self, field_name)
      serialize(field_value, file, field_type)

  @classmethod
  def _deserialize(cls, file: IO[bytes]):
    field_values = dict[str, Any]()

    for field_name, field_type in fields.items():
      field_values[field_name] = deserialize(file, field_type)

    obj = cls.__new__(cls)

    if hasattr(obj, '__init_deserialize__'):
      obj.__init_deserialize__(**field_values)
    else:
      for field_name, field_value in field_values.items():
        setattr(obj, field_name, field_value)

    return obj

  target.__deserialize__ = _deserialize
  target.__serialize__ = _serialize

  return target


def union_serializable(target: type[T]) -> type[T]:
  @functools.cache
  def get_encoding():
    return functools.reduce(operator.or_, target.__subclasses__())

  if not issubclass(target, ABC):
    raise ValueError("Target class must be an abstract base class")

  def _serialize(self, file: IO[bytes]):
    assert isinstance(target, Serializable)

    if type(self).__serialize__ is target.__serialize__:
      raise ValueError(f"Instance of '{type(self).__name__}' is not serializable")

    serialize(self, file, get_encoding())

  @staticmethod
  def _deserialize(file: IO[bytes]):
    return deserialize(file, get_encoding())

  target.__deserialize__ = _deserialize # type: ignore
  target.__serialize__ = _serialize # type: ignore

  return target


__all__ = [
  'serializable',
  'union_serializable'
]
