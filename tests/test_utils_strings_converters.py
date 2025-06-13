import pytest
from hammad.utils.text.converters import (
    convert_docstring_to_string,
    convert_type_to_string,
)
from dataclasses import dataclass
from typing import Optional, Union, List, Dict


# Test fixtures
@dataclass
class ExampleDataclass:
    """A test dataclass for testing purposes."""

    name: str
    age: int = 25
    optional_field: Optional[str] = None


class ExamplePydanticModel:
    """Mock Pydantic model for testing."""

    def __init__(self):
        self.name = "test"
        self.age = 30
        self.__class__.__name__ = "ExamplePydanticModel"

    def model_dump(self):
        return {"name": self.name, "age": self.age}


def example_function(param1: str, param2: int = 10) -> str:
    """Test function for docstring testing.

    Args:
        param1: First parameter
        param2: Second parameter with default

    Returns:
        A string result

    Raises:
        ValueError: If param1 is empty
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
    return f"{param1}_{param2}"


class TestConvertTypeToString:
    """Test cases for convert_type_to_string function."""

    def test_none_type(self):
        assert convert_type_to_string(None) == "None"
        assert convert_type_to_string(type(None)) == "None"

    def test_basic_types(self):
        assert convert_type_to_string(str) == "str"
        assert convert_type_to_string(int) == "int"
        assert convert_type_to_string(float) == "float"
        assert convert_type_to_string(bool) == "bool"
        assert convert_type_to_string(list) == "list"
        assert convert_type_to_string(dict) == "dict"

    def test_optional_type(self):
        assert convert_type_to_string(Optional[str]) == "Optional[str]"
        assert convert_type_to_string(Optional[int]) == "Optional[int]"

    def test_union_type(self):
        result = convert_type_to_string(Union[str, int])
        assert "Union[" in result
        assert "str" in result
        assert "int" in result

    def test_generic_types(self):
        assert convert_type_to_string(List[str]) == "list[str]"
        assert convert_type_to_string(Dict[str, int]) == "dict[str, int]"

    def test_custom_class(self):
        assert convert_type_to_string(ExampleDataclass) == "ExampleDataclass"

    def test_lambda_function(self):
        lambda_func = lambda x: x
        result = convert_type_to_string(type(lambda_func))
        assert result != "<lambda>"


class TestConvertDocstringToString:
    """Test cases for convert_docstring_to_string function."""

    def test_function_with_docstring(self):
        result = convert_docstring_to_string(example_function)
        assert "Test function for docstring testing." in result
        assert "param1" in result
        assert "param2" in result
        assert "Returns:" in result
        assert "Raises:" in result

    def test_function_without_docstring(self):
        def no_doc_func():
            pass

        result = convert_docstring_to_string(no_doc_func)
        assert result == ""

    def test_class_with_docstring(self):
        result = convert_docstring_to_string(ExampleDataclass)
        assert "A test dataclass for testing purposes." in result

    def test_exclude_sections(self):
        result = convert_docstring_to_string(
            example_function,
            exclude_params=True,
            exclude_returns=True,
            exclude_raises=True,
        )
        assert "param1" not in result
        assert "Returns:" not in result
        assert "Raises:" not in result
        assert "Test function for docstring testing." in result

    def test_override_sections(self):
        result = convert_docstring_to_string(
            example_function,
            params_override="Custom params section",
            returns_override="Custom returns section",
        )
        assert "Custom params section" in result
        assert "Custom returns section" in result

    def test_custom_prefixes(self):
        result = convert_docstring_to_string(
            example_function, params_prefix="Arguments:", returns_prefix="Output:"
        )
        assert "Arguments:" in result
        assert "Output:" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
