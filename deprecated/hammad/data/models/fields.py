"""hammad.data.models.fields"""

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Callable, Dict, List, Literal, Optional, Pattern, Set, Union

import msgspec
from msgspec import field as msgspec_field

__all__ = (
    "FieldInfo",
    "field",
    "Field",
    "str_field",
    "int_field",
    "float_field",
    "list_field",
)


@dataclass(frozen=True, slots=True)
class FieldInfo:
    """Immutable field information container optimized for performance.

    Uses frozen dataclass with slots for memory efficiency and faster attribute access.
    """

    # Core field configuration
    default: Any = msgspec.UNSET
    default_factory: Optional[Callable[[], Any]] = None

    # Naming and aliases
    alias: Optional[str] = None
    validation_alias: Optional[str] = None
    serialization_alias: Optional[str] = None

    # Documentation
    title: Optional[str] = None
    description: Optional[str] = None
    examples: Optional[List[Any]] = None

    # Serialization control
    exclude: bool = False
    include: bool = True
    repr: bool = True

    # Validation configuration
    strict: bool = False
    validate_default: bool = False
    frozen: bool = False
    allow_mutation: bool = True

    # Numeric constraints
    gt: Optional[Union[int, float]] = None
    ge: Optional[Union[int, float]] = None
    lt: Optional[Union[int, float]] = None
    le: Optional[Union[int, float]] = None
    multiple_of: Optional[Union[int, float]] = None
    allow_inf_nan: bool = True

    # String constraints
    pattern: Optional[Union[str, Pattern[str]]] = None
    strip_whitespace: bool = False
    to_lower: bool = False
    to_upper: bool = False

    # Collection constraints
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    unique_items: bool = False

    # Advanced configuration
    discriminator: Optional[str] = None
    json_schema_extra: Optional[Dict[str, Any]] = None
    kw_only: bool = False
    init: bool = True
    init_var: bool = False

    # Union handling
    union_mode: Literal["smart", "left_to_right"] = "smart"

    # Custom validators (stored as tuples for immutability)
    validators: tuple[Callable[[Any], Any], ...] = ()
    pre_validators: tuple[Callable[[Any], Any], ...] = ()
    post_validators: tuple[Callable[[Any], Any], ...] = ()

    def __post_init__(self):
        """Validate field configuration after initialization."""
        # Validate numeric constraints
        if self.gt is not None and self.ge is not None:
            raise ValueError("Cannot specify both 'gt' and 'ge'")
        if self.lt is not None and self.le is not None:
            raise ValueError("Cannot specify both 'lt' and 'le'")

        # Validate string pattern
        if self.pattern is not None and isinstance(self.pattern, str):
            try:
                object.__setattr__(self, "pattern", re.compile(self.pattern))
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {e}")

        # Ensure validators are tuples
        for attr in ("validators", "pre_validators", "post_validators"):
            val = getattr(self, attr)
            if not isinstance(val, tuple):
                object.__setattr__(self, attr, tuple(val) if val else ())

    @lru_cache(maxsize=None)
    def get_effective_alias(
        self, mode: Literal["validation", "serialization", "general"] = "general"
    ) -> Optional[str]:
        """Get the effective alias for a given mode with caching."""
        if mode == "validation" and self.validation_alias:
            return self.validation_alias
        elif mode == "serialization" and self.serialization_alias:
            return self.serialization_alias
        return self.alias

    def apply_constraints(self, value: Any, field_name: str) -> Any:
        """Apply validation constraints to a value."""
        # Pre-validators
        for validator in self.pre_validators:
            value = validator(value)

        # Type-specific constraints
        if isinstance(value, (int, float)):
            value = self._validate_numeric(value, field_name)
        elif isinstance(value, str):
            value = self._validate_string(value, field_name)
        elif isinstance(value, (list, tuple, set, frozenset)):
            value = self._validate_collection(value, field_name)

        # General validators
        for validator in self.validators:
            value = validator(value)

        # Post-validators
        for validator in self.post_validators:
            value = validator(value)

        return value

    def _validate_numeric(
        self, value: Union[int, float], field_name: str
    ) -> Union[int, float]:
        """Apply numeric constraints."""
        if not self.allow_inf_nan and isinstance(value, float):
            if value != value:  # NaN check
                raise ValueError(f"{field_name}: NaN values are not allowed")
            if value == float("inf") or value == float("-inf"):
                raise ValueError(f"{field_name}: Infinite values are not allowed")

        if self.gt is not None and value <= self.gt:
            raise ValueError(f"{field_name}: {value} is not greater than {self.gt}")
        if self.ge is not None and value < self.ge:
            raise ValueError(
                f"{field_name}: {value} is not greater than or equal to {self.ge}"
            )
        if self.lt is not None and value >= self.lt:
            raise ValueError(f"{field_name}: {value} is not less than {self.lt}")
        if self.le is not None and value > self.le:
            raise ValueError(
                f"{field_name}: {value} is not less than or equal to {self.le}"
            )

        if self.multiple_of is not None:
            if isinstance(value, float) or isinstance(self.multiple_of, float):
                # Use float comparison with small epsilon for floats
                remainder = value % self.multiple_of
                if abs(remainder) > 1e-9 and abs(remainder - self.multiple_of) > 1e-9:
                    raise ValueError(
                        f"{field_name}: {value} is not a multiple of {self.multiple_of}"
                    )
            else:
                # Exact comparison for integers
                if value % self.multiple_of != 0:
                    raise ValueError(
                        f"{field_name}: {value} is not a multiple of {self.multiple_of}"
                    )

        return value

    def _validate_string(self, value: str, field_name: str) -> str:
        """Apply string constraints and transformations."""
        # Transformations
        if self.strip_whitespace:
            value = value.strip()
        if self.to_lower:
            value = value.lower()
        if self.to_upper:
            value = value.upper()

        # Length validation
        if self.min_length is not None and len(value) < self.min_length:
            raise ValueError(
                f"{field_name}: String length {len(value)} is less than minimum {self.min_length}"
            )
        if self.max_length is not None and len(value) > self.max_length:
            raise ValueError(
                f"{field_name}: String length {len(value)} exceeds maximum {self.max_length}"
            )

        # Pattern validation
        if self.pattern is not None:
            pattern = (
                self.pattern
                if isinstance(self.pattern, Pattern)
                else re.compile(self.pattern)
            )
            if not pattern.match(value):
                raise ValueError(
                    f"{field_name}: String does not match pattern {pattern.pattern}"
                )

        return value

    def _validate_collection(
        self, value: Union[List, Set, tuple, frozenset], field_name: str
    ) -> Any:
        """Apply collection constraints."""
        # Length validation
        if self.min_length is not None and len(value) < self.min_length:
            raise ValueError(
                f"{field_name}: Collection length {len(value)} is less than minimum {self.min_length}"
            )
        if self.max_length is not None and len(value) > self.max_length:
            raise ValueError(
                f"{field_name}: Collection length {len(value)} exceeds maximum {self.max_length}"
            )

        # Unique items validation for lists/tuples
        if self.unique_items and isinstance(value, (list, tuple)):
            seen = set()
            for item in value:
                # Handle unhashable types
                try:
                    if item in seen:
                        raise ValueError(
                            f"{field_name}: Duplicate items are not allowed"
                        )
                    seen.add(item)
                except TypeError:
                    # For unhashable types, fall back to linear search
                    if value.count(item) > 1:
                        raise ValueError(
                            f"{field_name}: Duplicate items are not allowed"
                        )

        return value

    def to_json_schema(self) -> Dict[str, Any]:
        """Generate JSON schema for this field."""
        schema = {}

        if self.title:
            schema["title"] = self.title
        if self.description:
            schema["description"] = self.description
        if self.examples:
            schema["examples"] = self.examples

        # Numeric constraints
        if self.gt is not None:
            schema["exclusiveMinimum"] = self.gt
        if self.ge is not None:
            schema["minimum"] = self.ge
        if self.lt is not None:
            schema["exclusiveMaximum"] = self.lt
        if self.le is not None:
            schema["maximum"] = self.le
        if self.multiple_of is not None:
            schema["multipleOf"] = self.multiple_of

        # String constraints
        if self.pattern is not None:
            pattern = (
                self.pattern if isinstance(self.pattern, str) else self.pattern.pattern
            )
            schema["pattern"] = pattern
        if self.min_length is not None:
            schema["minLength"] = self.min_length
        if self.max_length is not None:
            schema["maxLength"] = self.max_length

        # Collection constraints
        if self.unique_items:
            schema["uniqueItems"] = True

        # Extra schema properties
        if self.json_schema_extra:
            schema.update(self.json_schema_extra)

        return schema


