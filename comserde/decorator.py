import dataclasses
import functools
import operator
from abc import ABC
from enum import Enum, Flag
from typing import IO, Any, Callable, Mapping, Optional, TypeVar, overload

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
  fields: dict[str, EncodingFormat]

  if (raw_fields is None):
    dataclass_params = target.__dataclass_params__

    if hasattr(target, '__annotations__'):
      fields = target.__annotations__

    for field_name, field in target.__dataclass_fields__.items():
      if not field.metadata.get('serialize', True) and (field.default is dataclasses.MISSING) and (field.default_factory is dataclasses.MISSING):
        raise ValueError(f"Field '{field_name}' is not serializable and has no default value")
  else:
    dataclass_params = None
    fields = raw_fields

  def _serialize(self, file: IO[bytes]):
    for field_name, field_type in fields.items():
      if dataclass_params:
        field = target.__dataclass_fields__[field_name]

        if not field.metadata.get('serialize', True):
          continue

      field_value = getattr(self, field_name)
      serialize(field_value, file, field_type)

  @classmethod
  def _deserialize(cls, file: IO[bytes]):
    field_values = dict[str, Any]()

    for field_name, field_type in fields.items():
      if dataclass_params:
        field = target.__dataclass_fields__[field_name]

        if field.metadata.get('serialize', True):
          field_values[field_name] = deserialize(file, field_type)
        elif field.default is not dataclasses.MISSING:
          field_values[field_name] = field.default
        elif field.default_factory is not dataclasses.MISSING:
          field_values[field_name] = field.default_factory()
      else:
        field_values[field_name] = deserialize(file, field_type)

    obj = cls.__new__(cls)

    if hasattr(obj, '__init_deserialize__'):
      obj.__init_deserialize__(**field_values)
    else:
      if dataclass_params and dataclass_params.frozen:
        if hasattr(obj, '__slots__'):
          new_state = tuple(field_values[field_name] for field_name in obj.__slots__)

          obj.__setstate__(new_state)
        else:
          for field_name, field_value in field_values.items():
            obj.__dict__[field_name] = field_value
      else:
        for field_name, field_value in field_values.items():
          setattr(obj, field_name, field_value)

    if hasattr(obj, '__post_init_deserialize__'):
      obj.__post_init_deserialize__()

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


@overload  # `default` and `default_factory` are optional and mutually exclusive.
def field(
    *,
    serialize: bool = True,

    default: T,
    init: bool = True,
    repr: bool = True,
    hash: Optional[bool] = None,
    compare: bool = True,
    metadata: Optional[Mapping[Any, Any]] = None,
    kw_only: bool = ...,
) -> T: ...

@overload
def field(
    *,
    serialize: bool = True,

    default_factory: Callable[[], T],
    init: bool = True,
    repr: bool = True,
    hash: Optional[bool] = None,
    compare: bool = True,
    metadata: Optional[Mapping[Any, Any]] = None,
    kw_only: bool = ...,
) -> T: ...

@overload
def field(
    *,
    serialize: bool = True,

    init: bool = True,
    repr: bool = True,
    hash: Optional[bool] = None,
    compare: bool = True,
    metadata: Optional[Mapping[Any, Any]] = None,
    kw_only: bool = ...,
) -> Any: ...

def field(
  *,
  serialize: bool = True,

  default: T = dataclasses.MISSING,
  default_factory: Callable[[], T] = dataclasses.MISSING, # type: ignore
  init: bool = True,
  repr: bool = True,
  hash: Optional[bool] = None,
  compare: bool = True,
  metadata: Optional[Mapping[Any, Any]] = None,
  kw_only: bool = dataclasses.MISSING # type: ignore
):
  return dataclasses.field(
    default=default,
    default_factory=default_factory,
    init=init,
    repr=repr,
    hash=hash,
    compare=compare,
    metadata={**(metadata or dict()), 'serialize': serialize },
    kw_only=kw_only
  ) # type: ignore


__all__ = [
  'field',
  'serializable',
  'union_serializable'
]
