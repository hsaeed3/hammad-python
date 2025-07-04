import pytest
from hammad.formatting.json import convert_to_json_schema


def test_convert_to_json_schema_basic_dict():
    """Test convert_to_json_schema with a basic dictionary."""
    test_dict = {"name": "John", "age": 30, "active": True}
    schema = convert_to_json_schema(test_dict)

    assert schema["type"] == "object"
    assert "properties" in schema
    assert "name" in schema["properties"]
    assert "age" in schema["properties"]
    assert "active" in schema["properties"]

    assert schema["properties"]["name"]["type"] == "str"
    assert schema["properties"]["age"]["type"] == "int"
    assert schema["properties"]["active"]["type"] == "bool"


def test_convert_to_json_schema_dataclass():
    """Test convert_to_json_schema with a dataclass."""
    from dataclasses import dataclass

    @dataclass
    class Person:
        name: str
        age: int
        active: bool = True

    schema = convert_to_json_schema(Person)

    assert schema["type"] == "object"
    assert "properties" in schema
    assert "name" in schema["properties"]
    assert "age" in schema["properties"]
    assert "active" in schema["properties"]

    # Check that default value is included
    assert schema["properties"]["active"]["default"] == True


def test_convert_to_json_schema_dataclass_instance():
    """Test convert_to_json_schema with a dataclass instance."""
    from dataclasses import dataclass

    @dataclass
    class Person:
        name: str
        age: int
        active: bool = True

    person = Person(name="Jane", age=25, active=False)
    schema = convert_to_json_schema(person)

    assert schema["type"] == "object"
    assert "properties" in schema
    assert schema["properties"]["name"]["value"] == "Jane"
    assert schema["properties"]["age"]["value"] == 25
    assert schema["properties"]["active"]["value"] == False


def test_convert_to_json_schema_msgspec_struct():
    """Test convert_to_json_schema with a msgspec Struct."""
    try:
        import msgspec

        class User(msgspec.Struct):
            name: str
            age: int
            email: str = "default@example.com"

        schema = convert_to_json_schema(User)

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "age" in schema["properties"]
        assert "email" in schema["properties"]

        # Check that default value is included for email
        assert schema["properties"]["email"]["default"] == "default@example.com"

    except ImportError:
        pytest.skip("msgspec not available")


def test_convert_to_json_schema_class_with_type_hints():
    """Test convert_to_json_schema with a regular class that has type hints."""

    class Configuration:
        server_host: str
        server_port: int
        debug_mode: bool

    schema = convert_to_json_schema(Configuration)

    assert schema["type"] == "object"
    assert "properties" in schema
    assert "server_host" in schema["properties"]
    assert "server_port" in schema["properties"]
    assert "debug_mode" in schema["properties"]


def test_convert_to_json_schema_empty_dict():
    """Test convert_to_json_schema with an empty dictionary."""
    schema = convert_to_json_schema({})

    assert schema["type"] == "object"
    assert schema["properties"] == {}


def test_convert_to_json_schema_nested_types():
    """Test convert_to_json_schema with complex type hints."""
    from typing import List, Dict, Optional
    from dataclasses import dataclass

    @dataclass
    class ComplexType:
        items: List[str]
        metadata: Dict[str, int]
        optional_field: Optional[str] = None

    schema = convert_to_json_schema(ComplexType)

    assert schema["type"] == "object"
    assert "properties" in schema
    assert "items" in schema["properties"]
    assert "metadata" in schema["properties"]
    assert "optional_field" in schema["properties"]


if __name__ == "__main__":
    pytest.main(["-v", __file__])
