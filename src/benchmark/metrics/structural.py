"""Structural fidelity metrics: element counting via markdown-it-py (EVAL-02).

Per D-09: Parse markdown and count structural elements (headings, tables, lists).
Uses markdown-it-py with table extension enabled (Pitfall 3: MUST call .enable("table")).
"""

from markdown_it import MarkdownIt

# Module-level parser instance with table extension enabled.
# Pitfall 3: Without .enable("table"), pipe tables are not parsed and table_open
# tokens never appear -- tables would count as zero for both tools.
_MD = MarkdownIt().enable("table")


def count_elements(markdown_text: str) -> dict:
    """Count structural elements in markdown text.

    Parses the markdown and counts heading_open, table_open,
    bullet_list_open, and ordered_list_open tokens.

    Args:
        markdown_text: Raw markdown string to analyze.

    Returns:
        Dict with keys:
          - headings (int): Number of headings
          - tables (int): Number of tables
          - lists (int): Number of bullet + ordered lists
          - heading_levels (list[str]): List of heading tags ("h1", "h2", etc.)
    """
    if not markdown_text:
        return {"headings": 0, "tables": 0, "lists": 0, "heading_levels": []}

    tokens = _MD.parse(markdown_text)
    headings = 0
    heading_levels: list[str] = []
    tables = 0
    lists = 0

    for t in tokens:
        if t.type == "heading_open":
            headings += 1
            heading_levels.append(t.tag)  # "h1", "h2", "h3", etc.
        elif t.type == "table_open":
            tables += 1
        elif t.type in ("bullet_list_open", "ordered_list_open"):
            lists += 1

    return {
        "headings": headings,
        "tables": tables,
        "lists": lists,
        "heading_levels": heading_levels,
    }
