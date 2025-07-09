## hammad-python

> __Happily Accelerated Micro-Modules (_for_) Application Development__

## Introduction

The `hammad-python` library, is a mix of a love letter and collection of mixed resources for
developing Python applications. This library is meant to be used for rapid prototyping and
development, and is focused on providing styled placeholder tools for common patterns, tasks
and workflows.

The package is currently built into the following structures:

- `hammad-python` : Contains most core functionality and resources.
- `hammad-python[ai]` : Contains easy to use resources for Generative AI related tasks such as
   generating completions with language models, or creating embeddings.
- `hammad-python[serve]` : Contains FastAPI / Uvicorn based resources for serving and running applications.

## Installation

You can install the package using `pip` or `uv`:

```bash
pip install hammad-python

# or install the `ai` extension
# pip install 'hammad-python[ai]'

# or install the `serve` extension
# pip install 'hammad-python[serve]'
```

```bash
uv pip install hammad-python

# or install the `ai` extension
# uv pip install 'hammad-python[ai]'

# or install the `serve` extension
# uv pip install 'hammad-python[serve]'
```

## Basic Usage

### Data Structures, Databases and Other Data Related Resources

#### Collections

Using `hammad.data.collections` is a simple way to create searchable collections of
data using both `bm25` and `vector` based search.

```python
from hammad.data.collections import create_collection

# Create either a `vector` or `searchable` collection
col = create_collection(type = "searchable")

# add anything to the collection
col.add("This is some text")
col.add(5)
col.add({'text' : "this is a dictionary"})

# search the collection
print(col.query("text"))
```

#### Databases

Any collection can be either used as a standalone database, or can be added as one
of the collections within a database. Databases provide a unified interface for handling
both `Searchable` and `Vector` based collections.

```python
from hammad.data.collections import create_collection
from hammad.data.databases import Database

# Create either a `vector` or `searchable` collection
col = create_collection(type = "searchable")

col.add("This is some text")

# Databases can either be created on memory or using a path
db = Database(location = "memory")

db.add_collection(col)

# search globally or within a single collection
print(db.query("text"))
```

### Styling / Introspection Resources

The `hammad-python` package contains a variety of components that can be used
to easily style, or run introspection (logging) on your code.

```python
from hammad.cli import print, input, animate

# Use extended `rich` styling easily
print("Hello, World", bg_settings = {"title" : "This is a title"})

# Easily collect various forms of input in a single function
class User(BaseModel):
    name : str
    age : int

# TIP:
# you can style this the same way with `print`
user = input("Enter some information about yourself: ", schema = User)

# easily run a collection of prebuilt animations
animate("This is a rainbow!", type = "rainbow", duration = 2, refresh_rate = 20)
```

Using the various `hammad.logging` resources, you can both create custom & styled
loggers, as well as easily inspect various aspects of your code during runtime.

```python
from hammad.logging import Logger

# create standard / file based loggers easily
logger = Logger("hammad", level = "info", rich = Trues)

file_logger = Logger("hammad-file", level = "info", file = "hammad.log")

# log to the console
logger.info("This is an info message")

# Use the various `trace_` methods to run various introspection tasks
from hammad.logging import (
   trace,
   trace_cls,
   trace_function,
   trace_http
)
```
