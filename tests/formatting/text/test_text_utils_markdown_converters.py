import pytest
from hammad.formatting.text.converters import (
    convert_to_text,
    convert_dataclass_to_text,
    convert_pydantic_to_text,
    convert_function_to_text,
    convert_collection_to_text,
    convert_dict_to_text,
)
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

try:
    from pydantic import BaseModel

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


@dataclass
class SampleDataClass:
    name: str
    age: int
    email: Optional[str] = None


if PYDANTIC_AVAILABLE:

    class SamplePydanticModel(BaseModel):
        name: str
        age: int
        email: Optional[str] = None


def sample_function(x: int, y: str = "default") -> str:
    """A sample function for testing.

    Args:
        x: An integer parameter
        y: A string parameter with default value

    Returns:
        A formatted string
    """
    return f"{x}_{y}"


class TestConvertToMarkdown:
    """Test the main convert_to_text function."""

    def test_convert_none(self):
        """Test converting None."""
        result = convert_to_text(None)
        assert result == "`None`"

    def test_convert_primitives(self):
        """Test converting primitive types."""
        assert convert_to_text(42) == "`42`"
        assert convert_to_text("hello") == "`hello`"
        assert convert_to_text(True) == "`True`"
        assert convert_to_text(3.14) == "`3.14`"

    def test_convert_primitives_compact(self):
        """Test converting primitives in compact mode."""
        assert convert_to_text(42, compact=True) == "42"
        assert convert_to_text("hello", compact=True) == "hello"

    def test_convert_bytes(self):
        """Test converting bytes."""
        result = convert_to_text(b"hello")
        assert "`b'" in result and "'`" in result

    def test_convert_list(self):
        """Test converting lists."""
        result = convert_to_text([1, 2, 3])
        assert "list" in result.lower()
        assert "- 1" in result
        assert "- 2" in result
        assert "- 3" in result

    def test_convert_list_with_indices(self):
        """Test converting lists with indices."""
        result = convert_to_text([1, 2, 3], show_indices=True)
        assert "[0]" in result
        assert "[1]" in result
        assert "[2]" in result

    def test_convert_empty_list(self):
        """Test converting empty lists."""
        result = convert_to_text([])
        assert "*" in result and "empty" in result

    def test_convert_dict(self):
        """Test converting dictionaries."""
        result = convert_to_text({"a": 1, "b": 2})
        assert "`a`" in result
        assert "`b`" in result

    def test_convert_dict_table_format(self):
        """Test converting dictionaries in table format."""
        result = convert_to_text({"a": 1, "b": 2}, table_format=True)
        assert "|" in result
        assert "Key" in result
        assert "Value" in result

    def test_convert_empty_dict(self):
        """Test converting empty dictionaries."""
        result = convert_to_text({})
        assert "*" in result and "empty" in result

    def test_convert_with_title_and_description(self):
        """Test converting with custom name and description."""
        result = convert_to_text([1, 2, 3], title="My List", description="A test list")
        assert "My List" in result
        assert "A test list" in result

    def test_convert_with_code_block(self):
        """Test converting with code block wrapper."""
        result = convert_to_text({"key": "value"}, code_block_language="json")
        assert "```json" in result
        assert "```" in result


class TestConvertDataclassToMarkdown:
    """Test dataclass conversion."""

    def test_convert_dataclass_instance(self):
        """Test converting dataclass instance."""
        obj = SampleDataClass(name="John", age=30)
        result = convert_dataclass_to_text(obj, None, None, False, True, True, True, 0)
        assert "SampleDataClass" in result
        assert "`name`" in result
        assert "`age`" in result
        assert "John" in result
        assert "30" in result

    def test_convert_dataclass_class(self):
        """Test converting dataclass class."""
        result = convert_dataclass_to_text(
            SampleDataClass, None, None, False, True, True, False, 0
        )
        assert "SampleDataClass" in result
        assert "`name`" in result
        assert "`age`" in result

    def test_convert_dataclass_table_format(self):
        """Test converting dataclass in table format."""
        obj = SampleDataClass(name="John", age=30)
        result = convert_dataclass_to_text(obj, None, None, True, True, True, True, 0)
        assert "|" in result
        assert "Field" in result


@pytest.mark.skipif(not PYDANTIC_AVAILABLE, reason="Pydantic not available")
class TestConvertPydanticToMarkdown:
    """Test Pydantic model conversion."""

    def test_convert_pydantic_instance(self):
        """Test converting Pydantic instance."""
        obj = SamplePydanticModel(name="John", age=30)
        result = convert_pydantic_to_text(
            obj, None, None, False, True, True, True, True, 0
        )
        assert "SamplePydanticModel" in result
        assert "`name`" in result
        assert "`age`" in result

    def test_convert_pydantic_class(self):
        """Test converting Pydantic class."""
        result = convert_pydantic_to_text(
            SamplePydanticModel, None, None, False, True, True, False, True, 0
        )
        assert "SamplePydanticModel" in result
        assert "`name`" in result
        assert "`age`" in result

    def test_convert_pydantic_table_format(self):
        """Test converting Pydantic model in table format."""
        obj = SamplePydanticModel(name="John", age=30)
        result = convert_pydantic_to_text(
            obj, None, None, True, True, True, True, True, 0
        )
        assert "|" in result
        assert "Field" in result