class Field:
    """Field descriptor that combines msgspec.field with FieldInfo metadata.

    This class wraps msgspec's field functionality while preserving our
    extended metadata for validation and serialization.
    """

    def __init__(self, field_info: FieldInfo):
        self.field_info = field_info
        self._msgspec_field = None

    def __set_name__(self, owner, name):
        """Called when the descriptor is assigned to a class attribute."""
        self.name = name

    def to_msgspec(self) -> Any:
        """Convert to a msgspec field."""
        kwargs = {}

        # Handle default value
        if self.field_info.default is not msgspec.UNSET:
            kwargs["default"] = self.field_info.default
        elif self.field_info.default_factory is not None:
            kwargs["default_factory"] = self.field_info.default_factory

        # Handle field naming
        if self.field_info.alias:
            # Use Annotated with Meta for field renaming
            return msgspec_field(**kwargs)

        return msgspec_field(**kwargs)

    def __repr__(self):
        return f"Field({self.field_info})"


def field(
    default: Any = msgspec.UNSET,
    *,
    default_factory: Optional[Callable[[], Any]] = None,
    alias: Optional[str] = None,
    validation_alias: Optional[str] = None,
    serialization_alias: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    examples: Optional[List[Any]] = None,
    exclude: bool = False,
    include: bool = True,
    repr: bool = True,
    strict: bool = False,
    validate_default: bool = False,
    frozen: bool = False,
    allow_mutation: bool = True,
    gt: Optional[Union[int, float]] = None,
    ge: Optional[Union[int, float]] = None,
    lt: Optional[Union[int, float]] = None,
    le: Optional[Union[int, float]] = None,
    multiple_of: Optional[Union[int, float]] = None,
    allow_inf_nan: bool = True,
    pattern: Optional[Union[str, Pattern[str]]] = None,
    strip_whitespace: bool = False,
    to_lower: bool = False,
    to_upper: bool = False,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    unique_items: bool = False,
    discriminator: Optional[str] = None,
    json_schema_extra: Optional[Dict[str, Any]] = None,
    kw_only: bool = False,
    init: bool = True,
    init_var: bool = False,
    union_mode: Literal["smart", "left_to_right"] = "smart",
    validators: Optional[List[Callable[[Any], Any]]] = None,
    pre_validators: Optional[List[Callable[[Any], Any]]] = None,
    post_validators: Optional[List[Callable[[Any], Any]]] = None,
) -> Any:
    """Create a field descriptor for Model with Pydantic-like configuration.

    This function creates a field with validation, serialization, and schema
    generation capabilities while maintaining msgspec's performance benefits.

    Args:
        default: Default value for the field
        default_factory: Factory function to generate default values
        alias: Alternative name for the field in serialization/deserialization
        validation_alias: Specific alias for validation (input) only
        serialization_alias: Specific alias for serialization (output) only
        title: Human-readable title for documentation
        description: Human-readable description for documentation
        examples: List of example valid values
        exclude: Whether to exclude this field from serialization
        include: Whether to include this field in serialization
        repr: Whether to include in string representation
        strict: Whether to use strict type validation
        validate_default: Whether to validate the default value
        frozen: Whether the field is immutable after creation
        allow_mutation: Whether the field can be modified
        gt: Value must be greater than this
        ge: Value must be greater than or equal to this
        lt: Value must be less than this
        le: Value must be less than or equal to this
        multiple_of: Value must be a multiple of this
        allow_inf_nan: Whether to allow infinity and NaN for floats
        pattern: Regex pattern for string validation
        strip_whitespace: Whether to strip whitespace from strings
        to_lower: Whether to convert strings to lowercase
        to_upper: Whether to convert strings to uppercase
        min_length: Minimum length for strings/collections
        max_length: Maximum length for strings/collections
        unique_items: Whether collection items must be unique
        discriminator: Field name for discriminating unions
        json_schema_extra: Additional JSON schema properties
        kw_only: Whether the field is keyword-only in __init__
        init: Whether to include in __init__
        init_var: Whether the field is init-only
        union_mode: How to validate union types
        validators: List of validation functions
        pre_validators: List of pre-processing validators
        post_validators: List of post-processing validators

    Returns:
        Field descriptor or Annotated type with metadata for use with Model
    """
    # Store field info for potential future use (validation, schema generation, etc.)
    info = FieldInfo(
        default=default,
        default_factory=default_factory,
        alias=alias,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        title=title,
        description=description,
        examples=examples,
        exclude=exclude,
        include=include,
        repr=repr,
        strict=strict,
        validate_default=validate_default,
        frozen=frozen,
        allow_mutation=allow_mutation,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        pattern=pattern,
        strip_whitespace=strip_whitespace,
        to_lower=to_lower,
        to_upper=to_upper,
        min_length=min_length,
        max_length=max_length,
        unique_items=unique_items,
        discriminator=discriminator,
        json_schema_extra=json_schema_extra,
        kw_only=kw_only,
        init=init,
        init_var=init_var,
        union_mode=union_mode,
        validators=tuple(validators or []),
        pre_validators=tuple(pre_validators or []),
        post_validators=tuple(post_validators or []),
    )

    # Build the kwargs for the msgspec field
    kwargs = {}
    if default is not msgspec.UNSET:
        kwargs["default"] = default
    elif default_factory is not None:
        kwargs["default_factory"] = default_factory

    # Create the msgspec field with validation info embedded
    msgspec_field_instance = msgspec_field(**kwargs)

    # For now, just return the msgspec field - let msgspec handle everything
    return msgspec_field_instance


