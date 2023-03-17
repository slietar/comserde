# Comserde

**Comserde** (**com**pact **ser**ialization and **de**serialization) is a Python package for serializing data structures into compact binary data.


## Installation

```sh
$ pip install comserde
```


## Usage

### Serializing dataclasses

Decorating a class with `@serializable` will mark it as serializable and deserializable. Type annotations are used to infer the encoding of each field.

```py
from comserde import serializable

# Add a decorator to make the dataclass serializable
# Order matters, the reverse won't work.
@serializable
@dataclass
class User:
  age: Optional[int]
  name: str
```

To produce and consume bytes from a serializable object, call `dumps()` and `loads()`. A major difference compared to other serialization algorithms (such as `json`) is that you must provide the type of object you want to decode, `User` in this example.

```py
from comserde import dumps, field, loads, serializable

user = User(age=34, name="John Doe")

data = dumps(user)
user = loads(data, User)
```

### Serializing regular classes

Regular classes can also be serialized, although the types of each attribute must be written twice, therefore dataclasses are preferred.

```py
from comserde import serializable

 # Define serialization fields explicitly
@serializable({
  'age': Optional[int],
  'name': str
})
class User:
  def __init__(self, age: Optional[int], name: str):
    self.age = age
    self.name = name

    # Not serialized
    self._cache: Optional[int] = None
```

### Customizing deserialization

If present, the `__init_deserialize__` method is called upon deserialization of an object. This is similar to the `__setstate__` method called when unpickling.

```py
@serializable({
  'age': Optional[int],
  'name': str
})
class User:
  def __init_deserialize__(self, *, age: Optional[int], name: str):
    self.age = age
    self.name = name
```

### Customizing serialization encodings

The full serialization and deserialization process can be customized by adding the `__serialize__` and `__deserialize__` methods.

```py
from comserde import Decoder

def User:
  def __serialize__(self):
    return struct.pack(...)

  @classmethod
  def __deserialize__(cls, decoder: Decoder):
    return cls(*struct.unpack(...))
```

### Specifying an explicit encoding

For every field in a class, an encoding can be explicitly selected by using the `typing.Annotated` type introduced in PEP 593. The use of this type doesn't affect the behavior of type checkers while providing additional information to Comserde.

```py
from comserde import SerializationEncoding, serializable

@serializable
@dataclass
class Vec2d:
  x: Annotated[float, SerializationEncoding('f64')]
  y: Annotated[float, SerializationEncoding('f64')]
```

The same syntax can be used on on regular classes, however the encoding can also be specified directly.

```py
@serializable({
  'x': 'f64',
  'y': 'f64'
})
class Vec2d:
  ...
```

### Serializing any object

Objects the are not marked with `@serializable` and that do not implement `__serializable__()` will be pickled, and a warning is emitted if the the `pickle` encoding is not explicit. Encoding a large number of pickled objects can significantly increase the output size due to the overhead of the pickle format.

### Handling exceptions

Any error caused by corrupt data raises a `DeserializationError` which can be caught if the data is not trusted.

```py
try:
  user = loads(data, User)
except DeserializationError:
  pass
```


## Reference

### Encodings

The following encodings are supported:

- Booleans and scalars
  - `bool`
  - `u8`/`u16`/`u32`/`u64`
  - `i8`/`i16`/`i32`/`i64`
  - `f32`/`f64`
  - `v8`/`v16`/`v32`/`v64` – unsigned variable-length quantity (VLQ) encoding of at least 1, 2, 4 and 8 bytes
  - `w8`/`w16`/`w32`/`w64` – signed VLQ encoding
- Bytes and strings
  - `bytes` – length-prefixed bytes
  - `nt-bytes` – null-terminated bytes
  - `bytearray`
  - `utf-8`/`utf-16`
- Other formats
  - `json`
  - `pickle`
  - `void`

Most types of the standard library are supported. In particular:

- `EllipsisType`, `NoneType` and `Literal[T]` do not produce any data.
- `complex` maps to two `f32`.
- `float` maps to `f32`.
- `int` maps to `v8`.
