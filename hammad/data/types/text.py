"""hammad.types.text

Contains the `BaseText` type, which is a functional type & object
for created intelligently rendered strings and markdown strings
from various input types and objects."""

from __future__ import annotations

import json
from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Union,
    Callable,
    Type,
    ClassVar,
    overload,
    TypeVar,
    Generic,
)

from ...formatting.text.markdown import (
    markdown_heading,
    markdown_code_block,
)
from ...formatting.text.converters import convert_to_text


# -----------------------------------------------------------------------------
# Enums and Types
# -----------------------------------------------------------------------------


class OutputFormat(Enum):
    """Supported output formats for text conversion."""

    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"
    TYPE = "type"
    ANY = "any"


class HeadingStyle(Enum):
    """Heading styles for different formats."""

    # Text formats
    HASH = "#"
    BRACKET = "[]"
    ANGLE = "<>"
    BRACE = "{}"
    # Markdown specific
    UNDERLINE = "="


# -----------------------------------------------------------------------------
# Base Text Class (Unified Type System)
# -----------------------------------------------------------------------------


@dataclass(repr=False, eq=False)
class BaseText(ABC):
    """
    Abstract base class for structured text conversion.

    This class provides a unified interface for converting objects
    to various text formats with extensive customization options.
    All sections are also BaseText instances, creating a unified type system.
    """

    # Class-level configuration
    DEFAULT_FORMAT: ClassVar[OutputFormat] = OutputFormat.TEXT
    SUPPORTED_FORMATS: ClassVar[List[OutputFormat]] = [
        OutputFormat.TEXT,
        OutputFormat.MARKDOWN,
        OutputFormat.JSON,
        OutputFormat.TYPE,
        OutputFormat.ANY,
    ]

    # Core attributes (both for documents and sections)
    type: str = "base"
    """The type identifier for this text object/section."""

    title: Optional[str] = None
    """Title for the document or section."""

    description: Optional[str] = None
    """Description for the document or section."""

    content: Optional[Union[str, Any]] = ""
    """The main content (for sections)."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Metadata for the document/section."""

    language: Optional[str] = None
    """Programming language for code sections (if applicable)."""

    # Hierarchical structure
    sections: List[BaseText] = field(default_factory=list)
    """Child sections (all are BaseText instances)."""

    # Formatting options
    heading_level: int = 2
    """Heading level (1-6) for this section."""

    show_in_toc: bool = True
    """Whether to include in table of contents."""

    collapsible: bool = False
    """Whether this section should be collapsible (for supported formats)."""

    format_config: Dict[OutputFormat, Dict[str, Any]] = field(default_factory=dict)
    """Format-specific configuration options."""

    def build_sections(self) -> List[BaseText]:
        """
        Build and return the sections for this text object.
        Default implementation returns existing sections.
        Subclasses can override to dynamically build sections.
        """
        return self.sections

    def add_section(self, section: BaseText) -> BaseText:
        """Add a section to this text object."""
        self.sections.append(section)
        return self

    def get_format_config(self, format: OutputFormat) -> Dict[str, Any]:
        """Get configuration for a specific format."""
        default_config = {
            OutputFormat.TEXT: {
                "compact": False,
                "show_types": True,
                "title_style": "##",
                "bullet_style": "-",
            },
            OutputFormat.MARKDOWN: {
                "table_format": False,
                "escape_special_chars": False,
                "add_toc": False,
                "add_horizontal_rules": False,
            },
            OutputFormat.JSON: {
                "indent": 2,
                "sort_keys": False,
            },
            OutputFormat.TYPE: {
                "show_full_path": True,
                "include_module": True,
            },
            OutputFormat.ANY: {
                "fallback_format": OutputFormat.TEXT,
                "auto_detect": True,
            },
        }

        config = default_config.get(format, {}).copy()
        config.update(self.format_config.get(format, {}))
        return config

    def to_format(self, format: OutputFormat = None, **kwargs) -> str:
        """
        Convert to the specified format.

        Args:
            format: The output format (defaults to DEFAULT_FORMAT)
            **kwargs: Additional format-specific options

        Returns:
            Formatted string representation
        """
        if format is None:
            format = self.DEFAULT_FORMAT

        if format not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {format}")

        # Ensure sections are built
        if not self.sections:
            self.sections = self.build_sections()

        # Merge configurations
        config = self.get_format_config(format)
        config.update(kwargs)

        # Convert based on format
        if format == OutputFormat.TEXT:
            return self._to_text(**config)
        elif format == OutputFormat.MARKDOWN:
            return self._to_markdown(**config)
        elif format == OutputFormat.JSON:
            return self._to_json(**config)
        elif format == OutputFormat.TYPE:
            return self._to_type(**config)
        elif format == OutputFormat.ANY:
            return self._to_any(**config)
        else:
            raise NotImplementedError(f"Format {format} not implemented")

    def _to_text(self, **kwargs) -> str:
        """Convert to plain text format."""
        parts = []

        # Handle title
        if self.title:
            title_style = kwargs.get("title_style", "##")
            if title_style == "#":
                parts.append("#" * self.heading_level + " " + self.title)
            elif title_style == "[]":
                parts.append(f"[{self.title}]")
            elif title_style == "<>":
                parts.append(f"<{self.title}>")
            elif title_style == "{}":
                parts.append(f"{{{self.title}}}")
            else:
                parts.append(self.title)

        # Handle description
        if self.description:
            parts.append(self.description)

        # Handle content (for sections)
        if self.content:
            if isinstance(self.content, str):
                parts.append(self.content)
            else:
                parts.append(convert_to_text(self.content, **kwargs))

        # Handle subsections
        for section in self.sections:
            sub_kwargs = kwargs.copy()
            sub_kwargs["indent"] = kwargs.get("indent", 0) + 1
            parts.append(section.to_format(OutputFormat.TEXT, **sub_kwargs))

        return "\n\n".join(filter(None, parts))

    def _to_markdown(self, **kwargs) -> str:
        """Convert to Markdown format."""
        parts = []

        # Handle title
        if self.title:
            parts.append(markdown_heading(self.title, self.heading_level))

        # Handle description
        if self.description:
            parts.append(self.description)

        # Handle content (for sections)
        if self.content:
            if isinstance(self.content, str):
                parts.append(self.content)
            else:
                parts.append(convert_to_text(self.content, **kwargs))

        # Add table of contents if requested (only for top-level documents)
        if kwargs.get("add_toc", False) and self.heading_level == 1:
            toc_headings = []
            for section in self.sections:
                if section.show_in_toc and section.title:
                    toc_headings.append((section.heading_level, section.title))

            if toc_headings:
                from ...formatting.text.markdown import markdown_table

                parts.append(markdown_table(toc_headings))

        # Handle subsections
        for section in self.sections:
            sub_kwargs = kwargs.copy()
            sub_kwargs["_indent_level"] = self.heading_level
            parts.append(section.to_format(OutputFormat.MARKDOWN, **sub_kwargs))

        return "\n\n".join(filter(None, parts))

    def _to_json(self, **kwargs) -> str:
        """Convert to JSON format."""
        data = {
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "metadata": self.metadata,
            "sections": [
                json.loads(s.to_format(OutputFormat.JSON, **kwargs))
                for s in self.sections
            ],
        }

        indent = kwargs.get("indent", 2)
        sort_keys = kwargs.get("sort_keys", False)

        return json.dumps(data, indent=indent, sort_keys=sort_keys)

    def _to_type(self, **kwargs) -> str:
        """Convert to type annotation format."""
        show_full_path = kwargs.get("show_full_path", True)
        include_module = kwargs.get("include_module", True)

        type_info = self.__class__.__name__

        if include_module:
            module = self.__class__.__module__
            if module != "__main__" and show_full_path:
                type_info = f"{module}.{type_info}"

        # Include key attributes in the type representation
        attrs = []
        if self.type != "base":
            attrs.append(f"type={self.type!r}")
        if self.title:
            attrs.append(f"title={self.title!r}")
        if self.sections:
            attrs.append(f"sections={len(self.sections)}")

        if attrs:
            type_info += f"({', '.join(attrs)})"

        return type_info

    def _to_any(self, **kwargs) -> str:
        """Convert using automatic format detection or fallback."""
        fallback_format = kwargs.get("fallback_format", OutputFormat.TEXT)
        auto_detect = kwargs.get("auto_detect", True)

        if auto_detect:
            # Simple heuristics for format detection
            if self.content and isinstance(self.content, str):
                content_lower = self.content.lower().strip()

                # Check for JSON content
                if content_lower.startswith("{") and content_lower.endswith("}"):
                    return self.to_format(OutputFormat.JSON, **kwargs)

                # Check for code content
                if any(
                    keyword in content_lower
                    for keyword in ["def ", "class ", "import ", "from "]
                ):
                    return self.to_format(OutputFormat.MARKDOWN, **kwargs)

            # Check if this looks like schema documentation
            if hasattr(self, "output_schema") or self.type in ["schema", "output"]:
                return self.to_format(OutputFormat.MARKDOWN, **kwargs)

        # Use fallback format
        return self.to_format(fallback_format, **kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "metadata": self.metadata,
            "sections": [s.to_dict() for s in self.sections],
        }

    # Convenience methods
    def __str__(self) -> str:
        """String representation using default format."""
        return self.to_format()

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        section_count = len(self.sections)
        section_text = "section" if section_count == 1 else "sections"
        if section_count > 0:
            return f"{self.__class__.__name__}(type={self.type!r}, title={self.title!r}, {section_count} {section_text})"
        else:
            return f"{self.__class__.__name__}(type={self.type!r}, title={self.title!r}, sections={section_count})"

    @property
    def text(self) -> str:
        """Quick access to text format."""
        return self.to_format(OutputFormat.TEXT)

    @property
    def markdown(self) -> str:
        """Quick access to markdown format."""
        return self.to_format(OutputFormat.MARKDOWN)

    @property
    def json(self) -> str:
        """Quick access to JSON format."""
        return self.to_format(OutputFormat.JSON)

    @property
    def type_info(self) -> str:
        """Quick access to type format."""
        return self.to_format(OutputFormat.TYPE)

    @property
    def any_format(self) -> str:
        """Quick access to any format (auto-detected)."""
        return self.to_format(OutputFormat.ANY)

    def __len__(self) -> int:
        """Return the length of the content."""
        if self.content is None:
            return 0
        return len(str(self.content))

    def __eq__(self, other) -> bool:
        """Check equality based on content."""
        if not isinstance(other, BaseText):
            return False
        return str(self.content or "") == str(other.content or "")


