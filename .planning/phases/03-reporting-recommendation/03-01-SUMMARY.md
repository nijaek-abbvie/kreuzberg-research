---
phase: 03-reporting-recommendation
plan: "01"
subsystem: reporting
tags: [report-generation, benchmark, pandas, markdown]
dependency_graph:
  requires:
    - results/results.csv (written by Phase 2)
    - output/kreuzberg/ (written by Phase 1)
    - output/iliad/ (written by Phase 2)
  provides:
    - run_report.py (report generation script)
    - BENCHMARK_REPORT.md (generated benchmark report)
    - tests/test_report_output.py (automated report validation)
  affects:
    - BENCHMARK_REPORT.md (repo root deliverable)
tech_stack:
  added: []
  patterns:
    - pandas groupby aggregation for per-format summary statistics
    - GFM markdown table construction via f-string/join (no external library)
    - module-scoped pytest fixture for report text (avoids repeated file reads)
    - idempotency guard with --force flag matching established runner pattern
key_files:
  created:
    - run_report.py
    - BENCHMARK_REPORT.md
    - tests/test_report_output.py
  modified: []
decisions:
  - "Used symlinks (output/, results/) in worktree to access Phase 1-2 artifacts from main repo"
  - "Report sections ordered: executive summary, methodology, corpus, results by format, known-failure, native PDF trade-off, recommendation, appendix"
  - "Structural delta aggregation uses sum (not mean) to surface extreme cases like the 90-heading Audit Plan"
metrics:
  duration_minutes: 11
  completed_date: "2026-04-15"
  tasks_completed: 2
  tasks_total: 2
  files_created: 3
  files_modified: 0
---

# Phase 3 Plan 1: Report Generation Summary

**One-liner:** Script-generated benchmark report with qualified GO recommendation, scanned PDF failure analysis, and per-format breakdown using pandas groupby over results.csv.

## What Was Built

### Task 1: Test scaffold (tests/test_report_output.py)

Five pytest tests covering REPT-01 and REPT-02:
- `test_report_exists` — file existence check
- `test_report_has_known_failure_section` — asserts `Sample_1_JE` present
- `test_report_char_counts_present` — asserts `619` and `3158` present
- `test_report_has_recommendation` — asserts `Recommendation` present
- `test_report_minimum_length` — asserts report > 2000 characters

Module-scoped `report_text` fixture reads BENCHMARK_REPORT.md once. No pandas, no config imports per the analog pattern from `test_evaluation_output.py`.

### Task 2: run_report.py and BENCHMARK_REPORT.md

`run_report.py` (290 lines) follows the established `run_*.py` runner pattern:
- `extract_snippet(md_path, n_lines=10)` — first N non-blank lines, gracefully returns placeholder if file missing
- `markdown_table(headers, rows)` — GFM table builder, no external dependencies
- `build_executive_summary`, `build_methodology_section`, `build_corpus_section` — opening sections
- `build_results_section` — pandas groupby aggregation sorted alphabetically by category
- `build_known_failure_section` — REPT-01: Sample_1_JE.pdf analysis with both tool excerpts and char counts
- `build_native_pdf_section` — heading vs table trade-off for native PDFs
- `build_recommendation_section` — REPT-02: qualified GO with 5 per-format verdicts
- `build_appendix` — all 7 results rows as GFM table
- `assemble_report` — joins sections with `\n\n`
- `main()` — argparse with `--force`, idempotency guard, reads RESULTS_PATH, writes BENCHMARK_REPORT.md

`BENCHMARK_REPORT.md` (7363 characters):
- Contains dedicated `Sample_1_JE.pdf` section with both tool excerpts (REPT-01)
- Contains character counts 619 (ILIAD) and 3158 (Kreuzberg) per D-07
- Contains qualified GO recommendation with scanned/native/DOCX/Excel/PPTX/images breakdown (REPT-02, D-09, D-10)
- Contains `Begin migration planning` next step per D-12
- Contains `90 headings` and `9 tables` native PDF trade-off per D-11
- Self-contained: all claims substantiated with inline numbers per D-08

## Verification Results

```
$ uv run pytest
30 passed in 1.11s
```

All 30 tests pass:
- 5 new report output tests (test_report_output.py)
- 5 evaluation output tests (test_evaluation_output.py)
- 9 OCR accuracy tests (test_ocr_accuracy.py)
- 11 structural tests (test_structural.py)

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | 65d29c5 | test(03-01): add test scaffold for report output validation |
| Task 2 | 62c8756 | feat(03-01): create run_report.py and generate BENCHMARK_REPORT.md |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Worktree lacks Phase 1-2 data artifacts**

- **Found during:** Task 2 (script execution)
- **Issue:** The git worktree only contains source code tracked in the repo. `results/results.csv` and `output/` directories are gitignored and only present in the main repo working tree. `run_report.py` via `benchmark.config` resolved PROJECT_ROOT to the worktree path, causing `RESULTS_PATH` not found error.
- **Fix:** Created symlinks `results -> main_repo/results` and `output -> main_repo/output` in the worktree to provide access to Phase 1-2 artifacts without duplicating data.
- **Files modified:** (symlinks only, not tracked in git)

## Known Stubs

None. The generated report contains real data from results.csv and actual output file excerpts.

## Threat Flags

No new network endpoints, auth paths, or trust boundaries introduced. Phase 3 is entirely local file I/O as documented in the threat model.

## Self-Check: PASSED

- [x] `run_report.py` exists and has valid Python syntax
- [x] `tests/test_report_output.py` exists and has valid Python syntax
- [x] `BENCHMARK_REPORT.md` exists at repo root (7363 chars > 2000 minimum)
- [x] Commit `65d29c5` exists (Task 1)
- [x] Commit `62c8756` exists (Task 2)
- [x] All 30 tests pass
- [x] BENCHMARK_REPORT.md contains `Sample_1_JE` (REPT-01)
- [x] BENCHMARK_REPORT.md contains `619` and `3158` (D-07)
- [x] BENCHMARK_REPORT.md contains `Recommendation` and `Qualified GO` (REPT-02, D-09)
- [x] BENCHMARK_REPORT.md contains `Begin migration planning` (D-12)
- [x] BENCHMARK_REPORT.md contains `90 headings` and `9 tables` (D-11)
