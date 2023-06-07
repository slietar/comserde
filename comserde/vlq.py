import itertools
from typing import IO

from .decoding import read_bytes


def read_vlq(file: IO[bytes], *, big_endian: bool = False):
  result = 0

  for index in itertools.count():
    byte = read_bytes(1, file)[0]

    if big_endian:
      result = (result << 7) | (byte & 0x7f)
    else:
      result |= (byte & 0x7f) << (7 * index)

    if (byte & 0x80) < 1:
      break

  return result


def write_vlq(value: int, /, file: IO[bytes]):
  current_value = value

  while True:
    byte_value = current_value & 0x7f
    current_value >>= 7
    last = current_value < 1

    file.write(bytes([byte_value | (0x80 if not last else 0)]))

    if last:
      break