# -----------------------------------------------------------------------------
# Specialized Section Classes (Now BaseText Subclasses)
# -----------------------------------------------------------------------------


@dataclass(repr=False, eq=False)
class CodeSection(BaseText):
    """Section specifically for code content."""

    type: str = "code"
    line_numbers: bool = False
    highlight_lines: Optional[List[int]] = None

    def _to_markdown(self, **kwargs) -> str:
        """Convert to Markdown with code block."""
        parts = []

        if self.title:
            parts.append(markdown_heading(self.title, self.heading_level))

        if self.description:
            parts.append(self.description)

        if self.content:
            parts.append(markdown_code_block(str(self.content), self.language or ""))

        # Handle subsections
        for section in self.sections:
            sub_kwargs = kwargs.copy()
            sub_kwargs["_indent_level"] = self.heading_level
            parts.append(section.to_format(OutputFormat.MARKDOWN, **sub_kwargs))

        return "\n\n".join(filter(None, parts))


@dataclass(repr=False, eq=False)
class SchemaSection(BaseText):
    """Section for schema/model documentation."""

    type: str = "schema"
    schema_object: Optional[Any] = None
    show_examples: bool = True
    table_format: bool = True

    def _to_markdown(self, **kwargs) -> str:
        """Convert schema to Markdown documentation."""
        if self.schema_object:
            return convert_to_text(
                self.schema_object,
                name=self.title,
                description=self.description,
                table_format=self.table_format,
                **kwargs,
            )
        return super()._to_markdown(**kwargs)


