import unittest
from dataclasses import dataclass
from typing import Self
from unittest import TestCase

from .. import Decoder, dumps, loads, primitive, serializable, vlq


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
      serialized = primitive.serialize(value, encoding)
      deserialized = primitive.deserialize(Decoder(serialized), encoding)

      self.assertEqual(value, deserialized)


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
      encoded = vlq.encode(value)
      length, decoded = vlq.decode(encoded)

      self.assertEqual(value, decoded)

if __name__ == "__main__":
  unittest.main()
