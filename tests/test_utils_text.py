import pytest
from hammad.utils.text_utils import (
    convert_docstring_to_text,
    convert_type_to_text,
    convert_to_text
)
from dataclasses import dataclass, field
from typing import Optional, Union, List, Dict, Any
from unittest.mock import Mock
import json


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


class TestConvertTypeToText:
    """Test cases for convert_type_to_text function."""
    
    def test_none_type(self):
        assert convert_type_to_text(None) == "None"
        assert convert_type_to_text(type(None)) == "None"
    
    def test_basic_types(self):
        assert convert_type_to_text(str) == "str"
        assert convert_type_to_text(int) == "int"
        assert convert_type_to_text(float) == "float"
        assert convert_type_to_text(bool) == "bool"
        assert convert_type_to_text(list) == "list"
        assert convert_type_to_text(dict) == "dict"
    
    def test_optional_type(self):
        assert convert_type_to_text(Optional[str]) == "Optional[str]"
        assert convert_type_to_text(Optional[int]) == "Optional[int]"
    
    def test_union_type(self):
        result = convert_type_to_text(Union[str, int])
        assert "Union[" in result
        assert "str" in result
        assert "int" in result
    
    def test_generic_types(self):
        assert convert_type_to_text(List[str]) == "list[str]"
        assert convert_type_to_text(Dict[str, int]) == "dict[str, int]"
    
    def test_custom_class(self):
        assert convert_type_to_text(ExampleDataclass) == "ExampleDataclass"
    
    def test_lambda_function(self):
        lambda_func = lambda x: x
        result = convert_type_to_text(type(lambda_func))
        assert result != "<lambda>"


class TestConvertDocstringToText:
    """Test cases for convert_docstring_to_text function."""
    
    def test_function_with_docstring(self):
        result = convert_docstring_to_text(example_function)
        assert "Test function for docstring testing." in result
        assert "param1" in result
        assert "param2" in result
        assert "Returns:" in result
        assert "Raises:" in result
    
    def test_function_without_docstring(self):
        def no_doc_func():
            pass
        result = convert_docstring_to_text(no_doc_func)
        assert result == ""
    
    def test_class_with_docstring(self):
        result = convert_docstring_to_text(ExampleDataclass)
        assert "A test dataclass for testing purposes." in result
    
    def test_exclude_sections(self):
        result = convert_docstring_to_text(
            example_function,
            exclude_params=True,
            exclude_returns=True,
            exclude_raises=True
        )
        assert "param1" not in result
        assert "Returns:" not in result
        assert "Raises:" not in result
        assert "Test function for docstring testing." in result
    
    def test_override_sections(self):
        result = convert_docstring_to_text(
            example_function,
            params_override="Custom params section",
            returns_override="Custom returns section"
        )
        assert "Custom params section" in result
        assert "Custom returns section" in result
    
    def test_custom_prefixes(self):
        result = convert_docstring_to_text(
            example_function,
            params_prefix="Arguments:",
            returns_prefix="Output:"
        )
        assert "Arguments:" in result
        assert "Output:" in result


