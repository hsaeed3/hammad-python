import pytest
from hammad.data.models.pydantic.converters import (
    is_pydantic_model_class,
    get_pydantic_fields_from_function,
    convert_to_pydantic_field,
    create_selection_pydantic_model,
    create_confirmation_pydantic_model,
    convert_to_pydantic_model,
)


def test_is_pydantic_model_class():
    """Test the is_pydantic_model_class function."""
    from pydantic import BaseModel

    class TestModel(BaseModel):
        name: str

    # Test with Pydantic model class
    assert is_pydantic_model_class(TestModel) is True

    # Test with Pydantic model instance
    assert is_pydantic_model_class(TestModel(name="test")) is False

    # Test with regular class
    class RegularClass:
        pass

    assert is_pydantic_model_class(RegularClass) is False

    # Test with built-in types
    assert is_pydantic_model_class(str) is False
    assert is_pydantic_model_class(int) is False
    assert is_pydantic_model_class("not a class") is False


def test_get_pydantic_fields_from_function():
    """Test extracting Pydantic fields from function signatures."""

    def test_func(name: str, age: int = 25, active: bool = True) -> str:
        """Test function.

        Args:
            name: The person's name
            age: The person's age
            active: Whether the person is active
        """
        return f"{name} is {age} years old"

    fields = get_pydantic_fields_from_function(test_func)

    assert "name" in fields
    assert "age" in fields
    assert "active" in fields
    assert "return" not in fields

    # Check types
    assert fields["name"][0] == str
    assert fields["age"][0] == int
    assert fields["active"][0] == bool

    # Check defaults
    from pydantic import Field
    from pydantic_core import PydanticUndefined

    assert fields["name"][1].default is PydanticUndefined  # Required field
    assert fields["age"][1].default == 25
    assert fields["active"][1].default is True


def test_convert_to_pydantic_field():
    """Test converting types to Pydantic field definitions."""

    # Test basic type conversion
    field_def = convert_to_pydantic_field(str)
    assert "value" in field_def
    assert field_def["value"][0] == str

    # Test with index
    field_def = convert_to_pydantic_field(int, index=1)
    assert "value_1" in field_def
    assert field_def["value_1"][0] == int

    # Test with description and default
    field_def = convert_to_pydantic_field(bool, description="Test field", default=False)
    assert field_def["value"][1].description == "Test field"
    assert field_def["value"][1].default is False


def test_create_selection_pydantic_model():
    """Test creating selection models."""

    # Test basic selection model
    options = ["option1", "option2", "option3"]
    SelectionModel = create_selection_pydantic_model(options)

    # Test valid selection
    instance = SelectionModel(selection="option1")
    assert instance.selection == "option1"

    # Test invalid selection should raise validation error
    with pytest.raises(Exception):  # Pydantic validation error
        SelectionModel(selection="invalid_option")

    # Test empty fields should raise ValueError
    with pytest.raises(ValueError, match="cannot be empty"):
        create_selection_pydantic_model([])


def test_create_confirmation_pydantic_model():
    """Test creating confirmation models."""

    # Test default confirmation model
    ConfirmModel = create_confirmation_pydantic_model()

    instance = ConfirmModel(confirmed=True)
    assert instance.confirmed is True

    # Test custom field name
    CustomConfirmModel = create_confirmation_pydantic_model(field_name="accepted")

    instance = CustomConfirmModel(accepted=False)
    assert instance.accepted is False


def test_convert_to_pydantic_model_with_types():
    """Test converting basic Python types to Pydantic models."""

    # Test string type
    StringModel = convert_to_pydantic_model(str)
    instance = StringModel(value="test")
    assert instance.value == "test"

    # Test with custom field name
    CustomModel = convert_to_pydantic_model(int, field_name="number", default=42)
    instance = CustomModel(number=10)
    assert instance.number == 10


def test_convert_to_pydantic_model_with_dataclass():
    """Test converting dataclasses to Pydantic models."""
    from dataclasses import dataclass

    @dataclass
    class Person:
        name: str
        age: int = 25

    # Test converting dataclass type
    PersonModel = convert_to_pydantic_model(Person)
    instance = PersonModel(name="John", age=30)
    assert instance.name == "John"
    assert instance.age == 30

    # Test converting dataclass instance with init=True
    person_instance = Person(name="Jane", age=28)
    pydantic_instance = convert_to_pydantic_model(person_instance, init=True)
    assert pydantic_instance.name == "Jane"
    assert pydantic_instance.age == 28


def test_convert_to_pydantic_model_with_function():
    """Test converting functions to Pydantic models."""

    def example_func(name: str, age: int = 30) -> str:
        """Example function.

        Args:
            name: Person's name
            age: Person's age
        """
        return f"{name} is {age}"

    FuncModel = convert_to_pydantic_model(example_func)
    instance = FuncModel(name="Alice", age=25)
    assert instance.name == "Alice"
    assert instance.age == 25


def test_convert_to_pydantic_model_with_sequence():
    """Test converting sequences of types to Pydantic models."""

    # Test sequence of types
    types_sequence = [str, int, bool]
    SeqModel = convert_to_pydantic_model(types_sequence)

    instance = SeqModel(value_0="test", value_1=42, value_2=True)
    assert instance.value_0 == "test"
    assert instance.value_1 == 42
    assert instance.value_2 is True

    # Test empty sequence should raise error
    with pytest.raises(ValueError, match="empty sequence"):
        convert_to_pydantic_model([])


def test_convert_to_pydantic_model_with_dict():
    """Test converting dictionaries to Pydantic models."""

    test_dict = {"name": "John", "age": 30, "active": True}

    # Test creating model class from dict
    DictModel = convert_to_pydantic_model(test_dict)
    instance = DictModel(name="Jane", age=25, active=False)
    assert instance.name == "Jane"
    assert instance.age == 25
    assert instance.active is False

    # Test creating initialized instance from dict
    dict_instance = convert_to_pydantic_model(test_dict, init=True)
    assert dict_instance.name == "John"
    assert dict_instance.age == 30
    assert dict_instance.active is True


def test_convert_to_pydantic_model_with_pydantic_model():
    """Test handling existing Pydantic models."""
    from pydantic import BaseModel

    class ExistingModel(BaseModel):
        name: str
        age: int = 25

    # Test with Pydantic model class
    result = convert_to_pydantic_model(ExistingModel)
    assert result is ExistingModel

    # Test with Pydantic model instance
    instance = ExistingModel(name="Test")
    result = convert_to_pydantic_model(instance)
    assert result is ExistingModel

    # Test init=True with model class (should handle missing required fields)
    result = convert_to_pydantic_model(ExistingModel, init=True)
    # Should return the class since it can't initialize without required fields
    assert result is ExistingModel


def test_convert_to_pydantic_model_error_handling():
    """Test error handling for unsupported types."""

    # Test with unsupported type
    with pytest.raises(TypeError, match="Cannot create Pydantic model"):
        convert_to_pydantic_model(object())

    # Test sequence with non-types
    with pytest.raises(TypeError, match="all its elements must be types"):
        convert_to_pydantic_model(["not", "a", "type"])


def test_convert_to_pydantic_model_custom_names_and_descriptions():
    """Test custom naming and descriptions."""

    # Test with custom name and description
    CustomModel = convert_to_pydantic_model(
        str,
        name="CustomStringModel",
        description="A custom model for strings",
        field_name="text",
    )

    assert CustomModel.__name__ == "CustomStringModel"
    assert "custom model for strings" in CustomModel.__doc__.lower()

    instance = CustomModel(text="hello")
    assert instance.text == "hello"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