def str_field(
    *,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    pattern: Optional[Union[str, Pattern[str]]] = None,
    strip_whitespace: bool = False,
    to_lower: bool = False,
    to_upper: bool = False,
    **kwargs,
) -> Any:
    """Create a string field with common string-specific options."""
    return field(
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        strip_whitespace=strip_whitespace,
        to_lower=to_lower,
        to_upper=to_upper,
        **kwargs,
    )


def int_field(
    *,
    gt: Optional[int] = None,
    ge: Optional[int] = None,
    lt: Optional[int] = None,
    le: Optional[int] = None,
    multiple_of: Optional[int] = None,
    **kwargs,
) -> Any:
    """Create an integer field with numeric constraints."""
    return field(gt=gt, ge=ge, lt=lt, le=le, multiple_of=multiple_of, **kwargs)


def float_field(
    *,
    gt: Optional[float] = None,
    ge: Optional[float] = None,
    lt: Optional[float] = None,
    le: Optional[float] = None,
    multiple_of: Optional[float] = None,
    allow_inf_nan: bool = True,
    **kwargs,
) -> Any:
    """Create a float field with numeric constraints."""
    return field(
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        **kwargs,
    )


def list_field(
    *,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    unique_items: bool = False,
    **kwargs,
) -> Any:
    """Create a list field with collection constraints."""
    return field(
        default_factory=list,
        min_length=min_length,
        max_length=max_length,
        unique_items=unique_items,
        **kwargs,
    )
