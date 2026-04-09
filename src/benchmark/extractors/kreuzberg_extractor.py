"""Kreuzberg extraction wrapper -- PIPE-01.

Wraps kreuzberg.extract_file_sync with ExtractionConfig for markdown output
using Tesseract OCR backend (per D-10, D-11).
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExtractionOutput:
    """Common output from any extractor."""

    content: str  # Markdown text
    tool: str  # "kreuzberg" | "markitdown-bare" | "markitdown-ocr"
    source_file: str  # Original document filename
    success: bool  # Whether extraction succeeded
    error: str | None = None  # Error message if failed


class KreuzbergExtractor:
    """Wrapper around kreuzberg.extract_file_sync for markdown extraction.

    Uses Tesseract OCR backend (per D-10) and markdown output format (per D-11).
    Kreuzberg intelligently routes: native/searchable PDFs use text extraction
    directly (no OCR needed), while scanned PDFs and images use Tesseract OCR.
    """

    def extract(self, file_path: Path) -> ExtractionOutput:
        """Extract markdown from a document using Kreuzberg.

        Args:
            file_path: Path to the source document.

        Returns:
            ExtractionOutput with markdown content or error details.
        """
        from kreuzberg import (
            ExtractionConfig,
            KreuzbergError,
            MissingDependencyError,
            OCRError,
            OcrConfig,
            extract_file_sync,
        )

        config = ExtractionConfig(
            output_format="markdown",
            ocr=OcrConfig(backend="tesseract", language="eng"),
        )

        try:
            result = extract_file_sync(str(file_path), config=config)
            return ExtractionOutput(
                content=result.content,
                tool="kreuzberg",
                source_file=file_path.name,
                success=True,
            )
        except MissingDependencyError as e:
            return ExtractionOutput(
                content="",
                tool="kreuzberg",
                source_file=file_path.name,
                success=False,
                error=f"Missing system dependency: {e}",
            )
        except OCRError as e:
            return ExtractionOutput(
                content="",
                tool="kreuzberg",
                source_file=file_path.name,
                success=False,
                error=f"OCR failed: {e}",
            )
        except KreuzbergError as e:
            return ExtractionOutput(
                content="",
                tool="kreuzberg",
                source_file=file_path.name,
                success=False,
                error=f"Extraction failed: {e}",
            )
        except Exception as e:
            return ExtractionOutput(
                content="",
                tool="kreuzberg",
                source_file=file_path.name,
                success=False,
                error=f"Unexpected error: {type(e).__name__}: {e}",
            )
