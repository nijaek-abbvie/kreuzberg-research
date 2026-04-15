"""Smoke test for report output (REPT-01 + REPT-02).

Validates that BENCHMARK_REPORT.md exists at the project root and contains
the required known-failure analysis and go/no-go recommendation sections
after run_report.py has been executed.
"""

from pathlib import Path

import pytest

# Project root: tests/ is one level below project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = PROJECT_ROOT / "BENCHMARK_REPORT.md"


@pytest.fixture(scope="module")
def report_text() -> str:
    """Read BENCHMARK_REPORT.md once for the test module."""
    assert REPORT_PATH.exists(), f"Run run_report.py first: {REPORT_PATH} not found"
    return REPORT_PATH.read_text(encoding="utf-8")


def test_report_exists() -> None:
    """BENCHMARK_REPORT.md must exist at project root after run_report.py."""
    assert REPORT_PATH.exists(), f"BENCHMARK_REPORT.md not found at {REPORT_PATH}"


def test_report_has_known_failure_section(report_text: str) -> None:
    """Report must contain a dedicated section for the scanned PDF failure case (REPT-01)."""
    assert "Sample_1_JE" in report_text


def test_report_char_counts_present(report_text: str) -> None:
    """Char counts 619 and 3158 must appear in report (D-07)."""
    assert "619" in report_text, "ILIAD char count 619 missing from report"
    assert "3158" in report_text, "Kreuzberg char count 3158 missing from report"


def test_report_has_recommendation(report_text: str) -> None:
    """Report must contain a go/no-go recommendation section (REPT-02)."""
    assert "Recommendation" in report_text


def test_report_minimum_length(report_text: str) -> None:
    """Report must be non-trivially sized (not just a stub)."""
    assert len(report_text) > 2000, (
        f"Report too short ({len(report_text)} chars) — expected substantial document"
    )
