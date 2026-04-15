"""Generate synthetic PDF test files using reportlab."""

import io
import random
from pathlib import Path

from generators.base import BaseGenerator

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, mm
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import (
        Image as RLImage,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.platypus.frames import Frame
    from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
    from reportlab.pdfgen import canvas as rl_canvas
    _RL_OK = True
except ImportError:
    _RL_OK = False

try:
    from PIL import Image as PILImage, ImageDraw, ImageFilter, ImageFont
    _PIL_OK = True
except ImportError:
    _PIL_OK = False


def _require_reportlab() -> None:
    if not _RL_OK:
        raise ImportError("reportlab is required: uv add reportlab")


def _require_pillow() -> None:
    if not _PIL_OK:
        raise ImportError("Pillow is required: uv add pillow")


def _pil_font(size: int):
    for path in [
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _render_text_to_pil(lines: list[str], dpi: int = 300, noise: int = 0,
                         angle: float = 0.0) -> "PILImage.Image":
    """Render lines of text to a PIL image at the given DPI."""
    _require_pillow()
    w, h = int(8.5 * dpi), int(11 * dpi)
    img = PILImage.new("RGB", (w, h), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_size = max(20, dpi // 10)
    font = _pil_font(font_size)
    y = int(0.5 * dpi)
    line_h = int(font_size * 1.5)
    for line in lines:
        draw.text((int(0.75 * dpi), y), line, font=font, fill=(0, 0, 0))
        y += line_h
    if noise > 0:
        pixels = img.load()
        rng = random.Random(42)
        for _ in range(noise):
            px = rng.randint(0, w - 1)
            py = rng.randint(0, h - 1)
            v = rng.randint(160, 230)
            pixels[px, py] = (v, v, v)
    if angle != 0.0:
        img = img.rotate(angle, expand=False, fillcolor=(255, 255, 255))
    return img


def _pil_image_to_bytes(img: "PILImage.Image") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PDF")
    buf.seek(0)
    return buf.read()


def _pil_page_to_png_bytes(img: "PILImage.Image") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


class PdfGenerator(BaseGenerator):
    category = "pdf_native"

    def generate(self, dry_run: bool = False) -> list[dict]:
        _require_reportlab()
        out = self.output_dir()
        if not dry_run:
            out.mkdir(parents=True, exist_ok=True)

        entries = []
        entries.append(self._simple_text(out, dry_run))
        entries.append(self._multipage_headers(out, dry_run))
        entries.append(self._two_column(out, dry_run))
        entries.append(self._tables_and_image(out, dry_run))
        entries.append(self._form_layout(out, dry_run))
        entries.append(self._large_50_pages(out, dry_run))
        return entries

    # ------------------------------------------------------------------
    def _simple_text(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_simple_text.pdf"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            styles = getSampleStyleSheet()
            doc = SimpleDocTemplate(str(out / filename), pagesize=letter)
            story = [
                Paragraph("Project Status Report", styles["Title"]),
                Spacer(1, 0.2 * inch),
                Paragraph("Executive Summary", styles["Heading2"]),
                Paragraph(
                    "This report provides an update on the current project status as of Q4 2024. "
                    "All major milestones are on track and within budget.",
                    styles["BodyText"],
                ),
                Spacer(1, 0.15 * inch),
                Paragraph("Key Achievements", styles["Heading2"]),
                Paragraph("Phase 1 infrastructure deployment completed ahead of schedule.", styles["BodyText"]),
                Paragraph("Integration testing passed with 98.7% success rate.", styles["BodyText"]),
                Paragraph("Security audit completed with no critical findings.", styles["BodyText"]),
                Spacer(1, 0.15 * inch),
                Paragraph("Next Steps", styles["Heading2"]),
                Paragraph(
                    "The team will proceed to Phase 2 in January 2025. Key activities include "
                    "user acceptance testing, staff training, and production cutover planning.",
                    styles["BodyText"],
                ),
            ]
            doc.build(story)
        return self._entry(filename, "easy",
                           ["pdf-native", "simple-text", "headings", "paragraphs"],
                           False, "Simple single-page native PDF with headings and body paragraphs.")

    def _multipage_headers(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_multipage_headers.pdf"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            styles = getSampleStyleSheet()

            def add_header_footer(canvas, doc):
                canvas.saveState()
                canvas.setFont("Helvetica-Bold", 9)
                canvas.drawString(inch, letter[1] - 0.5 * inch, "ACME CORP — INTERNAL REPORT")
                canvas.drawRightString(letter[0] - inch, letter[1] - 0.5 * inch, "CONFIDENTIAL")
                canvas.setFont("Helvetica", 8)
                canvas.drawCentredString(letter[0] / 2, 0.4 * inch,
                                         f"Page {doc.page} of 5")
                canvas.restoreState()

            doc = SimpleDocTemplate(str(out / filename), pagesize=letter,
                                    topMargin=inch, bottomMargin=0.75 * inch)
            story = []
            sections = [
                ("Annual Operations Review 2024", "Overview",
                 "This document provides a comprehensive review of operational performance "
                 "across all business units for fiscal year 2024. Key metrics, achievements, "
                 "and areas for improvement are documented herein."),
                ("Financial Performance", "Revenue & Profitability",
                 "Total revenue for 2024 reached $1.84 billion, representing 12% year-over-year "
                 "growth. Gross margin improved to 41.3%, up from 39.8% in 2023. Operating "
                 "income of $285M exceeded the annual target by 8%."),
                ("Operational Metrics", "Efficiency & Quality",
                 "Customer satisfaction scores averaged 4.6/5.0 across all service lines. "
                 "Order fulfillment accuracy reached 99.2%, a new company record. Mean time "
                 "to resolution for support tickets decreased from 4.2 to 2.8 hours."),
                ("Human Resources", "Talent & Culture",
                 "Total headcount grew to 4,200 employees across 18 countries. Voluntary "
                 "attrition rate decreased to 8.3%, well below the industry average of 13%. "
                 "Employee engagement score of 78% was the highest in company history."),
                ("Outlook 2025", "Strategic Priorities",
                 "For 2025, the company will focus on three strategic themes: geographic "
                 "expansion into Southeast Asia, continued investment in AI-powered automation, "
                 "and a new sustainability initiative targeting carbon neutrality by 2030."),
            ]
            for i, (title, heading, body) in enumerate(sections):
                if i == 0:
                    story.append(Paragraph(title, styles["Title"]))
                story.append(Paragraph(heading, styles["Heading1"]))
                story.append(Paragraph(body, styles["BodyText"]))
                story.append(Spacer(1, 0.3 * inch))
                if i < len(sections) - 1:
                    story.append(PageBreak())

            doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
        return self._entry(filename, "easy",
                           ["pdf-native", "multi-page", "headers-footers", "page-numbers"],
                           False, "Five-page native PDF with running header, footer, and page numbers.")

    def _two_column(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_two_column.pdf"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            styles = getSampleStyleSheet()
            body_style = ParagraphStyle("TwoColBody", parent=styles["BodyText"],
                                        fontSize=9, leading=13, alignment=TA_JUSTIFY)
            head_style = ParagraphStyle("TwoColHead", parent=styles["Heading3"],
                                        fontSize=11, spaceAfter=4)

            class TwoColumnDoc(BaseDocTemplate):
                def build(self, flowables, **kwargs):
                    self._calc()
                    frame_w = (self.width - 0.25 * inch) / 2
                    frame_h = self.height
                    left = Frame(self.leftMargin, self.bottomMargin,
                                 frame_w, frame_h, id="left")
                    right = Frame(self.leftMargin + frame_w + 0.25 * inch,
                                  self.bottomMargin, frame_w, frame_h, id="right")
                    self.addPageTemplates([PageTemplate(id="TwoCol", frames=[left, right])])
                    super().build(flowables, **kwargs)

            doc = TwoColumnDoc(str(out / filename), pagesize=letter)
            story = [
                Paragraph("Journal of Applied Research — Volume 12, Issue 3", styles["Title"]),
                Spacer(1, 0.1 * inch),
                Paragraph("Deep Learning Approaches for Document Understanding", styles["Heading2"]),
                Paragraph("Abstract", head_style),
                Paragraph(
                    "Recent advances in transformer-based architectures have significantly improved "
                    "the accuracy of document understanding tasks. This paper presents a novel "
                    "multi-modal approach combining visual and textual features for layout-aware "
                    "document parsing. Our method achieves state-of-the-art results on four "
                    "benchmark datasets, with a 7.3% improvement over prior methods on complex "
                    "multi-column layouts.",
                    body_style,
                ),
                Spacer(1, 0.1 * inch),
                Paragraph("1. Introduction", head_style),
                Paragraph(
                    "Document understanding encompasses a wide range of tasks including text "
                    "extraction, layout analysis, table detection, and semantic understanding. "
                    "Traditional approaches relied on rule-based systems that required manual "
                    "feature engineering. The emergence of deep learning has transformed this "
                    "field, enabling end-to-end trainable systems.",
                    body_style,
                ),
                Spacer(1, 0.08 * inch),
                Paragraph("2. Related Work", head_style),
                Paragraph(
                    "Prior work in document analysis can be categorized into three streams: "
                    "OCR-focused methods, layout detection approaches, and end-to-end systems. "
                    "LayoutLM (Xu et al., 2020) introduced the first pre-trained model combining "
                    "text and layout information. DocFormer (Appalaraju et al., 2021) extended "
                    "this with visual features. Our work builds on these foundations.",
                    body_style,
                ),
                Spacer(1, 0.08 * inch),
                Paragraph("3. Methodology", head_style),
                Paragraph(
                    "Our architecture consists of three components: a visual encoder based on "
                    "ViT-Base, a text encoder based on RoBERTa-Base, and a cross-modal fusion "
                    "module. Input documents are first converted to high-resolution images (300 DPI). "
                    "Regions of interest are extracted using a modified Faster R-CNN detector.",
                    body_style,
                ),
                Spacer(1, 0.08 * inch),
                Paragraph("4. Experiments", head_style),
                Paragraph(
                    "We evaluated our approach on FUNSD, CORD, DocVQA, and PubLayNet. For each "
                    "dataset, we used the standard train/dev/test splits. All models were trained "
                    "for 50 epochs with a batch size of 16 on 4 A100 GPUs. The AdamW optimizer "
                    "was used with a linear warmup schedule.",
                    body_style,
                ),
                Spacer(1, 0.08 * inch),
                Paragraph("5. Results", head_style),
                Paragraph(
                    "Our model achieves 92.4 F1 on FUNSD (vs. 89.6 for LayoutLMv3), 97.1 on CORD "
                    "(vs. 96.0), and 83.2 on DocVQA (vs. 78.9). The improvement is most pronounced "
                    "on multi-column documents, where our layout-aware fusion module provides "
                    "significant benefits over text-only baselines.",
                    body_style,
                ),
                Spacer(1, 0.08 * inch),
                Paragraph("6. Conclusion", head_style),
                Paragraph(
                    "We presented a multi-modal document understanding framework that outperforms "
                    "existing methods on standard benchmarks. Future work will explore zero-shot "
                    "generalization and efficiency improvements for edge deployment.",
                    body_style,
                ),
            ]
            doc.build(story)
        return self._entry(filename, "medium",
                           ["pdf-native", "two-column", "academic-paper", "multi-frame"],
                           False, "Two-column academic paper layout — tests column detection and reading order.")

    def _tables_and_image(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_tables_and_image.pdf"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            styles = getSampleStyleSheet()
            doc = SimpleDocTemplate(str(out / filename), pagesize=letter)

            # Build a small inline image with Pillow
            img_element = None
            if _PIL_OK:
                pil_img = PILImage.new("RGB", (400, 200), color=(220, 235, 250))
                draw = ImageDraw.Draw(pil_img)
                draw.text((20, 80), "[Chart: Q4 Revenue by Product Line]", fill=(40, 40, 140))
                buf = io.BytesIO()
                pil_img.save(buf, format="PNG")
                buf.seek(0)
                img_element = RLImage(buf, width=3.5 * inch, height=1.75 * inch)

            table_data = [
                ["Region", "Q1 ($M)", "Q2 ($M)", "Q3 ($M)", "Q4 ($M)", "Total"],
                ["North America", "142", "158", "171", "189", "660"],
                ["Europe", "87", "92", "98", "105", "382"],
                ["Asia Pacific", "54", "61", "68", "79", "262"],
                ["Other", "18", "20", "22", "25", "85"],
                ["Total", "301", "331", "359", "398", "1,389"],
            ]
            table_style = TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#D6E4F0")),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F5F9FF")]),
            ])
            tbl = Table(table_data, colWidths=[1.8 * inch] + [0.85 * inch] * 5)
            tbl.setStyle(table_style)

            story = [
                Paragraph("Annual Revenue Report 2024", styles["Title"]),
                Spacer(1, 0.15 * inch),
                Paragraph("Revenue by Region", styles["Heading2"]),
                Spacer(1, 0.1 * inch),
                tbl,
                Spacer(1, 0.2 * inch),
                Paragraph("Revenue Visualization", styles["Heading2"]),
            ]
            if img_element:
                story.append(img_element)
            story += [
                Spacer(1, 0.1 * inch),
                Paragraph(
                    "The chart above shows Q4 revenue performance by product line. "
                    "North America continues to be the largest region, contributing 47% "
                    "of total annual revenue. Asia Pacific showed the strongest growth "
                    "trajectory at 46% year-over-year.",
                    styles["BodyText"],
                ),
            ]
            doc.build(story)
        return self._entry(filename, "medium",
                           ["pdf-native", "tables", "embedded-image", "financial-report"],
                           False, "Native PDF with a styled data table and an embedded image/chart.")

    def _form_layout(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_form_layout.pdf"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            c = rl_canvas.Canvas(str(out / filename), pagesize=letter)
            w, h = letter

            # Header
            c.setFillColorRGB(0.12, 0.30, 0.47)
            c.rect(0, h - 80, w, 80, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica-Bold", 18)
            c.drawString(40, h - 50, "EMPLOYEE EXPENSE REIMBURSEMENT FORM")
            c.setFont("Helvetica", 10)
            c.drawString(40, h - 68, "Please complete all fields. Attach original receipts.")

            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(40, h - 110, "EMPLOYEE INFORMATION")
            c.line(40, h - 115, w - 40, h - 115)

            fields = [
                ("Employee Name:", 40, h - 145, 250),
                ("Employee ID:", 310, h - 145, 220),
                ("Department:", 40, h - 185, 250),
                ("Manager Name:", 310, h - 185, 220),
                ("Submission Date:", 40, h - 225, 250),
                ("Period Covered:", 310, h - 225, 220),
            ]
            c.setFont("Helvetica-Bold", 9)
            for label, x, y, fw in fields:
                c.drawString(x, y, label)
                c.line(x, y - 15, x + fw, y - 15)

            c.setFont("Helvetica-Bold", 11)
            c.drawString(40, h - 270, "EXPENSE DETAILS")
            c.line(40, h - 275, w - 40, h - 275)

            # Table header
            cols = [40, 130, 260, 340, 420, 500]
            labels = ["Date", "Description", "Category", "Amount ($)", "Receipt?", "Notes"]
            c.setFillColorRGB(0.12, 0.30, 0.47)
            c.rect(38, h - 310, w - 76, 22, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica-Bold", 9)
            for col_x, lbl in zip(cols, labels):
                c.drawString(col_x + 2, h - 302, lbl)
            c.setFillColorRGB(0, 0, 0)

            c.setFont("Helvetica", 9)
            for i in range(8):
                y_row = h - 330 - i * 25
                c.line(38, y_row, w - 38, y_row)
                c.drawString(42, y_row + 7, "________")
                c.drawString(132, y_row + 7, "___________________________")
                c.drawString(262, y_row + 7, "_______________")
                c.drawString(342, y_row + 7, "_________")
                c.drawString(422, y_row + 7, "[ ] Yes  [ ] No")

            # Totals section
            y_tot = h - 560
            c.line(38, y_tot, w - 38, y_tot)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(340, y_tot - 20, "SUBTOTAL:")
            c.line(420, y_tot - 22, 555, y_tot - 22)
            c.drawString(340, y_tot - 45, "ADVANCE RECEIVED:")
            c.line(420, y_tot - 47, 555, y_tot - 47)
            c.drawString(340, y_tot - 70, "TOTAL REIMBURSABLE:")
            c.line(420, y_tot - 72, 555, y_tot - 72)

            # Signature section
            y_sig = y_tot - 120
            c.setFont("Helvetica-Bold", 11)
            c.drawString(40, y_sig, "SIGNATURES")
            c.line(40, y_sig - 5, w - 40, y_sig - 5)
            c.setFont("Helvetica", 9)
            c.drawString(40, y_sig - 30, "Employee Signature:")
            c.line(170, y_sig - 32, 380, y_sig - 32)
            c.drawString(400, y_sig - 30, "Date:")
            c.line(425, y_sig - 32, 555, y_sig - 32)
            c.drawString(40, y_sig - 60, "Manager Approval:")
            c.line(170, y_sig - 62, 380, y_sig - 62)
            c.drawString(400, y_sig - 60, "Date:")
            c.line(425, y_sig - 62, 555, y_sig - 62)

            c.save()
        return self._entry(filename, "medium",
                           ["pdf-native", "form-layout", "expense-form", "field-lines", "tables"],
                           False, "Expense reimbursement form with labeled fields, a data table, and signature blocks.")

    def _large_50_pages(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_large_50pages.pdf"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            styles = getSampleStyleSheet()

            def header_footer(canvas, doc):
                canvas.saveState()
                canvas.setFont("Helvetica", 8)
                canvas.drawString(inch, letter[1] - 0.4 * inch,
                                  "ENTERPRISE TECHNOLOGY ASSESSMENT REPORT 2024")
                canvas.drawRightString(letter[0] - inch, letter[1] - 0.4 * inch,
                                       f"Page {doc.page}")
                canvas.line(inch, letter[1] - 0.45 * inch,
                             letter[0] - inch, letter[1] - 0.45 * inch)
                canvas.restoreState()

            doc = SimpleDocTemplate(str(out / filename), pagesize=letter,
                                    topMargin=0.75 * inch, bottomMargin=0.75 * inch)
            story = [
                Paragraph("Enterprise Technology Assessment Report 2024", styles["Title"]),
                Paragraph("Prepared by: IT Strategy Division", styles["Normal"]),
                Spacer(1, 0.3 * inch),
            ]

            topics = [
                "Infrastructure Overview", "Cloud Architecture", "Security Posture",
                "Network Performance", "Data Management", "Application Portfolio",
                "DevOps Maturity", "AI and Automation", "Vendor Relationships",
                "Disaster Recovery", "Identity Management", "Compliance Status",
                "Cost Optimization", "Capacity Planning", "Service Desk Metrics",
                "Change Management", "Release Cadence", "Monitoring & Observability",
                "API Ecosystem", "Mobile Platform", "Data Governance", "Integration Layer",
                "Database Performance", "Storage Architecture", "End User Computing",
            ]

            body_texts = [
                "This section provides a detailed analysis of the current state, gaps identified, "
                "and recommended improvements. The assessment was conducted over a six-week period "
                "involving interviews with 48 stakeholders and review of 200+ technical documents.",
                "Key findings indicate significant opportunities for modernization and cost reduction. "
                "The team identified 12 critical risks, 28 medium risks, and 45 low-risk items that "
                "require attention over the next 12-18 months.",
                "Recommended actions have been prioritized using a value-vs-effort matrix. Quick wins "
                "are identified for immediate action, while strategic initiatives require detailed "
                "planning and executive sponsorship before proceeding.",
            ]

            for i, topic in enumerate(topics):
                story.append(Paragraph(f"Section {i + 1}: {topic}", styles["Heading1"]))
                for j, body in enumerate(body_texts):
                    story.append(Paragraph(
                        body + f" (Section {i + 1}, subsection {j + 1})", styles["BodyText"]
                    ))
                    story.append(Spacer(1, 0.1 * inch))
                story.append(PageBreak())

            # Final summary
            story.append(Paragraph("Executive Summary", styles["Heading1"]))
            story.append(Paragraph(
                "This report has assessed 25 technology domains. The overall maturity score "
                "is 3.2 out of 5.0. Priority investment areas are Cloud Architecture, Security "
                "Posture, and Data Governance. Estimated annual savings from recommended "
                "optimizations: $4.2M.",
                styles["BodyText"],
            ))

            doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
        return self._entry(filename, "hard",
                           ["pdf-native", "50-pages", "large-document", "multi-section", "headers-footers"],
                           False, "50-page native PDF — stress-tests large document handling.")


class PdfScannedGenerator(BaseGenerator):
    """Generates image-based (scanned) PDFs using Pillow + reportlab."""
    category = "pdf_scanned"

    def generate(self, dry_run: bool = False) -> list[dict]:
        _require_reportlab()
        _require_pillow()
        out = self.output_dir()
        if not dry_run:
            out.mkdir(parents=True, exist_ok=True)

        entries = []
        entries.append(self._clean_300dpi(out, dry_run))
        entries.append(self._multi_page_200dpi(out, dry_run))
        entries.append(self._low_dpi_noisy(out, dry_run))
        entries.append(self._skewed(out, dry_run))
        entries.append(self._degraded_photocopy(out, dry_run))
        return entries

    def _page_lines(self, title: str, body_lines: list[str]) -> list[str]:
        return [title, "=" * 60, ""] + body_lines

    def _save_single_page_scanned_pdf(self, path: Path, lines: list[str],
                                       dpi: int = 300, noise: int = 0,
                                       angle: float = 0.0) -> None:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas as rl_canvas
        img = _render_text_to_pil(lines, dpi=dpi, noise=noise, angle=angle)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        c = rl_canvas.Canvas(str(path), pagesize=letter)
        w, h = letter
        c.drawImage(ImageReader(buf), 0, 0, width=w, height=h)
        c.save()

    def _save_multi_page_scanned_pdf(self, path: Path, pages: list[list[str]],
                                      dpi: int = 200, noise: int = 0) -> None:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas as rl_canvas
        c = rl_canvas.Canvas(str(path), pagesize=letter)
        w, h = letter
        for lines in pages:
            img = _render_text_to_pil(lines, dpi=dpi, noise=noise)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            c.drawImage(ImageReader(buf), 0, 0, width=w, height=h)
            c.showPage()
        c.save()

    def _clean_300dpi(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_clean_scan_300dpi.pdf"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            lines = self._page_lines("MEETING MINUTES — BOARD OF DIRECTORS", [
                "Date: November 15, 2024",
                "Location: Corporate Headquarters, Room 4B",
                "Attendees: J. Williams (Chair), M. Chen, R. Patel, S. Kowalski",
                "",
                "1. Call to Order",
                "   The meeting was called to order at 9:02 AM by Chair Williams.",
                "",
                "2. Approval of Previous Minutes",
                "   Minutes from the October 18 meeting were approved unanimously.",
                "",
                "3. Financial Report",
                "   CFO Chen presented Q3 financials. Revenue of $284M exceeded",
                "   the forecast by 4.2%. Operating expenses were within budget.",
                "",
                "4. Strategic Update",
                "   The Board reviewed progress on the three-year strategic plan.",
                "   Asia Pacific expansion is proceeding as scheduled.",
                "",
                "5. Action Items",
                "   - CFO to prepare Q4 forecast by December 1",
                "   - Legal to finalize Singapore entity registration",
                "   - HR to present succession planning framework in January",
                "",
                "Meeting adjourned at 11:45 AM.",
            ])
            self._save_single_page_scanned_pdf(out / filename, lines, dpi=300)
        return self._entry(filename, "easy",
                           ["pdf-scanned", "image-only", "300dpi", "clean-scan", "meeting-minutes"],
                           True, "Clean 300 DPI image-based PDF — easy OCR baseline for scanned docs.")

    def _multi_page_200dpi(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_multi_page_scan_200dpi.pdf"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            page1 = self._page_lines("RESEARCH GRANT APPLICATION — PAGE 1", [
                "Project Title: Novel Biomarkers for Early Disease Detection",
                "Principal Investigator: Dr. Amanda Foster, PhD",
                "Institution: Midwest Research University",
                "Funding Requested: $485,000 over 36 months",
                "",
                "ABSTRACT",
                "This proposal seeks funding to investigate novel protein biomarkers",
                "associated with early-stage metabolic disorders. Using a cohort of",
                "1,200 participants, we will employ mass spectrometry and machine",
                "learning to identify diagnostic signatures with >90% specificity.",
            ])
            page2 = self._page_lines("RESEARCH GRANT APPLICATION — PAGE 2", [
                "SPECIFIC AIMS",
                "",
                "Aim 1: Establish biomarker baseline profiles in healthy controls",
                "   We will recruit 400 age- and sex-matched healthy adults and",
                "   collect fasting blood samples at 6-month intervals over 2 years.",
                "",
                "Aim 2: Identify differential expression in early-disease subjects",
                "   Comparison cohort of 800 subjects with confirmed early-stage",
                "   metabolic syndrome will undergo identical sampling protocol.",
                "",
                "Aim 3: Validate ML-based diagnostic model in independent cohort",
                "   A held-out validation set of 200 subjects will be used to test",
                "   model performance before external validation.",
            ])
            page3 = self._page_lines("RESEARCH GRANT APPLICATION — PAGE 3", [
                "BUDGET JUSTIFICATION",
                "",
                "Personnel (60% of budget): $291,000",
                "   PI effort: 20% salary + fringe = $48,000/year",
                "   Postdoctoral fellow (full-time): $55,000/year",
                "   Research coordinator (50% effort): $22,000/year",
                "",
                "Equipment (15% of budget): $72,750",
                "   Mass spectrometer supplies and consumables",
                "   Computational infrastructure upgrades",
                "",
                "Indirect Costs (25% of budget): $121,250",
                "   Per institutional negotiated rate agreement",
                "",
                "TOTAL: $485,000",
            ])
            self._save_multi_page_scanned_pdf(out / filename, [page1, page2, page3], dpi=200)
        return self._entry(filename, "medium",
                           ["pdf-scanned", "multi-page", "200dpi", "grant-application"],
                           True, "Three-page scanned PDF at 200 DPI — tests multi-page OCR and continuity.")

    def _low_dpi_noisy(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_low_dpi_noisy.pdf"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            lines = self._page_lines("VENDOR CONTRACT SUMMARY", [
                "Contract No: VC-2024-00891",
                "Vendor: GlobalSupply Partners Ltd.",
                "Effective Date: January 1, 2024",
                "Expiration Date: December 31, 2025",
                "",
                "SCOPE OF SERVICES",
                "Vendor shall provide raw material components as specified in",
                "Exhibit A. Minimum order quantity: 5,000 units per month.",
                "Delivery lead time: 14 business days from purchase order.",
                "",
                "PRICING",
                "Unit price: $12.50 (Year 1), $13.00 (Year 2)",
                "Volume discount: 5% above 10,000 units/month",
                "",
                "TERMINATION",
                "Either party may terminate with 60 days written notice.",
            ])
            self._save_single_page_scanned_pdf(out / filename, lines, dpi=120, noise=5000)
        return self._entry(filename, "hard",
                           ["pdf-scanned", "low-dpi", "120dpi", "noisy", "scan-degradation"],
                           True, "Low-resolution (120 DPI) scanned PDF with added noise — hard OCR challenge.")

    def _skewed(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_skewed_scan.pdf"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            lines = self._page_lines("PURCHASE ORDER #PO-2024-7823", [
                "Bill To:                        Ship To:",
                "Acme Corporation                Acme Corp — Warehouse",
                "500 Commerce Blvd               12 Industrial Pkwy",
                "Chicago, IL 60601               Joliet, IL 60432",
                "",
                "Order Date: March 8, 2024       Required By: March 22, 2024",
                "",
                "Line  Description               Qty    Unit Price   Total",
                "----  ------------------------  -----  ----------   --------",
                "001   Steel bracket type A        500      $4.20    $2,100.00",
                "002   Hex bolt M8 x 25mm        2,000      $0.35      $700.00",
                "003   Rubber gasket 50mm          300      $1.80      $540.00",
                "004   Assembly kit complete       100     $22.50    $2,250.00",
                "",
                "                                Subtotal:           $5,590.00",
                "                                Tax (7%):             $391.30",
                "                                Total:             $5,981.30",
            ])
            # Rotate 3 degrees to simulate feeder skew
            self._save_single_page_scanned_pdf(out / filename, lines, dpi=200, angle=3.0)
        return self._entry(filename, "hard",
                           ["pdf-scanned", "skewed", "3-degree-rotation", "purchase-order", "table-content"],
                           True, "Scanned PDF with 3-degree skew — simulates a page fed at an angle.")

    def _degraded_photocopy(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_degraded_photocopy.pdf"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            lines = self._page_lines("POLICY MEMO — HR DEPARTMENT", [
                "TO:    All Employees",
                "FROM:  Human Resources",
                "DATE:  February 1, 2024",
                "RE:    Updated Workplace Safety Procedures",
                "",
                "Effective immediately, all employees must complete the",
                "mandatory safety refresher training before March 31.",
                "",
                "Training is available online via the Learning Portal.",
                "Estimated completion time: 45 minutes.",
                "",
                "Non-compliance will result in restricted building access",
                "until training requirements are fulfilled.",
                "",
                "Contact safety@company.com with questions.",
            ])
            # High noise + blur to simulate heavy degradation
            img = _render_text_to_pil(lines, dpi=150, noise=15000)
            img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
            # Reduce contrast (photocopy fade)
            from PIL import ImageEnhance
            img = ImageEnhance.Contrast(img).enhance(0.6)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.utils import ImageReader
            from reportlab.pdfgen import canvas as rl_canvas
            c = rl_canvas.Canvas(str(out / filename), pagesize=letter)
            w, h = letter
            buf.seek(0)
            c.drawImage(ImageReader(buf), 0, 0, width=w, height=h)
            c.save()
        return self._entry(filename, "hard",
                           ["pdf-scanned", "degraded", "photocopy", "blur", "low-contrast"],
                           True, "Heavily degraded photocopy simulation: noise, blur, and reduced contrast.")


class PdfMixedGenerator(BaseGenerator):
    """Generates mixed PDFs: some pages native text, some scanned images."""
    category = "pdf_mixed"

    def generate(self, dry_run: bool = False) -> list[dict]:
        _require_reportlab()
        _require_pillow()
        out = self.output_dir()
        if not dry_run:
            out.mkdir(parents=True, exist_ok=True)

        entries = []
        entries.append(self._native_then_scan(out, dry_run))
        entries.append(self._alternating(out, dry_run))
        entries.append(self._appendix_style(out, dry_run))
        return entries

    def _build_mixed_pdf(self, path: Path, pages: list[dict]) -> None:
        """Build a PDF where each page dict has type='native' or 'scanned'."""
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

        c = rl_canvas.Canvas(str(path), pagesize=letter)
        w, h = letter
        styles = getSampleStyleSheet()

        from reportlab.lib.utils import ImageReader
        for page in pages:
            if page["type"] == "scanned":
                img = _render_text_to_pil(page["lines"], dpi=200, noise=500)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                c.drawImage(ImageReader(buf), 0, 0, width=w, height=h)
            else:
                # Native text page
                c.setFont("Helvetica-Bold", 16)
                c.drawString(72, h - 80, page.get("title", ""))
                c.setFont("Helvetica", 11)
                y = h - 120
                for line in page.get("lines", []):
                    c.drawString(72, y, line)
                    y -= 20
                    if y < 72:
                        break
            c.showPage()
        c.save()

    def _native_then_scan(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_mixed_native_then_scan.pdf"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            pages = [
                {"type": "native", "title": "Inspection Report — Section 1",
                 "lines": [
                     "Site: Manufacturing Plant B", "Inspector: R. Thompson", "Date: April 10, 2024",
                     "", "1. OVERVIEW",
                     "This report documents findings from the quarterly safety inspection.",
                     "The inspection covered all production lines, warehouse areas,",
                     "emergency systems, and common areas.",
                     "", "2. SUMMARY OF FINDINGS",
                     "Total items inspected: 148", "Compliant: 139 (93.9%)",
                     "Minor issues: 7 (4.7%)", "Critical issues: 2 (1.4%)",
                 ]},
                {"type": "native", "title": "Section 2: Detailed Findings",
                 "lines": [
                     "CRITICAL ISSUES (require immediate action):",
                     "", "Issue #1: Fire extinguisher in Bay 3 expired February 2024",
                     "  Location: Bay 3, column D4", "  Action Required: Replace within 48 hours",
                     "", "Issue #2: Emergency exit signage damaged in Corridor C",
                     "  Location: Corridor C, near loading dock",
                     "  Action Required: Replace signage within 24 hours",
                     "", "MINOR ISSUES (resolve within 30 days):",
                     "  - Forklift charging station: cable fraying on unit #4",
                     "  - Break room: first aid kit needs restock",
                     "  - Warehouse aisle 7: floor marking faded",
                 ]},
                {"type": "scanned", "lines": [
                    "APPENDIX A — PHOTO DOCUMENTATION",
                    "(This page was submitted as a handwritten/photographed attachment)",
                    "",
                    "Photo 1: Bay 3 fire extinguisher — expiry tag visible",
                    "Photo 2: Corridor C emergency exit — sign damage",
                    "Photo 3: Forklift unit #4 — cable condition",
                    "",
                    "Inspector signature: ___________________________",
                    "Date signed: April 10, 2024",
                    "Supervisor review: ____________________________",
                ]},
                {"type": "scanned", "lines": [
                    "APPENDIX B — CORRECTIVE ACTION SIGN-OFF",
                    "",
                    "Item 1 (Bay 3 extinguisher) — Completed: ________",
                    "Completed by: ________________  Date: ___________",
                    "",
                    "Item 2 (Corridor C signage) — Completed: _________",
                    "Completed by: ________________  Date: ___________",
                    "",
                    "All critical items resolved: [ ] Yes  [ ] No",
                    "",
                    "Plant Manager sign-off: _________________________",
                ]},
            ]
            self._build_mixed_pdf(out / filename, pages)
        return self._entry(filename, "medium",
                           ["pdf-mixed", "native-then-scanned", "inspection-report", "appendix"],
                           True, "Mixed PDF: 2 native text pages followed by 2 scanned appendix pages.")

    def _alternating(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_mixed_alternating.pdf"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            pages = [
                {"type": "native", "title": "Clinical Trial Protocol — Summary",
                 "lines": ["Trial ID: CT-2024-0892", "Phase: II", "Sponsor: MedResearch Inc.",
                            "", "Primary Endpoint: Reduction in symptom severity score",
                            "at 12 weeks vs. baseline.", "Secondary Endpoints: Quality of life,",
                            "adverse event profile, biomarker response."]},
                {"type": "scanned", "lines": ["INFORMED CONSENT FORM — PAGE 1",
                                              "(Original signed document — scanned copy)",
                                              "", "I, the undersigned, voluntarily agree to participate...",
                                              "Patient Name: _____________________",
                                              "Signature: ________________________  Date: _______"]},
                {"type": "native", "title": "Inclusion/Exclusion Criteria",
                 "lines": ["INCLUSION:", "- Age 18-65", "- Confirmed diagnosis via validated criteria",
                            "- Able to provide informed consent",
                            "", "EXCLUSION:", "- Pregnancy or nursing", "- Prior treatment with XR-compound",
                            "- Severe hepatic impairment (Child-Pugh C)"]},
                {"type": "scanned", "lines": ["INVESTIGATOR ATTESTATION",
                                              "(Handwritten — scanned for records)",
                                              "", "I certify that the protocol has been reviewed",
                                              "and approved by the IRB on file.",
                                              "", "Principal Investigator: ___________________",
                                              "Signature: _________________  Date: __________"]},
            ]
            self._build_mixed_pdf(out / filename, pages)
        return self._entry(filename, "hard",
                           ["pdf-mixed", "alternating-pages", "clinical-trial", "consent-forms"],
                           True, "Hard mixed PDF: alternating native and scanned pages — tests page-type detection.")

    def _appendix_style(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_mixed_appendix.pdf"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            pages = [
                {"type": "native", "title": "Software Requirements Specification v2.1",
                 "lines": ["Project: Inventory Management System", "Version: 2.1",
                            "Date: March 2024", "", "1. INTRODUCTION",
                            "This document specifies functional and non-functional",
                            "requirements for the inventory management system (IMS).",
                            "It is intended for developers, QA, and stakeholders."]},
                {"type": "native", "title": "2. Functional Requirements",
                 "lines": ["FR-001: System shall support real-time inventory tracking",
                            "FR-002: System shall generate reorder alerts at configurable thresholds",
                            "FR-003: System shall integrate with ERP via REST API",
                            "FR-004: System shall support barcode and RFID scanning",
                            "FR-005: System shall produce audit trail for all transactions"]},
                {"type": "native", "title": "3. Non-Functional Requirements",
                 "lines": ["NFR-001: Response time < 200ms for 95th percentile",
                            "NFR-002: Availability > 99.9% excluding maintenance windows",
                            "NFR-003: Support 500 concurrent users",
                            "NFR-004: Data encryption at rest and in transit (AES-256)",
                            "NFR-005: Comply with SOC 2 Type II controls"]},
                {"type": "native", "title": "4. System Architecture",
                 "lines": ["The system follows a microservices architecture with:",
                            "- API Gateway: Kong",
                            "- Services: Node.js / FastAPI",
                            "- Database: PostgreSQL 15 with read replicas",
                            "- Cache: Redis Cluster",
                            "- Message Queue: Apache Kafka",
                            "- Container Orchestration: Kubernetes (EKS)"]},
                {"type": "native", "title": "5. Data Model Overview",
                 "lines": ["Core entities: Product, Location, Transaction, Supplier, Order",
                            "Relationships documented in Appendix A (ER diagram — scanned)."]},
                {"type": "scanned", "lines": ["APPENDIX A — ENTITY RELATIONSHIP DIAGRAM",
                                              "(Hand-drawn diagram — scanned attachment)",
                                              "", "Product --< Transaction >-- Location",
                                              "Product >-- Supplier", "Product --< OrderItem >-- Order",
                                              "", "[See original diagram in project wiki]"]},
                {"type": "scanned", "lines": ["APPENDIX B — STAKEHOLDER SIGN-OFF",
                                              "", "Product Owner: ____________  Date: _______",
                                              "Tech Lead: ________________  Date: _______",
                                              "QA Lead: __________________  Date: _______",
                                              "Security Review: ___________  Date: _______"]},
            ]
            self._build_mixed_pdf(out / filename, pages)
        return self._entry(filename, "medium",
                           ["pdf-mixed", "appendix-scanned", "software-spec", "5-native-2-scanned"],
                           True, "Mixed PDF: 5 native pages (software spec) + 2 scanned appendix pages.")
