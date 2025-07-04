import pytest
from typing import Optional, List, Dict, Any
import json

from hammad.data.models.base import (
    Model as BasedModel,
    field as basedfield,
    create_model as create_basedmodel,
)


def test_based_model_creation():
    """Test basic BasedModel creation and field access."""

    class User(BasedModel):
        name: str
        age: int
        email: str = basedfield(default="", alias="email_address")

    user = User(name="John", age=30, email="john@example.com")

    assert user.name == "John"
    assert user.age == 30
    assert user.email == "john@example.com"

    # Test dictionary access
    assert user["name"] == "John"
    assert user["age"] == 30
    assert user["email"] == "john@example.com"


def test_model_serialization():
    """Test model serialization methods."""

    class Person(BasedModel):
        name: str
        age: int
        email: str = basedfield(default=None)

    person = Person(name="Alice", age=28, email="alice@example.com")

    # Test model_dump
    data = person.model_dump()
    expected = {"name": "Alice", "age": 28, "email": "alice@example.com"}
    assert data == expected

    # Test model_dump with exclude_none
    person_no_email = Person(name="Bob", age=30, email=None)
    data_no_none = person_no_email.model_dump(exclude_none=True)
    assert "email" not in data_no_none

    # Test model_dump_json
    json_str = person.model_dump_json()
    assert isinstance(json_str, str)
    assert "Alice" in json_str


def test_model_validation():
    """Test model validation methods."""

    class User(BasedModel):
        name: str
        age: int
        active: bool = basedfield(default=True)

    # Test model_validate with dict
    user_data = {"name": "Charlie", "age": 35}
    user = User.model_validate(user_data)
    assert user.name == "Charlie"
    assert user.age == 35
    assert user.active is True

    # Test model_validate_json
    json_data = '{"name": "Diana", "age": 25, "active": false}'
    user_from_json = User.model_validate_json(json_data)
    assert user_from_json.name == "Diana"
    assert user_from_json.age == 25
    assert user_from_json.active is False


def test_model_copy():
    """Test model copying functionality."""

    class Settings(BasedModel):
        debug: bool = basedfield(default=False)
        timeout: int = basedfield(default=30)
        features: list = basedfield(default_factory=list)

    settings = Settings(debug=True, timeout=60, features=["auth", "logging"])

    # Test basic copy
    settings_copy = settings.model_copy()
    assert settings_copy.debug is True
    assert settings_copy.timeout == 60
    assert settings_copy.features == ["auth", "logging"]

    # Test copy with update
    updated_settings = settings.model_copy(update={"debug": False, "timeout": 45})
    assert updated_settings.debug is False
    assert updated_settings.timeout == 45
    assert updated_settings.features == ["auth", "logging"]


def test_field_access_methods():
    """Test various field access methods."""

    class Config(BasedModel):
        host: str = basedfield(default="localhost")
        port: int = basedfield(default=8080)
        ssl: bool = basedfield(default=False)

    config = Config(host="example.com", port=443, ssl=True)

    # Test get_field method
    assert config.get_field("host") == "example.com"
    assert config.get_field("port") == 443

    # Test field_keys property
    keys = config.field_keys
    assert "host" in keys
    assert "port" in keys
    assert "ssl" in keys

    # Test fields() accessor
    fields_accessor = config.fields()
    assert fields_accessor.host == "example.com"
    assert fields_accessor.port == 443
    assert fields_accessor.ssl is True

    # Test fields accessor methods
    assert "host" in fields_accessor.keys()
    assert "example.com" in fields_accessor.values()
    assert ("host", "example.com") in fields_accessor.items()


def test_model_json_schema():
    """Test JSON schema generation."""

    class APIResponse(BasedModel):
        success: bool
        timestamp: int  # Required field first
        message: str = basedfield(default="", description="Response message")
        data: dict = basedfield(default_factory=dict)

    schema = APIResponse.model_json_schema()

    assert isinstance(schema, dict)
    assert "type" in schema or "$defs" in schema  # msgspec may return different format
    if "properties" in schema:
        assert "success" in schema["properties"]
        assert "message" in schema["properties"]


def test_model_conversion():
    """Test model conversion to different formats."""

    class Item(BasedModel):
        id: int
        name: str
        price: float
        active: bool = basedfield(default=True)

    item = Item(id=1, name="Test Item", price=9.99)

    # Test conversion to dict
    dict_result = item.model_convert("dict")
    assert isinstance(dict_result, dict)
    assert dict_result["id"] == 1
    assert dict_result["name"] == "Test Item"

    # Test conversion to msgspec (should return same type)
    msgspec_result = item.model_convert("msgspec")
    assert isinstance(msgspec_result, Item)
    assert msgspec_result.id == 1