# -----------------------------------------------------------------------------
# Concrete Implementation Classes
# -----------------------------------------------------------------------------


@dataclass(repr=False, eq=False)
class SimpleText(BaseText):
    """Simple concrete implementation of BaseText for basic use cases."""

    type: str = "simple"

    def build_sections(self) -> List[BaseText]:
        """Simple text doesn't build sections dynamically."""
        return self.sections


@dataclass(repr=False, eq=False)
class OutputText(BaseText):
    """
    Implementation for structured output documentation.
    """

    DEFAULT_FORMAT: ClassVar[OutputFormat] = OutputFormat.MARKDOWN
    type: str = "output"

    # Specific attributes for output documentation
    output_schema: Optional[Any] = None
    """The schema/model to document."""

    examples: List[Dict[str, Any]] = field(default_factory=list)
    """Example outputs."""

    validation_rules: List[str] = field(default_factory=list)
    """Validation rules for the output."""

    error_cases: List[Dict[str, str]] = field(default_factory=list)
    """Common error cases and messages."""

    def build_sections(self) -> List[BaseText]:
        """Build sections for output documentation."""
        sections = []

        # Schema section
        if self.output_schema:
            sections.append(
                SchemaSection(
                    title="Output Schema",
                    schema_object=self.output_schema,
                    description="The following schema defines the structure of the output:",
                    table_format=True,
                )
            )

        # Examples section
        if self.examples:
            examples_section = SimpleText(
                type="examples",
                title="Examples",
                description="Here are some example outputs:",
            )

            for i, example in enumerate(self.examples, 1):
                examples_section.add_section(
                    CodeSection(
                        title=f"Example {i}",
                        content=json.dumps(example, indent=2),
                        language="json",
                        heading_level=3,
                    )
                )

            sections.append(examples_section)

        # Validation rules section
        if self.validation_rules:
            rules_content = "\n".join(f"- {rule}" for rule in self.validation_rules)
            sections.append(
                SimpleText(
                    type="validation",
                    title="Validation Rules",
                    content=rules_content,
                )
            )

        # Error cases section
        if self.error_cases:
            error_section = SimpleText(
                type="errors",
                title="Common Errors",
                description="The following errors may occur:",
            )

            for error in self.error_cases:
                error_content = f"**Error**: {error.get('error', 'Unknown')}\n"
                error_content += f"**Message**: {error.get('message', 'No message')}\n"
                if "solution" in error:
                    error_content += f"**Solution**: {error['solution']}"

                error_section.add_section(
                    SimpleText(
                        type="error",
                        title=error.get("code", "ERROR"),
                        content=error_content,
                        heading_level=3,
                    )
                )

            sections.append(error_section)

        return sections

    @classmethod
    def from_function(
        cls, func: Callable, include_examples: bool = True, **kwargs
    ) -> OutputText:
        """
        Create OutputText from a function's return type and docstring.

        Args:
            func: The function to document
            include_examples: Whether to parse examples from docstring
            **kwargs: Additional arguments for OutputText

        Returns:
            OutputText instance
        """
        from typing import get_type_hints

        # Extract function information
        func_name = func.__name__
        hints = get_type_hints(func)
        return_type = hints.get("return", Any)

        # Create instance
        output_text = cls(
            title=kwargs.get("title", f"Output for {func_name}"),
            description=kwargs.get("description", None),
            output_schema=return_type,
            **kwargs,
        )

        return output_text


