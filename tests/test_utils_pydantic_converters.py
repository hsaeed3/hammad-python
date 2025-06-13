import pytest
from hammad.utils.pydantic.converters import (
    convert_to_pydantic_model,
    convert_dataclass_to_pydantic_model,
    convert_type_to_pydantic_model,
    convert_function_to_pydantic_model,
    convert_sequence_to_pydantic_model,
    convert_dict_to_pydantic_model,
)

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Type, Union
from pydantic import BaseModel, Field


# Test fixtures
@dataclass
class SampleDataclass:
    """A sample dataclass for testing."""

    name: str
    age: int
    email: Optional[str] = None


class SamplePydanticModel(BaseModel):
    """A sample Pydantic model for testing."""

    title: str
    count: int = 0


def sample_function(name: str, age: int, active: bool = True) -> str:
    """
    A sample function for testing.

    Args:
        name: The person's name
        age: The person's age
        active: Whether the person is active

    Returns:
        A formatted string
    """
    return f"{name} is {age} years old and {'active' if active else 'inactive'}"


class TestConvertToPydanticModel:
    """Test the main convert_to_pydantic_model function."""

    def test_convert_existing_pydantic_model_class(self):
        """Test converting an existing Pydantic model class."""
        result = convert_to_pydantic_model(SamplePydanticModel)
        assert result is SamplePydanticModel

    def test_convert_existing_pydantic_model_class_with_init(self):
        """Test converting an existing Pydantic model class with init=True."""
        result = convert_to_pydantic_model(SamplePydanticModel, init=True)
        # When init=True but required fields are missing, should return the class
        assert result is SamplePydanticModel

    def test_convert_pydantic_model_instance(self):
        """Test converting a Pydantic model instance."""
        instance = SamplePydanticModel(title="Test", count=5)
        result = convert_to_pydantic_model(instance)
        assert result is SamplePydanticModel

    def test_convert_pydantic_model_instance_with_init(self):
        """Test converting a Pydantic model instance with init=True."""
        instance = SamplePydanticModel(title="Test", count=5)
        result = convert_to_pydantic_model(instance, init=True)
        assert isinstance(result, BaseModel)
        assert result.title == "Test"
        assert result.count == 5

    def test_convert_dataclass_type(self):
        """Test converting a dataclass type."""
        result = convert_to_pydantic_model(SampleDataclass)
        assert issubclass(result, BaseModel)
        assert "name" in result.model_fields
        assert "age" in result.model_fields
        assert "email" in result.model_fields

    def test_convert_dataclass_instance(self):
        """Test converting a dataclass instance."""
        instance = SampleDataclass(name="John", age=30, email="john@example.com")
        result = convert_to_pydantic_model(instance, init=True)
        assert isinstance(result, BaseModel)
        assert result.name == "John"
        assert result.age == 30
        assert result.email == "john@example.com"

    def test_convert_python_type(self):
        """Test converting a Python type."""
        result = convert_to_pydantic_model(str)
        assert issubclass(result, BaseModel)
        assert "value" in result.model_fields

    def test_convert_python_type_with_field_name(self):
        """Test converting a Python type with custom field name."""
        result = convert_to_pydantic_model(int, field_name="number", default=42)
        assert issubclass(result, BaseModel)
        assert "number" in result.model_fields

    def test_convert_function(self):
        """Test converting a function."""
        result = convert_to_pydantic_model(sample_function)
        assert issubclass(result, BaseModel)
        assert "name" in result.model_fields
        assert "age" in result.model_fields
        assert "active" in result.model_fields

    def test_convert_sequence_of_types(self):
        """Test converting a sequence of types."""
        types_seq = [str, int, bool]
        result = convert_to_pydantic_model(types_seq)
        assert issubclass(result, BaseModel)
        assert "value_0" in result.model_fields
        assert "value_1" in result.model_fields
        assert "value_2" in result.model_fields

    def test_convert_dict(self):
        """Test converting a dictionary."""
        test_dict = {"name": "John", "age": 30, "active": True}
        result = convert_to_pydantic_model(test_dict, init=True)
        assert isinstance(result, BaseModel)
        assert result.name == "John"
        assert result.age == 30
        assert result.active == True

    def test_convert_dict_without_init(self):
        """Test converting a dictionary without init."""
        test_dict = {"name": "John", "age": 30}
        result = convert_to_pydantic_model(test_dict)
        assert issubclass(result, BaseModel)
        assert "name" in result.model_fields
        assert "age" in result.model_fields

    def test_unsupported_type_raises_error(self):
        """Test that unsupported types raise TypeError."""
        with pytest.raises(TypeError):
            convert_to_pydantic_model(123)  # int instance, not type


