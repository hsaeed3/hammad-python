"""TEST : ham.core.typing"""

import pytest
from ham.core import typing


def test_core_typing_builtins():
    # Test basic type checking functions
    assert typing.is_builtin_type(str) == True
    assert typing.is_builtin_type(int) == True
    assert typing.is_builtin_type(list) == True
    assert typing.is_builtin_type(dict) == True
    assert typing.is_builtin_type(tuple) == True
    assert typing.is_builtin_type(set) == True
    assert typing.is_builtin_type(frozenset) == True
    assert typing.is_builtin_type(bytes) == True
    assert typing.is_builtin_type(bytearray) == True
    assert typing.is_builtin_type(bool) == True
    assert typing.is_builtin_type(float) == True

    # Test non-builtin types
    assert typing.is_builtin_type(typing.List) == False
    assert typing.is_builtin_type(typing.Dict) == False


def test_core_typing_inspect_extensions():
    # NOTE:
    # these dont even really need tests theyre direct extensions from
    # inspect / typing-inspect

    # Test function checking
    def test_func():
        return 42

    async def test_async_func():
        return 42

    assert typing.is_function(test_func) == True
    assert typing.is_function(test_async_func) == True
    assert typing.is_function(str) == False
    assert typing.is_function(42) == False

    # Test async function checking
    assert typing.is_async_function(test_async_func) == True
    assert typing.is_async_function(test_func) == False
    assert typing.is_async_function(str) == False

    # Test module checking
    import os

    assert typing.is_module(os) == True
    assert typing.is_module(str) == False
    assert typing.is_module(42) == False

    # Test generator checking
    def test_generator():
        yield 1
        yield 2

    async def test_async_generator():
        yield 1
        yield 2

    assert typing.is_generator(test_generator) == True
    assert typing.is_generator(test_generator()) == True
    assert typing.is_generator(test_func) == False

    assert typing.is_async_generator(test_async_generator) == True
    assert typing.is_async_generator(test_async_generator()) == True
    assert typing.is_async_generator(test_func) == False

    # Test type string generation
    assert typing.get_type_string(str) == "str"
    assert typing.get_type_string(int) == "int"
    assert typing.get_type_string(list) == "array"
    assert typing.get_type_string(dict) == "object"
    assert typing.get_type_string(tuple) == "tuple"

    # Test with generic types
    assert "array of str" in typing.get_type_string(typing.List[str])
    assert "object with str keys and int values" in typing.get_type_string(
        typing.Dict[str, int]
    )
    assert "optional str" in typing.get_type_string(typing.Optional[str])

    # Test literal types
    assert "one of: 1, 2, 3" in typing.get_type_string(typing.Literal[1, 2, 3])

    # Test union types
    union_str = typing.get_type_string(typing.Union[str, int])
    assert "one of:" in union_str

    # Test callable types
    callable_str = typing.get_type_string(typing.Callable[[str, int], bool])
    assert "function" in callable_str
    assert "bool" in callable_str

    # Test abstract base class
    from abc import ABC, abstractmethod

    class TestAbstract(ABC):
        @abstractmethod
        def test_method(self):
            pass

    class TestConcrete:
        def test_method(self):
            pass

    assert typing.is_abstract(TestAbstract) == True
    assert typing.is_abstract(TestConcrete) == False

    # Test dataclass checking (imported from dataclasses)
    from dataclasses import dataclass

    @dataclass
    class TestDataclass:
        name: str
        age: int

    class RegularClass:
        pass

    assert typing.is_dataclass(TestDataclass) == True
    assert typing.is_dataclass(TestDataclass("test", 25)) == True
    assert typing.is_dataclass(RegularClass) == False

    # Test typing-inspect functions are available
    assert hasattr(typing, "is_callable_type")
    assert hasattr(typing, "is_optional_type")
    assert hasattr(typing, "is_union_type")
    assert hasattr(typing, "is_generic_type")
    assert hasattr(typing, "get_origin")
    assert hasattr(typing, "get_args")

    # Test inspect functions are available
    assert hasattr(typing, "is_code")
    assert hasattr(typing, "is_class")
    assert hasattr(typing, "get_file")
    assert hasattr(typing, "get_module")
    assert hasattr(typing, "get_signature")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
