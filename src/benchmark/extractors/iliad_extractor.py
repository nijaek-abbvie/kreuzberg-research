"""ILIAD API extraction wrapper -- EVAL-01/EVAL-02 baseline.

Wraps ILIAD /api/v1/recognize/markdown endpoint for markdown extraction.
Per D-01: ILIAD is the MarkItDown-based production baseline.
Per D-02: Uses /api/v1/recognize/markdown endpoint.
Per D-03: Default mode (no classic flag).
Per D-04: Auth via ILIAD_API_KEY env var, base URL via ILIAD_BASE_URL env var.
Per D-05: Returns ExtractionOutput following the established extractor pattern.
"""

import os
from pathlib import Path

import httpx

from benchmark.extractors.kreuzberg_extractor import ExtractionOutput


class IliadExtractor:
    """Wrapper around ILIAD /api/v1/recognize/markdown for markdown extraction.

    Auth: ILIAD_API_KEY environment variable -> X-API-Key header (D-04).
    Base URL: ILIAD_BASE_URL environment variable (D-04).
    Returns ExtractionOutput following the established extractor pattern (D-05).
    """

    def extract(self, file_path: Path) -> ExtractionOutput:
        """Extract markdown from a document using the ILIAD API.

        Args:
            file_path: Path to the source document.

        Returns:
            ExtractionOutput with markdown content or error details.
        """
        api_key = os.environ.get("ILIAD_API_KEY")
        base_url = os.environ.get("ILIAD_BASE_URL", "").rstrip("/")

        if not api_key:
            return ExtractionOutput(
                content="",
                tool="iliad",
                source_file=file_path.name,
                success=False,
                error="ILIAD_API_KEY environment variable not set (D-04).",
            )
        if not base_url:
            return ExtractionOutput(
                content="",
                tool="iliad",
                source_file=file_path.name,
                success=False,
                error="ILIAD_BASE_URL environment variable not set (D-04).",
            )

        try:
            with open(file_path, "rb") as f:
                # Pitfall 2: httpx default timeout is 5s; large documents need 120s.
                with httpx.Client(timeout=120.0) as client:
                    response = client.post(
                        f"{base_url}/api/v1/recognize/markdown",
                        headers={"X-API-Key": api_key},
                        files={"file": (file_path.name, f, "application/octet-stream")},
                    )
            response.raise_for_status()
            data = response.json()
            # Response: {"response_id": "...", "text": "<markdown>", "cost": 0.0}
            markdown_text = data.get("text", "")
            return ExtractionOutput(
                content=markdown_text,
                tool="iliad",
                source_file=file_path.name,
                success=True,
            )
        except httpx.HTTPStatusError as e:
            # Truncate response body to avoid leaking sensitive info in error messages
            error_body = e.response.text[:200] if e.response.text else "no body"
            return ExtractionOutput(
                content="",
                tool="iliad",
                source_file=file_path.name,
                success=False,
                error=f"HTTP {e.response.status_code}: {error_body}",
            )
        except httpx.TimeoutException:
            return ExtractionOutput(
                content="",
                tool="iliad",
                source_file=file_path.name,
                success=False,
                error="Request timed out after 120s. Document may be too large for ILIAD processing.",
            )
        except Exception as e:
            return ExtractionOutput(
                content="",
                tool="iliad",
                source_file=file_path.name,
                success=False,
                error=f"{type(e).__name__}: {e}",
            )
