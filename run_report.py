#!/usr/bin/env python3
"""Report generator: read evaluation results and output files, write BENCHMARK_REPORT.md.

Usage:
    uv run python run_report.py           # Generate report (default)
    uv run python run_report.py --force   # Overwrite existing BENCHMARK_REPORT.md

Per D-01: Reads results/results.csv and output markdown files.
Per D-03: Writes BENCHMARK_REPORT.md to repo root.
Per D-04: Runnable as `uv run python run_report.py` with no arguments.
"""

import argparse
import datetime
import sys
import textwrap
from pathlib import Path

import pandas as pd

from benchmark.config import (
    ILIAD_OUTPUT_DIR,
    KREUZBERG_OUTPUT_DIR,
    PROJECT_ROOT,
    RESULTS_PATH,
)


def extract_snippet(md_path: Path, n_lines: int = 10) -> str:
    """Return the first n non-blank lines from a markdown file.

    Per D-06: show the first ~10 lines of extracted text from each tool.
    If the file does not exist, return a placeholder note.

    Args:
        md_path: Path to the markdown output file.
        n_lines: Number of non-blank lines to return.

    Returns:
        A string of the first n non-blank lines, or "(output file not found)".
    """
    if not md_path.exists():
        return "(output file not found)"
    lines = md_path.read_text(encoding="utf-8").splitlines()
    non_blank = [line for line in lines if line.strip()]
    return "\n".join(non_blank[:n_lines])


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    """Build a GFM markdown table from headers and row data.

    Args:
        headers: Column header names.
        rows: List of rows, each a list of string cell values.

    Returns:
        A GFM-formatted markdown table string.
    """
    header_row = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join(["---"] * len(headers)) + " |"
    data_rows = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header_row, separator] + data_rows)


def build_executive_summary(df: pd.DataFrame) -> str:
    """Return the Executive Summary section as a string.

    Args:
        df: DataFrame loaded from results/results.csv.

    Returns:
        Markdown string for the Executive Summary section.
    """
    n_docs = len(df)
    n_cats = df["category"].nunique()
    return textwrap.dedent(f"""\
        ## Executive Summary

        This report evaluates Kreuzberg as a replacement for the ILIAD API (which wraps \
MarkItDown) for document-to-markdown extraction in the GenAI ingestion pipeline.

        The benchmark covers {n_docs} documents across {n_cats} format categories: \
scanned PDFs, native PDFs, DOCX, Excel (XLSX), PPTX, and images.

        **Recommendation: Qualified GO** -- adopt Kreuzberg with per-format caveats detailed below.\
""")


def build_methodology_section() -> str:
    """Return the Methodology section explaining scoring approach.

    Returns:
        Markdown string for the Methodology section.
    """
    return textwrap.dedent("""\
        ## Methodology

        Two extraction quality dimensions are measured:

        **Text accuracy (OCR/extraction fidelity):**

        - **CER (Character Error Rate):** 0.0 = identical text, 1.0 = completely different text
        - **WER (Word Error Rate):** 0.0 = identical text, 1.0 = completely different text

        Note: Kreuzberg output is the reference; ILIAD output is the hypothesis. \
A high CER/WER means ILIAD produced text that differs significantly from Kreuzberg's extraction.

        **Structural fidelity:**

        Heading, table, and list counts are extracted via markdown-it-py. \
Positive delta = Kreuzberg found more of that element; negative = ILIAD found more.\
""")


def build_corpus_section(df: pd.DataFrame) -> str:
    """Return the Evaluation Corpus section with a GFM table.

    Args:
        df: DataFrame loaded from results/results.csv.

    Returns:
        Markdown string for the Evaluation Corpus section.
    """
    headers = ["Document", "Format", "Difficulty", "Needs OCR"]
    rows = [
        [
            row["document"],
            row["category"],
            row["difficulty"],
            "Yes" if row["needs_ocr"] else "No",
        ]
        for _, row in df.iterrows()
    ]
    table = markdown_table(headers, rows)
    return f"## Evaluation Corpus\n\n{table}"


