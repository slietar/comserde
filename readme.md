# Comserde

**Comserde** (**com**pact **ser**ialization and **de**serialization) is a Python library for serializing data structures into compact binary data.


## Installation

```sh
$ pip install comserde
```


## Usage

### Serializing dataclasses

Decorating a dataclass with `@serializable` will mark it as serializable and deserializable. Type annotations are used to infer the format of each field.

```py
from comserde import serializable

# Add a decorator to make the dataclass serializable
# The order of decorators matters, the reverse won't work.
@serializable
@dataclass
class User:
  age: Optional[int]
  name: str
```

To produce and consume bytes from a serializable object, call `dumps()` and `loads()`. A major difference compared to other serialization algorithms (such as `json`) is that you must provide the type of object you want to decode, `User` in this example.

```py
from comserde import dumps, loads

user = User(age=34, name="John Doe")

data = dumps(user)
user = loads(data, User)
```

More complex types can be defined using most of the typical type hints, such as generics and union types.

```py
from typing import NewType

class User:
  id: UserId
  friends: list[Admin | User]
  images: dict[ImageId, tuple[str, Optional[Image]]]
  profile_image: bytes
```

To prevent a specific field from being serialized, assign it with Comserde's `field()` instead of [`dataclasses.field()`](https://docs.python.org/3/library/dataclasses.html#dataclasses.field) and set `serialize=False`. Other field attributes can be set as usual.

```py
from comserde import field

class User:
  age: Optional[int]
  name: str
  _cache: Optional[int] = field(default=None, serialize=False)
```

### Serializing regular classes

Regular classes can also be serialized, although the types of each attribute must be explicitly provided, which is why dataclasses are preferred.

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

### Customizing serialization formats

The full serialization and deserialization process can be customized by adding the `__serialize__` and `__deserialize__` methods.

```py
from typing import IO

class User:
  def __serialize__(self, file: IO[bytes]):
    file.write(...)

  @classmethod
  def __deserialize__(cls, file: IO[bytes]):
    return cls(file.read(...))
```

### Specifying an explicit format

For every field in a class, a format can be explicitly selected by using the `typing.Annotated` type introduced by [PEP 593](https://peps.python.org/pep-0593/). The use of this type doesn't affect the behavior of type checkers while providing additional information to Comserde.

```py
from comserde import SerializationFormat, serializable

@serializable
@dataclass
class Vec2d:
  x: Annotated[float, SerializationFormat('f64')]
  y: Annotated[float, SerializationFormat('f64')]
```

The same syntax can be used on on regular classes, however the format can also be specified directly.

```py
@serializable({
  'x': 'f64',
  'y': 'f64'
})
class Vec2d:
  ...
```

### Serializing any object

Objects that are not marked with `@serializable` and that do not implement `__serializable__()` are pickled when serialized, and a warning is emitted if the the `pickle` format is not explicit. Keep in mind that pickling a large number of individual objects can significantly increase the output size due to the overhead of each pickled object.

### Handling exceptions

Any error caused by corrupt data raises a `DeserializationError` which can be caught if the data is not trusted.

```py
try:
  user = loads(data, User)
except DeserializationError:
  pass
```


## Reference

### Primitive formats

The following serialization formats are supported:

- Booleans and scalars
  - `bool`
  - `u8`, `u16`, `u32`, `u64`
  - `i8`, `i16`, `i32`, `i64`
  - `f32`, `f64`
  - `v8`, `v16`, `v32`, `v64` – unsigned variable-length quantity (VLQ) encoding of at least 1, 2, 4 and 8 bytes
  - `w8`, `w16`, `w32`, `w64` – signed VLQ encoding
- Bytes and strings
  - `bytes` – length-prefixed bytes
  - `nt-bytes` – null-terminated bytes
  - `utf-8`, `utf-16`
- Others
  - `json`
  - `object` – stores the full qualified name of the object's class and uses the class as the serialization format; useful when the class is not known in advance, e.g. because it might be a subclass
  - `pickle`
  - `void`

### Composite formats

- [`deque[T]`](https://docs.python.org/3/library/collections.html#collections.deque)
- [`NewType('X', T)`](https://docs.python.org/3/library/typing.html#typing.NewType)
- [`PurePath`](https://docs.python.org/3/library/pathlib.html#pathlib.PurePath) and all of its subclasses
- `bool`
- `bytearray`, `bytes`
- `complex` – as two `f64`
- `dict[K, V]`
- `EllipsisType`, `NoneType`, `Literal[T]`, `tuple[()]` – no data produced
- `float` – as `f64`
- `frozenset`
- `int` – as `w8`
- `list[T]`
- `Literal[T, S, etc.]`
- `set[T]`
- `str`
- `T | S`
- `tuple[T, ...]`
- `tuple[T, S, etc.]`
