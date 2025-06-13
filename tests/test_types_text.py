import pytest
from hammad.types.text import Text

def test_text_init():
    """Test Text object initialization."""
    text = Text()
    assert text.text == ""
    
    text_with_content = Text(text="Hello, World!")
    assert text_with_content.text == "Hello, World!"


def test_text_str():
    """Test Text.__str__ method."""
    text = Text(text="Test content")
    assert str(text) == "Test content"


def test_text_repr():
    """Test Text.__repr__ method."""
    text = Text(text="Test content")
    assert repr(text) == "Text(text='Test content')"


def test_text_eq():
    """Test Text.__eq__ method."""
    text1 = Text(text="Same content")
    text2 = Text(text="Same content")
    text3 = Text(text="Different content")
    
    assert text1 == text2
    assert text1 != text3


def test_from_text():
    """Test Text.from_text class method."""
    text = Text.from_text("Hello, World!")
    assert text.text == "Hello, World!"
    assert isinstance(text, Text)


def test_from_type():
    """Test Text.from_type class method."""
    text = Text.from_type(str)
    assert isinstance(text, Text)
    assert "str" in text.text


def test_from_docstring():
    """Test Text.from_docstring class method."""
    def sample_function():
        """This is a sample function docstring."""
        pass
    
    text = Text.from_docstring(sample_function)
    assert isinstance(text, Text)
    assert "sample function docstring" in text.text


def test_from_object_basic():
    """Test Text.from_object class method with basic object."""
    from dataclasses import dataclass
    
    @dataclass
    class Person:
        """A person with name and age."""
        name: str
        age: int
    
    text = Text.from_object(Person)
    assert isinstance(text, Text)
    assert "Person" in text.text
    assert "name" in text.text
    assert "age" in text.text


def test_from_object_with_settings():
    """Test Text.from_object class method with TextSettings."""
    from hammad.settings import TextSettings
    from dataclasses import dataclass
    
    @dataclass
    class Product:
        """A product with name and price."""
        name: str
        price: float
    
    settings: TextSettings = {
        "title": "Custom Product Title",
        "compact": True,
        "show_types": False
    }
    
    text = Text.from_object(Product, settings=settings)
    assert isinstance(text, Text)
    assert "Custom Product Title" in text.text


def test_from_object_with_parameters():
    """Test Text.from_object class method with individual parameters."""
    from dataclasses import dataclass
    
    @dataclass
    class Book:
        """A book with title and author."""
        title: str
        author: str
    
    text = Text.from_object(
        Book,
        title="Custom Book Title",
        compact=True,
        show_types=False,
        show_description=False
    )
    assert isinstance(text, Text)
    assert "Custom Book Title" in text.text


def test_from_object_primitive_types():
    """Test Text.from_object with primitive types."""
    # Test string
    text_str = Text.from_object("Hello")
    assert text_str.text == "Hello"
    
    # Test integer
    text_int = Text.from_object(42)
    assert text_int.text == "42"
    
    # Test boolean
    text_bool = Text.from_object(True)
    assert text_bool.text == "True"
    
    # Test None
    text_none = Text.from_object(None)
    assert text_none.text == "None"


def test_from_object_code_block():
    """Test Text.from_object with code_block=True."""
    from dataclasses import dataclass
    
    @dataclass
    class Config:
        """Configuration settings."""
        debug: bool
        port: int
    
    text = Text.from_object(Config, code_block=True, show_json_schema=True)
    assert isinstance(text, Text)
    assert "```json" in text.text or "```" in text.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])