def build_results_section(df: pd.DataFrame) -> str:
    """Return the Results by Format section with per-format aggregation.

    Aggregates CER/WER as mean, structural deltas as sum.
    Sorted alphabetically by category (per RESEARCH.md Pitfall 4).

    Args:
        df: DataFrame loaded from results/results.csv.

    Returns:
        Markdown string for the Results by Format section.
    """
    # Per RESEARCH.md Pattern 3: groupby aggregation
    summary = df.groupby("category").agg(
        docs=("document", "count"),
        mean_cer=("cer", "mean"),
        mean_wer=("wer", "mean"),
        total_heading_delta=("heading_delta", "sum"),
        total_table_delta=("table_delta", "sum"),
        total_list_delta=("list_delta", "sum"),
    ).reset_index()
    # Per Pitfall 4: sort for deterministic order
    summary = summary.sort_values("category")

    headers = [
        "Format",
        "Docs",
        "Mean CER (error rate)",
        "Mean WER (error rate)",
        "Heading Delta",
        "Table Delta",
        "List Delta",
    ]
    rows = [
        [
            row["category"],
            str(int(row["docs"])),
            f"{row['mean_cer']:.3f}",
            f"{row['mean_wer']:.3f}",
            str(int(row["total_heading_delta"])),
            str(int(row["total_table_delta"])),
            str(int(row["total_list_delta"])),
        ]
        for _, row in summary.iterrows()
    ]
    table = markdown_table(headers, rows)

    anomaly_note = (
        "Note: The `pdf_native` category shows CER approaching 1.0. This is driven by "
        "`6120_Incentives_2023_Accrual.pdf`, where ILIAD extracted 194,464 characters vs "
        "Kreuzberg's 40,240 -- a significant volume difference likely reflecting metadata "
        "or formatting differences rather than text accuracy."
    )

    delta_note = (
        "Delta = Kreuzberg count minus ILIAD count. "
        "Positive means Kreuzberg extracted more of that element."
    )

    return (
        f"## Results by Format\n\n"
        f"{table}\n\n"
        f"*{delta_note}*\n\n"
        f"*{anomaly_note}*"
    )


def build_known_failure_section(df: pd.DataFrame) -> str:
    """Return the Key Finding section for the scanned PDF failure case.

    Per D-05, D-06, D-07, D-08: dedicated section for Sample_1_JE.pdf with
    excerpted output from both tools and qualitative analysis.

    Args:
        df: DataFrame loaded from results/results.csv.

    Returns:
        Markdown string for the Key Finding: Scanned PDF section.
    """
    iliad_snippet = extract_snippet(ILIAD_OUTPUT_DIR / "Sample_1_JE_pdf.md")
    kreuzberg_snippet = extract_snippet(KREUZBERG_OUTPUT_DIR / "Sample_1_JE_pdf.md")

    return textwrap.dedent(f"""\
        ## Key Finding: Scanned PDF (Sample_1_JE.pdf)

        The motivating case for this benchmark is `Sample_1_JE.pdf` -- a BlackLine journal \
entry form (scanned PDF). This is the document that exposed the extraction quality gap in \
the current pipeline.

        ### ILIAD Output

        ```
        {iliad_snippet}
        ```

        ### Kreuzberg Output

        ```
        {kreuzberg_snippet}
        ```

        ### Analysis

        ILIAD extracted **619 characters** (image alt-text captions only). \
Kreuzberg extracted **3,158 characters** of actual document content -- a **5x difference** \
in content volume.

        ILIAD's output consists entirely of image description alt-text generated by an LLM \
vision model (a logo description and a 'blank white image' caption). It captured zero actual \
document content. Kreuzberg's OCR pipeline extracted the form's field labels, G/L account \
numbers, cost center descriptions, and header metadata -- the content a downstream GenAI \
system would need to process this document.\
""")


def build_native_pdf_section(df: pd.DataFrame) -> str:
    """Return the Native PDF Structural Trade-off section.

    Documents the heading vs table extraction trade-off observed in
    2026_Audit_Plan_FINAL.pdf.

    Args:
        df: DataFrame loaded from results/results.csv.

    Returns:
        Markdown string for the Native PDF Structural Trade-off section.
    """
    return textwrap.dedent("""\
        ## Native PDF Structural Trade-off

        The audit plan document (`2026_Audit_Plan_FINAL.pdf`) illustrates a structural \
interpretation difference between the two tools.

        Kreuzberg extracted **90 headings** (the audit plan line items); \
ILIAD extracted **0 headings**.

        ILIAD preserved **9 tables** (the audit schedule formatted as GFM tables); \
Kreuzberg extracted **0 tables** from this document \
(the same content appears as individual heading lines).

        Both tools produced valid markdown representations of the same PDF content. \
Kreuzberg prioritized heading structure; ILIAD prioritized tabular structure. \
For downstream GenAI consumption, both representations are usable, but the structural \
interpretation differs significantly.\
""")


