# Cookbook - `hammad-python-core`

---

## CLI & Logging Resources

### `ham.core.cli`

The `ham.core.cli` module contains a couple of extensions over the `rich` and
`alive-progress` libraries to provide quicker and a more 'parameterized' implementation of standard terminal methods.

```python
from ham.core.cli import print

# extended version of `rich.console.Console.print()`
# no performance overhead
print("Hello, World!")

# use various parameters from rich.panel / rich.box / rich.live
# everything (including all standard rich colors) are literally
# typed when possible
print("Hello, [blue]World![/blue]", style="green", border="rounded")
```

The `animate` method provides a couple of predefined animations, just for fun.

```python
from ham.core.cli import animate

animate("Hello, World!", type = "pulsing")
```

The `input` method provides a quick way to get iterative and schema based input
from the user in a quicker way.

```python
from ham.core.cli import input
from dataclasses import dataclass

# define some schema you want the user to input
@dataclass
class User:
    name: str
    age: int

user = input(User)
```

---

## Converters

---

## File / Data Models

---

## Caching & Runtime Decorators