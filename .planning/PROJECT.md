# Kreuzberg Research

## What This Is

A benchmark study evaluating the Kreuzberg document processing framework as a replacement for Microsoft's MarkItDown (and supporting libraries) in the file-to-markdown ingestion layer of our internal company GenAI API. The deliverable is a side-by-side comparison report covering markdown fidelity and OCR accuracy across priority file types.

## Core Value

Determine whether Kreuzberg produces higher-fidelity, structure-preserving markdown from PDFs, scanned documents, images, and Office files than the current MarkItDown-based pipeline — with a specific focus on scanned PDF extraction where MarkItDown currently fails.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Benchmark Kreuzberg vs MarkItDown on markdown fidelity (tables, headers, lists preservation)
- [ ] Benchmark Kreuzberg vs MarkItDown on OCR accuracy for scanned documents
- [ ] Test against the known-failure scanned PDF (text not extracted, only one image captured)
- [ ] Evaluate format coverage across PDFs (native + scanned), Office docs (Word, Excel, PowerPoint), and images
- [ ] Document Kreuzberg's Python integration path (native bindings available)
- [ ] Produce a benchmark report with go/no-go recommendation

### Out of Scope

- Production integration — this is research/evaluation only, integration comes later if Kreuzberg passes
- Code file parsing — not a priority for the GenAI ingestion layer
- Performance/throughput benchmarking — medium volume (~hundreds/day) means performance is secondary to quality
- MarkItDown replacement implementation — out of scope until benchmark results justify it

## Context

**Current ingestion pipeline:** Uses Microsoft's MarkItDown as the primary file-to-markdown converter, supplemented by additional per-format libraries. Scanned/image-heavy documents use LLM-based image captioning as a fallback.

**Motivating failure:** A scanned PDF document where MarkItDown extracted only one image (handled via LLM captioning) but completely missed the rest of the document's text content. This is the primary test case.

**Kreuzberg framework:** Open-source polyglot document processing library (Rust core, Python bindings). Supports 91+ formats with multiple OCR backends (Tesseract, PaddleOCR, EasyOCR). Designed for AI pipelines with TOON output format (~30-50% fewer tokens than JSON). Available as library, CLI, REST API, or MCP server.

**GenAI API stack:** Python-based internal API. Medium document volume (hundreds per day). Structure-preserving markdown is critical — tables, headers, and lists must survive conversion faithfully for downstream LLM consumption.

## Constraints

- **Tech stack**: Python — Kreuzberg must integrate via its native Python bindings
- **Quality bar**: Markdown output must preserve document structure (tables, headers, lists) — plain text extraction is insufficient
- **Test data**: User has representative sample documents including the known-failure scanned PDF
- **Scope**: Research/benchmarking only — no production deployment in this project

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Kreuzberg as evaluation target | Unified framework covering 91+ formats with OCR, vs current multi-library approach | — Pending |
| Markdown fidelity + OCR accuracy as primary metrics | These are the current pain points with MarkItDown | — Pending |
| Research-first approach | Need evidence before committing to a production migration | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-02 after initialization*
