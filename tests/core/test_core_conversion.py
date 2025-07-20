"""Tests for ham.core.conversion module."""

import pytest
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from ham.core.conversion import (
    convert_to_model,
    convert_to_json_schema,
    convert_to_text,
    convert_type_to_text,
    convert_docstring_to_text,
)


# Test fixtures
@dataclass
class ExampleDataclass:
    """A test dataclass for conversion testing."""

    name: str
    age: int
    email: Optional[str] = None


def example_function(x: int, y: str = "default") -> bool:
    """A test function with parameters and return value.

    Args:
        x: An integer parameter
        y: A string parameter with default value

    Returns:
        Always returns True

    Raises:
        ValueError: If x is negative
    """
    if x < 0:
        raise ValueError("x must be positive")
    return True


class TestConvertToText:
    """Tests for convert_to_text function."""

    def test_convert_primitive_types(self):
        """Test conversion of primitive types."""
        assert convert_to_text(42, compact=True) == "42"
        assert convert_to_text("hello", compact=True) == "hello"
        assert convert_to_text(True, compact=True) == "True"
        assert convert_to_text(None) == "`None`"

    def test_convert_dataclass_instance(self):
        """Test conversion of dataclass instances."""
        obj = ExampleDataclass(name="John", age=30)
        result = convert_to_text(obj)
        assert "ExampleDataclass" in result
        assert "name" in result
        assert "age" in result
        assert "John" in result
        assert "30" in result

    def test_convert_function(self):
        """Test conversion of functions."""
        result = convert_to_text(example_function)
        assert "example_function" in result
        assert callable(example_function)

    def test_convert_collection(self):
        """Test conversion of collections."""
        data = [1, 2, 3]
        result = convert_to_text(data)
        assert "1" in result
        assert "2" in result
        assert "3" in result

    def test_convert_dict(self):
        """Test conversion of dictionaries."""
        data = {"key1": "value1", "key2": 42}
        result = convert_to_text(data)
        assert "key1" in result
        assert "value1" in result
        assert "key2" in result
        assert "42" in result

    def test_compact_mode(self):
        """Test compact mode formatting."""
        obj = ExampleDataclass(name="Jane", age=25)
        compact_result = convert_to_text(obj, compact=True)
        normal_result = convert_to_text(obj, compact=False)
        # Compact should be shorter
        assert len(compact_result) <= len(normal_result)

    def test_custom_title_and_description(self):
        """Test custom title and description."""
        data = [1, 2, 3]
        result = convert_to_text(
            data, title="Custom List", description="A custom description"
        )
        assert "Custom List" in result
        assert "A custom description" in result


class TestConvertTypeToText:
    """Tests for convert_type_to_text function."""

    def test_basic_types(self):
        """Test conversion of basic types."""
        assert convert_type_to_text(int) == "int"
        assert convert_type_to_text(str) == "str"
        assert convert_type_to_text(bool) == "bool"
        assert convert_type_to_text(float) == "float"

    def test_optional_types(self):
        """Test conversion of Optional types."""
        result = convert_type_to_text(Optional[str])
        assert "Optional" in result
        assert "str" in result

    def test_union_types(self):
        """Test conversion of Union types."""
        result = convert_type_to_text(Union[str, int])
        assert "Union" in result
        assert "str" in result
        assert "int" in result

    def test_generic_types(self):
        """Test conversion of generic types."""
        result = convert_type_to_text(List[str])
        assert "list" in result.lower() or "List" in result
        assert "str" in result

        result = convert_type_to_text(Dict[str, int])
        assert "dict" in result.lower() or "Dict" in result
        assert "str" in result
        assert "int" in result

    def test_none_type(self):
        """Test conversion of None type."""
        assert convert_type_to_text(type(None)) == "None"
        assert convert_type_to_text(None) == "None"

    def test_custom_class_types(self):
        """Test conversion of custom class types."""
        result = convert_type_to_text(ExampleDataclass)
        assert "ExampleDataclass" in result


