import unittest
from dataclasses import dataclass
from io import BytesIO
from tempfile import NamedTemporaryFile
from typing import Self
from unittest import TestCase

from .. import (DeserializationEOFError, dump, dumps, field, load, loads,
                serializable, vlq)


class DecoratorTest(TestCase):
  def test1(self):
    @serializable
    @dataclass
    class A:
      a: int
      b: str
      c: list[int]
      d: dict[int, int]
      e: tuple[int, int]
      f: tuple[int, ...]
      g: tuple[()]

    value = A(
      a=4091,
      b='61128',
      c=[3, 4, -5],
      d={6: 7, 8: 9},
      e=(10, 11),
      f=(12, 13, 14),
      g=()
    )

    encoded = dumps(value)
    decoded = loads(encoded, A)

    self.assertEqual(decoded, value)

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

    self.assertEqual(decoded, value)

  def test3(self):
    @serializable
    @dataclass
    class A:
      a: int = 4091
      b: str = '61128'
      c: int = field(default=16, serialize=False)

    value = A(a=4, c=32)
    encoded = dumps(value)
    decoded = loads(encoded, A)

    self.assertEqual(decoded, A(a=4))

  def test4(self):
    @serializable
    @dataclass
    class A:
      a: int = 4091
      b: str = '61128'

    file = BytesIO()

    for _ in range(3):
      dump(A(), file)

    file.seek(0)

    for _ in range(3):
      load(file, A)

    with self.assertRaises(DeserializationEOFError):
      load(file, A)


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
      file = BytesIO()
      vlq.write_vlq(value, file)
      vlq.write_vlq_signed(value, file)
      vlq.write_vlq_signed(-value, file)
      vlq.write_vlq_signed(value, file, fixed_size=1)
      vlq.write_vlq_signed(-value, file, fixed_size=1)

      file.seek(0)
      self.assertEqual(vlq.read_vlq(file), value)
      self.assertEqual(vlq.read_vlq_signed(file), value)
      self.assertEqual(vlq.read_vlq_signed(file), -value)
      self.assertEqual(vlq.read_vlq_signed(file, fixed_size=1), value)
      self.assertEqual(vlq.read_vlq_signed(file, fixed_size=1), -value)

if __name__ == "__main__":
  unittest.main()