class TestConvertFunctionToMarkdown:
    """Test function conversion."""

    def test_convert_function_with_signature(self):
        """Test converting function with signature."""
        result = convert_function_to_text(sample_function, None, None, True, False, 0)
        assert "sample_function" in result
        assert "`sample_function(" in result

    def test_convert_function_with_docstring(self):
        """Test converting function with docstring."""
        result = convert_function_to_text(sample_function, None, None, False, True, 0)
        assert "sample_function" in result
        assert "A sample function for testing" in result

    def test_convert_function_with_custom_name(self):
        """Test converting function with custom name."""
        result = convert_function_to_text(
            sample_function, "Custom Name", "Custom description", False, False, 0
        )
        assert "Custom Name" in result
        assert "Custom description" in result


class TestConvertCollectionToMarkdown:
    """Test collection conversion."""

    def test_convert_list(self):
        """Test converting list."""
        result = convert_collection_to_text(
            [1, 2, 3], None, None, False, False, 0, set()
        )
        assert "list" in result
        assert "- 1" in result

    def test_convert_tuple(self):
        """Test converting tuple."""
        result = convert_collection_to_text(
            (1, 2, 3), None, None, False, False, 0, set()
        )
        assert "tuple" in result
        assert "- 1" in result

    def test_convert_set(self):
        """Test converting set."""
        result = convert_collection_to_text(
            {1, 2, 3}, None, None, False, False, 0, set()
        )
        assert "set" in result

    def test_convert_collection_compact(self):
        """Test converting collection in compact mode."""
        result = convert_collection_to_text(
            [1, 2, 3], None, None, True, False, 0, set()
        )
        assert "- 1" in result
        # Should not have heading in compact mode
        assert "#" not in result

    def test_convert_collection_with_indices(self):
        """Test converting collection with indices."""
        result = convert_collection_to_text(
            [1, 2, 3], None, None, False, True, 0, set()
        )
        assert "[0]" in result
        assert "[1]" in result
        assert "[2]" in result


class TestConvertDictToMarkdown:
    """Test dictionary conversion."""

    def test_convert_dict_list_format(self):
        """Test converting dict in list format."""
        result = convert_dict_to_text(
            {"a": 1, "b": 2}, None, None, False, False, 0, set()
        )
        assert "`a`" in result
        assert "`b`" in result
        assert "- " in result

    def test_convert_dict_table_format(self):
        """Test converting dict in table format."""
        result = convert_dict_to_text(
            {"a": 1, "b": 2}, None, None, True, False, 0, set()
        )
        assert "|" in result
        assert "Key" in result
        assert "Value" in result

    def test_convert_dict_compact(self):
        """Test converting dict in compact mode."""
        result = convert_dict_to_text(
            {"a": 1, "b": 2}, None, None, False, True, 0, set()
        )
        assert "`a`" in result
        # Should not have heading in compact mode
        assert "#" not in result

    def test_convert_empty_dict(self):
        """Test converting empty dict."""
        result = convert_dict_to_text({}, None, None, False, False, 0, set())
        assert "*" in result and "empty" in result


class TestCircularReferences:
    """Test handling of circular references."""

    def test_circular_reference_handling(self):
        """Test that circular references are handled gracefully."""
        # Create a circular reference
        d1 = {"key": "value"}
        d2 = {"ref": d1}
        d1["circular"] = d2

        result = convert_to_text(d1)
        assert "circular reference" in result


class TestErrorHandling:
    """Test error handling in converters."""

    def test_convert_custom_object(self):
        """Test converting custom objects without special handling."""

        class CustomClass:
            def __str__(self):
                return "custom object"

        obj = CustomClass()
        result = convert_to_text(obj)
        assert "CustomClass" in result
        assert "custom object" in result


class TestSpecialOptions:
    """Test special formatting options."""

    def test_escape_special_chars(self):
        """Test escaping special markdown characters."""
        result = convert_to_text("text with *special* chars", escape_special_chars=True)
        assert "\\*" in result

    def test_horizontal_rules(self):
        """Test adding horizontal rules."""
        result = convert_to_text([1, 2, 3], add_horizontal_rules=True)
        assert "---" in result


if __name__ == "__main__":
    pytest.main(["-v", __file__])
