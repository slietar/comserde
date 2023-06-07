from typing import IO, Protocol, Self, runtime_checkable


@runtime_checkable
class Serializable(Protocol):
  """
  Protocol implemented by classes that are serializable.
  """

  def __serialize__(self, file: IO[bytes]):
    ...

@runtime_checkable
class Deserializable(Protocol):
  """
  Protocol implemented by classes that are deserializable.
  """

  @classmethod
  def __deserialize__(cls, file: IO[bytes]) -> Self:
    ...


__all__ = [
  'Deserializable',
  'Serializable'
]
