# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a benchmark study evaluating the [Kreuzberg](https://github.com/Goldziher/kreuzberg) document processing framework as a potential replacement for Microsoft MarkItDown in an internal GenAI API's document-to-markdown ingestion layer. The comparison baseline is **ILIAD** — the internal production API that wraps MarkItDown. See [`.planning/PROJECT.md`](.planning/PROJECT.md) for the full charter, constraints, and key decisions.

## Quick Reference

Package manager: **uv**

```bash
uv sync                          # Install dependencies
uv run pytest                    # Run all tests
uv run pytest tests/test_ocr_accuracy.py::test_identical_texts  # Single test
uv run python run_benchmark.py   # Phase 1: run Kreuzberg + MarkItDown extraction
uv run python run_benchmark.py --force   # Re-run extraction even if outputs exist
uv run python run_evaluation.py  # Phase 2: run ILIAD extraction + score vs Kreuzberg
uv run python run_evaluation.py --score-only  # Re-score without re-running ILIAD
uv run python run_report.py      # Phase 3: generate BENCHMARK_REPORT.md from results
uv run python run_report.py --force  # Re-generate even if BENCHMARK_REPORT.md exists
```

### Corpus Management

```bash
uv run python scripts/generate_test_corpus.py                        # Generate all 41 synthetic test files
uv run python scripts/generate_test_corpus.py --category pdf_native  # Generate one category only
uv run python scripts/generate_test_corpus.py --dry-run              # Preview without writing files
uv run python scripts/generate_test_corpus.py --clean                # Remove old generated entries first
uv run python scripts/manage_manifest.py scan                        # Find unregistered files
uv run python scripts/manage_manifest.py validate                    # Verify manifest integrity
uv run python scripts/manage_manifest.py stats                       # Print corpus summary by category
uv run python scripts/manage_manifest.py add <filepath>              # Add a file interactively
```

Internal documents (not committed to git) live in `test_documents/internal/` and have `"committed": false` in the manifest. Curated public documents go in `test_documents/{category}/`; register with `manage_manifest.py add`.

## Codebase Documentation

Detailed codebase reference lives in [`.planning/codebase/`](.planning/codebase/):

| Topic | Reference |
|---|---|
| Architecture & data flow | [`ARCHITECTURE.md`](.planning/codebase/ARCHITECTURE.md) |
| Directory layout & file map | [`STRUCTURE.md`](.planning/codebase/STRUCTURE.md) |
| Stack, dependencies, env setup | [`STACK.md`](.planning/codebase/STACK.md) |
| Naming, types, commit style | [`CONVENTIONS.md`](.planning/codebase/CONVENTIONS.md) |
| ILIAD API, Kreuzberg config, SDKs | [`INTEGRATIONS.md`](.planning/codebase/INTEGRATIONS.md) |
| Test patterns & fixtures | [`TESTING.md`](.planning/codebase/TESTING.md) |

## Project Planning

All planning artifacts live in [`.planning/`](.planning/):

| File | Purpose |
|---|---|
| [`STATE.md`](.planning/STATE.md) | Current phase, progress, and accumulated decisions |
| [`ROADMAP.md`](.planning/ROADMAP.md) | Three-phase plan and milestone tracking |
| [`REQUIREMENTS.md`](.planning/REQUIREMENTS.md) | Formal requirement IDs and phase mapping |
| [`research/`](.planning/research/) | Pre-implementation research synthesis |
| [`phases/`](.planning/phases/) | Per-phase context, plans, and summaries |

## Post-Execution Behavior

After a plan is **approved and executed**, review this CLAUDE.md file and update it if the executed changes affect any of the following:

- New or modified CLI commands (Quick Reference section)
- New documentation files or planning artifacts (Codebase Documentation / Project Planning tables)
- Changes to project overview, scope, or baseline comparisons
- New integrations, dependencies, or environment setup requirements
