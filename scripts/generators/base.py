"""Base class for all synthetic document generators."""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseGenerator(ABC):
    """Abstract base for format-specific generators.

    Each subclass implements generate() and returns a list of manifest entry
    dicts ready to be merged into manifest.json.
    """

    def __init__(self, corpus_dir: Path) -> None:
        self.corpus_dir = corpus_dir

    @property
    @abstractmethod
    def category(self) -> str:
        """The FORMAT_CATEGORIES key this generator targets."""

    @abstractmethod
    def generate(self, dry_run: bool = False) -> list[dict]:
        """Generate all files for this category.

        Returns a list of manifest entry dicts (one per generated file).
        If dry_run=True, prints what would be created without writing files.
        """

    def output_dir(self) -> Path:
        return self.corpus_dir / self.category

    def _entry(
        self,
        filename: str,
        difficulty: str,
        characteristics: list[str],
        needs_ocr: bool,
        notes: str,
    ) -> dict:
        """Build a manifest entry dict for a generated file."""
        return {
            "filename": filename,
            "category": self.category,
            "path": f"{self.category}/{filename}",
            "difficulty": difficulty,
            "characteristics": characteristics,
            "source": "synthetic",
            "needs_ocr": needs_ocr,
            "notes": notes,
            "committed": True,
            "generated": True,
        }
