import pytest
from hammad.typing import (
    get_type_description,
    is_pydantic_basemodel,
    is_pydantic_basemodel_instance,
    is_msgspec_struct,
)


from typing import Any, Optional, Union, List, Dict, Tuple, Callable, Final
from typing_extensions import Literal


def test_get_type_description_basic_types():
    """Test get_type_description with basic types."""
    assert get_type_description(int) == "int"
    assert get_type_description(str) == "str"
    assert get_type_description(bool) == "bool"
    assert get_type_description(float) == "float"


def test_get_type_description_list():
    """Test get_type_description with list types."""
    assert get_type_description(List[int]) == "array of int"
    assert get_type_description(List[str]) == "array of str"
    assert get_type_description(list) == "array"


def test_get_type_description_dict():
    """Test get_type_description with dict types."""
    assert get_type_description(Dict[str, int]) == "object with str keys and int values"
    assert get_type_description(dict) == "object"


def test_get_type_description_tuple():
    """Test get_type_description with tuple types."""
    assert get_type_description(Tuple[int, str]) == "tuple of (int, str)"
    assert get_type_description(Tuple[int, str, bool]) == "tuple of (int, str, bool)"
    assert get_type_description(tuple) == "tuple"


def test_get_type_description_literal():
    """Test get_type_description with literal types."""
    assert (
        get_type_description(Literal["red", "green", "blue"])
        == "one of: 'red', 'green', 'blue'"
    )
    assert get_type_description(Literal[1, 2, 3]) == "one of: 1, 2, 3"


def test_get_type_description_optional():
    """Test get_type_description with optional types."""
    assert get_type_description(Optional[int]) == "optional int"
    assert get_type_description(Optional[str]) == "optional str"


def test_get_type_description_union():
    """Test get_type_description with union types."""
    assert get_type_description(Union[int, str]) == "one of: int, str"
    assert get_type_description(Union[int, str, bool]) == "one of: int, str, bool"


def test_get_type_description_callable():
    """Test get_type_description with callable types."""
    assert (
        get_type_description(Callable[[int, str], bool]) == "function(int, str) -> bool"
    )
    assert get_type_description(Callable[[], int]) == "function() -> int"
    assert get_type_description(Callable) == "function"


def test_get_type_description_nested():
    """Test get_type_description with nested complex types."""
    assert (
        get_type_description(List[Dict[str, int]])
        == "array of object with str keys and int values"
    )
    assert get_type_description(Optional[List[str]]) == "optional array of str"
    assert (
        get_type_description(Dict[str, List[int]])
        == "object with str keys and array of int values"
    )


def test_get_type_description_custom_class():
    """Test get_type_description with custom classes."""

    class CustomClass:
        pass

    assert get_type_description(CustomClass) == "CustomClass"


def test_get_type_description_any():
    """Test get_type_description with Any type."""
    assert get_type_description(Any) == "Any"


def test_is_pydantic_basemodel():
    """Test is_pydantic_basemodel function."""
    # Test with non-Pydantic objects
    assert is_pydantic_basemodel(dict) == False
    assert is_pydantic_basemodel(list) == False
    assert is_pydantic_basemodel(str) == False
    assert is_pydantic_basemodel(42) == False

    # Test with actual Pydantic objects if available
    try:
        from pydantic import BaseModel

        class User(BaseModel):
            name: str
            age: int = 25

        # Test with Pydantic class and instance
        assert is_pydantic_basemodel(User) == True
        user_instance = User(name="John")
        assert is_pydantic_basemodel(user_instance) == True

    except ImportError:
        # Fallback to mock objects if Pydantic is not available
        class MockPydanticClass:
            model_fields = {}

            def model_dump(self):
                return {}

        class MockPydanticInstance:
            model_fields = {}

            def model_dump(self):
                return {}

        # Test with objects that have the required attributes
        assert is_pydantic_basemodel(MockPydanticClass) == True
        assert is_pydantic_basemodel(MockPydanticInstance()) == True

    # Test with objects missing required attributes
    class MissingModelFields:
        def model_dump(self):
            return {}

    class MissingModelDump:
        model_fields = {}

    class NonCallableModelDump:
        model_fields = {}
        model_dump = "not_callable"

    assert is_pydantic_basemodel(MissingModelFields) == False
    assert is_pydantic_basemodel(MissingModelDump) == False
    assert is_pydantic_basemodel(NonCallableModelDump) == False


def test_is_pydantic_basemodel_instance():
    """Test is_pydantic_basemodel_instance function."""
    # Test with non-Pydantic objects
    assert is_pydantic_basemodel_instance(dict) == False
    assert is_pydantic_basemodel_instance(list) == False
    assert is_pydantic_basemodel_instance(str) == False
    assert is_pydantic_basemodel_instance(42) == False

    # Test with actual Pydantic objects if available
    try:
        from pydantic import BaseModel

        class User(BaseModel):
            name: str
            age: int = 25

        # Test that class itself returns False (not an instance)
        assert is_pydantic_basemodel_instance(User) == False

        # Test that instance returns True
        user_instance = User(name="John")
        assert is_pydantic_basemodel_instance(user_instance) == True

    except ImportError:
        # Fallback to mock objects if Pydantic is not available
        class MockPydanticClass:
            model_fields = {}

            def model_dump(self):
                return {}

        class MockPydanticInstance:
            model_fields = {}

            def model_dump(self):
                return {}

        # Test that class itself returns False (not an instance)
        assert is_pydantic_basemodel_instance(MockPydanticClass) == False

        # Test that instance returns True
        assert is_pydantic_basemodel_instance(MockPydanticInstance()) == True

    # Test with objects missing required attributes
    class MissingModelFields:
        def model_dump(self):
            return {}

    class MissingModelDump:
        model_fields = {}

    assert is_pydantic_basemodel_instance(MissingModelFields()) == False
    assert is_pydantic_basemodel_instance(MissingModelDump()) == False


def test_is_msgspec_struct():
    """Test is_msgspec_struct function."""
    # Test with non-msgspec objects
    assert is_msgspec_struct(dict) == False
    assert is_msgspec_struct(list) == False
    assert is_msgspec_struct(str) == False
    assert is_msgspec_struct(42) == False

    # Test with mock msgspec-like objects
    class MockMsgspecClass:
        __struct_fields__ = ("name", "age")
        __struct_config__ = {}

    class MockMsgspecInstance:
        __struct_fields__ = ("name", "age")
        __struct_config__ = {}

    # Test with objects that have the required attributes
    assert is_msgspec_struct(MockMsgspecClass) == True
    assert is_msgspec_struct(MockMsgspecInstance()) == True

    # Test with objects missing required attributes
    class MissingStructFields:
        __struct_config__ = {}

    class MissingStructConfig:
        __struct_fields__ = ("name",)

    assert is_msgspec_struct(MissingStructFields) == False
    assert is_msgspec_struct(MissingStructConfig) == False


if __name__ == "__main__":
    pytest.main(["-v", __file__])