class TestConvertDataclassToPydanticModel:
    """Test the convert_dataclass_to_pydantic_model function."""

    def test_convert_dataclass_type(self):
        """Test converting a dataclass type."""
        result = convert_dataclass_to_pydantic_model(
            SampleDataclass,
            init=False,
            name="TestModel",
            description="Test description",
        )
        assert issubclass(result, BaseModel)
        assert result.__name__ == "TestModel"

    def test_convert_dataclass_instance(self):
        """Test converting a dataclass instance."""
        instance = SampleDataclass(name="Alice", age=25)
        result = convert_dataclass_to_pydantic_model(
            instance, init=True, name=None, description=None
        )
        assert isinstance(result, BaseModel)
        assert result.name == "Alice"
        assert result.age == 25


class TestConvertTypeToPydanticModel:
    """Test the convert_type_to_pydantic_model function."""

    def test_convert_basic_type(self):
        """Test converting a basic Python type."""
        result = convert_type_to_pydantic_model(
            str,
            name="StringModel",
            description="A string model",
            field_name="text",
            default="hello",
        )
        assert issubclass(result, BaseModel)
        assert result.__name__ == "StringModel"
        assert "text" in result.model_fields

    def test_convert_type_without_field_name(self):
        """Test converting a type without custom field name."""
        result = convert_type_to_pydantic_model(
            int, name="IntModel", description="An int model", field_name=None, default=0
        )
        assert issubclass(result, BaseModel)
        assert "value" in result.model_fields


class TestConvertFunctionToPydanticModel:
    """Test the convert_function_to_pydantic_model function."""

    def test_convert_function(self):
        """Test converting a function to Pydantic model."""
        result = convert_function_to_pydantic_model(
            sample_function, name="FunctionModel", description="A function model"
        )
        assert issubclass(result, BaseModel)
        assert result.__name__ == "FunctionModel"
        assert "name" in result.model_fields
        assert "age" in result.model_fields
        assert "active" in result.model_fields


class TestConvertSequenceToPydanticModel:
    """Test the convert_sequence_to_pydantic_model function."""

    def test_convert_sequence_of_types(self):
        """Test converting a sequence of types."""
        types_seq = [str, int, float]
        result = convert_sequence_to_pydantic_model(
            types_seq,
            name="SequenceModel",
            description="A sequence model",
            field_name=None,
            default=...,
        )
        assert issubclass(result, BaseModel)
        assert result.__name__ == "SequenceModel"
        assert "value_0" in result.model_fields
        assert "value_1" in result.model_fields
        assert "value_2" in result.model_fields

    def test_convert_sequence_with_field_name(self):
        """Test converting a sequence with custom field name for first element."""
        types_seq = [str, int]
        result = convert_sequence_to_pydantic_model(
            types_seq,
            name="SequenceModel",
            description="A sequence model",
            field_name="primary",
            default="test",
        )
        assert issubclass(result, BaseModel)
        assert "primary" in result.model_fields
        assert "value_1" in result.model_fields

    def test_invalid_sequence_raises_error(self):
        """Test that sequence with non-types raises ValueError."""
        invalid_seq = [str, "not a type", int]
        with pytest.raises(ValueError):
            convert_sequence_to_pydantic_model(
                invalid_seq,
                name="InvalidModel",
                description="Invalid",
                field_name=None,
                default=...,
            )


class TestConvertDictToPydanticModel:
    """Test the convert_dict_to_pydantic_model function."""

    def test_convert_dict_without_init(self):
        """Test converting a dict to model class."""
        test_dict = {"name": "John", "age": 30, "score": 95.5}
        result = convert_dict_to_pydantic_model(
            test_dict, init=False, name="DictModel", description="A dict model"
        )
        assert issubclass(result, BaseModel)
        assert result.__name__ == "DictModel"
        assert "name" in result.model_fields
        assert "age" in result.model_fields
        assert "score" in result.model_fields

    def test_convert_dict_with_init(self):
        """Test converting a dict to model instance."""
        test_dict = {"name": "Jane", "age": 28, "active": True}
        result = convert_dict_to_pydantic_model(
            test_dict, init=True, name="DictModel", description="A dict model"
        )
        assert isinstance(result, BaseModel)
        assert result.name == "Jane"
        assert result.age == 28
        assert result.active == True


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_dict(self):
        """Test converting an empty dictionary."""
        result = convert_to_pydantic_model({})
        assert issubclass(result, BaseModel)
        assert len(result.model_fields) == 0

    def test_empty_sequence_raises_error(self):
        """Test that empty sequence raises appropriate error."""
        # This should raise an error since we can't create fields from empty sequence
        with pytest.raises((ValueError, IndexError)):
            convert_sequence_to_pydantic_model(
                [], name="EmptyModel", description="Empty", field_name=None, default=...
            )

    def test_none_values_in_dict(self):
        """Test dict with None values."""
        test_dict = {"name": "John", "value": None}
        result = convert_to_pydantic_model(test_dict, init=True)
        assert isinstance(result, BaseModel)
        assert result.name == "John"
        assert result.value is None

    def test_custom_name_and_description(self):
        """Test that custom name and description are applied."""
        result = convert_to_pydantic_model(
            str, name="CustomModel", description="Custom description"
        )
        assert result.__name__ == "CustomModel"
        assert "Custom description" in (result.__doc__ or "")