def test_model_with_complex_types():
    """Test model with complex field types."""

    class ComplexModel(BasedModel):
        tags: List[str] = basedfield(default_factory=list)
        metadata: Optional[dict] = basedfield(default=None)
        scores: List[float] = basedfield(
            default_factory=list, min_length=0, max_length=10
        )

    model = ComplexModel(
        tags=["python", "testing"], metadata={"author": "test"}, scores=[1.0, 2.5, 3.7]
    )

    assert model.tags == ["python", "testing"]
    assert model.metadata == {"author": "test"}
    assert model.scores == [1.0, 2.5, 3.7]


def test_model_load_from_model():
    """Test model_load_from_model functionality."""

    # Define source models - put required fields first for msgspec
    class SourceModel(BasedModel):
        name: str
        age: int
        email: str = basedfield(default="")

    class TargetModel(BasedModel):
        name: str
        age: int
        city: str = basedfield(default="Unknown")

    # Create source instance
    source = SourceModel(name="John", age=30, email="john@example.com")

    # Test basic loading
    target = TargetModel.model_load_from_model(source, init=True)
    assert target.name == "John"
    assert target.age == 30
    assert target.city == "Unknown"  # Default value

    # Test loading with exclusion
    target_excluded = TargetModel.model_load_from_model(
        source, exclude={"email"}, init=True
    )
    assert target_excluded.name == "John"
    assert target_excluded.age == 30
    assert target_excluded.city == "Unknown"

    # Test loading from dictionary
    data_dict = {"name": "Alice", "age": 25, "extra_field": "ignored"}
    target_from_dict = TargetModel.model_load_from_model(data_dict, init=True)
    assert target_from_dict.name == "Alice"
    assert target_from_dict.age == 25

    # Test loading from object with __dict__
    class SimpleObject:
        def __init__(self):
            self.name = "Bob"
            self.age = 35
            self.unused = "ignored"

    obj = SimpleObject()
    target_from_obj = TargetModel.model_load_from_model(obj, init=True)
    assert target_from_obj.name == "Bob"
    assert target_from_obj.age == 35


def test_model_load_from_model_edge_cases():
    """Test edge cases for model_load_from_model."""

    class TestModel(BasedModel):
        name: str
        value: int = basedfield(default=42)

    # Test with namedtuple
    from collections import namedtuple

    Point = namedtuple("Point", ["name", "value"])
    point = Point("test", 100)

    result = TestModel.model_load_from_model(point, init=True)
    assert result.name == "test"
    assert result.value == 100

    # Test with unsupported type (should use fallback)
    class WeirdObject:
        def __init__(self):
            self.name = "weird"
            self.value = 999

        def __iter__(self):
            yield ("name", self.name)
            yield ("value", self.value)

    weird = WeirdObject()
    result = TestModel.model_load_from_model(weird, init=True)
    assert result.name == "weird"
    assert result.value == 999


def test_model_fields_info():
    """Test getting field information."""

    class DocumentModel(BasedModel):
        title: str
        content: str = basedfield(default="")
        published: bool = basedfield(default=False)
        views: int = basedfield(default=0, ge=0)

    fields_info = DocumentModel.model_fields()

    assert isinstance(fields_info, dict)
    assert "title" in fields_info
    assert "content" in fields_info
    assert "published" in fields_info
    assert "views" in fields_info


def test_model_to_pydantic():
    """Test conversion to pydantic model."""

    class User(BasedModel):
        name: str
        age: int = basedfield(default=0)
        email: Optional[str] = basedfield(default=None)

    user = User(name="Alice", age=30, email="alice@example.com")

    # Convert to pydantic
    pydantic_user = user.model_to_pydantic()

    # Verify the conversion
    assert pydantic_user.name == "Alice"
    assert pydantic_user.age == 30
    assert pydantic_user.email == "alice@example.com"

    # Verify it's a pydantic model
    assert hasattr(pydantic_user, "model_validate")
    assert hasattr(pydantic_user, "model_dump")


def test_pydantic_compatibility_interface():
    """Test that BasedModel can be used where pydantic models are expected."""

    class User(BasedModel):
        name: str
        age: int
        email: str = basedfield(default="")

    user = User(name="John", age=30, email="john@example.com")

    # Test pydantic-like methods exist and work
    assert hasattr(user, "model_dump")
    assert hasattr(user, "model_validate")
    assert hasattr(user, "model_validate_json")
    assert hasattr(user, "model_copy")
    assert hasattr(user, "model_fields")
    assert hasattr(user, "model_json_schema")

    # Test that these methods return expected types
    assert isinstance(user.model_dump(), dict)
    assert isinstance(user.model_dump_json(), str)
    assert isinstance(user.model_fields(), dict)
    assert isinstance(user.model_json_schema(), dict)

    # Test copy returns same type
    copied = user.model_copy()
    assert isinstance(copied, User)
    assert copied.name == "John"


