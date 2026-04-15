"""Project paths and constants for the Kreuzberg benchmark."""

import json
from pathlib import Path

# Project root (two levels up from this file: src/benchmark/config.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Corpus directory
CORPUS_DIR = PROJECT_ROOT / "test_documents"
MANIFEST_PATH = CORPUS_DIR / "manifest.json"

# Output directories (per D-09, D-12)
OUTPUT_DIR = PROJECT_ROOT / "output"
KREUZBERG_OUTPUT_DIR = OUTPUT_DIR / "kreuzberg"
MARKITDOWN_BARE_OUTPUT_DIR = OUTPUT_DIR / "markitdown" / "bare"
MARKITDOWN_OCR_OUTPUT_DIR = OUTPUT_DIR / "markitdown" / "ocr"
ILIAD_OUTPUT_DIR = OUTPUT_DIR / "iliad"

# Results directory for evaluation output (Phase 2 -> Phase 3 contract)
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_PATH = RESULTS_DIR / "results.csv"

# Format categories (per D-04; csv and pdf_mixed added for corpus expansion)
FORMAT_CATEGORIES = [
    "pdf_native",
    "pdf_scanned",
    "pdf_mixed",
    "docx",
    "xlsx",
    "pptx",
    "csv",
    "images",
]

# MarkItDown OCR plugin config (per D-08)
MARKITDOWN_OCR_MODEL = "gpt-4o-2024-11-20"


def load_manifest() -> dict:
    """Load the corpus manifest from test_documents/manifest.json."""
    with open(MANIFEST_PATH) as f:
        return json.load(f)


def get_corpus_files() -> list[dict]:
    """Return list of document entries from manifest."""
    manifest = load_manifest()
    return manifest["documents"]


def ensure_output_dirs() -> None:
    """Create output directories if they don't exist."""
    for d in [
        KREUZBERG_OUTPUT_DIR,
        MARKITDOWN_BARE_OUTPUT_DIR,
        MARKITDOWN_OCR_OUTPUT_DIR,
        ILIAD_OUTPUT_DIR,
        RESULTS_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)
