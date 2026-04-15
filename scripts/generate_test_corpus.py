#!/usr/bin/env python3
"""Generate synthetic test corpus documents for the Kreuzberg benchmark.

Usage:
    uv run python scripts/generate_test_corpus.py                       # Generate all
    uv run python scripts/generate_test_corpus.py --category pdf_native  # One category
    uv run python scripts/generate_test_corpus.py --dry-run              # Preview only
"""

import argparse
import sys
from pathlib import Path

# Ensure scripts/ is on the path so generators/ imports work
sys.path.insert(0, str(Path(__file__).resolve().parent))

from manifest_utils import (
    CORPUS_DIR,
    MANIFEST_PATH,
    add_entry,
    load_manifest,
    remove_generated_entries,
    save_manifest,
)
from generators.csv_generator import CsvGenerator
from generators.docx_generator import DocxGenerator
from generators.image_generator import ImageGenerator
from generators.pdf_generator import PdfGenerator, PdfMixedGenerator, PdfScannedGenerator
from generators.pptx_generator import PptxGenerator
from generators.xlsx_generator import XlsxGenerator

ALL_GENERATORS = [
    PdfGenerator,
    PdfScannedGenerator,
    PdfMixedGenerator,
    DocxGenerator,
    XlsxGenerator,
    PptxGenerator,
    CsvGenerator,
    ImageGenerator,
]

CATEGORY_MAP = {g(CORPUS_DIR).category: g for g in ALL_GENERATORS}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic test corpus files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--category",
        choices=list(CATEGORY_MAP.keys()),
        help="Generate only a specific category (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be created without writing files or updating manifest",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove all previously generated entries from manifest before regenerating",
    )
    args = parser.parse_args()

    manifest = load_manifest()

    if args.clean and not args.dry_run:
        removed = remove_generated_entries(manifest)
        if removed:
            print(f"Removed {len(removed)} previously generated manifest entries.")

    generators_to_run = (
        [CATEGORY_MAP[args.category]] if args.category else list(CATEGORY_MAP.values())
    )

    total_entries = 0
    total_errors = 0

    for gen_cls in generators_to_run:
        gen = gen_cls(CORPUS_DIR)
        print(f"\n[{gen.category}] Generating...")
        try:
            entries = gen.generate(dry_run=args.dry_run)
            for entry in entries:
                if not args.dry_run:
                    add_entry(manifest, entry)
                print(f"  {'[dry-run] ' if args.dry_run else ''}OK  {entry['filename']}")
            total_entries += len(entries)
        except ImportError as e:
            print(f"  SKIP: {e}")
        except Exception as e:
            print(f"  ERROR: {e}")
            total_errors += 1

    if not args.dry_run:
        save_manifest(manifest)
        print(f"\nManifest updated: {MANIFEST_PATH}")

    print(f"\nDone: {total_entries} files {'would be ' if args.dry_run else ''}generated, {total_errors} errors.")
    if total_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
