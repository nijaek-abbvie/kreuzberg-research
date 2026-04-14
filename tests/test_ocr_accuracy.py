"""Unit tests for OCR accuracy metrics (EVAL-01)."""

import pytest
from benchmark.metrics.ocr_accuracy import compute_ocr_metrics


def test_identical_texts():
    result = compute_ocr_metrics("hello world", "hello world")
    assert result["wer"] == 0.0
    assert result["cer"] == 0.0


def test_close_match(sample_reference_text, sample_hypothesis_close):
    result = compute_ocr_metrics(sample_reference_text, sample_hypothesis_close)
    assert 0.0 < result["wer"] < 1.0
    assert 0.0 < result["cer"] < 1.0


def test_completely_different(sample_reference_text, sample_hypothesis_different):
    result = compute_ocr_metrics(sample_reference_text, sample_hypothesis_different)
    assert result["wer"] >= 0.8  # substantially different


def test_failure_penalty():
    """D-06: Failed extraction (empty hypothesis) scores max error."""
    result = compute_ocr_metrics("some reference text with actual content", "")
    assert result["wer"] == 1.0
    assert result["cer"] == 1.0


def test_both_empty():
    """D-06: Both empty = both equally failed = 0.0 error."""
    result = compute_ocr_metrics("", "")
    assert result["wer"] == 0.0
    assert result["cer"] == 0.0


def test_html_comment_stripping():
    """Pitfall 4: ILIAD output contains HTML comment page markers."""
    result = compute_ocr_metrics(
        "hello world",
        "<!-- Page number: 0 -->hello world"
    )
    assert result["wer"] < 0.1  # near zero after stripping
    assert result["cer"] < 0.1


def test_case_insensitive():
    result = compute_ocr_metrics("Hello World", "hello world")
    assert result["wer"] == 0.0
    assert result["cer"] == 0.0


def test_whitespace_normalization():
    result = compute_ocr_metrics("hello   world", "hello world")
    assert result["wer"] == 0.0


def test_return_type():
    result = compute_ocr_metrics("test", "test")
    assert isinstance(result, dict)
    assert set(result.keys()) == {"wer", "cer"}
    assert isinstance(result["wer"], float)
    assert isinstance(result["cer"], float)