def test_pydantic_replacement_serialization():
    """Test that BasedModel can replace pydantic in serialization scenarios."""

    class Product(BasedModel):
        id: int
        name: str
        price: float
        tags: List[str] = basedfield(default_factory=list)
        metadata: Dict[str, Any] = basedfield(default_factory=dict)

    product = Product(
        id=1,
        name="Widget",
        price=19.99,
        tags=["electronics", "gadget"],
        metadata={"color": "blue", "weight": 1.5},
    )

    # Test serialization matches pydantic patterns
    data = product.model_dump()
    assert data["id"] == 1
    assert data["name"] == "Widget"
    assert data["price"] == 19.99
    assert data["tags"] == ["electronics", "gadget"]
    assert data["metadata"] == {"color": "blue", "weight": 1.5}

    # Test JSON serialization
    json_str = product.model_dump_json()
    parsed = json.loads(json_str)
    assert parsed == data

    # Test deserialization from dict
    new_product = Product.model_validate(data)
    assert new_product.id == product.id
    assert new_product.name == product.name
    assert new_product.price == product.price

    # Test deserialization from JSON
    json_product = Product.model_validate_json(json_str)
    assert json_product.id == product.id
    assert json_product.name == product.name


def test_pydantic_replacement_validation():
    """Test that BasedModel validation works like pydantic."""

    class ValidatedUser(BasedModel):
        username: str
        age: int
        email: str = basedfield(default="")

    # Test successful validation
    valid_data = {"username": "alice", "age": 30, "email": "alice@example.com"}
    user = ValidatedUser.model_validate(valid_data)
    assert user.username == "alice"
    assert user.age == 30
    assert user.email == "alice@example.com"

    # Test validation from JSON
    json_data = '{"username": "bob", "age": 25}'
    user_from_json = ValidatedUser.model_validate_json(json_data)
    assert user_from_json.username == "bob"
    assert user_from_json.age == 25
    assert user_from_json.email == ""  # default value


def test_dictionary_interface_compatibility():
    """Test that BasedModel supports dictionary-like access patterns."""

    class Config(BasedModel):
        host: str = basedfield(default="localhost")
        port: int = basedfield(default=8080)
        debug: bool = basedfield(default=False)

    config = Config(host="example.com", port=443, debug=True)

    # Test dictionary-style access
    assert config["host"] == "example.com"
    assert config["port"] == 443
    assert config["debug"] is True

    # Test contains
    assert "host" in config
    assert "nonexistent" not in config

    # Test iteration
    field_names = list(config)
    assert "host" in field_names
    assert "port" in field_names
    assert "debug" in field_names

    # Test setting values
    config["host"] = "new.example.com"
    assert config.host == "new.example.com"
    assert config["host"] == "new.example.com"


def test_nested_model_compatibility():
    """Test nested BasedModel structures work like pydantic."""

    class Address(BasedModel):
        street: str
        city: str
        country: str = basedfield(default="USA")

    class Person(BasedModel):
        name: str
        age: int
        address: Address

    # Create nested structure
    address_data = {"street": "123 Main St", "city": "Anytown"}
    address = Address.model_validate(address_data)

    person = Person(name="John", age=30, address=address)

    # Test access
    assert person.name == "John"
    assert person.address.street == "123 Main St"
    assert person.address.city == "Anytown"
    assert person.address.country == "USA"

    # Test serialization includes nested data
    data = person.model_dump()
    assert data["name"] == "John"
    assert data["address"]["street"] == "123 Main St"
    assert data["address"]["city"] == "Anytown"
    assert data["address"]["country"] == "USA"


def test_pydantic_style_usage():
    """Test that create_basedmodel works exactly like pydantic.create_model."""
    print("Testing pydantic-style usage...")

    # This mimics exactly how you'd use pydantic.create_model

    # Basic model equivalent to:
    # User = create_model('User', name=str, age=int)
    User = create_basedmodel("User", name=str, age=int)

    user = User(name="Alice", age=30)
    assert user.name == "Alice"
    assert user.age == 30

    # Model with defaults equivalent to:
    # Config = create_model('Config', host=(str, 'localhost'), port=(int, 8080))
    Config = create_basedmodel("Config", host=(str, "localhost"), port=(int, 8080))

    config = Config()
    assert config.host == "localhost"
    assert config.port == 8080

    config2 = Config(host="example.com", port=443)
    assert config2.host == "example.com"
    assert config2.port == 443

    print("✓ Pydantic-style basic usage works")


