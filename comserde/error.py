class DeserializationError(Exception):
  """
  An error raised upon reaching invalid data during deserialization.
  """


class DeserializationEOFError(DeserializationError):
  """
  An error raised upon reaching the end of the file during deserialization.
  """


__all__ = [
  'DeserializationEOFError',
  'DeserializationError'
]
