---
phase: 02-evaluation
plan: 02
subsystem: extractors
tags: [iliad, api-wrapper, httpx, extraction]
dependency_graph:
  requires: [01-02]
  provides: [IliadExtractor, ILIAD_OUTPUT_DIR, RESULTS_DIR, RESULTS_PATH]
  affects: [02-03]
tech_stack:
  added: [httpx]
  patterns: [env-var-auth, multipart-upload, graceful-failure]
key_files:
  created:
    - src/benchmark/extractors/iliad_extractor.py
  modified:
    - src/benchmark/config.py
    - src/benchmark/extractors/__init__.py
decisions:
  - "httpx with 120s timeout for ILIAD API calls (Pitfall 2)"
  - "Error response body truncated to 200 chars to prevent info leakage (T-02-03)"
  - "Separate handlers for HTTPStatusError and TimeoutException for descriptive errors"
metrics:
  duration: 2m 5s
  completed: "2026-04-14T15:37:12Z"
  tasks: 2/2
  files_changed: 3
---

# Phase 02 Plan 02: IliadExtractor Wrapper Summary

ILIAD API extraction wrapper with 120s httpx timeout, env-var auth (ILIAD_API_KEY/ILIAD_BASE_URL), multipart file upload to /api/v1/recognize/markdown, and graceful failure when credentials missing.

## What Was Done

### Task 1: Update config.py with ILIAD output directory and results path constants
**Commit:** `ae885f7`

Added three new constants to `src/benchmark/config.py`:
- `ILIAD_OUTPUT_DIR = OUTPUT_DIR / "iliad"` -- output directory for ILIAD extraction results
- `RESULTS_DIR = PROJECT_ROOT / "results"` -- results directory for evaluation output
- `RESULTS_PATH = RESULTS_DIR / "results.csv"` -- Phase 2 to Phase 3 contract path

Updated `ensure_output_dirs()` to create both `ILIAD_OUTPUT_DIR` and `RESULTS_DIR` alongside existing output directories.

### Task 2: Create IliadExtractor wrapper and update extractors __init__.py
**Commit:** `0f33651`

Created `src/benchmark/extractors/iliad_extractor.py` implementing the IliadExtractor class:
- Posts documents to `/api/v1/recognize/markdown` endpoint (D-02)
- Reads `ILIAD_API_KEY` and `ILIAD_BASE_URL` from environment variables (D-04)
- Sends API key in `X-API-Key` header over HTTPS (D-04)
- Does NOT set the classic flag -- uses default mode (D-03)
- Uses `httpx.Client(timeout=120.0)` to handle large documents (Pitfall 2)
- Returns `ExtractionOutput(success=False)` with clear error when env vars missing
- Truncates error response body to 200 chars to prevent sensitive info leakage (T-02-03)
- Separate exception handlers for `HTTPStatusError`, `TimeoutException`, and generic exceptions

Updated `src/benchmark/extractors/__init__.py` to export `IliadExtractor` in `__all__`.

## Verification Results

All verification checks passed:
- `from benchmark.extractors import IliadExtractor` -- imports successfully
- `from benchmark.config import ILIAD_OUTPUT_DIR, RESULTS_DIR, RESULTS_PATH` -- imports successfully
- `ensure_output_dirs()` creates iliad and results directories
- Graceful failure when `ILIAD_API_KEY` not set: `success=False`, error contains "ILIAD_API_KEY"
- No `classic` flag in request code (D-03 compliance confirmed)
- `httpx.Client(timeout=120.0)` present (Pitfall 2 compliance confirmed)

## Deviations from Plan

None -- plan executed exactly as written.

## Threat Mitigations Applied

| Threat ID | Mitigation | Status |
|-----------|-----------|--------|
| T-02-03 | API key read from env var only, never hardcoded; error messages truncate response body to 200 chars | Applied |
| T-02-04 | API key passed in X-API-Key header (HTTPS assumed via base URL); key never in URL query string or body | Applied |
| T-02-07 | 120s timeout on httpx.Client; TimeoutException caught with descriptive error | Applied |

## Known Stubs

None -- all functionality is fully wired. ILIAD API calls will work when `ILIAD_API_KEY` and `ILIAD_BASE_URL` environment variables are set.

## Self-Check: PASSED

All 3 created/modified files verified on disk. Both task commits (ae885f7, 0f33651) verified in git log.