# -----------------------------------------------------------------------------
# Example Usage
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    from dataclasses import dataclass
    from typing import Optional

    # Define a sample schema
    @dataclass
    class UserResponse:
        """User information response."""

        id: int
        username: str
        email: str
        is_active: bool = True
        role: Optional[str] = None

    # Create output documentation
    output_doc = OutputText(
        title="User API Response",
        description="Documentation for the user endpoint response format.",
        output_schema=UserResponse,
        examples=[
            {
                "id": 123,
                "username": "john_doe",
                "email": "john@example.com",
                "is_active": True,
                "role": "admin",
            },
            {
                "id": 456,
                "username": "jane_smith",
                "email": "jane@example.com",
                "is_active": False,
                "role": None,
            },
        ],
        validation_rules=[
            "ID must be a positive integer",
            "Username must be unique and contain only alphanumeric characters and underscores",
            "Email must be a valid email address",
            "Role must be one of: admin, user, guest (or null)",
        ],
        error_cases=[
            {
                "code": "USER_NOT_FOUND",
                "error": "User not found",
                "message": "The requested user ID does not exist",
                "solution": "Verify the user ID and try again",
            },
            {
                "code": "INVALID_EMAIL",
                "error": "Invalid email format",
                "message": "The provided email address is not valid",
                "solution": "Ensure the email follows the format: user@domain.com",
            },
        ],
    )

    # Get different formats
    print("=== MARKDOWN FORMAT ===")
    print(output_doc.markdown)

    print("\n\n=== TEXT FORMAT ===")
    print(output_doc.text)

    print("\n\n=== JSON FORMAT ===")
    print(output_doc.json)

    print("\n\n=== TYPE FORMAT ===")
    print(output_doc.type_info)

    print("\n\n=== ANY FORMAT (auto-detected) ===")
    print(output_doc.any_format)


# -----------------------------------------------------------------------------
# Unified Text Class - Main Entry Point
# -----------------------------------------------------------------------------

T = TypeVar("T")