class TestConvertToText:
    """Test cases for convert_to_text function."""
    
    def test_none_value(self):
        result = convert_to_text(None)
        assert result == "None"
    
    def test_primitive_types(self):
        assert convert_to_text("hello") == "hello"
        assert convert_to_text(42) == "42"
        assert convert_to_text(3.14) == "3.14"
        assert convert_to_text(True) == "True"
    
    def test_bytes(self):
        result = convert_to_text(b"hello")
        assert result.startswith("b'")
        assert result.endswith("'")
    
    def test_list(self):
        result = convert_to_text([1, 2, 3])
        assert "1" in result
        assert "2" in result
        assert "3" in result
    
    def test_empty_list(self):
        result = convert_to_text([])
        assert result == "[]"
    
    def test_dict(self):
        result = convert_to_text({"key": "value", "num": 42})
        assert "key" in result
        assert "value" in result
        assert "num" in result
        assert "42" in result
    
    def test_empty_dict(self):
        result = convert_to_text({})
        assert result == "{}"
    
    def test_dataclass_instance(self):
        instance = ExampleDataclass(name="John", age=30)
        result = convert_to_text(instance)
        assert "ExampleDataclass" in result
        assert "name" in result
        assert "John" in result
        assert "age" in result
        assert "30" in result
    
    def test_dataclass_class(self):
        result = convert_to_text(ExampleDataclass)
        assert "ExampleDataclass" in result
        assert "name" in result
        assert "age" in result
        assert "str" in result
        assert "int" in result
    
    def test_function(self):
        result = convert_to_text(example_function)
        assert "example_function" in result or "Test function" in result
    
    def test_code_block_format(self):
        result = convert_to_text([1, 2, 3], code_block=True)
        assert result.startswith("```json")
        assert result.endswith("```")
    
    def test_compact_format(self):
        instance = ExampleDataclass(name="John", age=30)
        result = convert_to_text(instance, compact=True)
        # Compact format should be more condensed
        assert "ExampleDataclass" in result
    
    def test_custom_title(self):
        result = convert_to_text([1, 2, 3], title="My Custom List")
        assert "My Custom List" in result
    
    def test_custom_description(self):
        result = convert_to_text([1, 2, 3], description="This is a custom description")
        assert "This is a custom description" in result
    
    def test_prefix_suffix(self):
        result = convert_to_text("test", prefix="PREFIX: ", suffix=" :SUFFIX")
        assert result.startswith("PREFIX: ")
        assert result.endswith(" :SUFFIX")
    
    def test_indent(self):
        result = convert_to_text([1, 2, 3], indent=2)
        lines = result.split('\n')
        # Check that some lines are indented
        indented_lines = [line for line in lines if line.startswith("    ")]
        assert len(indented_lines) > 0
    
    def test_bullet_style(self):
        result = convert_to_text([1, 2, 3], bullet_style="*")
        assert "*" in result
    
    def test_title_style(self):
        result = convert_to_text([1, 2, 3], title_style="[]", title="Test")
        assert "[TEST]" in result or "[Test]" in result
    
    def test_show_types_false(self):
        instance = ExampleDataclass(name="John", age=30)
        result = convert_to_text(instance, show_types=False)
        # Should not contain type information
        assert "str" not in result
        assert "int" not in result
    
    def test_show_values_false(self):
        instance = ExampleDataclass(name="John", age=30)
        result = convert_to_text(instance, show_values=False)
        # Should not show actual values
        assert "John" not in result
        assert "30" not in result
    
    def test_show_defaults(self):
        result = convert_to_text(ExampleDataclass, show_defaults=True)
        assert "25" in result  # Default age value
    
    def test_examples(self):
        result = convert_to_text("test", examples=["example1", "example2"])
        assert "example1" in result
        assert "example2" in result
    
    def test_circular_reference_detection(self):
        # Create a circular reference
        data = {"key": "value"}
        data["self"] = data
        
        result = convert_to_text(data)
        assert "<circular>" in result
    
    def test_nested_structures(self):
        nested = {
            "list": [1, 2, 3],
            "dict": {"inner": "value"},
            "dataclass": ExampleDataclass(name="nested", age=25)
        }
        result = convert_to_text(nested)
        assert "list" in result
        assert "dict" in result
        assert "dataclass" in result
        assert "nested" in result
    
    def test_tuple(self):
        result = convert_to_text((1, 2, 3))
        assert "1" in result
        assert "2" in result
        assert "3" in result
    
    def test_empty_tuple(self):
        result = convert_to_text(())
        assert result == "()"
    
    def test_set(self):
        result = convert_to_text({1, 2, 3})
        assert "1" in result
        assert "2" in result
        assert "3" in result
    
    def test_empty_set(self):
        result = convert_to_text(set())
        assert result == "{}"
    
    def test_json_schema_fallback(self):
        # Test with an object that might fail JSON schema conversion
        class CustomClass:
            def __init__(self):
                self.value = "test"
        
        obj = CustomClass()
        result = convert_to_text(obj, code_block=True, show_json_schema=True)
        # Should fallback gracefully
        assert isinstance(result, str)
    
    def test_callable_object(self):
        def my_func():
            """A test function."""
            pass
        
        result = convert_to_text(my_func)
        assert "my_func" in result or "test function" in result.lower()
    
    def test_dataclass_with_optional_fields(self):
        instance = ExampleDataclass(name="John")  # age will use default, optional_field is None
        result = convert_to_text(instance)
        assert "John" in result
        assert "25" in result  # default age
    
    def test_show_required_fields(self):
        result = convert_to_text(ExampleDataclass, show_required=True)
        assert "REQUIRED" in result or "OPTIONAL" in result
    
    def test_show_field_descriptions(self):
        @dataclass
        class WithFieldDocs:
            """Class with field documentation."""
            name: str  # The name field
            age: int = 25  # The age field with default
        
        result = convert_to_text(WithFieldDocs, show_field_descriptions=True)
        assert "WithFieldDocs" in result


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_very_deep_nesting(self):
        # Create deeply nested structure
        deep = {"level": 1}
        current = deep
        for i in range(2, 10):
            current["next"] = {"level": i}
            current = current["next"]
        
        result = convert_to_text(deep)
        assert "level" in result
        assert isinstance(result, str)
    
    def test_large_data_structure(self):
        large_list = list(range(100))
        result = convert_to_text(large_list)
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_unicode_strings(self):
        unicode_data = {"emoji": "🚀", "chinese": "你好", "arabic": "مرحبا"}
        result = convert_to_text(unicode_data)
        assert "🚀" in result
        assert "你好" in result
        assert "مرحبا" in result
    
    def test_special_characters(self):
        special_data = {"newline": "line1\nline2", "tab": "col1\tcol2", "quote": 'say "hello"'}
        result = convert_to_text(special_data)
        assert isinstance(result, str)
    
    def test_none_in_collections(self):
        data_with_none = [1, None, "test", None]
        result = convert_to_text(data_with_none)
        assert "None" in result
        assert "test" in result
    
    def test_mixed_type_collections(self):
        mixed = [1, "string", 3.14, True, None, [1, 2], {"key": "value"}]
        result = convert_to_text(mixed)
        assert isinstance(result, str)
        assert len(result) > 0


