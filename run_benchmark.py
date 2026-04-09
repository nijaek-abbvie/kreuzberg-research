#!/usr/bin/env python3
"""Benchmark runner: convert all corpus documents with Kreuzberg and MarkItDown.

Usage:
    uv run python run_benchmark.py           # Convert all, skip existing outputs
    uv run python run_benchmark.py --force   # Overwrite existing outputs

Per D-13: Single-command invocation.
Per D-14: Idempotent re-runs (skip if output exists, unless --force).
Per D-15: Logs skip/convert/fail status per document.
"""

import argparse
import sys
from pathlib import Path

from benchmark.config import (
    CORPUS_DIR,
    KREUZBERG_OUTPUT_DIR,
    MARKITDOWN_BARE_OUTPUT_DIR,
    MARKITDOWN_OCR_OUTPUT_DIR,
    ensure_output_dirs,
    get_corpus_files,
)
from benchmark.extractors import (
    ExtractionOutput,
    KreuzbergExtractor,
    MarkItDownExtractor,
)


def output_path_for(doc_filename: str, output_dir: Path) -> Path:
    """Compute the .md output path for a document in a given output directory.

    Appends the original extension as a suffix before .md to avoid collisions
    between documents sharing a stem (e.g. foo.pdf and foo.xlsx both map to
    foo_pdf.md and foo_xlsx.md). Sanitizes filename by replacing spaces and
    special characters with underscores (per Pitfall 5).
    """
    p = Path(doc_filename)
    stem = p.stem
    ext = p.suffix.lstrip(".")  # e.g. "pdf", "xlsx"
    # Sanitize: replace spaces, plus signs, hash, and other special chars
    safe_stem = stem.replace(" ", "_").replace("+", "_").replace("#", "_")
    # Collapse multiple underscores
    while "__" in safe_stem:
        safe_stem = safe_stem.replace("__", "_")
    safe_stem = safe_stem.strip("_")
    return output_dir / f"{safe_stem}_{ext}.md"


def should_process(output_file: Path, force: bool) -> bool:
    """Check if a document should be processed (per D-14).

    Returns True if --force is set or the output file does not exist.
    """
    if force:
        return True
    return not output_file.exists()


def run_extraction(
    extractor: KreuzbergExtractor | MarkItDownExtractor,
    file_path: Path,
    output_file: Path,
    force: bool,
) -> str:
    """Run a single extraction and persist the output.

    Returns a status string: 'SKIP', 'OK', 'NO-KEY' (graceful skip when
    OPENAI_API_KEY is absent for OCR mode), or 'FAIL: <error>'.
    """
    if not should_process(output_file, force):
        return "SKIP"

    result: ExtractionOutput = extractor.extract(file_path)

    if result.success:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(result.content, encoding="utf-8")
        return "OK"
    elif result.error and "OPENAI_API_KEY" in result.error:
        # Graceful skip: no API key configured for OCR mode (expected in Bedrock/Azure envs)
        return f"NO-KEY: {result.error}"
    else:
        return f"FAIL: {result.error}"


def main() -> None:
    """Main entry point for the benchmark runner."""
    parser = argparse.ArgumentParser(
        description="Run Kreuzberg and MarkItDown conversions on the test corpus."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing output files (default: skip if output exists)",
    )
    args = parser.parse_args()

    # Ensure output directories exist (per D-09, D-12)
    ensure_output_dirs()

    # Load corpus manifest
    documents = get_corpus_files()
    if not documents:
        print("ERROR: No documents found in manifest. Check test_documents/manifest.json.")
        sys.exit(1)

    print(f"Corpus: {len(documents)} documents")
    print(f"Force overwrite: {args.force}")
    print("-" * 70)

    # Initialize extractors
    kreuzberg = KreuzbergExtractor()
    markitdown_bare = MarkItDownExtractor(mode="bare")
    markitdown_ocr = MarkItDownExtractor(mode="ocr")

    # Counters for summary
    stats = {"ok": 0, "skip": 0, "no_key": 0, "fail": 0}

    def _tally(status: str) -> None:
        """Increment the appropriate counter for a status string."""
        if status == "OK":
            stats["ok"] += 1
        elif status == "SKIP":
            stats["skip"] += 1
        elif status.startswith("NO-KEY"):
            stats["no_key"] += 1
        else:
            stats["fail"] += 1

    for doc in documents:
        doc_filename = doc["filename"]
        doc_path = CORPUS_DIR / doc["path"]
        needs_ocr = doc.get("needs_ocr", False)

        if not doc_path.exists():
            print(f"  MISSING: {doc_filename} (path: {doc_path})")
            stats["fail"] += 1
            continue

        print(f"\n[{doc['category']}] {doc_filename}")

        # --- Kreuzberg extraction (always, per D-11) ---
        kb_output = output_path_for(doc_filename, KREUZBERG_OUTPUT_DIR)
        status = run_extraction(kreuzberg, doc_path, kb_output, args.force)
        print(f"  kreuzberg:       {status}")
        _tally(status)

        # --- MarkItDown bare mode (always, per D-06/D-07) ---
        md_bare_output = output_path_for(doc_filename, MARKITDOWN_BARE_OUTPUT_DIR)
        status = run_extraction(markitdown_bare, doc_path, md_bare_output, args.force)
        print(f"  markitdown-bare: {status}")
        _tally(status)

        # --- MarkItDown OCR mode (only for scanned/image docs, per D-06/D-07) ---
        if needs_ocr:
            md_ocr_output = output_path_for(doc_filename, MARKITDOWN_OCR_OUTPUT_DIR)
            status = run_extraction(markitdown_ocr, doc_path, md_ocr_output, args.force)
            print(f"  markitdown-ocr:  {status}")
            _tally(status)

    # Summary
    print("\n" + "=" * 70)
    no_key_note = f", {stats['no_key']} no-key (OCR skipped)" if stats["no_key"] else ""
    print(f"DONE: {stats['ok']} converted, {stats['skip']} skipped{no_key_note}, {stats['fail']} failed")

    if stats["fail"] > 0:
        print("\nWARNING: Some extractions failed. Review errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
