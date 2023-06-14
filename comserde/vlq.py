import itertools
from typing import IO

from .decoding import read_bytes


def read_vlq(file: IO[bytes]):
  result = 0

  for index in itertools.count():
    byte = read_bytes(1, file)[0]
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


def read_vlq_sized(file: IO[bytes], *, fixed_size: int = 0):
  data = int.from_bytes(read_bytes(fixed_size, file), byteorder='little')
  return (read_vlq(file) << (fixed_size * 8)) + data

def write_vlq_sized(value: int, /, file: IO[bytes], *, fixed_size: int = 0):
  bit_count = fixed_size * 8
  data = value & ((1 << bit_count) - 1)

  file.write(data.to_bytes(byteorder='little', length=fixed_size))
  write_vlq(value >> bit_count, file)


def read_vlq_signed(file: IO[bytes], *, fixed_size: int = 0):
  result = read_vlq_sized(file, fixed_size=fixed_size)
  return (result >> 1) * (-1 if (result & 0x1) > 0 else 1)

def write_vlq_signed(value: int, /, file: IO[bytes], *, fixed_size: int = 0):
  write_vlq_sized((abs(value) << 1) | (0b1 if value < 0 else 0b0), file, fixed_size=fixed_size)
