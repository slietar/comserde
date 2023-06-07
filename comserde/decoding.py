import struct
from typing import IO


class DecodingError(Exception):
  pass


def read_nt_bytes(file: IO[bytes]):
  data = bytes()

  while (byte := file.read(1)):
    if byte == b"\x00":
      break

    data += byte
  else:
    raise DecodingError("No null terminator found")

  return data

def read_bytes(length: int, /, file: IO[bytes]):
  data = file.read(length)

  if len(data) != length:
    raise DecodingError("Unexpected end of file")

  return data

def read_struct(format: str, file: IO[bytes]):
  length = struct.calcsize(format)
  return struct.unpack(format, read_bytes(length, file))


__all__ = [
  'DecodingError'
]