def test_complex_pydantic_replacement():
    """Test complex scenarios that would use pydantic.create_model."""
    print("\nTesting complex pydantic replacement scenarios...")

    # Complex model with various field types
    Product = create_basedmodel(
        "Product",
        # Required fields
        name=str,
        id=int,
        # Optional fields with defaults
        price=(float, 0.0),
        description=(str, ""),
        # Fields with constraints (using basedfield instead of pydantic Field)
        tags=(List[str], basedfield(default_factory=list)),
        rating=(Optional[float], basedfield(default=None, ge=0, le=5)),
        # Boolean with default
        active=(bool, True),
    )

    # Test with minimal data
    product1 = Product(name="Widget", id=1)
    assert product1.name == "Widget"
    assert product1.id == 1
    assert product1.price == 0.0
    assert product1.description == ""
    assert product1.tags == []
    assert product1.rating is None
    assert product1.active is True

    # Test with full data
    product2 = Product(
        name="Advanced Widget",
        id=2,
        price=99.99,
        description="A premium widget",
        tags=["premium", "advanced"],
        rating=4.5,
        active=True,
    )
    assert product2.name == "Advanced Widget"
    assert product2.price == 99.99
    assert product2.rating == 4.5
    assert product2.tags == ["premium", "advanced"]

    print("✓ Complex pydantic replacement works")


def test_model_methods_compatibility():
    """Test that the created models have pydantic-compatible methods."""
    print("\nTesting model methods compatibility...")

    User = create_basedmodel(
        "User",
        name=str,
        age=int,
        email=(str, ""),
    )

    user = User(name="Bob", age=25, email="bob@example.com")

    # Test all the pydantic-like methods exist and work
    methods_to_test = [
        "model_dump",
        "model_dump_json",
        "model_validate",
        "model_validate_json",
        "model_copy",
        "model_fields",
        "model_json_schema",
    ]

    for method_name in methods_to_test:
        assert hasattr(user, method_name), f"Missing method: {method_name}"
        assert callable(getattr(user, method_name)), (
            f"Method {method_name} is not callable"
        )

    # Test that they actually work
    data = user.model_dump()
    assert isinstance(data, dict)
    assert data["name"] == "Bob"

    json_str = user.model_dump_json()
    assert isinstance(json_str, str)
    assert "Bob" in json_str

    copied_user = user.model_copy()
    assert copied_user.name == "Bob"
    assert copied_user is not user  # Different instance

    schema = User.model_json_schema()
    assert isinstance(schema, dict)

    print("✓ Model methods compatibility works")


def test_drop_in_replacement():
    """Test that you can literally replace pydantic.create_model with create_basedmodel."""
    print("\nTesting drop-in replacement capability...")

    # This function simulates using create_model in existing pydantic code
    def create_user_model(create_model_func):
        """Function that uses create_model - could be from pydantic or our replacement."""
        return create_model_func(
            "DynamicUser",
            username=str,
            password=str,
            email=(str, ""),
            is_active=(bool, True),
            metadata=(dict, basedfield(default_factory=dict)),
        )

    # Use our create_basedmodel instead of pydantic.create_model
    UserModel = create_user_model(create_basedmodel)

    # Verify it works exactly the same
    user = UserModel(username="testuser", password="secret123")
    assert user.username == "testuser"
    assert user.password == "secret123"
    assert user.email == ""
    assert user.is_active is True
    assert user.metadata == {}

    # Test serialization/deserialization
    data = user.model_dump()
    new_user = UserModel.model_validate(data)
    assert new_user.username == user.username
    assert new_user.password == user.password

    print("✓ Drop-in replacement works perfectly")


def test_advanced_features():
    """Test advanced features that pydantic.create_model supports."""
    print("\nTesting advanced features...")

    # Test with docstring
    DocumentedModel = create_basedmodel(
        "DocumentedModel",
        title=str,
        content=str,
        __doc__="A model for documents with title and content",
    )

    assert DocumentedModel.__doc__ == "A model for documents with title and content"

    # Test with base class
    class BaseDocument(BasedModel):
        id: int
        created_at: str

    ExtendedDocument = create_basedmodel(
        "ExtendedDocument", title=str, content=str, __base__=BaseDocument
    )

    doc = ExtendedDocument(
        id=1, created_at="2024-01-01", title="Test", content="Content"
    )
    assert isinstance(doc, BaseDocument)
    assert doc.title == "Test"
    assert doc.id == 1

    print("✓ Advanced features work")


