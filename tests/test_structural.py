"""Unit tests for structural fidelity metrics (EVAL-02)."""

import pytest
from benchmark.metrics.structural import count_elements


def test_headings_counted():
    md = "# Heading 1\n\nParagraph.\n\n## Heading 2\n\nMore text.\n\n### Heading 3\n"
    result = count_elements(md)
    assert result["headings"] == 3


def test_heading_levels_tracked():
    md = "# H1\n\n## H2\n\n### H3\n"
    result = count_elements(md)
    assert result["heading_levels"] == ["h1", "h2", "h3"]


def test_table_detection():
    md = "| Col A | Col B |\n|-------|-------|\n| val1  | val2  |\n"
    result = count_elements(md)
    assert result["tables"] == 1


def test_table_enable_regression():
    """Pitfall 3: Table parsing MUST be enabled. This test catches if .enable('table') is removed."""
    md = "| A | B |\n|---|---|\n| 1 | 2 |\n"
    result = count_elements(md)
    assert result["tables"] == 1, "Table not detected -- did .enable('table') get removed from MarkdownIt()?"


def test_bullet_list():
    md = "- item one\n- item two\n- item three\n"
    result = count_elements(md)
    assert result["lists"] == 1


def test_ordered_list():
    md = "1. first\n2. second\n3. third\n"
    result = count_elements(md)
    assert result["lists"] == 1


def test_mixed_lists():
    md = "- bullet one\n- bullet two\n\n1. ordered one\n2. ordered two\n"
    result = count_elements(md)
    assert result["lists"] == 2


def test_full_structure(sample_markdown_with_structure):
    result = count_elements(sample_markdown_with_structure)
    assert result["headings"] == 2  # # Title, ## Section One
    assert result["tables"] == 1
    assert result["lists"] == 1
    assert result["heading_levels"] == ["h1", "h2"]


def test_empty_input():
    result = count_elements("")
    assert result == {"headings": 0, "tables": 0, "lists": 0, "heading_levels": []}


def test_plain_text(sample_markdown_plain):
    result = count_elements(sample_markdown_plain)
    assert result["headings"] == 0
    assert result["tables"] == 0
    assert result["lists"] == 0


def test_return_keys():
    result = count_elements("# Test\n")
    assert set(result.keys()) == {"headings", "tables", "lists", "heading_levels"}
