"""OCR accuracy metrics: CER and WER via jiwer (EVAL-01).

Per D-07: Character Error Rate and Word Error Rate using jiwer library.
Per D-08: Kreuzberg is reference, ILIAD is hypothesis (head-to-head comparison).
Per D-06: Failed extractions (empty strings) naturally score as max error:
  - jiwer.wer(non_empty_ref, "") returns 1.0
  - jiwer.wer("", "") returns 0.0

Pitfall 4: Strip HTML comments (<!-- ... -->) from ILIAD output before comparison.
Pitfall 5: Use lighter normalization -- lowercase + collapse whitespace only.
           Do NOT use RemovePunctuation (strips markdown syntax characters).
"""

import re

import jiwer
from jiwer import Compose, RemoveMultipleSpaces, Strip, ToLowerCase

# Normalization: lowercase + collapse whitespace. No RemovePunctuation (Pitfall 5).
_NORMALIZE = Compose([ToLowerCase(), RemoveMultipleSpaces(), Strip()])

# Regex to strip HTML comments like <!-- Page number: 0 --> (Pitfall 4)
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def _strip_html_comments(text: str) -> str:
    """Remove HTML comments from text (Pitfall 4: ILIAD page markers)."""
    return _HTML_COMMENT_RE.sub("", text)


def compute_ocr_metrics(kreuzberg_text: str, iliad_text: str) -> dict:
    """Compute CER and WER between Kreuzberg (reference) and ILIAD (hypothesis).

    Args:
        kreuzberg_text: Kreuzberg markdown output (reference).
        iliad_text: ILIAD markdown output (hypothesis).

    Returns:
        Dict with 'wer' (float) and 'cer' (float).
        Both are 0.0 when both inputs are empty.
        WER and CER are 1.0 when reference has content but hypothesis is empty (D-06).
    """
    # Strip HTML comments from both (Pitfall 4)
    kreuzberg_clean = _strip_html_comments(kreuzberg_text)
    iliad_clean = _strip_html_comments(iliad_text)

    # Normalize
    ref = _NORMALIZE(kreuzberg_clean) if kreuzberg_clean.strip() else ""
    hyp = _NORMALIZE(iliad_clean) if iliad_clean.strip() else ""

    # Both empty: 0.0 (both equally failed/empty)
    if not ref and not hyp:
        return {"wer": 0.0, "cer": 0.0}

    # Reference empty but hypothesis has content: 0.0 (nothing to measure against)
    if not ref:
        return {"wer": 0.0, "cer": 0.0}

    # Reference has content, hypothesis empty: max error (D-06)
    if not hyp:
        return {"wer": 1.0, "cer": 1.0}

    return {
        "wer": float(jiwer.wer(ref, hyp)),
        "cer": float(jiwer.cer(ref, hyp)),
    }
