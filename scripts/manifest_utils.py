"""Shared manifest I/O utilities for corpus management scripts."""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = PROJECT_ROOT / "test_documents"
MANIFEST_PATH = CORPUS_DIR / "manifest.json"

VALID_CATEGORIES = [
    "pdf_native",
    "pdf_scanned",
    "pdf_mixed",
    "docx",
    "xlsx",
    "pptx",
    "csv",
    "images",
]

VALID_DIFFICULTIES = ["easy", "medium", "hard"]


def load_manifest() -> dict:
    with open(MANIFEST_PATH) as f:
        return json.load(f)


def save_manifest(manifest: dict) -> None:
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")


def get_documents(manifest: dict) -> list[dict]:
    return manifest["documents"]


def add_entry(manifest: dict, entry: dict) -> None:
    """Add or replace a manifest entry by filename+category."""
    docs = manifest["documents"]
    for i, d in enumerate(docs):
        if d["filename"] == entry["filename"] and d["category"] == entry["category"]:
            docs[i] = entry
            return
    docs.append(entry)


def remove_generated_entries(manifest: dict) -> list[dict]:
    """Remove all entries with generated=True; return the removed entries."""
    docs = manifest["documents"]
    removed = [d for d in docs if d.get("generated", False)]
    manifest["documents"] = [d for d in docs if not d.get("generated", False)]
    return removed
