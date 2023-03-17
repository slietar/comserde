from unittest import TestCase
import unittest


def encode(value: int, /):
  current_value = value
  result = bytes()

  while True:
    byte_value = current_value & 0x7f
    current_value >>= 7
    last = current_value < 1

    result += bytes([byte_value | (0x80 if not last else 0)])

    if last:
      break

  return result


def decode(data: bytes, /, big_endian: bool = False):
  index = -1
  result = 0

  for index, byte in enumerate(data):
    if big_endian:
      result = (result << 7) | (byte & 0x7f)
    else:
      result |= (byte & 0x7f) << (7 * index)

    if (byte & 0x80) < 1:
      break

  return index + 1, result


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
      encoded = encode(value)
      length, decoded = decode(encoded)

      self.assertEqual(value, decoded)


if __name__ == "__main__":
  unittest.main()