class TestConvertDocstringToText:
    """Tests for convert_docstring_to_text function."""

    def example_function_with_docstring(self):
        """Test conversion of function docstrings."""
        result = convert_docstring_to_text(example_function)
        assert "A test function" in result
        assert "Args:" in result or "Parameters:" in result
        assert "Returns:" in result
        assert "Raises:" in result

    def test_class_with_docstring(self):
        """Test conversion of class docstrings."""
        result = convert_docstring_to_text(ExampleDataclass)
        assert "A test dataclass" in result

    def test_object_without_docstring(self):
        """Test handling of objects without docstrings."""

        def no_doc_func():
            pass

        result = convert_docstring_to_text(no_doc_func)
        assert result == ""

    def test_exclude_sections(self):
        """Test excluding specific docstring sections."""
        result = convert_docstring_to_text(
            example_function, exclude_params=True, exclude_returns=True
        )
        # Should still have the description but not params/returns
        assert "A test function" in result
        assert "Args:" not in result and "Parameters:" not in result
        assert "Returns:" not in result

    def test_custom_overrides(self):
        """Test custom section overrides."""
        result = convert_docstring_to_text(
            example_function,
            params_override="Custom parameters section",
            returns_override="Custom returns section",
        )
        assert "Custom parameters section" in result
        assert "Custom returns section" in result


class TestConvertToJsonSchema:
    """Tests for convert_to_json_schema function."""

    def test_dataclass_schema(self):
        """Test JSON schema generation for dataclasses."""
        schema = convert_to_json_schema(ExampleDataclass)
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "age" in schema["properties"]
        assert "email" in schema["properties"]

    def test_dict_schema(self):
        """Test JSON schema generation for dictionaries."""
        data = {"name": "John", "age": 30}
        schema = convert_to_json_schema(data)
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "age" in schema["properties"]

    def test_basic_type_schema(self):
        """Test JSON schema generation for basic types."""
        schema = convert_to_json_schema(str)
        assert "type" in schema

    def test_list_type_schema(self):
        """Test JSON schema generation for list types."""
        schema = convert_to_json_schema(List[str])
        assert schema["type"] == "array"
        assert "items" in schema

    def test_optional_type_schema(self):
        """Test JSON schema generation for optional types."""
        schema = convert_to_json_schema(Optional[str])
        assert "nullable" in schema or "type" in schema


class TestConvertToModel:
    """Tests for convert_to_model function."""

    def test_convert_dict_to_pydantic(self):
        """Test converting dictionary to Pydantic model."""
        data = {"name": "John", "age": 30}
        model_class = convert_to_model(data, model_type="pydantic")
        assert hasattr(model_class, "model_fields") or hasattr(
            model_class, "__fields__"
        )

        # Test with init=True
        model_instance = convert_to_model(data, model_type="pydantic", init=True)
        assert hasattr(model_instance, "name")
        assert hasattr(model_instance, "age")

    def test_convert_dataclass_to_pydantic(self):
        """Test converting dataclass to Pydantic model."""
        model_class = convert_to_model(ExampleDataclass, model_type="pydantic")
        assert hasattr(model_class, "model_fields") or hasattr(
            model_class, "__fields__"
        )

    def test_convert_with_custom_name(self):
        """Test converting with custom model name."""
        data = {"field1": "value1"}
        model_class = convert_to_model(data, model_type="pydantic", title="CustomModel")
        assert model_class.__name__ == "CustomModel"

    def test_convert_function_signature(self):
        """Test converting function signature to model."""
        model_class = convert_to_model(example_function, model_type="pydantic")
        assert hasattr(model_class, "model_fields") or hasattr(
            model_class, "__fields__"
        )


class TestIntegration:
    """Integration tests combining multiple conversion functions."""

    def test_round_trip_conversions(self):
        """Test converting between different formats."""
        # Start with a dataclass
        original = ExampleDataclass(name="Alice", age=28, email="alice@example.com")

        # Convert to text
        text_result = convert_to_text(original)
        assert "Alice" in text_result

        # Convert to JSON schema
        schema = convert_to_json_schema(ExampleDataclass)
        assert "name" in schema["properties"]

        # Convert to Pydantic model
        pydantic_model = convert_to_model(ExampleDataclass, model_type="pydantic")
        assert hasattr(pydantic_model, "model_fields") or hasattr(
            pydantic_model, "__fields__"
        )

    def test_complex_nested_structures(self):
        """Test handling of complex nested data structures."""
        complex_data = {
            "users": [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}],
            "metadata": {"version": "1.0", "created_at": "2023-01-01"},
        }

        # Test text conversion
        text_result = convert_to_text(complex_data)
        assert "users" in text_result
        assert "John" in text_result
        assert "metadata" in text_result

        # Test schema conversion
        schema = convert_to_json_schema(complex_data)
        assert "properties" in schema
        assert "users" in schema["properties"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