class TestParameterCombinations:
    """Test various parameter combinations."""
    
    def test_all_show_flags_false(self):
        instance = ExampleDataclass(name="John", age=30)
        result = convert_to_text(
            instance,
            show_types=False,
            show_values=False,
            show_description=False,
            show_examples=False,
            show_defaults=False,
            show_required=False
        )
        assert isinstance(result, str)
    
    def test_all_show_flags_true(self):
        result = convert_to_text(
            ExampleDataclass,
            show_types=True,
            show_values=True,
            show_description=True,
            show_examples=True,
            show_defaults=True,
            show_required=True,
            examples=["example"]
        )
        assert isinstance(result, str)
        assert "example" in result
    
    def test_compact_with_code_block(self):
        result = convert_to_text([1, 2, 3], compact=True, code_block=True)
        assert "```json" in result
    
    def test_different_title_styles(self):
        data = [1, 2, 3]
        styles = ["<>", "[]", "{}", "#", "##"]
        
        for style in styles:
            result = convert_to_text(data, title_style=style, title="Test")
            assert isinstance(result, str)
    
    def test_different_bullet_styles(self):
        data = [1, 2, 3]
        bullets = ["-", "*", "+", ">"]
        
        for bullet in bullets:
            result = convert_to_text(data, bullet_style=bullet)
            assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
