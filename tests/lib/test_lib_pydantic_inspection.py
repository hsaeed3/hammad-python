import pytest
from ham.lib.pydantic import inspection
from pydantic import BaseModel


class TestIsPydanticBasemodel:
    def test_is_pydantic_basemodel_class(self):
        class User(BaseModel):
            name: str

        assert inspection.is_pydantic_basemodel(User) is True

    def test_is_pydantic_basemodel_instance(self):
        class User(BaseModel):
            name: str

        user = User(name="John")
        assert inspection.is_pydantic_basemodel(user) is True

    def test_is_pydantic_basemodel_non_pydantic_class(self):
        assert inspection.is_pydantic_basemodel(dict) is False

    def test_is_pydantic_basemodel_non_pydantic_instance(self):
        assert inspection.is_pydantic_basemodel({}) is False

    def test_is_pydantic_basemodel_subclass(self):
        class BaseUser(BaseModel):
            name: str

        class User(BaseUser):
            age: int

        assert inspection.is_pydantic_basemodel(User) is True

    def test_is_pydantic_basemodel_none(self):
        assert inspection.is_pydantic_basemodel(None) is False


class TestIsPydanticBasemodelInstance:
    def test_is_pydantic_basemodel_instance_true(self):
        class User(BaseModel):
            name: str

        user = User(name="John")
        assert inspection.is_pydantic_basemodel_instance(user) is True

    def test_is_pydantic_basemodel_instance_class_false(self):
        class User(BaseModel):
            name: str

        assert inspection.is_pydantic_basemodel_instance(User) is False

    def test_is_pydantic_basemodel_instance_non_pydantic_false(self):
        assert inspection.is_pydantic_basemodel_instance({}) is False

    def test_is_pydantic_basemodel_instance_none_false(self):
        assert inspection.is_pydantic_basemodel_instance(None) is False


class TestGetPydanticModelFieldNames:
    def test_get_pydantic_model_field_names_class(self):
        class User(BaseModel):
            name: str
            age: int

        assert inspection.get_pydantic_model_field_names(User) == ["name", "age"]

    def test_get_pydantic_model_field_names_instance(self):
        class User(BaseModel):
            name: str
            age: int

        user = User(name="John", age=30)
        assert inspection.get_pydantic_model_field_names(user) == ["name", "age"]

    def test_get_pydantic_model_field_names_subclass(self):
        class BaseUser(BaseModel):
            name: str

        class User(BaseUser):
            age: int

        assert inspection.get_pydantic_model_field_names(User) == ["name", "age"]

    def test_get_pydantic_model_field_names_non_pydantic_raises(self):
        with pytest.raises(
            TypeError, match="Provided object is not a Pydantic BaseModel"
        ):
            inspection.get_pydantic_model_field_names(dict)

    def test_get_pydantic_model_field_names_empty_model(self):
        class EmptyModel(BaseModel):
            pass

        assert inspection.get_pydantic_model_field_names(EmptyModel) == []


class TestGetPydanticModelCls:
    def test_get_pydantic_model_cls_instance(self):
        class User(BaseModel):
            name: str

        user = User(name="John")
        assert inspection.get_pydantic_model_cls(user) == User

    def test_get_pydantic_model_cls_class_raises(self):
        class User(BaseModel):
            name: str

        with pytest.raises(
            TypeError, match="Provided object is not a Pydantic BaseModel instance"
        ):
            inspection.get_pydantic_model_cls(User)

    def test_get_pydantic_model_cls_non_pydantic_raises(self):
        with pytest.raises(
            TypeError, match="Provided object is not a Pydantic BaseModel instance"
        ):
            inspection.get_pydantic_model_cls({})

    def test_get_pydantic_model_cls_none_raises(self):
        with pytest.raises(
            TypeError, match="Provided object is not a Pydantic BaseModel instance"
        ):
            inspection.get_pydantic_model_cls(None)


if __name__ == "__main__":
    pytest.main(["-v", "--tb=short", "tests/lib/test_lib_pydantic_inspection.py"])
