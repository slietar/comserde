import unittest
from dataclasses import dataclass
from tempfile import NamedTemporaryFile, TemporaryFile
from typing import Self
from unittest import TestCase

from .. import dump, dumps, load, loads, serializable


class DecoratorTest(TestCase):
  def test1(self):
    @serializable
    @dataclass
    class A:
      a: int = 4091
      b: str = '61128'

    value = A()
    encoded = dumps(value)
    decoded = loads(encoded, A)

    self.assertEqual(value, decoded)

  def test2(self):
    @serializable({
      'a': int,
      'b': str
    })
    class A:
      def __init__(self):
        self.a = 4091
        self.b = '61128'

      def __eq__(self, other: Self, /):
        return (other.a, other.b) == (self.a, self.b)

    value = A()
    encoded = dumps(value)
    decoded = loads(encoded, A)

    self.assertEqual(value, decoded)


class PrimitiveTest(TestCase):
  def test1(self):
    for encoding, value in [
      ('f32', 6),
      ('f64', 6.28),
      ('u8', 42),
      ('u16', 42),
      ('u32', 42),
      ('bytes', b"foobar"),
      ('nt-bytes', b"foobar")
    ]:
      serialized = dumps(value, encoding)
      deserialized = loads(serialized, encoding)

      self.assertEqual(value, deserialized)


class FileTest(TestCase):
  def test1(self):
    @serializable
    @dataclass
    class User:
      name: str
      age: int

    users = [
      User("Alice", 42),
      User("Bob", 35)
    ]

    format = list[User]

    temp_file = NamedTemporaryFile(delete=False)

    with open(temp_file.name, "wb") as file:
      dump(users, file, format)

    with open(temp_file.name, "rb") as file:
      deserialized = load(file, format)

    self.assertEqual(users, deserialized)


class VlqTest(TestCase):
  def test1(self):
    for value in [
      *range(0, 0xffff),
      0x8a533f,
      0xe19db8,
      0x945efb43,
      0xa1e887e9,
      0x09e20c6f2af3dd3207ae
    ]:
      encoded = dumps(value, 'v8')
      decoded = loads(encoded, 'v8')

      self.assertEqual(value, decoded)

if __name__ == "__main__":
  unittest.main()
