"""hammad.data.types

Contains functional alias, or model-like objects that are meant to be used
by users as bases as well as for type hints. These objects define simple
interfaces for various types of common objects."""

from typing import TYPE_CHECKING
from ..._internal import create_getattr_importer


if TYPE_CHECKING:
    from .text import (
        BaseText,
        Text,
        SimpleText,
        CodeSection,
        SchemaSection,
        OutputText,
        convert_to_simple_text,
        convert_to_output_text,
        convert_to_output_instructions,
        convert_to_code_section,
        convert_to_schema_section,
        convert_to_base_text,
    )
    from .file import (
        File,
        read_file_from_bytes,
        read_file_from_path,
        read_file_from_url,
    )
    from .multimodal import (
        Audio,
        Image,
        read_audio_from_path,
        read_audio_from_url,
        read_image_from_path,
        read_image_from_url,
    )


__all__ = (
    # hammad.data.types.text
    "BaseText",
    "Text",
    "SimpleText",
    "CodeSection",
    "SchemaSection",
    "OutputText",
    "convert_to_simple_text",
    "convert_to_output_text",
    "convert_to_output_instructions",
    "convert_to_code_section",
    "convert_to_schema_section",
    "convert_to_base_text",
    # hammad.data.types.file
    "File",
    "read_file_from_bytes",
    "read_file_from_path",
    "read_file_from_url",
    # hammad.data.types.multimodal
    "Audio",
    "Image",
    "read_audio_from_path",
    "read_audio_from_url",
    "read_image_from_path",
    "read_image_from_url",
)


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
