import pytest
from ham.lib.dataclasses import inspection
from typing import Literal, Union, Optional, List, Dict, Tuple
from enum import Enum
from pydantic import BaseModel
from ham.lib.typing import inspection
from typing import TypedDict


class SampleModel(BaseModel):
    name: str


class SampleEnum(Enum):
    A = "a"
    B = "b"


def test_is_simple_type():
    assert inspection.is_simple_type(str) == True
    assert inspection.is_simple_type(int) == True
    assert inspection.is_simple_type(bool) == True
    assert inspection.is_simple_type(SampleModel) == False
    assert inspection.is_simple_type(List[str]) == True
    # NOTE: list[model] is simple type as the 'field' within the model
    # is represented the same wasy if it was given as list[str]
    assert inspection.is_simple_type(List[SampleModel]) == True


def test_get_type_description():
    assert inspection.get_type_description(str) == "str"
    assert inspection.get_type_description(List[str]) == "array of str"
    assert (
        inspection.get_type_description(Dict[str, int])
        == "object with str keys and int values"
    )
    assert inspection.get_type_description(Literal["a", "b"]) == "one of: 'a', 'b'"
    assert inspection.get_type_description(Optional[str]) == "optional str"


def test_get_standardized_type_name():
    assert inspection.get_standardized_type_name(str) == "str"
    assert inspection.get_standardized_type_name(List[str]) == "ArrayOfstr"
    assert inspection.get_standardized_type_name(Dict[str, int]) == "DictOfstrToint"
    assert inspection.get_standardized_type_name(Literal["a", "b"]) == "Options"
    assert inspection.get_standardized_type_name(Optional[str]) == "Optionalstr"


def test_get_literal_type_values():
    assert inspection.get_literal_type_values(Literal["a", "b"]) == ["a", "b"]
    assert inspection.get_literal_type_values(str) == []


def test_is_value_in_literal_type():
    assert inspection.is_value_in_literal_type("a", Literal["a", "b"]) == True
    assert inspection.is_value_in_literal_type("c", Literal["a", "b"]) == False


def test_get_enum_type_values():
    assert inspection.get_enum_type_values(SampleEnum) == ["a", "b"]
    assert inspection.get_enum_type_values(str) == []


def test_is_key_in_enum_type():
    assert inspection.is_key_in_enum_type("A", SampleEnum) == True
    assert inspection.is_key_in_enum_type("C", SampleEnum) == False


def test_is_value_in_enum_type():
    assert inspection.is_value_in_enum_type("a", SampleEnum) == True
    assert inspection.is_value_in_enum_type("c", SampleEnum) == False


def test_get_typeddict_field_names():
    class SampleTypedDict(TypedDict):
        name: str
        age: int

    assert inspection.get_typeddict_field_names(SampleTypedDict) == ["name", "age"]
    with pytest.raises(TypeError):
        inspection.get_typeddict_field_names(str)


if __name__ == "__main__":
    pytest.main(["-v", "--tb=short", "tests/lib/test_lib_typing_inspection.py"])
