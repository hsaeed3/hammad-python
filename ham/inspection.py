"""ham.inspection"""

from .lib.utils.import_utils import (
    TYPE_CHECKING,
    type_checking_dir_fn,
    type_checking_getattr_fn,
)


if TYPE_CHECKING:
    # ham.lib.typing.inspection
    from .lib.typing.inspection import (
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
        get_typeddict_field_names,
    )

    # ham.lib.pydantic.inspection
    from .lib.pydantic.inspection import (
        is_pydantic_basemodel,
        is_pydantic_basemodel_instance,
        get_pydantic_model_field_names,
        get_pydantic_model_cls,
    )

    # ham.lib.dataclasses.inspection
    from .lib.dataclasses.inspection import (
        is_dataclass,
        is_dataclass_instance,
        get_dataclass_cls,
        get_dataclass_field_names,
    )


__all__ = (
    # ham.lib.typing.inspection
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
    "get_typeddict_field_names",
    # ham.lib.pydantic.inspection
    "is_pydantic_basemodel",
    "is_pydantic_basemodel_instance",
    "get_pydantic_model_field_names",
    "get_pydantic_model_cls",
    # ham.lib.dataclasses.inspection
    "is_dataclass",
    "is_dataclass_instance",
    "get_dataclass_cls",
    "get_dataclass_field_names",
)


__getattr__ = type_checking_getattr_fn(__all__)
__dir__ = type_checking_dir_fn(__all__)
