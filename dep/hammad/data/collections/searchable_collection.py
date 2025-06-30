"""hammad.data.collections.searchable_collection"""

import uuid
import json
from typing import Any, Dict, Optional, List, Generic
from datetime import datetime, timezone, timedelta
from dataclasses import asdict, is_dataclass
import tantivy

from .base_collection import BaseCollection, Object, Filters, Schema

__all__ = ("SearchableCollection",)


class SearchableCollection(BaseCollection, Generic[Object]):
    """
    Base collection class that can be used independently or with a database.

    This provides the core collection functionality that can work standalone
    or be integrated with the main Database class.
    """

    def __init__(
        self,
        name: str,
        schema: Optional[Schema] = None,
        default_ttl: Optional[int] = None,
        storage_backend: Optional[Any] = None,
        tantivy_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a collection.

        Args:
            name: The name of the collection
            schema: Optional schema for type validation
            default_ttl: Default TTL for items in seconds
            storage_backend: Optional storage backend (Database instance or custom)
            tantivy_config: Optional tantivy configuration for field properties and index settings
                          Example: {
                              "text_fields": {"fast": True, "stored": True},
                              "numeric_fields": {"fast": True, "indexed": True},
                              "writer_heap_size": 256_000_000,
                              "writer_num_threads": 2
                          }
        """
        self.name = name
        self.schema = schema
        self.default_ttl = default_ttl
        self._storage_backend = storage_backend

        # Store tantivy configuration
        self._tantivy_config = tantivy_config or {}

        # In-memory storage when used independently
        self._items: Dict[str, Dict[str, Any]] = {}

        # Initialize tantivy index
        self._init_tantivy_index()

    def _init_tantivy_index(self):
        """Initialize the tantivy search index."""
        # Build schema for tantivy
        schema_builder = tantivy.SchemaBuilder()

        # Get configuration for different field types
        text_config = self._tantivy_config.get(
            "text_fields", {"stored": True, "fast": True}
        )
        numeric_config = self._tantivy_config.get(
            "numeric_fields", {"stored": True, "indexed": True, "fast": True}
        )
        date_config = self._tantivy_config.get(
            "date_fields", {"stored": True, "indexed": True, "fast": True}
        )
        json_config = self._tantivy_config.get("json_fields", {"stored": True})

        # Add ID field (stored and indexed)
        schema_builder.add_text_field("id", **text_config)

        # Add content field for general text search
        content_config = {
            **text_config,
            "tokenizer_name": "default",
            "index_option": "position",
        }
        schema_builder.add_text_field("content", **content_config)

        # Add dynamic fields that might be searched and sorted
        title_config = {
            **text_config,
            "tokenizer_name": "default",
            "index_option": "position",
        }
        schema_builder.add_text_field("title", **title_config)

        # Add JSON field for storing the actual data
        schema_builder.add_json_field("data", **json_config)

        # Add filter fields as facets
        schema_builder.add_facet_field("filters")

        # Add timestamp fields
        schema_builder.add_date_field("created_at", **date_config)
        schema_builder.add_date_field("expires_at", **date_config)

        # Add numeric fields for sorting
        schema_builder.add_integer_field("score", **numeric_config)

        # Build the schema
        self._tantivy_schema = schema_builder.build()

        # Create index in memory (no path means in-memory)
        self._index = tantivy.Index(self._tantivy_schema)

        # Configure index writer with custom settings if provided
        writer_config = {}
        if "writer_heap_size" in self._tantivy_config:
            writer_config["heap_size"] = self._tantivy_config["writer_heap_size"]
        if "writer_num_threads" in self._tantivy_config:
            writer_config["num_threads"] = self._tantivy_config["writer_num_threads"]

        self._index_writer = self._index.writer(**writer_config)

        # Configure index reader if settings provided
        reader_config = self._tantivy_config.get("reader_config", {})
        if reader_config:
            reload_policy = reader_config.get("reload_policy", "commit")
            num_warmers = reader_config.get("num_warmers", 0)
            self._index.config_reader(
                reload_policy=reload_policy, num_warmers=num_warmers
            )

    def __repr__(self) -> str:
        item_count = len(self._items) if self._storage_backend is None else "managed"
        return f"<{self.__class__.__name__} name='{self.name}' items={item_count}>"

    def _calculate_expires_at(self, ttl: Optional[int]) -> Optional[datetime]:
        """Calculate expiry time based on TTL."""
        if ttl is None:
            ttl = self.default_ttl
        if ttl and ttl > 0:
            return datetime.now(timezone.utc) + timedelta(seconds=ttl)
        return None

    def _is_expired(self, expires_at: Optional[datetime]) -> bool:
        """Check if an item has expired."""
        if expires_at is None:
            return False
        now = datetime.now(timezone.utc)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return now >= expires_at

    def _match_filters(
        self, stored: Optional[Filters], query: Optional[Filters]
    ) -> bool:
        """Check if stored filters match query filters."""
        if query is None:
            return True
        if stored is None:
            return False
        return all(stored.get(k) == v for k, v in query.items())

    def get(self, id: str, *, filters: Optional[Filters] = None) -> Optional[Object]:
        """Get an item by ID."""
        if self._storage_backend is not None:
            # Delegate to storage backend (Database instance)
            return self._storage_backend.get(id, collection=self.name, filters=filters)

        # Independent operation
        item = self._items.get(id)
        if not item:
            return None

        if self._is_expired(item.get("expires_at")):
            del self._items[id]
            return None

        if not self._match_filters(item.get("filters"), filters):
            return None

        return item["value"]

    def _serialize_for_json(self, obj: Any) -> Any:
        """Serialize object for JSON storage."""
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        elif isinstance(obj, (list, tuple)):
            return [self._serialize_for_json(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: self._serialize_for_json(v) for k, v in obj.items()}
        elif is_dataclass(obj):
            return self._serialize_for_json(asdict(obj))
        elif hasattr(obj, "__dict__"):
            return self._serialize_for_json(obj.__dict__)
        else:
            return str(obj)

    def add(
        self,
        entry: Object,
        *,
        id: Optional[str] = None,
        filters: Optional[Filters] = None,
        ttl: Optional[int] = None,
    ) -> None:
        """Add an item to the collection."""
        if self._storage_backend is not None:
            # Delegate to storage backend
            self._storage_backend.add(
                entry, id=id, collection=self.name, filters=filters, ttl=ttl
            )
            return

        # Independent operation
        item_id = id or str(uuid.uuid4())
        expires_at = self._calculate_expires_at(ttl)
        created_at = datetime.now(timezone.utc)

        # Store in memory
        self._items[item_id] = {
            "value": entry,
            "filters": filters or {},
            "created_at": created_at,
            "updated_at": created_at,
            "expires_at": expires_at,
        }

        # Add to tantivy index
        doc = tantivy.Document()
        doc.add_text("id", item_id)

        # Extract searchable content
        content = self._extract_content_for_indexing(entry)
        doc.add_text("content", content)

        # Add title field if present
        if isinstance(entry, dict) and "title" in entry:
            doc.add_text("title", str(entry["title"]))

        # Store the full data as JSON
        serialized_data = self._serialize_for_json(entry)
        # Wrap in object structure for tantivy JSON field
        json_data = {"value": serialized_data}
        doc.add_json("data", json.dumps(json_data))

        # Add filters as facets
        if filters:
            for key, value in filters.items():
                facet_value = f"/{key}/{value}"
                doc.add_facet("filters", tantivy.Facet.from_string(facet_value))

        # Add timestamps
        doc.add_date("created_at", created_at)
        if expires_at:
            doc.add_date("expires_at", expires_at)

        # Add score field if present
        if (
            isinstance(entry, dict)
            and "score" in entry
            and isinstance(entry["score"], (int, float))
        ):
            doc.add_integer("score", int(entry["score"]))

        self._index_writer.add_document(doc)
        self._index_writer.commit()

    def _extract_content_for_indexing(self, value: Any) -> str:
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
                    content_parts.append(json.dumps(v))
                else:
                    content_parts.append(str(v))
            return " ".join(content_parts)
        else:
            return str(value)

    def query(
        self,
        *,
        filters: Optional[Filters] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        fields: Optional[List[str]] = None,
        fuzzy: bool = False,
        fuzzy_distance: int = 2,
        fuzzy_transposition_cost_one: bool = True,
        fuzzy_prefix: bool = False,
        phrase: bool = False,
        phrase_slop: int = 0,
        boost_fields: Optional[Dict[str, float]] = None,
        min_score: Optional[float] = None,
        sort_by: Optional[str] = None,
        ascending: bool = True,
        count: bool = True,
        regex_search: Optional[str] = None,
    ) -> List[Object]:
        """
        Query items from the collection using tantivy search.

        Args:
            filters: Dictionary of filters to apply to results
            search: Search query string supporting boolean operators (AND, OR, NOT, +, -)
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            fields: Specific fields to search in (defaults to content field)
            fuzzy: Enable fuzzy matching for approximate string matching
            fuzzy_distance: Maximum edit distance for fuzzy matching (default: 2)
            fuzzy_transposition_cost_one: Whether transpositions have cost 1 in fuzzy matching
            fuzzy_prefix: Whether to match only as prefix in fuzzy search
            phrase: Treat search query as exact phrase match
            phrase_slop: Maximum number of words that can appear between phrase terms
            boost_fields: Field-specific score boosting weights (field_name -> boost_factor)
            min_score: Minimum relevance score threshold for results
            sort_by: Field name to sort results by (defaults to relevance score)
            ascending: Sort order direction (True for ascending, False for descending)
            count: Whether to count total matches (performance optimization)
            regex_search: Regular expression pattern to search for in specified fields

        Returns:
            List of matching objects sorted by relevance or specified field
        """
        if self._storage_backend is not None:
            # Delegate to storage backend with enhanced parameters
            return self._storage_backend.query(
                collection=self.name,
                filters=filters,
                search=search,
                limit=limit,
                offset=offset,
                fields=fields,
                fuzzy=fuzzy,
                fuzzy_distance=fuzzy_distance,
                fuzzy_transposition_cost_one=fuzzy_transposition_cost_one,
                fuzzy_prefix=fuzzy_prefix,
                phrase=phrase,
                phrase_slop=phrase_slop,
                boost_fields=boost_fields,
                min_score=min_score,
                sort_by=sort_by,
                ascending=ascending,
                count=count,
                regex_search=regex_search,
            )

        # Refresh index and get searcher
        self._index.reload()
        searcher = self._index.searcher()

        # Build the query
        query_parts = []

        # Add filter queries
        if filters:
            for key, value in filters.items():
                facet_query = tantivy.Query.term_query(
                    self._tantivy_schema,
                    "filters",
                    tantivy.Facet.from_string(f"/{key}/{value}"),
                )
                query_parts.append((tantivy.Occur.Must, facet_query))

        # Add search query
        if regex_search:
            # Regular expression query
            search_query = tantivy.Query.regex_query(
                self._tantivy_schema, fields[0] if fields else "content", regex_search
            )
            query_parts.append((tantivy.Occur.Must, search_query))
        elif search:
            if phrase:
                # Phrase query
                words = search.split()
                search_query = tantivy.Query.phrase_query(
                    self._tantivy_schema, "content", words, slop=phrase_slop
                )
            elif fuzzy:
                # Fuzzy query for each term
                terms = search.split()
                fuzzy_queries = []
                for term in terms:
                    fuzzy_q = tantivy.Query.fuzzy_term_query(
                        self._tantivy_schema,
                        "content",
                        term,
                        distance=fuzzy_distance,
                        transposition_cost_one=fuzzy_transposition_cost_one,
                        prefix=fuzzy_prefix,
                    )
                    fuzzy_queries.append((tantivy.Occur.Should, fuzzy_q))
                search_query = tantivy.Query.boolean_query(fuzzy_queries)
            else:
                # Use tantivy's query parser for boolean operators
                # Handle None boost_fields
                if boost_fields:
                    search_query = self._index.parse_query(
                        search,
                        default_field_names=fields or ["content", "title"],
                        field_boosts=boost_fields,
                    )
                else:
                    search_query = self._index.parse_query(
                        search, default_field_names=fields or ["content", "title"]
                    )

            query_parts.append((tantivy.Occur.Must, search_query))

        # Build final query
        if query_parts:
            final_query = tantivy.Query.boolean_query(query_parts)
        else:
            final_query = tantivy.Query.all_query()

        # Execute search
        limit = limit or 100

        # Use tantivy's built-in sorting for known fast fields, otherwise manual sort
        tantivy_sortable_fields = {
            "score",
            "created_at",
            "expires_at",
        }  # Remove title for now

        if sort_by and sort_by in tantivy_sortable_fields:
            # Use tantivy's built-in sorting for fast fields
            try:
                search_result = searcher.search(
                    final_query,
                    limit=limit,
                    offset=offset,
                    count=count,
                    order_by_field=sort_by,
                    order=tantivy.Order.Asc if ascending else tantivy.Order.Desc,
                )
                manual_sort_needed = False
            except Exception:
                # Fallback to manual sorting if tantivy sorting fails
                search_result = searcher.search(
                    final_query, limit=1000, offset=offset, count=count
                )
                manual_sort_needed = True
        else:
            # Default search or manual sorting needed
            search_result = searcher.search(
                final_query,
                limit=1000 if sort_by else limit,
                offset=offset,
                count=count,
            )
            manual_sort_needed = bool(sort_by and sort_by != "score")

        # Extract results
        if manual_sort_needed:
            # Manual sorting needed for non-tantivy fields
            all_results = []
            for score, doc_address in search_result.hits:
                # Skip if min_score is set and score is too low
                if min_score and score < min_score:
                    continue

                doc = searcher.doc(doc_address)

                # Check expiration
                expires_at = doc.get_first("expires_at")
                if expires_at and self._is_expired(expires_at):
                    continue

                # Get the stored data
                data = doc.get_first("data")
                if data:
                    # Parse JSON data back to Python object
                    if isinstance(data, str):
                        json_obj = json.loads(data)
                        parsed_data = json_obj.get("value", json_obj)
                    else:
                        parsed_data = (
                            data.get("value", data) if isinstance(data, dict) else data
                        )
                    all_results.append((score, parsed_data))

            # Sort by the specified field
            all_results.sort(
                key=lambda x: self._get_sort_value(x[1], sort_by), reverse=not ascending
            )

            # Apply limit and extract just the data
            results = [data for _, data in all_results[:limit]]
        else:
            # Direct extraction for tantivy-sorted or unsorted results
            results = []
            for score, doc_address in search_result.hits:
                # Skip if min_score is set and score is too low
                if min_score and score < min_score:
                    continue

                doc = searcher.doc(doc_address)

                # Check expiration
                expires_at = doc.get_first("expires_at")
                if expires_at and self._is_expired(expires_at):
                    continue

                # Get the stored data
                data = doc.get_first("data")
                if data:
                    # Parse JSON data back to Python object
                    if isinstance(data, str):
                        json_obj = json.loads(data)
                        parsed_data = json_obj.get("value", json_obj)
                    else:
                        parsed_data = (
                            data.get("value", data) if isinstance(data, dict) else data
                        )
                    results.append(parsed_data)

        return results

    def _get_sort_value(self, value: Any, sort_field: str) -> Any:
        """Extract sort value from object for specified field."""
        if isinstance(value, dict):
            # For dictionaries, return the value or a default that sorts appropriately
            if sort_field in value:
                val = value[sort_field]
                # Handle numeric values properly
                if isinstance(val, (int, float)):
                    return val
                return str(val)
            # Return a value that sorts to the end for missing fields
            return float("inf") if sort_field == "score" else ""
        elif hasattr(value, sort_field):
            val = getattr(value, sort_field)
            if isinstance(val, (int, float)):
                return val
            return str(val)
        else:
            # Return a value that sorts to the end for missing fields
            return float("inf") if sort_field == "score" else ""

    def attach_to_database(self, database: Any) -> None:
        """Attach this collection to a database instance."""
        self._storage_backend = database
        # Ensure the collection exists in the database
        database.create_collection(
            self.name, schema=self.schema, default_ttl=self.default_ttl
        )
