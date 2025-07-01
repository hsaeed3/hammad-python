import pytest
from hammad.data.models.pydantic.models import (
    ArbitraryModel as ArbitraryBaseModel,
    CacheableModel as CacheableBaseModel,
    FastModel as FastBaseModel,
    SubscriptableModel as SubscriptableBaseModel,
    FunctionModel as CallableBaseModel,
)


def test_subscriptable_base_model_get_set_contains():
    class Message(SubscriptableBaseModel):
        role: str
        content: str = "default"

    msg = Message(role="user")
    # __getitem__ and __setitem__
    assert msg["role"] == "user"
    msg["role"] = "assistant"
    assert msg.role == "assistant"
    # __contains__
    assert "role" in msg
    assert "content" in msg
    assert "nonexistent" not in msg
    # get
    assert msg.get("role") == "assistant"
    assert msg.get("nonexistent", "fallback") == "fallback"


def test_arbitrary_base_model_dynamic_fields():
    data = ArbitraryBaseModel()
    data.name = "John"
    data.age = 30
    data.metadata = {"key": "value"}
    # Attribute and dict access
    assert data.name == "John"
    assert data["age"] == 30
    # Dynamic fields in to_dict
    d = data.to_dict()
    assert d["name"] == "John"
    assert d["age"] == 30
    assert d["metadata"] == {"key": "value"}


def test_arbitrary_base_model_extra_fields():
    data = ArbitraryBaseModel(foo="bar", x=1)
    assert data.foo == "bar"
    assert data["x"] == 1
    d = data.to_dict()
    assert d["foo"] == "bar"
    assert d["x"] == 1


def test_cacheable_base_model_cached_property_and_invalidation():
    class MyModel(CacheableBaseModel):
        value: int

        @CacheableBaseModel.cached_property(dependencies=["value"])
        def squared(self):
            return self.value**2

    m = MyModel(value=3)
    # First access computes and caches
    assert m.squared == 9
    # Change value, cache should invalidate
    m.value = 4
    assert m.squared == 16
    # Clear cache manually
    m.clear_cache("squared")
    m.value = 5
    assert m.squared == 25


def test_cacheable_base_model_clear_all_cache():
    class MyModel(CacheableBaseModel):
        a: int
        b: int

        @CacheableBaseModel.cached_property(dependencies=["a"])
        def double_a(self):
            return self.a * 2

        @CacheableBaseModel.cached_property(dependencies=["b"])
        def double_b(self):
            return self.b * 2

    m = MyModel(a=2, b=3)
    assert m.double_a == 4
    assert m.double_b == 6
    m.clear_cache()
    m.a = 5
    m.b = 7
    assert m.double_a == 10
    assert m.double_b == 14


def test_fastmodel_dot_and_dict_access():
    class Person(FastBaseModel):
        name: str
        age: int

    p = Person(name="Alice", age=30)
    # Dot access
    assert p.name == "Alice"
    assert p.age == 30
    # Dict access
    assert p["name"] == "Alice"
    assert p["age"] == 30
    # Set via dot
    p.name = "Bob"
    assert p["name"] == "Bob"
    # Set via dict
    p["age"] = 40
    assert p.age == 40


def test_fastmodel_model_dump_and_from_dict():
    class Item(FastBaseModel):
        id: int
        label: str

    item = Item(id=1, label="foo")
    d = item.model_dump()
    assert d == {"id": 1, "label": "foo"}
    item2 = Item.model_from_dict({"id": 2, "label": "bar"})
    assert item2.id == 2
    assert item2.label == "bar"


def test_fastmodel_deepcopy():
    class Data(FastBaseModel):
        x: int
        y: list

    d1 = Data(x=1, y=[1, 2, 3])
    d2 = d1.__deepcopy__()
    assert d2.x == 1
    assert d2.y == [1, 2, 3]
    d2.y.append(4)
    assert d1.y == [1, 2, 3]  # original not affected


def test_fastmodel_set_reserved_key_raises():
    class Foo(FastBaseModel):
        bar: int

    f = Foo(bar=1)
    with pytest.raises(TypeError):
        f.model_set_attribute("keys", 123)  # 'keys' is reserved in dict


