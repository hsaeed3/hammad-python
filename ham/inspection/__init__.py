"""ham.inspection

Contains 'inspection'/'introspection' utilities for various Pythonic objects,
types and constructs. Most of these resources are used for type analysis."""

from ..utils.import_utils import (
    TYPE_CHECKING,
    type_checking_dir_fn,
    type_checking_getattr_fn,
)


if TYPE_CHECKING:
    # ham.inspection.dataclasses
    from .dataclasses import (
        is_dataclass,
        is_dataclass_instance,
        get_dataclass_field_names,
        get_dataclass_type,
    )

    # ham.inspection.pydantic
    from .pydantic import (
        is_pydantic_basemodel,
        is_pydantic_basemodel_instance,
        get_pydantic_model_field_names,
        get_pydantic_model_type,
    )

    # ham.inspection.typing
    from .typing import (
        is_simple_type,
        get_type_description,
        get_standardized_type_name,
        get_literal_type_values,
        is_value_in_literal_type,
        get_enum_type_values,
        is_key_in_enum_type,
        is_value_in_enum_type,
        is_typeddict,
        is_protocol,
        is_function,
        is_union_type,
        is_literal_type,
        is_optional_type,
    )


__all__ = (
    # ham.inspection.dataclasses
    "is_dataclass",
    "is_dataclass_instance",
    "get_dataclass_field_names",
    "get_dataclass_type",
    # ham.inspection.pydantic
    "is_pydantic_basemodel",
    "is_pydantic_basemodel_instance",
    "get_pydantic_model_field_names",
    "get_pydantic_model_type",
    # ham.inspection.typing
    "is_simple_type",
    "get_type_description",
    "get_standardized_type_name",
    "get_literal_type_values",
    "is_value_in_literal_type",
    "get_enum_type_values",
    "is_key_in_enum_type",
    "is_value_in_enum_type",
    "is_typeddict",
    "is_protocol",
    "is_function",
    "is_union_type",
    "is_literal_type",
    "is_optional_type",
)


__getattr__ = type_checking_getattr_fn(__all__)
__dir__ = type_checking_dir_fn(__all__)
