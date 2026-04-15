#!/usr/bin/env python3
"""Evaluation runner: extract with ILIAD, compute metrics, write results CSV.

Usage:
    uv run python run_evaluation.py           # Run ILIAD extraction + scoring
    uv run python run_evaluation.py --force   # Re-extract ILIAD outputs even if they exist
    uv run python run_evaluation.py --score-only  # Skip ILIAD extraction, only score existing outputs

Per D-01: Compares Kreuzberg vs ILIAD only.
Per D-08: Kreuzberg is reference, ILIAD is hypothesis.
Per D-06: Failed extractions (empty content) score as WER=1.0, CER=1.0.

Output: results/results.csv with per-document scores for Phase 3 reporting.
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import pandas as pd

from benchmark.config import (
    CORPUS_DIR,
    ILIAD_OUTPUT_DIR,
    KREUZBERG_OUTPUT_DIR,
    RESULTS_DIR,
    RESULTS_PATH,
    ensure_output_dirs,
    get_corpus_files,
)
from benchmark.extractors import ExtractionOutput, IliadExtractor
from benchmark.metrics import compute_ocr_metrics, count_elements


def output_path_for(doc_filename: str, output_dir: Path) -> Path:
    """Compute the .md output path for a document (same convention as run_benchmark.py).

    Appends the original extension as a suffix before .md to avoid collisions.
    E.g., Sample_1_JE.pdf -> Sample_1_JE_pdf.md
    """
    p = Path(doc_filename)
    stem = p.stem.replace(" ", "_").replace("+", "_").replace("#", "_")
    while "__" in stem:
        stem = stem.replace("__", "_")
    safe_stem = stem.strip("_")
    ext = p.suffix.lstrip(".")
    return output_dir / f"{safe_stem}_{ext}.md"


def run_iliad_extraction(
    doc_path: Path, output_file: Path, extractor: IliadExtractor, force: bool
) -> tuple[bool, str]:
    """Run ILIAD extraction for a single document.

    Returns (success: bool, status: str).
    Status is one of: "OK", "SKIP", "NO-KEY: ...", "FAIL: ...".
    """
    if not force and output_file.exists():
        return True, "SKIP"

    result: ExtractionOutput = extractor.extract(doc_path)

    if result.success:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(result.content, encoding="utf-8")
        return True, "OK"
    elif result.error and ("ILIAD_API_KEY" in result.error or "ILIAD_BASE_URL" in result.error):
        return False, f"NO-KEY: {result.error}"
    else:
        return False, f"FAIL: {result.error}"


def main() -> None:
    """Main entry point for the evaluation runner."""
    parser = argparse.ArgumentParser(
        description="Run ILIAD extraction and compute evaluation metrics."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-extract ILIAD outputs even if they already exist",
    )
    parser.add_argument(
        "--score-only",
        action="store_true",
        help="Skip ILIAD extraction, only score existing outputs",
    )
    args = parser.parse_args()

    ensure_output_dirs()

    documents = get_corpus_files()
    if not documents:
        print("ERROR: No documents found in manifest.")
        sys.exit(1)

    print(f"Corpus: {len(documents)} documents")
    print(f"Force re-extract: {args.force}")
    print(f"Score only: {args.score_only}")
    print("-" * 70)

    extractor = IliadExtractor()
    rows = []
    extraction_stats = {"ok": 0, "skip": 0, "no_key": 0, "fail": 0}

    for doc in documents:
        filename = doc["filename"]
        doc_path = CORPUS_DIR / doc["path"]

        print(f"\n[{doc['category']}] {filename}")

        # --- ILIAD extraction ---
        iliad_out = output_path_for(filename, ILIAD_OUTPUT_DIR)

        if args.score_only:
            iliad_success = iliad_out.exists() and iliad_out.stat().st_size > 0
            print(f"  iliad: {'EXISTS' if iliad_success else 'MISSING'} (score-only mode)")
        else:
            iliad_success, status = run_iliad_extraction(doc_path, iliad_out, extractor, args.force)
            print(f"  iliad: {status}")
            if status == "OK":
                extraction_stats["ok"] += 1
            elif status == "SKIP":
                extraction_stats["skip"] += 1
            elif status.startswith("NO-KEY"):
                extraction_stats["no_key"] += 1
            else:
                extraction_stats["fail"] += 1

        # --- Load outputs ---
        kb_path = output_path_for(filename, KREUZBERG_OUTPUT_DIR)
        kb_text = kb_path.read_text(encoding="utf-8") if kb_path.exists() else ""
        iliad_text = iliad_out.read_text(encoding="utf-8") if iliad_out.exists() else ""

        # --- Compute metrics ---
        ocr = compute_ocr_metrics(kb_text, iliad_text)
        kb_struct = count_elements(kb_text)
        il_struct = count_elements(iliad_text)

        print(f"  WER={min(ocr['wer'], 1.0):.3f}  CER={min(ocr['cer'], 1.0):.3f}  "
              f"KB_headings={kb_struct['headings']}  IL_headings={il_struct['headings']}  "
              f"KB_tables={kb_struct['tables']}  IL_tables={il_struct['tables']}")

        rows.append({
            "document": filename,
            "category": doc["category"],
            "difficulty": doc["difficulty"],
            "needs_ocr": doc.get("needs_ocr", False),
            "kreuzberg_success": bool(kb_text),
            "iliad_success": iliad_success,
            "kreuzberg_chars": len(kb_text),
            "iliad_chars": len(iliad_text),
            "wer": min(ocr["wer"], 1.0),  # Cap at 1.0 for reporting (Pitfall 1)
            "cer": min(ocr["cer"], 1.0),
            "kreuzberg_headings": kb_struct["headings"],
            "iliad_headings": il_struct["headings"],
            "kreuzberg_tables": kb_struct["tables"],
            "iliad_tables": il_struct["tables"],
            "kreuzberg_lists": kb_struct["lists"],
            "iliad_lists": il_struct["lists"],
            "heading_delta": kb_struct["headings"] - il_struct["headings"],
            "table_delta": kb_struct["tables"] - il_struct["tables"],
            "list_delta": kb_struct["lists"] - il_struct["lists"],
        })

    # --- Write results CSV ---
    df = pd.DataFrame(rows)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(RESULTS_PATH, index=False)

    # --- Summary ---
    print("\n" + "=" * 70)
    if not args.score_only:
        no_key_note = f", {extraction_stats['no_key']} no-key" if extraction_stats["no_key"] else ""
        fail_note = f", {extraction_stats['fail']} failed" if extraction_stats["fail"] else ""
        print(f"ILIAD extraction: {extraction_stats['ok']} extracted, "
              f"{extraction_stats['skip']} skipped{no_key_note}{fail_note}")
    print(f"Results written to {RESULTS_PATH}")
    print(f"\n{df[['document', 'wer', 'cer', 'heading_delta', 'table_delta', 'list_delta']].to_string(index=False)}")


if __name__ == "__main__":
    main()
