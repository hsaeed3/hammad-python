"""hammad.based.utils"""

from functools import lru_cache
from typing import Any, Callable, Optional, Pattern, Union, Tuple, Dict, TYPE_CHECKING
import ast
import inspect

from msgspec.structs import Struct

from .fields import BasedFieldInfo, basedfield, BasedField
from .model import BasedModel

__all__ = (
    "create_basedmodel",
    "get_field_info",
    "is_basedfield",
    "is_basedmodel",
    "based_validator",
    "create_lazy_loader",
    "auto_create_lazy_loader",
    "install",
)


def create_basedmodel(
    __model_name: str,
    *,
    __base__: Optional[Union[type, Tuple[type, ...]]] = None,
    __module__: Optional[str] = None,
    __qualname__: Optional[str] = None,
    __doc__: Optional[str] = None,
    __validators__: Optional[Dict[str, Any]] = None,
    __config__: Optional[type] = None,
    **field_definitions: Any,
) -> type[BasedModel]:
    """Create a BasedModel dynamically with Pydantic-compatible interface.

    This function provides a drop-in replacement for pydantic.create_model()
    that creates BasedModel classes instead of pydantic BaseModel classes.

    Args:
        __model_name: Name of the model class to create
        __base__: Base class(es) to inherit from. If None, uses BasedModel.
                  Can be a single class or tuple of classes.
        __module__: Module name for the created class
        __qualname__: Qualified name for the created class
        __doc__: Docstring for the created class
        __validators__: Dictionary of validators (for compatibility - not fully implemented)
        __config__: Configuration class (for compatibility - not fully implemented)
        **field_definitions: Field definitions as keyword arguments.
                           Each can be:
                           - A type annotation (e.g., str, int)
                           - A tuple of (type, default_value)
                           - A tuple of (type, Field(...))
                           - A Field instance

    Returns:
        A new BasedModel class with the specified fields

    Examples:
        # Simple model with basic types
        User = create_basedmodel('User', name=str, age=int)

        # Model with defaults
        Config = create_basedmodel('Config',
                                  host=(str, 'localhost'),
                                  port=(int, 8080))

        # Model with field constraints
        Product = create_basedmodel('Product',
                                   name=str,
                                   price=(float, basedfield(gt=0)),
                                   tags=(List[str], basedfield(default_factory=list)))

        # Model with custom base class
        class BaseEntity(BasedModel):
            id: int
            created_at: str

        User = create_basedmodel('User',
                                name=str,
                                email=str,
                                __base__=BaseEntity)
    """
    # Handle base class specification
    if __base__ is not None and __config__ is not None:
        raise ValueError(
            "Cannot specify both '__base__' and '__config__' - "
            "use a base class with the desired configuration instead"
        )

    # Determine base classes
    if __base__ is None:
        bases = (BasedModel,)
    elif isinstance(__base__, tuple):
        # Ensure all bases are compatible
        for base in __base__:
            if not (issubclass(base, BasedModel) or issubclass(base, Struct)):
                raise ValueError(
                    f"Base class {base} must be a subclass of BasedModel or msgspec.Struct"
                )
        bases = __base__
    else:
        if not (issubclass(__base__, BasedModel) or issubclass(__base__, Struct)):
            raise ValueError(
                f"Base class {__base__} must be a subclass of BasedModel or msgspec.Struct"
            )
        bases = (__base__,)

    # Build class dictionary
    class_dict = {}
    annotations = {}

    # Set metadata
    if __doc__ is not None:
        class_dict["__doc__"] = __doc__
    if __module__ is not None:
        class_dict["__module__"] = __module__
    if __qualname__ is not None:
        class_dict["__qualname__"] = __qualname__

    # Process field definitions in two passes to ensure proper ordering
    # First pass: collect required and optional fields separately
    required_fields = {}
    optional_fields = {}

    for field_name, field_definition in field_definitions.items():
        if field_name.startswith("__") and field_name.endswith("__"):
            # Skip special attributes that were passed as field definitions
            continue

        # Parse field definition
        is_optional = False

        if isinstance(field_definition, tuple):
            if len(field_definition) == 2:
                field_type, field_value = field_definition
                annotations[field_name] = field_type

                # Check if field_value is a Field instance or basedfield
                if hasattr(field_value, "__class__") and (
                    "field" in field_value.__class__.__name__.lower()
                    or hasattr(field_value, "default")
                    or callable(getattr(field_value, "__call__", None))
                ):
                    # It's a field descriptor
                    optional_fields[field_name] = field_value
                else:
                    # It's a default value - create a basedfield with this default
                    optional_fields[field_name] = basedfield(default=field_value)
                is_optional = True
            else:
                raise ValueError(
                    f"Field definition for '{field_name}' must be a 2-tuple of (type, default/Field)"
                )
        elif hasattr(field_definition, "__origin__") or hasattr(
            field_definition, "__class__"
        ):
            # It's a type annotation (like str, int, List[str], etc.) - required field
            annotations[field_name] = field_definition
            required_fields[field_name] = None
        else:
            # It's likely a default value without type annotation
            # We'll infer the type from the value
            annotations[field_name] = type(field_definition)
            optional_fields[field_name] = basedfield(default=field_definition)
            is_optional = True

    # Second pass: add fields in correct order (required first, then optional)
    # This ensures msgspec field ordering requirements are met
    for field_name, field_value in required_fields.items():
        if field_value is not None:
            class_dict[field_name] = field_value

    for field_name, field_value in optional_fields.items():
        class_dict[field_name] = field_value

    # Set annotations in proper order (required fields first, then optional)
    ordered_annotations = {}

    # Add required field annotations first
    for field_name in required_fields:
        if field_name in annotations:
            ordered_annotations[field_name] = annotations[field_name]

    # Add optional field annotations second
    for field_name in optional_fields:
        if field_name in annotations:
            ordered_annotations[field_name] = annotations[field_name]

    class_dict["__annotations__"] = ordered_annotations

    # Handle validators (basic implementation for compatibility)
    if __validators__:
        # Store validators for potential future use
        class_dict["_based_validators"] = __validators__
        # Note: Full validator implementation would require more complex integration

    # Create the dynamic class
    try:
        DynamicModel = type(__model_name, bases, class_dict)
    except Exception as e:
        raise ValueError(f"Failed to create model '{__model_name}': {e}") from e

    return DynamicModel


