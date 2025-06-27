"""hammad.data.types.files.document"""

import httpx
from typing import Any, Self, Iterator
from markdown_it import MarkdownIt

from .file import File, FileSource
from ....based.fields import basedfield

__all__ = ("Document",)


class Document(File):
    """A representation of a document, that is loadable from both a URL, file path
    or bytes. This document can additionally be used to represent web pages, as well
    as implement markdown formatting for both documents and web pages."""

    # Cached properties for text processing
    _lines: list[str] | None = basedfield(default=None)
    _content: str | None = basedfield(default=None)
    _md_parser: MarkdownIt | None = basedfield(default=None)
    metadata: dict[str, Any] = basedfield(default_factory=dict)

    @property
    def content(self) -> str:
        """Get the document content as string."""
        if self._content is None:
            data = self.read()
            self._content = (
                data
                if isinstance(data, str)
                else data.decode(self.source.encoding or "utf-8")
            )
        return self._content

    @property
    def lines(self) -> list[str]:
        """Get lines of the document (cached for efficiency)."""
        if self._lines is None:
            self._lines = self.content.splitlines(keepends=False)
        return self._lines

    @property
    def line_count(self) -> int:
        """Get the number of lines in the document."""
        return len(self.lines)

    @property
    def word_count(self) -> int:
        """Get the word count of the document."""
        return len(self.content.split())

    @property
    def char_count(self) -> int:
        """Get the character count of the document."""
        return len(self.content)

    @property
    def is_markdown(self) -> bool:
        """Check if the document is a markdown file."""
        return self.extension in {".md", ".markdown", ".mdown", ".mkd", ".mdx"}

    @property
    def md_parser(self) -> MarkdownIt:
        """Get the markdown parser (lazy initialization)."""
        if self._md_parser is None:
            self._md_parser = MarkdownIt()
        return self._md_parser

    def iter_lines(self, *, strip: bool = False) -> Iterator[str]:
        """Iterate over lines in the document.

        Args:
            strip: If True, strip whitespace from each line.

        Yields:
            Lines from the document.
        """
        for line in self.lines:
            yield line.strip() if strip else line

    def iter_paragraphs(self) -> Iterator[str]:
        """Iterate over paragraphs (text blocks separated by empty lines)."""
        paragraph = []
        for line in self.lines:
            if line.strip():
                paragraph.append(line)
            elif paragraph:
                yield "\n".join(paragraph)
                paragraph = []
        if paragraph:
            yield "\n".join(paragraph)

    def search(
        self, pattern: str, *, case_sensitive: bool = False
    ) -> list[tuple[int, str]]:
        """Search for a pattern in the document.

        Args:
            pattern: The pattern to search for.
            case_sensitive: If True, search is case-sensitive.

        Returns:
            List of tuples (line_number, line_content) for matching lines.
        """
        results = []
        search_pattern = pattern if case_sensitive else pattern.lower()

        for i, line in enumerate(self.lines):
            search_line = line if case_sensitive else line.lower()
            if search_pattern in search_line:
                results.append((i + 1, line))  # 1-indexed line numbers

        return results

    def render_markdown(self) -> str:
        """Render markdown content to HTML."""
        if not self.is_markdown:
            return self.content
        return self.md_parser.render(self.content)

    def extract_headers(self) -> list[tuple[int, str]]:
        """Extract headers from markdown documents.

        Returns:
            List of tuples (level, text) for each header.
        """
        headers = []
        if self.is_markdown:
            tokens = self.md_parser.parse(self.content)
            i = 0
            while i < len(tokens):
                if tokens[i].type == "heading_open":
                    level = int(tokens[i].tag[1])  # h1 -> 1, h2 -> 2, etc.
                    # Next token should be inline with the content
                    if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                        headers.append((level, tokens[i + 1].content))
                i += 1
        else:
            # For non-markdown files, look for common header patterns
            for line in self.lines:
                stripped = line.strip()
                if stripped.startswith("#"):
                    level = len(line) - len(line.lstrip("#"))
                    text = line.lstrip("#").strip()
                    headers.append((level, text))
        return headers

    @classmethod
    def from_url(
        cls,
        url: str,
        *,
        lazy: bool = True,
        timeout: float = 30.0,
    ) -> Self:
        """Download and create a document from a URL.

        Args:
            url: The URL to download from.
            lazy: If True, defer loading content until needed.
            timeout: Request timeout in seconds.

        Returns:
            A new Document instance.
        """
        data = None
        size = None
        encoding = None
        type = None

        if not lazy:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(url)
                response.raise_for_status()

                # Always get text for documents
                data = response.text
                size = len(data.encode("utf-8"))
                encoding = response.encoding

                # Get content type
                content_type = response.headers.get("content-type", "")
                type = content_type.split(";")[0] if content_type else "text/plain"

        return cls(
            data=data,
            type=type,
            source=FileSource(
                is_url=True,
                url=url,
                size=size,
                encoding=encoding,
            ),
        )
