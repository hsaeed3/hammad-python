# **hammad-python**

---

`hammad-python` is an ecosystem of **wrappers** with the sole purpose of defining
opinionated resources that I myself use in my projects and day to day work when
building with Python.

The ecosystem is split into **4** main sub-packages:

- `hammad-python-core` : Contains "stdlib" like resources such as converters, types, caching, etc. All of these resources can easily be implemented from scratch, and are built soley for convenience.
- `hammad-python-data` : Contains a `Collection` class / system that implements a simple vector / non vector database system.
- `hammad-python-genai` : Contains a collection of patterns for using **Generative AI** models as well as implementing concepts like *Agentic Reasoning*.
- `hammad-python-http` : HTTP / API related resources and utilities. Contains resources related to *MCP, HTTP, OpenAPI & GraphQL Servers*.

---

## Installation

You can install any of the sub-packages, or the main package through `pip` or `uv`.

```bash
pip install hammad-python
```

---

## Documentation

Currently, I don't have any any plans for releasing a full API documentation for
this package, as the direct documentation for the resources that the packages depend
on are much more comprehensive.

However, you can view a bunch of example patterns within the `cookbooks` 
section of this documentation.