@lru_cache(maxsize=None)
def get_field_info(field: Any) -> Optional[BasedFieldInfo]:
    """Extract FieldInfo from a field descriptor with caching."""
    if isinstance(field, tuple) and len(field) == 2:
        _, field_info = field
        if isinstance(field_info, BasedFieldInfo):
            return field_info
    elif hasattr(field, "_basedfield_info"):
        return field._basedfield_info
    elif hasattr(field, "field_info"):
        return field.field_info
    elif isinstance(field, BasedField):
        return field.field_info
    elif hasattr(field, "__class__") and field.__class__.__name__ == "FieldDescriptor":
        return field.field_info
    return None


def is_basedfield(field: Any) -> bool:
    """Check if a field is a basedfield."""
    return get_field_info(field) is not None


def is_basedmodel(model: Any) -> bool:
    """Check if a model is a basedmodel."""
    # Check if it's an instance of BasedModel
    if isinstance(model, BasedModel):
        return True

    # Check if it's a BasedModel class (not instance)
    if isinstance(model, type) and issubclass(model, BasedModel):
        return True

    # Check for BasedModel characteristics using duck typing
    # Look for key BasedModel/msgspec.Struct attributes and methods
    if hasattr(model, "__struct_fields__") and hasattr(model, "model_dump"):
        # Check for BasedModel-specific methods
        if (
            hasattr(model, "model_copy")
            and hasattr(model, "model_validate")
            and hasattr(model, "model_to_pydantic")
        ):
            return True

    # Check if it's an instance of any msgspec Struct with BasedModel methods
    try:
        if isinstance(model, Struct) and hasattr(model, "model_dump"):
            return True
    except ImportError:
        pass

    return False