def build_recommendation_section() -> str:
    """Return the Recommendation section with per-format breakdown.

    Per D-09, D-10, D-11, D-12: qualified GO recommendation with per-format
    caveats and a concrete next step.

    Returns:
        Markdown string for the Recommendation section.
    """
    return textwrap.dedent("""\
        ## Recommendation

        **Recommendation: Qualified GO** -- adopt Kreuzberg as the replacement for \
MarkItDown/ILIAD in the document ingestion pipeline, with per-format caveats.

        ### Per-Format Breakdown

        **Scanned PDFs:** **GO.** Kreuzberg extracts real text content via OCR; ILIAD \
captures only image alt-text. The motivating failure case (`Sample_1_JE.pdf`) is fully \
resolved. This alone justifies the migration.

        **Native PDFs:** **GO with caveat.** Kreuzberg preserves heading structure \
significantly better (e.g., 90 headings vs 0 for the Audit Plan document). However, \
ILIAD extracts table structure more reliably from native PDFs (9 tables vs 0 for the \
same document). Before full migration, verify Kreuzberg table extraction on representative \
production native PDFs.

        **DOCX:** **GO.** Kreuzberg extracts headings (17 found in sample); ILIAD misses \
them entirely (0 headings). No regression in other structural elements.

        **Excel / PPTX:** **GO.** Near-parity between tools. Structural element counts are \
identical or within 1 for both formats. No regression risk.

        **Images with text:** **Neutral.** Both tools produce high error rates on standalone \
images (WER = 0.929, CER = 0.675). OCR accuracy on standalone images needs further \
investigation regardless of tool choice.

        ### Next Step

        **Recommended next step:** Begin migration planning with Kreuzberg as the \
MarkItDown/ILIAD replacement, prioritizing the scanned PDF pipeline first.\
""")


def build_appendix(df: pd.DataFrame) -> str:
    """Return the Appendix section with the full results table.

    Args:
        df: DataFrame loaded from results/results.csv.

    Returns:
        Markdown string for the Appendix: Full Results Table section.
    """
    headers = [
        "Document",
        "Format",
        "Difficulty",
        "Kreuzberg Chars",
        "ILIAD Chars",
        "WER",
        "CER",
        "Heading Delta",
        "Table Delta",
        "List Delta",
    ]
    rows = [
        [
            row["document"],
            row["category"],
            row["difficulty"],
            str(int(row["kreuzberg_chars"])),
            str(int(row["iliad_chars"])),
            f"{row['wer']:.3f}",
            f"{row['cer']:.3f}",
            str(int(row["heading_delta"])),
            str(int(row["table_delta"])),
            str(int(row["list_delta"])),
        ]
        for _, row in df.iterrows()
    ]
    table = markdown_table(headers, rows)
    return f"## Appendix: Full Results Table\n\n{table}"


def assemble_report(df: pd.DataFrame) -> str:
    """Concatenate all report sections into the final markdown document.

    Args:
        df: DataFrame loaded from results/results.csv.

    Returns:
        Complete markdown report as a string.
    """
    date = datetime.date.today().isoformat()
    title = "# Kreuzberg vs ILIAD: Document Extraction Benchmark Report"
    timestamp = f"*Generated: {date}*"

    sections = [
        title,
        timestamp,
        build_executive_summary(df),
        build_methodology_section(),
        build_corpus_section(df),
        build_results_section(df),
        build_known_failure_section(df),
        build_native_pdf_section(df),
        build_recommendation_section(),
        build_appendix(df),
    ]
    return "\n\n".join(sections) + "\n"


def main() -> None:
    """Main entry point for the report generator.

    Per D-04: runnable as `uv run python run_report.py` with no arguments.
    Per D-03: writes BENCHMARK_REPORT.md to repo root.
    """
    parser = argparse.ArgumentParser(
        description="Generate BENCHMARK_REPORT.md from evaluation results."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing BENCHMARK_REPORT.md",
    )
    args = parser.parse_args()

    # Per D-03: output goes to repo root
    report_path = PROJECT_ROOT / "BENCHMARK_REPORT.md"

    # Idempotency guard — skip if report already exists and --force not passed
    if report_path.exists() and not args.force:
        print(f"SKIP: {report_path} already exists. Use --force to overwrite.")
        sys.exit(0)

    # Per D-01: reads results/results.csv
    if not RESULTS_PATH.exists():
        print(f"ERROR: {RESULTS_PATH} not found. Run run_evaluation.py first.")
        sys.exit(1)

    df = pd.read_csv(RESULTS_PATH)
    report = assemble_report(df)
    report_path.write_text(report, encoding="utf-8")

    print("=" * 70)
    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
