"""hammad.data.collections.indexes.tantivy.index"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Generic, List, Optional, Type, final
import uuid
from pathlib import Path
import json

import tantivy

from ....sql.types import (
    DatabaseItemType,
    DatabaseItemFilters,
    DatabaseItem,
)
from ....sql.database import Database
from . import utils
from .settings import (
    TantivyCollectionIndexSettings,
    TantivyCollectionIndexQuerySettings,
)


@final
class TantivyCollectionIndex(Generic[DatabaseItemType]):
    """A standalone (simplified) index that can be used as the
    storage / search engine for a collection, that implements
    fast indexing & querying capabilities using the
    `tantivy` package.

    This collection index is built into the core dependencies
    of the `hammad-python` package, and is the default index
    used by the `Collection` class."""

    def __init__(
        self,
        *,
        name: str = "default",
        schema: Optional[Type[DatabaseItemType]] = None,
        ttl: Optional[int] = None,
        path: Optional[Path | str] = None,
        fast: bool = True,
        settings: Optional[TantivyCollectionIndexSettings] = None,
        query_settings: Optional[TantivyCollectionIndexQuerySettings] = None,
    ) -> None:
        """Initialize a new `TantivyCollectionIndex` with a given set
        of parameters.

        Args:
            name: The name of the index.
            schema: The schema of the items that can be stored
                within this index.
            ttl: The time to live for the items within this index.
            path: The path to the directory where the index will be stored.
                (If not provided, the collection will be built on memory. This is how to
                distinguish between different collection locations.)
            fast: Whether to use fast schema building & indexing
                from `tantivy`'s builtin implementation.
            settings: Default settings to use for indexing & schema
                building.
            query_settings: Default settings to use for the query
                engine.
        """
        self.name = name
        self.schema = schema
        self.ttl = ttl

        if path is not None and not isinstance(path, Path):
            path = Path(path)

        self.path = path
        """The file path to the collection index.

        (You wouldnt know), but earlier versions of this package allowed
        for implementing `databases` with file system paths. The new
        structure of the package does not implement the `Database` class
        anymore, and rather allows for creating custom extensions using
        collections directly.
        
        Ex: `/database/collection.db | /database/collection.myextension`"""

        if not settings:
            settings = TantivyCollectionIndexSettings(
                fast=fast,
            )

        if not query_settings:
            query_settings = TantivyCollectionIndexQuerySettings()

        self.settings = settings
        """The default settings to use when indexing and schema building
        for this index."""

        self.query_settings = query_settings
        """The default settings to use when querying this index."""

        # Initialize SQL Database as storage backend
        database_path = None
        if self.path is not None:
            database_path = self.path / f"{name}.db"

        self._database = Database[DatabaseItemType](
            name=name,
            schema=schema,
            ttl=ttl,
            path=database_path,
            table_name=f"tantivy_{name}",
        )

        try:
            self._tantivy_wrapper = utils.build_tantivy_index_from_settings(
                settings=settings
            )
            self._index = self._tantivy_wrapper.index
            self._schema = self._tantivy_wrapper.schema
            self._writer = self._tantivy_wrapper.index_writer
        except Exception as e:
            raise utils.TantivyCollectionIndexError(
                f"Failed to build tantivy index from settings: {e}"
            ) from e

    def add(
        self,
        item: DatabaseItemType,
        *,
        id: Optional[str] = None,
        filters: Optional[DatabaseItemFilters] = None,
        ttl: Optional[int] = None,
    ) -> str:
        """Add a new item to the index.

        Args:
            item: The item to add to the index.
            id: The id of the item.
            filters: The filters to apply to the item.
            ttl: The time to live for the item.

        Returns:
            The ID of the added item.
        """
        # Add to SQL database first
        item_id = self._database.add(
            item=item,
            id=id,
            filters=filters,
            ttl=ttl,
        )

        # Add to tantivy index for search
        self._add_to_tantivy_index(item_id, item, filters)

        return item_id

    def _add_to_tantivy_index(
        self,
        item_id: str,
        item: DatabaseItemType,
        filters: Optional[DatabaseItemFilters] = None,
    ) -> None:
        """Add item to tantivy search index."""
        doc = tantivy.Document()

        # Add ID field
        doc.add_text("id", item_id)

        # Extract and add content for search
        content = utils.extract_content_for_indexing(item)
        doc.add_text("content", content)

        # Add title field if present
        if isinstance(item, dict) and "title" in item:
            doc.add_text("title", str(item["title"]))

        # Store the full data as JSON in tantivy
        serialized_data = utils.serialize(item)
        json_data = {"value": serialized_data}
        doc.add_json("data", json.dumps(json_data))

        # Add filters as facets
        if filters:
            for key, value in filters.items():
                facet_value = f"/{key}/{value}"
                doc.add_facet("filters", tantivy.Facet.from_string(facet_value))

        # Add timestamps
        now = datetime.now(timezone.utc)
        doc.add_date("created_at", now)

        # Add score field if present
        if (
            isinstance(item, dict)
            and "score" in item
            and isinstance(item["score"], (int, float))
        ):
            doc.add_integer("score", int(item["score"]))

        # Add to index
        self._writer.add_document(doc)
        self._writer.commit()

    def get(
        self,
        id: str,
        *,
        filters: Optional[DatabaseItemFilters] = None,
    ) -> Optional[DatabaseItem[DatabaseItemType]]:
        """Get an item by ID.

        Args:
            id: The item ID.
            filters: Optional filters to match.

        Returns:
            The database item or None if not found.
        """
        return self._database.get(id, filters=filters)

    def query(
        self,
        query: Optional[str] = None,
        *,
        filters: Optional[DatabaseItemFilters] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        fuzzy: bool = False,
        fuzzy_distance: int = 2,
        phrase: bool = False,
        phrase_slop: int = 0,
        boost_fields: Optional[Dict[str, float]] = None,
        min_score: Optional[float] = None,
        sort_by: Optional[str] = None,
        ascending: bool = True,
    ) -> List[DatabaseItem[DatabaseItemType]]:
        """Query items using tantivy search.

        Args:
            query: Search query string.
            filters: Dictionary of filters to apply.
            limit: Maximum number of results.
            offset: Number of results to skip.
            fuzzy: Enable fuzzy matching.
            fuzzy_distance: Maximum edit distance for fuzzy matching.
            phrase: Treat query as exact phrase match.
            phrase_slop: Max words between phrase terms.
            boost_fields: Field-specific score boosting.
            min_score: Minimum relevance score threshold.
            sort_by: Field to sort by.
            ascending: Sort direction.

        Returns:
            List of matching database items.
        """
        if not query:
            # No search query - use database query directly
            return self._database.query(
                limit=limit,
                offset=offset,
                order_by=sort_by,
                ascending=ascending,
            )

        # Use tantivy for search
        self._index.reload()
        searcher = self._index.searcher()

        # Build tantivy query
        query_parts = []

        # Add filter queries
        if filters:
            for key, value in filters.items():
                facet_query = tantivy.Query.term_query(
                    self._schema,
                    "filters",
                    tantivy.Facet.from_string(f"/{key}/{value}"),
                )
                query_parts.append((tantivy.Occur.Must, facet_query))

        # Add search query
        if phrase:
            words = query.split()
            search_query = tantivy.Query.phrase_query(
                self._schema, "content", words, slop=phrase_slop
            )
        elif fuzzy:
            terms = query.split()
            fuzzy_queries = []
            for term in terms:
                fuzzy_q = tantivy.Query.fuzzy_term_query(
                    self._schema,
                    "content",
                    term,
                    distance=fuzzy_distance,
                )
                fuzzy_queries.append((tantivy.Occur.Should, fuzzy_q))
            search_query = tantivy.Query.boolean_query(fuzzy_queries)
        else:
            # Use tantivy's query parser
            if boost_fields:
                search_query = self._index.parse_query(
                    query,
                    default_field_names=["content", "title"],
                    field_boosts=boost_fields,
                )
            else:
                search_query = self._index.parse_query(
                    query, default_field_names=["content", "title"]
                )

        query_parts.append((tantivy.Occur.Must, search_query))

        # Build final query
        if query_parts:
            final_query = tantivy.Query.boolean_query(query_parts)
        else:
            final_query = tantivy.Query.all_query()

        # Execute search
        search_limit = limit or self.query_settings.limit

        # Perform search
        search_result = searcher.search(
            final_query,
            limit=search_limit,
            offset=offset,
        )

        # Get IDs from search results and fetch from database
        item_ids = []
        for score, doc_address in search_result.hits:
            if min_score and score < min_score:
                continue

            doc = searcher.doc(doc_address)
            item_id = doc.get_first("id")
            if item_id:
                item_ids.append(item_id)

        # Fetch items from database by IDs
        results = []
        for item_id in item_ids:
            db_item = self._database.get(item_id, filters=filters)
            if db_item:
                results.append(db_item)

        return results

    def delete(self, id: str) -> bool:
        """Delete an item by ID.

        Args:
            id: The item ID.

        Returns:
            True if item was deleted, False if not found.
        """
        # Delete from database
        deleted = self._database.delete(id)

        if deleted:
            # Remove from tantivy index by reindexing without this item
            # Note: Tantivy doesn't have efficient single-document deletion
            # For now, we rely on the database as the source of truth
            pass

        return deleted

    def count(
        self,
        query: Optional[str] = None,
        *,
        filters: Optional[DatabaseItemFilters] = None,
    ) -> int:
        """Count items matching the query and filters.

        Args:
            query: Search query string.
            filters: Dictionary of filters to apply.

        Returns:
            Number of matching items.
        """
        if not query:
            # Simple count from database
            from ....sql.types import QueryFilter, QueryCondition

            query_filter = None
            if filters:
                conditions = [
                    QueryCondition(
                        field="filters", operator="contains", value=json.dumps(filters)
                    )
                ]
                query_filter = QueryFilter(conditions=conditions)

            return self._database.count(query_filter)
        else:
            # Count via search results
            results = self.query(query, filters=filters, limit=None)
            return len(results)

    def clear(self) -> int:
        """Clear all items from the index.

        Returns:
            Number of items deleted.
        """
        count = self._database.clear()

        # Clear tantivy index by rebuilding it
        try:
            self._tantivy_wrapper = utils.build_tantivy_index_from_settings(
                settings=self.settings
            )
            self._index = self._tantivy_wrapper.index
            self._schema = self._tantivy_wrapper.schema
            self._writer = self._tantivy_wrapper.index_writer
        except Exception:
            pass

        return count

    def __repr__(self) -> str:
        """String representation of the index."""
        location = str(self.path) if self.path else "memory"
        return f"<TantivyCollectionIndex name='{self.name}' location='{location}'>"
