import pytest
from hammad.data.types.text import (
    BaseText,
    CodeSection,
    SchemaSection,
    SimpleText,
    OutputText,
    Text,
)


class TestBaseText:
    """Test the BaseText class."""

    def test_default_initialization(self):
        """Test BaseText with default values."""
        text = BaseText()
        assert text.content == ""
        assert text.language is None
        assert text.title is None
        assert text.metadata == {}

    def test_initialization_with_content(self):
        """Test BaseText with content."""
        content = "Hello, world!"
        text = BaseText(content=content)
        assert text.content == content
        assert text.language is None
        assert text.title is None

    def test_initialization_with_all_params(self):
        """Test BaseText with all parameters."""
        content = "Test content"
        language = "python"
        title = "Test Title"
        metadata = {"author": "test", "version": "1.0"}

        text = BaseText(
            content=content, language=language, title=title, metadata=metadata
        )

        assert text.content == content
        assert text.language == language
        assert text.title == title
        assert text.metadata == metadata

    def test_str_representation(self):
        """Test string representation."""
        text = BaseText(content="Test content")
        assert str(text) == "Test content"

    def test_repr_representation(self):
        """Test repr representation."""
        text = BaseText(content="Test content", title="Test")
        repr_str = repr(text)
        assert "BaseText" in repr_str
        assert "Test" in repr_str

    def test_equality(self):
        """Test equality comparison."""
        text1 = BaseText(content="same content")
        text2 = BaseText(content="same content")
        text3 = BaseText(content="different content")

        assert text1 == text2
        assert text1 != text3

    def test_length(self):
        """Test length calculation."""
        text = BaseText(content="Hello world")
        assert len(text) == 11

    def test_empty_content(self):
        """Test with empty content."""
        text = BaseText(content="")
        assert len(text) == 0
        assert str(text) == ""


class TestCodeSection:
    """Test the CodeSection class."""

    def test_default_initialization(self):
        """Test CodeSection with default values."""
        code = CodeSection()
        assert code.content == ""
        assert code.language is None
        assert code.title is None

    def test_initialization_with_python_code(self):
        """Test CodeSection with Python code."""
        python_code = """
def hello_world():
    print("Hello, world!")
        """.strip()

        code = CodeSection(content=python_code, language="python")
        assert code.content == python_code
        assert code.language == "python"

    def test_initialization_with_title(self):
        """Test CodeSection with title."""
        code_content = "console.log('Hello');"
        title = "JavaScript Example"

        code = CodeSection(content=code_content, language="javascript", title=title)
        assert code.content == code_content
        assert code.language == "javascript"
        assert code.title == title

    def test_inheritance_from_base_text(self):
        """Test that CodeSection inherits from BaseText."""
        code = CodeSection(content="test code")
        assert isinstance(code, BaseText)
        assert isinstance(code, CodeSection)

    def test_with_metadata(self):
        """Test CodeSection with metadata."""
        metadata = {"file": "example.py", "lines": "1-10"}
        code = CodeSection(
            content="print('test')", language="python", metadata=metadata
        )
        assert code.metadata == metadata


class TestSchemaSection:
    """Test the SchemaSection class."""

    def test_default_initialization(self):
        """Test SchemaSection with default values."""
        schema = SchemaSection()
        assert schema.content == ""
        assert schema.language is None
        assert schema.title is None

    def test_initialization_with_json_schema(self):
        """Test SchemaSection with JSON schema."""
        json_schema = """
{
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "number"}
    }
}
        """.strip()

        schema = SchemaSection(content=json_schema, language="json")
        assert schema.content == json_schema
        assert schema.language == "json"

    def test_initialization_with_yaml_schema(self):
        """Test SchemaSection with YAML schema."""
        yaml_schema = """
type: object
properties:
  name:
    type: string
  age:
    type: number
        """.strip()

        schema = SchemaSection(content=yaml_schema, language="yaml")
        assert schema.content == yaml_schema
        assert schema.language == "yaml"

    def test_inheritance_from_base_text(self):
        """Test that SchemaSection inherits from BaseText."""
        schema = SchemaSection(content="test schema")
        assert isinstance(schema, BaseText)
        assert isinstance(schema, SchemaSection)

    def test_with_title_and_metadata(self):
        """Test SchemaSection with title and metadata."""
        title = "User Schema"
        metadata = {"version": "1.0", "description": "User data schema"}

        schema = SchemaSection(
            content='{"type": "object"}',
            language="json",
            title=title,
            metadata=metadata,
        )

        assert schema.title == title
        assert schema.metadata == metadata