def test_fastmodel_missing_attribute_raises():
    class Foo(FastBaseModel):
        bar: int

    f = Foo(bar=1)
    with pytest.raises(AttributeError):
        _ = f.baz


def test_fastmodel_reserved_keys():
    class Foo(FastBaseModel):
        bar: int

    f = Foo(bar=1)
    assert f.model_has_attr("bar")
    assert not f.model_has_attr("keys")


def test_callable_base_model_basic_functionality():
    @CallableBaseModel()
    def add_numbers(x: int, y: int = 5) -> int:
        """Add two numbers together."""
        return x + y

    # Test basic call
    result = add_numbers.call(x=3)
    assert result == 8  # 3 + 5 (default)

    result = add_numbers.call(x=3, y=7)
    assert result == 10  # 3 + 7

    # Test call_from_dict
    result = add_numbers.call_from_dict({"x": 2, "y": 3})
    assert result == 5


def test_callable_base_model_with_exclude():
    @CallableBaseModel(exclude=["debug"])
    def process_data(data: str, debug: bool = False) -> str:
        """Process some data."""
        if debug:
            return f"DEBUG: {data.upper()}"
        return data.upper()

    # Test that excluded parameter is not used even if provided
    result = process_data.call(data="hello", debug=True)
    assert result == "HELLO"  # debug should be ignored due to exclude


def test_callable_base_model_function_schema():
    @CallableBaseModel()
    def calculate(x: int, y: float = 2.5, name: str = "default") -> float:
        """Calculate something with x and y."""
        return x * y

    schema = calculate.function_schema()

    assert schema["name"] == "calculate"
    assert schema["description"] == "Calculate something with x and y."
    assert schema["parameters"]["type"] == "object"

    # Check properties
    props = schema["parameters"]["properties"]
    assert props["x"]["type"] == "integer"
    assert props["y"]["type"] == "number"
    assert props["y"]["default"] == 2.5
    assert props["name"]["type"] == "string"
    assert props["name"]["default"] == "default"

    # Check required fields
    assert "x" in schema["parameters"]["required"]
    assert "y" not in schema["parameters"]["required"]
    assert "name" not in schema["parameters"]["required"]


def test_callable_base_model_function_schema_with_exclude():
    @CallableBaseModel(exclude=["internal"])
    def process(data: str, internal: bool = True) -> str:
        """Process data."""
        return data

    schema = process.function_schema()

    # Excluded parameter should not be in schema
    assert "internal" not in schema["parameters"]["properties"]
    assert "internal" not in schema["parameters"]["required"]
    assert "data" in schema["parameters"]["properties"]


def test_callable_base_model_partial_application():
    @CallableBaseModel()
    def multiply(a: int, b: int, c: int = 1) -> int:
        """Multiply three numbers."""
        return a * b * c

    # Create partial with some arguments pre-filled
    partial_multiply = multiply.partial(a=2, c=3)

    # Call with remaining argument
    result = partial_multiply.call(b=4)
    assert result == 24  # 2 * 4 * 3


def test_callable_base_model_error_handling():
    # Test using call before decorating
    model = CallableBaseModel()
    with pytest.raises(ValueError, match="No function wrapped"):
        model.call(x=1)

    with pytest.raises(ValueError, match="No function wrapped"):
        model.function_schema()

    with pytest.raises(ValueError, match="No function wrapped"):
        model.partial(x=1)


def test_callable_base_model_type_conversion():
    @CallableBaseModel()
    def test_types(
        integer: int, number: float, text: str, flag: bool, items: list, data: dict
    ) -> str:
        """Test various types."""
        return f"{integer},{number},{text},{flag},{len(items)},{len(data)}"

    schema = test_types.function_schema()
    props = schema["parameters"]["properties"]

    assert props["integer"]["type"] == "integer"
    assert props["number"]["type"] == "number"
    assert props["text"]["type"] == "string"
    assert props["flag"]["type"] == "boolean"
    assert props["items"]["type"] == "array"
    assert props["data"]["type"] == "object"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
