---
phase: 02-evaluation
plan: 03
subsystem: evaluation-runner
tags: [evaluation, iliad, metrics, csv, pipeline, score-only]
dependency_graph:
  requires: [02-01, 02-02]
  provides: [run_evaluation.py, results/results.csv]
  affects: [phase-03-reporting]
tech_stack:
  added: []
  patterns: [argparse-cli, pandas-csv-output, idempotent-extraction, score-only-mode]
key_files:
  created:
    - run_evaluation.py
    - tests/test_evaluation_output.py
  modified:
    - .gitignore
decisions:
  - "WER/CER capped at 1.0 for reporting (Pitfall 1: raw jiwer values can exceed 1.0 with insertions)"
  - "output_path_for duplicated from run_benchmark.py to keep evaluation script self-contained"
  - "results/ added to .gitignore since CSV is generated output regenerated on each evaluation run"
metrics:
  duration: 2m 21s
  completed: "2026-04-14T15:46:39Z"
  tasks: 1/1 auto tasks completed (Task 2 is checkpoint:human-verify)
  tests: 25 (20 unit + 5 smoke)
  files_created: 2
  files_modified: 1
---

# Phase 02 Plan 03: Evaluation Runner Summary

Evaluation orchestration script with --score-only and --force flags, computing CER/WER and structural element deltas for 7 corpus documents (Kreuzberg=ref, ILIAD=hyp), writing 19-column results.csv for Phase 3 consumption.

## Task Completion

| Task | Name | Commits | Status |
|------|------|---------|--------|
| 1 | Create run_evaluation.py and smoke test | 65664c8, 4457b0a | Done |
| 2 | Run evaluation and verify results | -- | Checkpoint: awaiting human verification |

## What Was Built

### Evaluation Runner (`run_evaluation.py`)

- `main()` entry point with argparse: `--force` (re-extract), `--score-only` (skip ILIAD extraction)
- `output_path_for(doc_filename, output_dir)` -- same filename convention as `run_benchmark.py`
- `run_iliad_extraction(doc_path, output_file, extractor, force)` -- returns `(success, status)` tuple
- Iterates all 7 corpus documents from manifest, computing per-document:
  - ILIAD extraction (or skip in score-only mode)
  - CER/WER via `compute_ocr_metrics(kb_text, iliad_text)`
  - Structural counts via `count_elements()` for both Kreuzberg and ILIAD
  - Delta computation (kreuzberg - iliad) for headings, tables, lists
- WER/CER capped at 1.0 via `min()` (Pitfall 1)
- Writes `results/results.csv` with 19 columns matching RESEARCH.md schema
- Console summary with extraction stats and per-document score table

### Results CSV Schema (19 columns)

`document, category, difficulty, needs_ocr, kreuzberg_success, iliad_success, kreuzberg_chars, iliad_chars, wer, cer, kreuzberg_headings, iliad_headings, kreuzberg_tables, iliad_tables, kreuzberg_lists, iliad_lists, heading_delta, table_delta, list_delta`

### Smoke Tests (`tests/test_evaluation_output.py`)

- `test_results_csv_exists` -- results.csv must exist after evaluation
- `test_results_csv_has_7_rows` -- one row per corpus document
- `test_results_csv_has_correct_columns` -- all 19 expected columns present
- `test_results_csv_wer_cer_bounded` -- WER/CER in [0.0, 1.0] range
- `test_results_csv_known_failure_case` -- Sample_1_JE.pdf row present

## Verification Results

```
uv run python run_evaluation.py --help
# Exits 0 with correct usage text

uv run python run_evaluation.py --score-only
# Processes all 7 documents, writes results.csv (7 rows, 19 cols)
# All WER/CER = 0.0 (both-empty case since no Kreuzberg/ILIAD outputs in worktree)

uv run pytest tests/ -v
# 25 passed in 0.24s (20 unit + 5 smoke)
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing] Added results/ to .gitignore**
- **Found during:** Task 1 post-verification
- **Issue:** `results/` directory (containing generated `results.csv`) was not in `.gitignore`, meaning generated output would be accidentally committed
- **Fix:** Added `results/` to `.gitignore` alongside existing `output/` entry
- **Files modified:** `.gitignore`
- **Commit:** 4457b0a

## Checkpoint Status

Task 2 is a `checkpoint:human-verify` gate. The executor has:
1. Verified `--score-only` mode works end-to-end (7 rows, 19 columns in CSV)
2. Verified all 25 tests pass (unit + smoke)
3. Confirmed `--help` exits 0

Awaiting human to:
1. Set `ILIAD_API_KEY` and `ILIAD_BASE_URL` environment variables
2. Run `uv run python run_evaluation.py` for full ILIAD extraction
3. Verify `output/iliad/` contains 7 markdown files
4. Verify `results/results.csv` has meaningful WER/CER scores
5. Run `uv run pytest tests/ -v` to confirm all tests pass with real data

## Known Stubs

None -- all functionality is fully wired. ILIAD API calls will execute when environment variables are set.

## Self-Check: PASSED

All 2 created files verified on disk. Both commit hashes (65664c8, 4457b0a) verified in git log. results/results.csv generated with 7 rows and 19 columns.