class TestSimpleText:
    """Test the SimpleText class."""

    def test_default_initialization(self):
        """Test SimpleText with default values."""
        text = SimpleText()
        assert text.content == ""
        assert text.language is None
        assert text.title is None

    def test_initialization_with_content(self):
        """Test SimpleText with content."""
        content = "This is simple text content."
        text = SimpleText(content=content)
        assert text.content == content

    def test_initialization_with_title(self):
        """Test SimpleText with title."""
        content = "Content with title"
        title = "Important Note"

        text = SimpleText(content=content, title=title)
        assert text.content == content
        assert text.title == title

    def test_inheritance_from_base_text(self):
        """Test that SimpleText inherits from BaseText."""
        text = SimpleText(content="test text")
        assert isinstance(text, BaseText)
        assert isinstance(text, SimpleText)

    def test_multiline_content(self):
        """Test SimpleText with multiline content."""
        multiline_content = """
This is a multiline
text content that spans
multiple lines.
        """.strip()

        text = SimpleText(content=multiline_content)
        assert text.content == multiline_content
        assert len(text.content.split("\n")) == 3


class TestOutputText:
    """Test the OutputText class."""

    def test_default_initialization(self):
        """Test OutputText with default values."""
        output = OutputText()
        assert output.content == ""
        assert output.language is None
        assert output.title is None

    def test_initialization_with_output(self):
        """Test OutputText with output content."""
        output_content = "Process completed successfully.\nResult: 42"
        output = OutputText(content=output_content)
        assert output.content == output_content

    def test_initialization_with_title(self):
        """Test OutputText with title."""
        content = "Error: File not found"
        title = "Error Output"

        output = OutputText(content=content, title=title)
        assert output.content == content
        assert output.title == title

    def test_inheritance_from_base_text(self):
        """Test that OutputText inherits from BaseText."""
        output = OutputText(content="test output")
        assert isinstance(output, BaseText)
        assert isinstance(output, OutputText)

    def test_with_metadata(self):
        """Test OutputText with metadata."""
        metadata = {"exit_code": 0, "timestamp": "2023-01-01T00:00:00Z"}
        output = OutputText(content="Command executed successfully", metadata=metadata)
        assert output.metadata == metadata


class TestText:
    """Test the Text class (composite text container)."""

    def test_default_initialization(self):
        """Test Text with default values."""
        text = Text()
        assert text.sections == []
        assert text.title is None
        assert text.metadata == {}

    def test_initialization_with_sections(self):
        """Test Text with initial sections."""
        section1 = SimpleText(content="First section")
        section2 = CodeSection(content="print('hello')", language="python")

        text = Text(sections=[section1, section2])
        assert len(text.sections) == 2
        assert text.sections[0] == section1
        assert text.sections[1] == section2

    def test_initialization_with_title(self):
        """Test Text with title."""
        title = "Complete Documentation"
        text = Text(title=title)
        assert text.title == title

    def test_add_section(self):
        """Test adding sections to Text."""
        text = Text()
        section = SimpleText(content="New section")

        text.add_section(section)
        assert len(text.sections) == 1
        assert text.sections[0] == section

    def test_add_multiple_sections(self):
        """Test adding multiple sections."""
        text = Text()

        simple = SimpleText(content="Simple text")
        code = CodeSection(content="x = 1", language="python")
        schema = SchemaSection(content='{"type": "string"}', language="json")

        text.add_section(simple)
        text.add_section(code)
        text.add_section(schema)

        assert len(text.sections) == 3
        assert isinstance(text.sections[0], SimpleText)
        assert isinstance(text.sections[1], CodeSection)
        assert isinstance(text.sections[2], SchemaSection)

    def test_str_representation(self):
        """Test string representation of composite text."""
        text = Text()
        text.add_section(SimpleText(content="First line"))
        text.add_section(CodeSection(content="print('test')", language="python"))

        str_result = str(text)
        assert "First line" in str_result
        assert "print('test')" in str_result

    def test_repr_representation(self):
        """Test repr representation."""
        text = Text(title="Test Document")
        text.add_section(SimpleText(content="Content"))

        repr_str = repr(text)
        assert "Text" in repr_str
        assert "1 section" in repr_str

    def test_length_calculation(self):
        """Test length calculation for composite text."""
        text = Text()
        text.add_section(SimpleText(content="Hello"))  # 5 chars
        text.add_section(SimpleText(content="World"))  # 5 chars

        # Should include sections plus separators
        assert len(text) > 10

    def test_empty_text(self):
        """Test empty Text object."""
        text = Text()
        assert len(text.sections) == 0
        assert len(text) == 0
        assert str(text) == ""

    def test_with_metadata(self):
        """Test Text with metadata."""
        metadata = {"author": "test", "created": "2023-01-01"}
        text = Text(metadata=metadata)
        assert text.metadata == metadata