def based_validator(
    *fields: str, pre: bool = False, post: bool = False, always: bool = False
):
    """Decorator to create a validator for specific fields.

    Args:
        *fields: Field names to validate
        pre: Whether this is a pre-validator
        post: Whether this is a post-validator
        always: Whether to run even if the value is not set

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        func._validator_fields = fields
        func._validator_pre = pre
        func._validator_post = post
        func._validator_always = always
        return func

    return decorator


def create_lazy_loader(
    imports_dict: dict[str, str], package: str
) -> Callable[[str], Any]:
    """Create a lazy loader function for __getattr__.

    Args:
        imports_dict: Dictionary mapping attribute names to their module paths
        package: The package name for import_module

    Returns:
        A __getattr__ function that lazily imports modules
    """

    def __getattr__(name: str) -> Any:
        if name in imports_dict:
            from importlib import import_module

            module_path, original_name = imports_dict[name]
            module = import_module(module_path, package)
            return getattr(module, original_name)
        raise AttributeError(f"module '{package}' has no attribute '{name}'")

    return __getattr__


def auto_create_lazy_loader(all_exports: tuple[str, ...]) -> Callable[[str], Any]:
    """Automatically create a lazy loader by inspecting the calling module.

    This function inspects the calling module's source code to extract
    TYPE_CHECKING imports and automatically builds the import map.

    Args:
        all_exports: The __all__ tuple from the calling module

    Returns:
        A __getattr__ function that lazily imports modules
    """
    # Get the calling module's frame
    frame = inspect.currentframe()
    if frame is None or frame.f_back is None:
        raise RuntimeError("Cannot determine calling module")

    calling_frame = frame.f_back
    module_name = calling_frame.f_globals.get("__name__", "")
    package = calling_frame.f_globals.get("__package__", "")
    filename = calling_frame.f_globals.get("__file__", "")

    # Read the source file
    try:
        with open(filename, "r") as f:
            source_code = f.read()
    except (IOError, OSError):
        # Fallback: try to get source from the module
        import sys

        module = sys.modules.get(module_name)
        if module:
            source_code = inspect.getsource(module)
        else:
            raise RuntimeError(f"Cannot read source for module {module_name}")

    # Parse the source to extract TYPE_CHECKING imports
    imports_map = _parse_type_checking_imports(source_code)

    # Filter to only include exports that are in __all__
    filtered_map = {
        name: path for name, path in imports_map.items() if name in all_exports
    }

    return create_lazy_loader(filtered_map, package)


def _parse_type_checking_imports(source_code: str) -> dict[str, tuple[str, str]]:
    """Parse TYPE_CHECKING imports from source code to build import map.

    Args:
        source_code: The source code containing TYPE_CHECKING imports

    Returns:
        Dictionary mapping local names to (module_path, original_name) tuples
    """
    tree = ast.parse(source_code)
    imports_map = {}

    class TypeCheckingVisitor(ast.NodeVisitor):
        def __init__(self):
            self.in_type_checking = False
            self.imports = {}

        def visit_If(self, node):
            # Check if this is a TYPE_CHECKING block
            is_type_checking = False

            if isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
                is_type_checking = True
            elif isinstance(node.test, ast.Attribute):
                if (
                    isinstance(node.test.value, ast.Name)
                    and node.test.value.id == "typing"
                    and node.test.attr == "TYPE_CHECKING"
                ):
                    is_type_checking = True

            if is_type_checking:
                old_state = self.in_type_checking
                self.in_type_checking = True
                for stmt in node.body:
                    self.visit(stmt)
                self.in_type_checking = old_state
            else:
                self.generic_visit(node)

        def visit_ImportFrom(self, node):
            if self.in_type_checking and node.module:
                module_path = f".{node.module}"
                for alias in node.names:
                    original_name = alias.name
                    local_name = alias.asname or original_name
                    self.imports[local_name] = (module_path, original_name)
            self.generic_visit(node)

    visitor = TypeCheckingVisitor()
    visitor.visit(tree)

    return visitor.imports


def install(
    traceback: bool = True,
    uvloop: bool = True,
    print: bool = False,
    input: bool = False,
):
    """Installs various 'opinionated' and optional resources that help
    enhance the development experience, or increase performance.

    Args:
        traceback (bool): Whether to install the rich traceback handler.
        uvloop (bool): Whether to install uvloop.
        print (bool): Whether to install the stylized `print` method as a builtin
            from `hammad.cli`. NOTE: IDEs will not recognize this change statically.
        input (bool): Whether to install the stylized `input` method as a builtin
            from `hammad.cli`. NOTE: IDEs will not recognize this change statically.

    Note:
        IDE limitations: Static analysis tools cannot detect runtime builtin modifications.
        The IDE will still show the original builtin definitions. Consider using explicit
        imports for better IDE support:

        from hammad.cli.plugins import print, input
    """
    import builtins

    if traceback:
        from rich.traceback import install

        install()
    if uvloop:
        from uvloop import install

        install()
    if print:
        from hammad.cli.plugins import print as print_fn

        builtins.print = print_fn
    if input:
        from hammad.cli.plugins import input as input_fn

        builtins.input = input_fn
