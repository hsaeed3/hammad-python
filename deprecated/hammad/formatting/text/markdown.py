"""hammad.formatting.text.markdown"""

from typing import (
    List,
    Literal,
    Optional,
)

__all__ = (
    "markdown_bold",
    "markdown_italic",
    "markdown_code",
    "markdown_code_block",
    "markdown_heading",
    "markdown_link",
    "markdown_list_item",
    "markdown_table_row",
    "markdown_blockquote",
    "markdown_horizontal_rule",
    "markdown_table",
)


def markdown_bold(text: str) -> str:
    """Format text as bold in Markdown."""
    return f"**{text}**"


def markdown_italic(text: str) -> str:
    """Format text as italic in Markdown."""
    return f"*{text}*"


def markdown_code(text: str) -> str:
    """Format text as inline code in Markdown."""
    return f"`{text}`"


def markdown_code_block(text: str, language: str = "") -> str:
    """Format text as a code block in Markdown."""
    return f"```{language}\n{text}\n```"


def markdown_heading(text: str, level: int = 1) -> str:
    """Format text as a heading in Markdown."""
    if not 1 <= level <= 6:
        level = 1
    return f"{'#' * level} {text}"


def markdown_link(text: str, url: str) -> str:
    """Format text as a link in Markdown."""
    return f"[{text}]({url})"


def markdown_list_item(
    text: str, level: int = 0, ordered: bool = False, index: int = 1
) -> str:
    """Format text as a list item in Markdown."""
    indent = "  " * level
    marker = f"{index}." if ordered else "-"
    return f"{indent}{marker} {text}"


def markdown_table_row(cells: List[str], is_header: bool = False) -> str:
    """Format a table row in Markdown."""
    row = "| " + " | ".join(cells) + " |"
    if is_header:
        separator = "|" + "|".join([" --- " for _ in cells]) + "|"
        return f"{row}\n{separator}"
    return row


def markdown_blockquote(text: str, level: int = 1) -> str:
    """Format text as a blockquote in Markdown."""
    prefix = ">" * level + " "
    lines = text.split("\n")
    return "\n".join(f"{prefix}{line}" for line in lines)


def markdown_horizontal_rule() -> str:
    """Create a horizontal rule in Markdown."""
    return "---"


def markdown_table(
    headers: List[str],
    rows: List[List[str]],
    alignment: Optional[List[Literal["left", "center", "right"]]] = None,
) -> str:
    """
    Create a Markdown table from headers and rows.

    Args:
        headers: List of header strings
        rows: List of row data (each row is a list of strings)
        alignment: Optional list of alignments for each column

    Returns:
        Formatted Markdown table
    """
    if not headers:
        return ""

    parts = []

    # Add header
    parts.append("| " + " | ".join(headers) + " |")

    # Add separator with alignment
    separators = []
    for i, header in enumerate(headers):
        if alignment and i < len(alignment):
            align = alignment[i]
            if align == "center":
                separators.append(" :---: ")
            elif align == "right":
                separators.append(" ---: ")
            else:
                separators.append(" --- ")
        else:
            separators.append(" --- ")
    parts.append("|" + "|".join(separators) + "|")

    # Add rows
    for row in rows:
        # Ensure row has same number of columns as headers
        padded_row = row + [""] * (len(headers) - len(row))
        parts.append("| " + " | ".join(padded_row[: len(headers)]) + " |")

    return "\n".join(parts)
