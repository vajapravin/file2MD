"""Markdown stitching and normalization for parallel document chunks."""

import re
from typing import List


def merge_csv_tables(table_markdowns: List[str]) -> str:
    """Merge multiple Markdown tables generated from CSV chunks into a single table.

    The first chunk provides the header and separator rows. Subsequent chunks have
    their table header and separator stripped to produce one unified table.
    """
    if not table_markdowns:
        return ""

    if len(table_markdowns) == 1:
        return table_markdowns[0].strip()

    combined_rows: List[str] = []

    for idx, table_md in enumerate(table_markdowns):
        lines = [line.strip() for line in table_md.strip().split("\n") if line.strip()]
        if not lines:
            continue

        if idx == 0:
            # Keep entire first table
            combined_rows.extend(lines)
        else:
            # Check if first line is a table header matching the table format
            # Filter out header row (line 0) and separator row (line 1 with |---|)
            content_lines = []
            for line_idx, line in enumerate(lines):
                if line_idx == 0 and line.startswith("|") and line.endswith("|"):
                    continue
                if line_idx == 1 and re.match(r"^\|[\s\-:|]+\|$", line):
                    continue
                content_lines.append(line)

            combined_rows.extend(content_lines)

    return "\n".join(combined_rows).strip()


def merge_markdown_chunks(chunk_markdowns: List[str], extension: str) -> str:
    """Stitch multiple converted Markdown chunks into a single unified Markdown document.

    Args:
        chunk_markdowns: Ordered list of Markdown strings from each chunk.
        extension: Original file extension (e.g. '.pdf', '.csv', '.txt').

    Returns:
        Consolidated, cleaned Markdown document.
    """
    ext = extension.lower()

    if not chunk_markdowns:
        return ""

    if ext == ".csv":
        merged = merge_csv_tables(chunk_markdowns)
    elif ext == ".pdf":
        # Separate page chunks with clean spacing
        merged = "\n\n".join(md.strip() for md in chunk_markdowns if md.strip())
    else:
        # Standard text/markdown chunk merge
        merged = "\n\n".join(md.strip() for md in chunk_markdowns if md.strip())

    # Normalize excessive newlines
    normalized = re.sub(r"\n{3,}", "\n\n", merged)
    return normalized.strip()
