"""hammad.data.collections.indexes.tantivy.utils"""

from dataclasses import dataclass, is_dataclass, asdict
from msgspec import json
from typing import Any, Dict, List, Optional, final

import tantivy

from .....cache import cached
from .settings import (
    TantivyCollectionIndexSettings,
    TantivyCollectionIndexQuerySettings,
)


__all__ = (
    "TantivyCollectionIndexError",
    "extract_content_for_indexing",
)


class TantivyCollectionIndexError(Exception):
    """Exception raised when an error occurs in the `TantivyCollectionIndex`."""


@dataclass
class TantivyIndexWrapper:
    """Wrapper over the `tantivy` index object."""

    index: tantivy.Index
    """The `tantivy` index object."""

    schema: tantivy.Schema
    """The `tantivy` schema object."""

    index_writer: Any
    """The `tantivy` index writer object."""


@cached
def match_filters_for_query(
    stored_filters: Dict[str, Any] | None = None,
    query_filters: Dict[str, Any] | None = None,
) -> bool:
    """Checks if stored filters match query filters."""
    if query_filters is None:
        return True
    if stored_filters is None:
        return False
    return all(stored_filters.get(k) == v for k, v in query_filters.items())


@cached
def serialize(obj: Any) -> Any:
    """Serializes an object to JSON."""
    try:
        return json.decode(json.encode(obj))
    except Exception:
        # Fallback to manual serialization if msgspec fails
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        elif isinstance(obj, (list, tuple)):
            return [serialize(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: serialize(v) for k, v in obj.items()}
        elif is_dataclass(obj):
            return serialize(asdict(obj))
        elif hasattr(obj, "__dict__"):
            return serialize(obj.__dict__)
        else:
            return str(obj)


@cached
def build_tantivy_index_from_settings(
    settings: TantivyCollectionIndexSettings,
) -> TantivyIndexWrapper:
    """Builds a new `tantivy` index from the given settings."""
    # Init schema for index
    schema_builder = tantivy.SchemaBuilder()

    # Add fields
    # ID (stored and indexed)
    schema_builder.add_text_field("id", **settings.get_tantivy_config()["text_fields"])
    # Content (stored and indexed) Contains entry content
    schema_builder.add_text_field(
        "content",
        **{
            **settings.get_tantivy_config()["text_fields"],
            "tokenizer_name": "default",
            "index_option": "position",
        },
    )
    # Title (stored and indexed) Contains entry title
    schema_builder.add_text_field(
        "title",
        **{
            **settings.get_tantivy_config()["text_fields"],
            "tokenizer_name": "default",
            "index_option": "position",
        },
    )
    # JSON (stored) Contains actual entry data
    schema_builder.add_json_field(
        "data", **settings.get_tantivy_config()["json_fields"]
    )

    # Timestamps
    schema_builder.add_date_field(
        "created_at", **settings.get_tantivy_config()["date_fields"]
    )
    schema_builder.add_date_field(
        "expires_at", **settings.get_tantivy_config()["date_fields"]
    )

    # Sorting / Scoring
    schema_builder.add_integer_field(
        "score", **settings.get_tantivy_config()["numeric_fields"]
    )

    # Facet for Optional filters
    schema_builder.add_facet_field("filters")

    # Build the schema
    schema = schema_builder.build()

    # Create index in memory (no path means in-memory)
    index = tantivy.Index(schema)

    # Configure index writer with custom settings if provided
    writer_config = {}
    if "writer_heap_size" in settings.get_tantivy_config():
        writer_config["heap_size"] = settings.get_tantivy_config()["writer_heap_size"]
    if "writer_num_threads" in settings.get_tantivy_config():
        writer_config["num_threads"] = settings.get_tantivy_config()[
            "writer_num_threads"
        ]

    index_writer = index.writer(**writer_config)

    # Configure index reader if settings provided
    reader_config = settings.get_tantivy_config().get("reader_config", {})
    if reader_config:
        reload_policy = reader_config.get("reload_policy", "commit")
        num_warmers = reader_config.get("num_warmers", 0)
        index.config_reader(reload_policy=reload_policy, num_warmers=num_warmers)

    return TantivyIndexWrapper(schema=schema, index=index, index_writer=index_writer)


@cached
def extract_content_for_indexing(value: Any) -> str:
    """Extract searchable text content from value for indexing."""
    if isinstance(value, str):
        return value
    elif isinstance(value, dict):
        # Concatenate all string values
        content_parts = []
        for v in value.values():
            if isinstance(v, str):
                content_parts.append(v)
            elif isinstance(v, (list, dict)):
                content_parts.append(json.encode(v).decode())
            else:
                content_parts.append(str(v))
        return " ".join(content_parts)
    elif isinstance(value, (list, tuple)):
        content_parts = []
        for item in value:
            if isinstance(item, str):
                content_parts.append(item)
            else:
                content_parts.append(str(item))
        return " ".join(content_parts)
    else:
        return str(value)
