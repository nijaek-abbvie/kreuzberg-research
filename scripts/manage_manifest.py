#!/usr/bin/env python3
"""Corpus manifest management CLI.

Usage:
    uv run python scripts/manage_manifest.py scan            # Find unregistered files
    uv run python scripts/manage_manifest.py validate        # Verify manifest integrity
    uv run python scripts/manage_manifest.py stats           # Print corpus summary
    uv run python scripts/manage_manifest.py add <filepath>  # Add a file interactively
"""

import argparse
import sys
from pathlib import Path

from manifest_utils import (
    CORPUS_DIR,
    VALID_CATEGORIES,
    VALID_DIFFICULTIES,
    add_entry,
    get_documents,
    load_manifest,
    save_manifest,
)

# Files to ignore when scanning
_IGNORE = {".gitkeep", "manifest.json", ".DS_Store"}
# Directories to skip entirely
_SKIP_DIRS = {"internal"}


def cmd_scan(args: argparse.Namespace) -> int:
    """Find files in test_documents/ not yet registered in the manifest."""
    manifest = load_manifest()
    registered = {d["path"] for d in get_documents(manifest)}

    unregistered = []
    for f in sorted(CORPUS_DIR.rglob("*")):
        if not f.is_file():
            continue
        if f.name in _IGNORE:
            continue
        # Skip internal/ — those are managed separately
        rel = f.relative_to(CORPUS_DIR)
        if rel.parts[0] in _SKIP_DIRS:
            continue
        rel_str = str(rel)
        if rel_str not in registered:
            unregistered.append(rel_str)

    if not unregistered:
        print("All files are registered in the manifest.")
        return 0

    print(f"Found {len(unregistered)} unregistered file(s):")
    for p in unregistered:
        print(f"  {p}")
    print("\nRun `manage_manifest.py add <filepath>` to register each file.")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check manifest integrity: files exist, categories valid, no duplicates."""
    manifest = load_manifest()
    docs = get_documents(manifest)
    errors = []
    seen = set()

    for d in docs:
        key = (d.get("filename"), d.get("category"))

        # Duplicate check
        if key in seen:
            errors.append(f"Duplicate entry: {key}")
        seen.add(key)

        # Category check
        cat = d.get("category")
        if cat not in VALID_CATEGORIES:
            errors.append(f"{d.get('filename')}: unknown category '{cat}'")

        # Difficulty check
        diff = d.get("difficulty")
        if diff not in VALID_DIFFICULTIES:
            errors.append(f"{d.get('filename')}: unknown difficulty '{diff}'")

        # File existence check (only for committed files)
        if d.get("committed", True):
            fpath = CORPUS_DIR / d["path"]
            if not fpath.exists():
                errors.append(f"{d.get('filename')}: committed=true but file missing at {fpath}")

        # Required fields
        for field in ("filename", "category", "path", "difficulty", "needs_ocr"):
            if field not in d:
                errors.append(f"{d.get('filename', '?')}: missing required field '{field}'")

    if errors:
        print(f"Validation FAILED — {len(errors)} error(s):")
        for e in errors:
            print(f"  {e}")
        return 1

    print(f"Validation PASSED — {len(docs)} entries, no issues found.")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """Print a summary of the corpus by category, difficulty, and source."""
    manifest = load_manifest()
    docs = get_documents(manifest)

    committed = [d for d in docs if d.get("committed", True)]
    internal = [d for d in docs if not d.get("committed", True)]
    synthetic = [d for d in docs if d.get("generated", False)]
    curated = [d for d in docs if not d.get("generated", False)]

    present = [d for d in docs if (CORPUS_DIR / d["path"]).exists()]

    print(f"Corpus Statistics")
    print(f"  Total entries:    {len(docs)}")
    print(f"  Files on disk:    {len(present)}")
    print(f"  Committed to git: {len(committed)}   Internal (local-only): {len(internal)}")
    print(f"  Synthetic:        {len(synthetic)}   Curated/manual: {len(curated)}")
    print()

    # By category
    print("  By category:")
    for cat in VALID_CATEGORIES:
        cat_docs = [d for d in docs if d["category"] == cat]
        if not cat_docs:
            continue
        easy = sum(1 for d in cat_docs if d.get("difficulty") == "easy")
        med = sum(1 for d in cat_docs if d.get("difficulty") == "medium")
        hard = sum(1 for d in cat_docs if d.get("difficulty") == "hard")
        print(f"    {cat:<14} {len(cat_docs):>3} total  ({easy}e / {med}m / {hard}h)")

    return 0


def cmd_add(args: argparse.Namespace) -> int:
    """Interactively add a single file to the manifest."""
    filepath = Path(args.filepath)
    if not filepath.exists():
        print(f"ERROR: File not found: {filepath}")
        return 1

    # Determine path relative to CORPUS_DIR
    try:
        rel = filepath.resolve().relative_to(CORPUS_DIR.resolve())
    except ValueError:
        print(f"ERROR: File must be inside {CORPUS_DIR}")
        return 1

    rel_str = str(rel)

    # Infer category from directory
    inferred_cat = rel.parts[0] if len(rel.parts) > 1 else None
    if inferred_cat not in VALID_CATEGORIES:
        inferred_cat = None

    print(f"Adding: {rel_str}")
    print()

    # Category
    if inferred_cat:
        cat_input = input(f"Category [{inferred_cat}]: ").strip() or inferred_cat
    else:
        cat_input = input(f"Category ({', '.join(VALID_CATEGORIES)}): ").strip()
    if cat_input not in VALID_CATEGORIES:
        print(f"ERROR: '{cat_input}' is not a valid category.")
        return 1

    # Difficulty
    diff_input = input("Difficulty (easy/medium/hard): ").strip().lower()
    if diff_input not in VALID_DIFFICULTIES:
        print(f"ERROR: '{diff_input}' is not a valid difficulty.")
        return 1

    # needs_ocr
    ocr_input = input("Needs OCR? (y/n): ").strip().lower()
    needs_ocr = ocr_input in ("y", "yes")

    # committed
    committed_input = input("Committed to git? (y/n): ").strip().lower()
    committed = committed_input in ("y", "yes")

    # source
    source = input("Source (e.g. 'Public - ArXiv' or 'Internal sample'): ").strip()

    # characteristics
    chars_raw = input("Characteristics (comma-separated tags, or blank): ").strip()
    characteristics = [c.strip() for c in chars_raw.split(",") if c.strip()] if chars_raw else []

    # notes
    notes = input("Notes (optional): ").strip()

    entry = {
        "filename": filepath.name,
        "category": cat_input,
        "path": rel_str,
        "difficulty": diff_input,
        "characteristics": characteristics,
        "source": source,
        "needs_ocr": needs_ocr,
        "notes": notes,
        "committed": committed,
        "generated": False,
    }

    manifest = load_manifest()
    add_entry(manifest, entry)
    save_manifest(manifest)
    print(f"\nAdded '{filepath.name}' to manifest.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manage the test corpus manifest.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("scan", help="Find files not yet in the manifest")
    sub.add_parser("validate", help="Verify manifest integrity")
    sub.add_parser("stats", help="Print corpus summary")
    add_p = sub.add_parser("add", help="Add a file to the manifest interactively")
    add_p.add_argument("filepath", help="Path to the file to add")

    args = parser.parse_args()
    dispatch = {
        "scan": cmd_scan,
        "validate": cmd_validate,
        "stats": cmd_stats,
        "add": cmd_add,
    }
    sys.exit(dispatch[args.command](args))


if __name__ == "__main__":
    main()
