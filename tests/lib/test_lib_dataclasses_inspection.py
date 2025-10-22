import pytest
from ham.lib.dataclasses import inspection
from dataclasses import dataclass


@dataclass
class SimpleDataclass:
    field1: str
    field2: int


@dataclass
class EmptyDataclass:
    pass


@dataclass
class DataclassWithDefaults:
    field1: str = "default"
    field2: int = 42


class NonDataclass:
    pass


def test_get_dataclass_field_names_with_instance():
    instance = SimpleDataclass("test", 123)
    assert inspection.get_dataclass_field_names(instance) == ["field1", "field2"]


def test_get_dataclass_field_names_with_class():
    assert inspection.get_dataclass_field_names(SimpleDataclass) == ["field1", "field2"]


def test_get_dataclass_field_names_with_empty_dataclass():
    instance = EmptyDataclass()
    assert inspection.get_dataclass_field_names(instance) == []


def test_get_dataclass_field_names_with_defaults():
    instance = DataclassWithDefaults()
    assert inspection.get_dataclass_field_names(instance) == ["field1", "field2"]


def test_get_dataclass_field_names_non_dataclass_raises():
    with pytest.raises(TypeError, match="Provided object is not a dataclass."):
        inspection.get_dataclass_field_names(NonDataclass())


def test_get_dataclass_field_names_non_dataclass_instance_raises():
    instance = NonDataclass()
    with pytest.raises(TypeError, match="Provided object is not a dataclass."):
        inspection.get_dataclass_field_names(instance)


def test_get_dataclass_cls_with_instance():
    instance = SimpleDataclass("test", 123)
    assert inspection.get_dataclass_cls(instance) == SimpleDataclass


def test_get_dataclass_cls_with_class():
    assert inspection.get_dataclass_cls(SimpleDataclass) == SimpleDataclass


def test_get_dataclass_cls_with_empty_dataclass():
    instance = EmptyDataclass()
    assert inspection.get_dataclass_cls(instance) == EmptyDataclass


def test_get_dataclass_cls_non_dataclass_raises():
    with pytest.raises(TypeError, match="Provided object is not a dataclass."):
        inspection.get_dataclass_cls(NonDataclass())


def test_get_dataclass_cls_non_dataclass_instance_raises():
    instance = NonDataclass()
    with pytest.raises(TypeError, match="Provided object is not a dataclass."):
        inspection.get_dataclass_cls(instance)


def test_is_dataclass_instance_with_instance():
    instance = SimpleDataclass("test", 123)
    assert inspection.is_dataclass_instance(instance) is True


def test_is_dataclass_instance_with_class():
    assert inspection.is_dataclass_instance(SimpleDataclass) is False


def test_is_dataclass_instance_with_empty_dataclass():
    instance = EmptyDataclass()
    assert inspection.is_dataclass_instance(instance) is True


def test_is_dataclass_instance_with_non_dataclass_instance():
    instance = NonDataclass()
    assert inspection.is_dataclass_instance(instance) is False


def test_is_dataclass_instance_with_non_dataclass_class():
    assert inspection.is_dataclass_instance(NonDataclass) is False


def test_is_dataclass_instance_with_builtin():
    assert inspection.is_dataclass_instance("string") is False
    assert inspection.is_dataclass_instance(42) is False
    assert inspection.is_dataclass_instance([]) is False


if __name__ == "__main__":
    pytest.main(["-v", "--tb=short", "tests/lib/test_lib_dataclasses_inspection.py"])
