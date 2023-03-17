import struct

from . import vlq


class DecodingError(Exception):
  pass

class Decoder:
  """
  Utility class to decode binary data.
  """

  def __init__(self, data: bytes, /):
    self._data = data
    self._index = 0

  @property
  def _partial_data(self):
    return self._data[self._index:]

  def read_bytes(self, length: int):
    value = self._partial_data[:length]
    self._index += length

    return value

  def read_nt_bytes(self):
    for length, byte in enumerate(self._partial_data):
      if byte == 0x00:
        break
    else:
      raise DecodingError("No null terminator found")

    return self.read_bytes(length)

  def read_struct(self, format: str):
    length = struct.calcsize(format)
    value = struct.unpack(format, self._partial_data[:length])
    self._index += length

    return value

  def read_vlq(self):
    length, value = vlq.decode(self._partial_data)
    self._index += length
    return value