@dataclass(repr=False, eq=False)
class Text(BaseText, Generic[T]):
    """
    Unified Text class - the main entry point for all text operations.

    This class provides a clean, fully-typed interface for creating and managing
    structured text content with support for multiple output formats.
    """

    DEFAULT_FORMAT: ClassVar[OutputFormat] = OutputFormat.MARKDOWN
    type: str = "text"

    # Enhanced typing for content
    content: Optional[Union[str, T, Any]] = None

    def __init__(
        self,
        content: Optional[Union[str, T, Any]] = None,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        type: str = "text",
        format: Optional[OutputFormat] = None,
        heading_level: int = 1,
        show_in_toc: bool = True,
        collapsible: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        sections: Optional[List[BaseText]] = None,
        format_config: Optional[Dict[OutputFormat, Dict[str, Any]]] = None,
        **kwargs,
    ) -> None:
        """
        Initialize a Text instance.

        Args:
            content: The main content (string, object, or any serializable type)
            title: Optional title for the text
            description: Optional description
            type: Type identifier (default: "text")
            format: Default output format
            heading_level: Heading level (1-6)
            show_in_toc: Whether to show in table of contents
            collapsible: Whether the section should be collapsible
            metadata: Additional metadata
            sections: Child sections
            format_config: Format-specific configuration
            **kwargs: Additional arguments
        """
        super().__init__(
            type=type,
            title=title,
            description=description,
            content=content,
            metadata=metadata or {},
            sections=sections or [],
            heading_level=heading_level,
            show_in_toc=show_in_toc,
            collapsible=collapsible,
            format_config=format_config or {},
        )

        # Set default format if provided
        if format is not None:
            self.DEFAULT_FORMAT = format

    @classmethod
    def from_string(
        cls,
        text: str,
        *,
        title: Optional[str] = None,
        format: OutputFormat = OutputFormat.TEXT,
        **kwargs,
    ) -> "Text[str]":
        """Create Text from a simple string."""
        return cls(content=text, title=title, format=format, **kwargs)

    @classmethod
    def from_markdown(
        cls, markdown: str, *, title: Optional[str] = None, **kwargs
    ) -> "Text[str]":
        """Create Text from markdown content."""
        return cls(
            content=markdown, title=title, format=OutputFormat.MARKDOWN, **kwargs
        )

    @classmethod
    def from_object(
        cls,
        obj: T,
        *,
        title: Optional[str] = None,
        format: OutputFormat = OutputFormat.MARKDOWN,
        **kwargs,
    ) -> "Text[T]":
        """Create Text from any object."""
        return cls(
            content=obj,
            title=title or f"{type(obj).__name__} Documentation",
            format=format,
            **kwargs,
        )

    @classmethod
    def from_schema(
        cls,
        schema: Type[T],
        *,
        title: Optional[str] = None,
        examples: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> "Text[Type[T]]":
        """Create Text from a schema/dataclass type."""
        output_text = OutputText(
            title=title or f"{schema.__name__} Schema",
            output_schema=schema,
            examples=examples or [],
            **kwargs,
        )
        return cls(
            content=output_text,
            title=output_text.title,
            format=OutputFormat.MARKDOWN,
            type="schema",
        )

    @classmethod
    def from_function(
        cls,
        func: Callable[..., T],
        *,
        title: Optional[str] = None,
        include_examples: bool = True,
        **kwargs,
    ) -> "Text[Callable[..., T]]":
        """Create Text from a function's documentation."""
        output_text = OutputText.from_function(
            func, title=title, include_examples=include_examples, **kwargs
        )
        return cls(
            content=output_text,
            title=output_text.title,
            format=OutputFormat.MARKDOWN,
            type="function",
        )

    def add_code_section(
        self,
        code: str,
        *,
        language: str = "python",
        title: Optional[str] = None,
        description: Optional[str] = None,
        line_numbers: bool = False,
        **kwargs,
    ) -> "Text[T]":
        """Add a code section to this text."""
        code_section = CodeSection(
            content=code,
            language=language,
            title=title,
            description=description,
            line_numbers=line_numbers,
            heading_level=self.heading_level + 1,
            **kwargs,
        )
        self.add_section(code_section)
        return self

    def add_text_section(
        self,
        content: Union[str, Any],
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs,
    ) -> "Text[T]":
        """Add a text section to this text."""
        text_section = SimpleText(
            content=content,
            title=title,
            description=description,
            heading_level=self.heading_level + 1,
            **kwargs,
        )
        self.add_section(text_section)
        return self

    def add_schema_section(
        self,
        schema: Any,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        table_format: bool = True,
        **kwargs,
    ) -> "Text[T]":
        """Add a schema documentation section."""
        schema_section = SchemaSection(
            schema_object=schema,
            title=title,
            description=description,
            table_format=table_format,
            heading_level=self.heading_level + 1,
            **kwargs,
        )
        self.add_section(schema_section)
        return self

    @overload
    def render(self, format: Literal[OutputFormat.TEXT]) -> str: ...

    @overload
    def render(self, format: Literal[OutputFormat.MARKDOWN]) -> str: ...

    @overload
    def render(self, format: Literal[OutputFormat.JSON]) -> str: ...

    @overload
    def render(self, format: Literal[OutputFormat.TYPE]) -> str: ...

    @overload
    def render(self, format: Literal[OutputFormat.ANY]) -> str: ...

    def render(self, format: Optional[OutputFormat] = None, **kwargs) -> str:
        """
        Render the text in the specified format.

        Args:
            format: Output format (uses DEFAULT_FORMAT if None)
            **kwargs: Format-specific options

        Returns:
            Formatted string representation
        """
        return self.to_format(format, **kwargs)

    def save(
        self,
        filepath: str,
        *,
        format: Optional[OutputFormat] = None,
        encoding: str = "utf-8",
        **kwargs,
    ) -> None:
        """
        Save the text to a file.

        Args:
            filepath: Path to save the file
            format: Output format (auto-detected from extension if None)
            encoding: File encoding
            **kwargs: Format-specific options
        """
        import os

        # Auto-detect format from file extension if not provided
        if format is None:
            ext = os.path.splitext(filepath)[1].lower()
            format_map = {
                ".md": OutputFormat.MARKDOWN,
                ".markdown": OutputFormat.MARKDOWN,
                ".json": OutputFormat.JSON,
                ".txt": OutputFormat.TEXT,
                ".text": OutputFormat.TEXT,
            }
            format = format_map.get(ext, self.DEFAULT_FORMAT)

        # Render content
        content = self.render(format, **kwargs)

        # Write to file
        with open(filepath, "w", encoding=encoding) as f:
            f.write(content)

    def chain(self, other: "Text") -> "Text[T]":
        """Chain another Text instance as a section."""
        self.add_section(other)
        return self

    def __add__(self, other: Union["Text", str, BaseText]) -> "Text[T]":
        """Add operator for chaining texts."""
        if isinstance(other, str):
            return self.add_text_section(other)
        elif isinstance(other, BaseText):
            return self.add_section(other)
        else:
            raise TypeError(f"Cannot add {type(other)} to Text")

    def __or__(self, format: OutputFormat) -> str:
        """Pipe operator for format conversion."""
        return self.render(format)

    def __getitem__(self, key: Union[int, str]) -> BaseText:
        """Access sections by index or title."""
        if isinstance(key, int):
            return self.sections[key]
        elif isinstance(key, str):
            for section in self.sections:
                if section.title == key:
                    return section
            raise KeyError(f"Section with title '{key}' not found")
        else:
            raise TypeError(f"Invalid key type: {type(key)}")

    def __len__(self) -> int:
        """Return total character count of all sections."""
        if not self.sections:
            return 0
        total_length = 0
        for section in self.sections:
            total_length += len(section)
        # Add separators between sections (2 chars for \n\n)
        return total_length + (len(self.sections) - 1) * 2

    def __iter__(self):
        """Iterate over sections."""
        return iter(self.sections)

    def __bool__(self) -> bool:
        """Check if text has content or sections."""
        return bool(self.content or self.sections or self.title)

    # Enhanced property access with type hints
    @property
    def text(self) -> str:
        """Get text format representation."""
        return self.render(OutputFormat.TEXT)

    @property
    def markdown(self) -> str:
        """Get markdown format representation."""
        return self.render(OutputFormat.MARKDOWN)

    @property
    def json(self) -> str:
        """Get JSON format representation."""
        return self.render(OutputFormat.JSON)

    @property
    def type_info(self) -> str:
        """Get type format representation."""
        return self.render(OutputFormat.TYPE)

    @property
    def auto(self) -> str:
        """Get auto-detected format representation."""
        return self.render(OutputFormat.ANY)


__all__ = (
    "OutputFormat",
    "HeadingStyle",
    "BaseText",
    "CodeSection",
    "SchemaSection",
    "SimpleText",
    "OutputText",
    "Text",
)
