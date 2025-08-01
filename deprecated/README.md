# **hammad-python**

> **Harmoniously Accelerated Micro-Modules (for) Application Development**

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

## Quickstart

### Easily Use Language Models With Various Tools & Patterns

```python
from ham.genai import Agent, LanguageModel
from ham.http import SearchClient

client = SearchClient()

def search_web(query: str) -> str:
    return client.search(query)

# create your agent
# agents have rich functionality, and use `litellm` & `instructor` under the hood
agent = Agent(
    instructions = "You are a helpful assistant who can search the web",
    tools = [search_web]
)

print(agent.run("What is the weather in Tokyo?"))
```

```bash
>>> AgentResponse:
city='Tokyo' temperature=25.0 description='Clear sky'

>>> Model: openai/gpt-4o-mini
>>> Steps: 2
>>> Output Type: Response
>>> Total Tool Calls: 1
```

### Vectorized & Searchable Collections

```python
from ham.data import Collection

collection = Collection(vector=True)

collection.add("Rocks")
collection.add("Cucumber")
collection.add("Dragon")
collection.add("Apple")

# query the collection
for result in collection.query("Fruit"):
    print(result.item)
```

```bash
>>> Apple
>>> Cucumber
>>> Dragon
>>> Rocks
```

### HTTP & API Resources

```python
from ham.http import function_server

# instantly launch a server by decorating a function
@function_server(path="/some-endpoint", auto_start=True)
def some_endpoint(name : str) -> str:
    return f"Hello, {name}!"
```

Now in a separate file:

```python
import requests

print(
    requests.post(
        "http://0.0.0.0:8000/some-endpoint",
        json = {"name": "John"}
    ).json()
)
```

```bash
>>> {'result' : 'Hello, John!'}
```