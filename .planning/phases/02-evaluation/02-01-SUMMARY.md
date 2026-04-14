---
phase: 02-evaluation
plan: 01
subsystem: metrics
tags: [ocr-accuracy, structural-fidelity, jiwer, markdown-it-py, unit-tests, tdd]
dependency_graph:
  requires: []
  provides: [compute_ocr_metrics, count_elements]
  affects: [run_evaluation.py, results.csv]
tech_stack:
  added: [jiwer==4.0.0, pytest>=9.0.3]
  patterns: [jiwer CER/WER normalization, markdown-it-py token counting, TDD red-green]
key_files:
  created:
    - src/benchmark/metrics/__init__.py
    - src/benchmark/metrics/ocr_accuracy.py
    - src/benchmark/metrics/structural.py
    - tests/__init__.py
    - tests/conftest.py
    - tests/test_ocr_accuracy.py
    - tests/test_structural.py
  modified:
    - pyproject.toml
    - uv.lock
decisions:
  - "Lighter normalization (no RemovePunctuation) to preserve markdown syntax in CER/WER (Pitfall 5)"
  - "Kreuzberg as WER/CER reference, ILIAD as hypothesis (D-08 direction convention)"
  - "Structural stub created during Task 2 GREEN phase to unblock __init__.py imports"
metrics:
  duration: 3 minutes
  completed: "2026-04-14T15:38:17Z"
  tasks: 3
  tests: 20
  files_created: 7
  files_modified: 2
---

# Phase 02 Plan 01: Evaluation Metrics Modules Summary

CER/WER computation via jiwer with HTML comment stripping and lightweight normalization, plus structural element counting via markdown-it-py with table extension enabled -- 20 unit tests covering D-06 failure penalty, Pitfall 3 table regression, and Pitfall 4 comment stripping.

## Task Completion

| Task | Name | Commits | Status |
|------|------|---------|--------|
| 1 | Install jiwer and pytest, create metrics package and test scaffold | 643d8f8 | Done |
| 2 | Create OCR accuracy metrics module with CER/WER (EVAL-01) | 5c518d6 (RED), 42aa6ba (GREEN) | Done |
| 3 | Create structural fidelity metrics module with element counting (EVAL-02) | 487c8ba (RED), bae864d (GREEN) | Done |

## What Was Built

### OCR Accuracy Metrics (`src/benchmark/metrics/ocr_accuracy.py`)

- `compute_ocr_metrics(kreuzberg_text, iliad_text) -> dict` with `wer` and `cer` keys
- HTML comment stripping via regex before comparison (Pitfall 4: ILIAD page markers)
- Normalization: `Compose([ToLowerCase(), RemoveMultipleSpaces(), Strip()])` -- no `RemovePunctuation` (Pitfall 5)
- D-06 failure penalty: empty hypothesis returns `{"wer": 1.0, "cer": 1.0}`
- Both-empty returns `{"wer": 0.0, "cer": 0.0}`

### Structural Fidelity Metrics (`src/benchmark/metrics/structural.py`)

- `count_elements(markdown_text) -> dict` with `headings`, `tables`, `lists`, `heading_levels` keys
- Uses `MarkdownIt().enable("table")` for table token detection (Pitfall 3)
- Counts `heading_open`, `table_open`, `bullet_list_open`, `ordered_list_open` tokens
- Tracks heading levels via `t.tag` attribute (`h1`, `h2`, `h3`)

### Test Suite (20 tests)

- `tests/test_ocr_accuracy.py`: 9 tests (identical, close match, completely different, failure penalty, both empty, HTML comments, case insensitive, whitespace normalization, return type)
- `tests/test_structural.py`: 11 tests (heading count, heading levels, table detection, table regression guard, bullet list, ordered list, mixed lists, full structure fixture, empty input, plain text, return keys)
- `tests/conftest.py`: 5 shared fixtures (structured markdown, plain markdown, reference text, close hypothesis, different hypothesis)

## Verification Results

```
uv run pytest tests/ -x -q
20 passed in 0.03s

uv run python -c "from benchmark.metrics import compute_ocr_metrics, count_elements; print('OK')"
OK
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created structural.py stub during Task 2**
- **Found during:** Task 2 GREEN phase
- **Issue:** `src/benchmark/metrics/__init__.py` imports both `compute_ocr_metrics` and `count_elements`. When running Task 2 OCR tests, the import of `__init__.py` failed because `structural.py` did not exist yet.
- **Fix:** Created a minimal stub `structural.py` with `raise NotImplementedError` to allow `__init__.py` to import. Full implementation replaced the stub in Task 3.
- **Files modified:** `src/benchmark/metrics/structural.py`
- **Commit:** 42aa6ba (included with OCR implementation commit)

## Decisions Made

1. **No RemovePunctuation in normalization** -- jiwer's `RemovePunctuation` uses `string.punctuation` which strips `|`, `#`, `-`, `*` (all markdown syntax). Using lighter normalization (lowercase + whitespace collapse) preserves meaningful content differences.
2. **Kreuzberg as reference direction** -- `compute_ocr_metrics(kreuzberg_text, iliad_text)` treats Kreuzberg as reference and ILIAD as hypothesis, measuring ILIAD completeness relative to Kreuzberg output.
3. **Structural stub for import unblocking** -- Created a stub `structural.py` during Task 2 to unblock `__init__.py` imports; replaced with full implementation in Task 3. This is a standard TDD accommodation when a package `__init__.py` imports all submodules.

## Self-Check: PASSED

All 7 created files verified on disk. All 5 commit hashes (643d8f8, 5c518d6, 42aa6ba, 487c8ba, bae864d) verified in git log.