class TestIntegration:
    """Integration tests for text classes."""

    def test_mixed_content_composition(self):
        """Test composing different types of text content."""
        text = Text(title="API Documentation")

        # Add introduction
        intro = SimpleText(
            content="This API provides user management functionality.",
            title="Introduction",
        )
        text.add_section(intro)

        # Add code example
        code_example = CodeSection(
            content="""
def get_user(user_id):
    return User.objects.get(id=user_id)
            """.strip(),
            language="python",
            title="Code Example",
        )
        text.add_section(code_example)

        # Add schema
        user_schema = SchemaSection(
            content="""
{
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "email": {"type": "string"}
    }
}
            """.strip(),
            language="json",
            title="User Schema",
        )
        text.add_section(user_schema)

        # Add output example
        output_example = OutputText(
            content="""
{
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com"
}
            """.strip(),
            title="Example Response",
        )
        text.add_section(output_example)

        assert len(text.sections) == 4
        assert text.title == "API Documentation"

        # Verify content is accessible
        full_text = str(text)
        assert "This API provides" in full_text
        assert "def get_user" in full_text
        assert '"type": "object"' in full_text
        assert '"id": 123' in full_text

    def test_polymorphic_behavior(self):
        """Test that all text classes work as BaseText objects."""
        sections = [
            SimpleText(content="Simple"),
            CodeSection(content="code", language="python"),
            SchemaSection(content="schema", language="json"),
            OutputText(content="output"),
        ]

        for section in sections:
            assert isinstance(section, BaseText)
            assert hasattr(section, "content")
            assert hasattr(section, "language")
            assert hasattr(section, "title")
            assert hasattr(section, "metadata")

            # All should be stringifiable
            str_result = str(section)
            assert isinstance(str_result, str)

    def test_equality_across_types(self):
        """Test equality comparison across different text types."""
        content = "same content"

        simple = SimpleText(content=content)
        code = CodeSection(content=content)
        schema = SchemaSection(content=content)
        output = OutputText(content=content)

        # Same content should be equal regardless of type
        assert simple == code
        assert code == schema
        assert schema == output

    def test_metadata_preservation(self):
        """Test that metadata is preserved across operations."""
        metadata = {"source": "test", "version": "1.0"}

        text = SimpleText(content="test", metadata=metadata)
        assert text.metadata == metadata

        # Metadata should be accessible after string operations
        str(text)
        assert text.metadata == metadata

    def test_complex_document_structure(self):
        """Test creating a complex document with nested information."""
        doc = Text(
            title="Python Tutorial",
            metadata={"author": "Test Author", "level": "beginner"},
        )

        # Introduction section
        doc.add_section(
            SimpleText(
                content="Python is a high-level programming language.",
                title="What is Python?",
            )
        )

        # Variables section with code
        doc.add_section(
            SimpleText(
                content="Variables in Python are created when you assign a value to them.",
                title="Variables",
            )
        )

        doc.add_section(
            CodeSection(
                content="x = 5\nname = 'Python'\nprint(f'Hello {name}, x = {x}')",
                language="python",
                title="Variable Example",
            )
        )

        # Expected output
        doc.add_section(
            OutputText(content="Hello Python, x = 5", title="Expected Output")
        )

        assert len(doc.sections) == 4
        assert doc.title == "Python Tutorial"
        assert doc.metadata["author"] == "Test Author"

        # Verify the document can be converted to string
        doc_str = str(doc)
        assert "Python is a high-level" in doc_str
        assert "x = 5" in doc_str
        assert "Hello Python, x = 5" in doc_str


if __name__ == "__main__":
    pytest.main(["-v", __file__])
