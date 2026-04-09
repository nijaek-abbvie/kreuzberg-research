"""MarkItDown extraction wrapper -- PIPE-02.

Wraps markitdown.MarkItDown with two modes:
- bare: No OCR plugin, reproduces original production failure (per D-06 mode 1)
- ocr: LLM Vision via markitdown-ocr plugin with GPT-4o (per D-06 mode 2, D-08)

Per D-07, non-scanned documents only need bare mode (OCR is irrelevant).
"""

import os
from pathlib import Path

from benchmark.config import MARKITDOWN_OCR_MODEL
from benchmark.extractors.kreuzberg_extractor import ExtractionOutput


class MarkItDownExtractor:
    """Wrapper around markitdown.MarkItDown for markdown extraction.

    Supports two modes per D-06:
    - 'bare': Default MarkItDown without OCR plugin. Tests the out-of-box experience.
    - 'ocr': MarkItDown with markitdown-ocr plugin enabled, using OpenAI GPT-4o vision.
              Requires OPENAI_API_KEY environment variable (per D-08).
    """

    def __init__(self, mode: str = "bare") -> None:
        """Initialize the extractor.

        Args:
            mode: 'bare' for no OCR, 'ocr' for LLM Vision OCR plugin.

        Raises:
            ValueError: If mode is not 'bare' or 'ocr'.
        """
        if mode not in ("bare", "ocr"):
            raise ValueError(f"Invalid mode '{mode}'. Must be 'bare' or 'ocr'.")
        self.mode = mode

    def extract(self, file_path: Path) -> ExtractionOutput:
        """Extract markdown from a document using MarkItDown.

        Args:
            file_path: Path to the source document.

        Returns:
            ExtractionOutput with markdown content or error details.
        """
        from markitdown import MarkItDown

        tool_name = f"markitdown-{self.mode}"

        try:
            if self.mode == "ocr":
                # Check for API key before attempting OCR mode (Pitfall 3)
                api_key = os.environ.get("OPENAI_API_KEY")
                if not api_key:
                    return ExtractionOutput(
                        content="",
                        tool=tool_name,
                        source_file=file_path.name,
                        success=False,
                        error="OPENAI_API_KEY environment variable not set. Required for markitdown-ocr mode (D-08).",
                    )

                from openai import OpenAI

                md = MarkItDown(
                    enable_plugins=True,
                    llm_client=OpenAI(),
                    llm_model=MARKITDOWN_OCR_MODEL,
                )
            else:
                md = MarkItDown()

            result = md.convert(str(file_path))
            return ExtractionOutput(
                content=result.text_content,
                tool=tool_name,
                source_file=file_path.name,
                success=True,
            )
        except Exception as e:
            return ExtractionOutput(
                content="",
                tool=tool_name,
                source_file=file_path.name,
                success=False,
                error=f"{type(e).__name__}: {e}",
            )