def test_basic_model_creation():
    """Test basic model creation with simple types."""
    print("Testing basic model creation...")

    # Create a simple model
    User = create_basedmodel("User", name=str, age=int)

    # Test instantiation
    user = User(name="Alice", age=30)
    print(f"Created user: {user}")
    assert user.name == "Alice"
    assert user.age == 30
    assert isinstance(user, BasedModel)
    print("✓ Basic model creation works")


def test_model_with_defaults():
    """Test model creation with default values."""
    print("\nTesting model with defaults...")

    # Create model with defaults
    Config = create_basedmodel(
        "Config", host=(str, "localhost"), port=(int, 8080), debug=(bool, False)
    )

    # Test with defaults
    config1 = Config()
    print(f"Config with defaults: {config1}")
    assert config1.host == "localhost"
    assert config1.port == 8080
    assert config1.debug is False

    # Test with overrides
    config2 = Config(host="example.com", port=443, debug=True)
    print(f"Config with overrides: {config2}")
    assert config2.host == "example.com"
    assert config2.port == 443
    assert config2.debug is True
    print("✓ Model with defaults works")


def test_model_with_basedfields():
    """Test model creation with basedfield constraints."""
    print("\nTesting model with basedfields...")

    # Create model with field constraints
    Product = create_basedmodel(
        "Product",
        name=str,
        price=(float, basedfield(gt=0)),
        tags=(List[str], basedfield(default_factory=list)),
        description=(str, basedfield(default="", max_length=500)),
    )

    # Test instantiation
    product = Product(
        name="Widget",
        price=19.99,
        tags=["electronics", "gadget"],
        description="A useful widget",
    )

    print(f"Created product: {product}")
    assert product.name == "Widget"
    assert product.price == 19.99
    assert product.tags == ["electronics", "gadget"]
    assert product.description == "A useful widget"
    print("✓ Model with basedfields works")


def test_model_with_base_class():
    """Test model creation with custom base class."""
    print("\nTesting model with base class...")

    # Create base class with only required fields to avoid ordering issues
    class BaseEntity(BasedModel):
        id: int
        created_at: str

    # Create model with base class
    User = create_basedmodel("User", name=str, email=str, __base__=BaseEntity)

    # Test instantiation
    user = User(id=1, created_at="2024-01-01", name="Bob", email="bob@example.com")
    print(f"Created user with base: {user}")
    assert user.id == 1
    assert user.name == "Bob"
    assert user.email == "bob@example.com"
    assert user.created_at == "2024-01-01"
    assert isinstance(user, BaseEntity)
    assert isinstance(user, BasedModel)
    print("✓ Model with base class works")


def test_model_with_docstring():
    """Test model creation with docstring."""
    print("\nTesting model with docstring...")

    # Create model with docstring
    Person = create_basedmodel(
        "Person", name=str, age=int, __doc__="A person model for testing"
    )

    print(f"Model docstring: {Person.__doc__}")
    assert Person.__doc__ == "A person model for testing"
    print("✓ Model with docstring works")


def test_pydantic_compatibility():
    """Test that the created models work like pydantic models."""
    print("\nTesting pydantic compatibility...")

    # Create a model similar to what you'd do with pydantic.create_model
    APIResponse = create_basedmodel(
        "APIResponse",
        success=bool,
        message=(str, "OK"),
        data=(dict, basedfield(default_factory=dict)),
        status_code=(int, 200),
    )

    # Test model methods
    response = APIResponse(success=True, message="Request successful")

    # Test pydantic-like methods
    assert hasattr(response, "model_dump")
    assert hasattr(response, "model_validate")
    assert hasattr(response, "model_validate_json")

    data = response.model_dump()
    print(f"Response data: {data}")
    assert data["success"] is True
    assert data["message"] == "Request successful"
    assert data["data"] == {}
    assert data["status_code"] == 200

    # Test validation
    new_response = APIResponse.model_validate(data)
    assert new_response.success is True
    assert new_response.message == "Request successful"

    print("✓ Pydantic compatibility works")


def test_error_cases():
    """Test error handling."""
    print("\nTesting error cases...")

    # Test invalid base class
    try:
        create_basedmodel("BadModel", name=str, __base__=dict)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✓ Caught expected error for invalid base: {e}")

    # Test base + config conflict
    try:
        create_basedmodel("BadModel", name=str, __base__=BasedModel, __config__=dict)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✓ Caught expected error for base+config: {e}")

    print("✓ Error handling works")


if __name__ == "__main__":
    pytest.main([__file__, "--verbose"])
