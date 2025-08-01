"""ham.core.types

Internal types, as well as forwarded types from:

- `pydantic-extra-types`
- `pydantic-settings`

```markdown
Core type collection within the `hammad-python` ecosystem. This module contains a
very wide collection of both 'static' or just referenced types, as well as full
models with a lot of useful utilities and functionality.
```"""

from typing import TYPE_CHECKING
from .._internal import type_checking_importer


if TYPE_CHECKING:
    from .configuration import Configuration
    from .file import File
    from .text import Text
    from .jsonrpc import (
        JSONRPCRequest,
        JSONRPCNotification,
        JSONRPCResponse,
        JSONRPCError,
        JSONRPCMessage,
    )
    from .image import Image
    from .audio import Audio

    # forwarding
    from pydantic.types import (
        AnyType,
        Base64Bytes,
        Base64Encoder,
        Base64Str,
        ByteSize,
        conbytes,
        condate,
        condecimal,
        confloat,
        confrozenset,
        conint,
        conlist,
        conset,
        constr,
        DirectoryPath,
        Discriminator,
        EncodedBytes,
        EncodedStr,
        EncoderProtocol,
        FilePath,
        FailFast,
        FiniteFloat,
        FutureDate,
        FutureDatetime,
        GetPydanticSchema,
        ImportString,
        Json,
        JsonValue,
        NewPath,
        OnErrorOmit,
        PaymentCardBrand,
        Secret,
        SecretBytes,
        SecretStr,
        SecretType,
        SocketPath,
        Strict,
        StrictBool,
        StrictBytes,
        StrictFloat,
        StrictInt,
        StrictStr,
        StringConstraints,
        Tag,
        UUID1,
        UUID3,
        UUID4,
        UUID5,
        UUID6,
        UUID7,
        UUID8,
        UuidVersion,
    )
    from pydantic_extra_types.color import Color
    from pydantic_extra_types.coordinate import Coordinate, CoordinateType
    from pydantic_extra_types.currency_code import Currency
    from pydantic_extra_types.domain import DomainStr
    from pydantic_extra_types.epoch import EPOCH
    from pydantic_extra_types.isbn import ISBN
    from pydantic_extra_types.language_code import LanguageName, LanguageInfo
    from pydantic_extra_types.mac_address import MacAddress
    from pydantic_extra_types.mongo_object_id import MongoObjectId
    from pydantic_extra_types.phone_numbers import PhoneNumber, PhoneNumberValidator
    from pydantic_extra_types.path import (
        ExistingPath,
        ResolvedFilePath,
        ResolvedDirectoryPath,
        ResolvedNewPath,
        ResolvedExistingPath,
    )
    from pydantic_extra_types.routing_number import ABARoutingNumber
    from pydantic_extra_types.s3 import S3Path
    from pydantic_extra_types.timezone_name import TimeZoneName, TimeZoneNameSettings
    from pydantic_extra_types.ulid import ULID, UlidType


__all__ = (
    # ham.core.types.configuration
    "Configuration",
    # ham.core.types.file
    "File",
    # ham.core.types.text
    "Text",
    # ham.core.types.jsonrpc
    "JSONRPCRequest",
    "JSONRPCNotification",
    "JSONRPCResponse",
    "JSONRPCError",
    "JSONRPCMessage",
    # ham.core.types.image
    "Image",
    # ham.core.types.audio
    "Audio",
    # forwarding (pydantic)
    "AnyType",
    "Base64Bytes",
    "Base64Encoder",
    "Base64Str",
    "ByteSize",
    "conbytes",
    "condate",
    "condecimal",
    "confloat",
    "confrozenset",
    "conint",
    "conlist",
    "conset",
    "constr",
    "DirectoryPath",
    "Discriminator",
    "EncodedBytes",
    "EncodedStr",
    "EncoderProtocol",
    "FilePath",
    "FailFast",
    "FiniteFloat",
    "FutureDate",
    "FutureDatetime",
    "GetPydanticSchema",
    "ImportString",
    "Json",
    "JsonValue",
    "NewPath",
    "OnErrorOmit",
    "PaymentCardBrand",
    "Secret",
    "SecretBytes",
    "SecretStr",
    "SecretType",
    "SocketPath",
    "Strict",
    "StrictBool",
    "StrictBytes",
    "StrictFloat",
    "StrictInt",
    "StrictStr",
    "StringConstraints",
    "Tag",
    "UUID1",
    "UUID3",
    "UUID4",
    "UUID5",
    "UUID6",
    "UUID7",
    "UUID8",
    "UuidVersion",
    # forwarding (pydantic-extra-types)
    "Color",
    "Coordinate",
    "CoordinateType",
    "Currency",
    "DomainStr",
    "EPOCH",
    "ISBN",
    "LanguageName",
    "LanguageInfo",
    "MacAddress",
    "MongoObjectId",
    "PhoneNumber",
    "PhoneNumberValidator",
    "ExistingPath",
    "ResolvedFilePath",
    "ResolvedDirectoryPath",
    "ResolvedNewPath",
    "ResolvedExistingPath",
    "ABARoutingNumber",
    "S3Path",
    "TimeZoneName",
    "TimeZoneNameSettings",
    "ULID",
    "UlidType",
)


__getattr__ = type_checking_importer(__all__)


def __dir__() -> list[str]:
    return list(__all__)
