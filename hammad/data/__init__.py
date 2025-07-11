"""hammad.data"""

from typing import TYPE_CHECKING
from .._internal import create_getattr_importer

if TYPE_CHECKING:
    from .types import (
        BaseText,
        Text,
    )
    from .models import (
        Model,
        model_settings,
        field,
        validator,
        is_field,
        is_model,
        convert_to_pydantic_model,
        convert_to_pydantic_field,
        is_pydantic_model_class,
    )
    from .collections import (
        Collection,
        create_collection,
        TantivyCollectionIndex,
        QdrantCollectionIndex,
        TantivyCollectionIndexSettings,
        TantivyCollectionIndexQuerySettings,
        QdrantCollectionIndexSettings,
        QdrantCollectionIndexQuerySettings,
    )
    from .sql import (
        DatabaseItemType,
        DatabaseItem,
        Database,
    )
    from .configurations import (
        Configuration,
        read_configuration_from_file,
        read_configuration_from_url,
        read_configuration_from_os_vars,
        read_configuration_from_os_prefix,
        read_configuration_from_dotenv,
    )


__all__ = (
    # hammad.data.types
    "BaseText",
    "Text",
    # hammad.data.models
    "Model",
    "model_settings",
    "field",
    "validator",
    "is_field",
    "is_model",
    "convert_to_pydantic_model",
    "convert_to_pydantic_field",
    "is_pydantic_model_class",
    # hammad.data.collections
    "Collection",
    "create_collection",
    "TantivyCollectionIndex",
    "QdrantCollectionIndex",
    "TantivyCollectionIndexSettings",
    "TantivyCollectionIndexQuerySettings",
    "QdrantCollectionIndexSettings",
    "QdrantCollectionIndexQuerySettings",
    # hammad.data.sql
    "DatabaseItemType",
    "DatabaseItem",
    "Database",
    # hammad.data.configurations
    "Configuration",
    "read_configuration_from_file",
    "read_configuration_from_url",
    "read_configuration_from_os_vars",
    "read_configuration_from_os_prefix",
    "read_configuration_from_dotenv",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    """Get the attributes of the hammad.data module."""
    return list(__all__)
