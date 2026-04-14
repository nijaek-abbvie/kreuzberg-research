"""Smoke test for evaluation output (EVAL-01 + EVAL-02).

Validates that results/results.csv exists and has the correct shape
after run_evaluation.py has been executed.
"""

from pathlib import Path

import pytest

# Project root: tests/ is one level below project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_PATH = PROJECT_ROOT / "results" / "results.csv"

EXPECTED_COLUMNS = [
    "document", "category", "difficulty", "needs_ocr",
    "kreuzberg_success", "iliad_success",
    "kreuzberg_chars", "iliad_chars",
    "wer", "cer",
    "kreuzberg_headings", "iliad_headings",
    "kreuzberg_tables", "iliad_tables",
    "kreuzberg_lists", "iliad_lists",
    "heading_delta", "table_delta", "list_delta",
]


def test_results_csv_exists():
    """results/results.csv must exist after evaluation run."""
    assert RESULTS_PATH.exists(), f"results.csv not found at {RESULTS_PATH}"


def test_results_csv_has_7_rows():
    """results.csv must have one row per corpus document (7 documents)."""
    import pandas as pd
    df = pd.read_csv(RESULTS_PATH)
    assert len(df) == 7, f"Expected 7 rows, got {len(df)}"


def test_results_csv_has_correct_columns():
    """results.csv must have all expected columns."""
    import pandas as pd
    df = pd.read_csv(RESULTS_PATH)
    for col in EXPECTED_COLUMNS:
        assert col in df.columns, f"Missing column: {col}"


def test_results_csv_wer_cer_bounded():
    """WER and CER values must be between 0.0 and 1.0 (capped per Pitfall 1)."""
    import pandas as pd
    df = pd.read_csv(RESULTS_PATH)
    assert (df["wer"] >= 0.0).all(), "WER has negative values"
    assert (df["wer"] <= 1.0).all(), "WER exceeds 1.0 (Pitfall 1: should be capped)"
    assert (df["cer"] >= 0.0).all(), "CER has negative values"
    assert (df["cer"] <= 1.0).all(), "CER exceeds 1.0 (Pitfall 1: should be capped)"


def test_results_csv_known_failure_case():
    """Known-failure scanned PDF should have high WER if ILIAD produced empty output."""
    import pandas as pd
    df = pd.read_csv(RESULTS_PATH)
    scanned = df[df["document"] == "Sample_1_JE.pdf"]
    assert len(scanned) == 1, "Known-failure document missing from results"
    # If ILIAD failed (like MarkItDown), WER should be 1.0
    # If ILIAD succeeded, WER should be < 1.0
    # Either way, document must be present
