from typing import Protocol, Self, runtime_checkable

from .decoder import Decoder


@runtime_checkable
class Serializable(Protocol):
  """
  Protocol implemented by classes that are serializable.
  """

  def __serialize__(self) -> bytes:
    ...

@runtime_checkable
class Deserializable(Protocol):
  """
  Protocol implemented by classes that are deserializable.
  """

  @classmethod
  def __deserialize__(cls, decoder: Decoder) -> Self:
    ...
