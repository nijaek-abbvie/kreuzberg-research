"""Shared fixtures for benchmark tests."""

import pytest


@pytest.fixture
def sample_markdown_with_structure():
    """Markdown containing headings, a table, and a list."""
    return (
        "# Title\n\n"
        "## Section One\n\n"
        "Some paragraph text.\n\n"
        "| Col A | Col B |\n"
        "|-------|-------|\n"
        "| val1  | val2  |\n\n"
        "- item one\n"
        "- item two\n"
        "- item three\n"
    )


@pytest.fixture
def sample_markdown_plain():
    """Markdown with only paragraph text, no structural elements."""
    return "Just some plain text with no headings, tables, or lists.\n"


@pytest.fixture
def sample_reference_text():
    """Reference text for OCR accuracy tests."""
    return "the quick brown fox jumps over the lazy dog"


@pytest.fixture
def sample_hypothesis_close():
    """Hypothesis text with minor errors for OCR accuracy tests."""
    return "the quik brown fox jumps over the laxy dog"


@pytest.fixture
def sample_hypothesis_different():
    """Hypothesis text substantially different from reference."""
    return "completely different text with no overlap whatsoever"
