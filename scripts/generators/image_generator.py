"""Generate synthetic image test files using Pillow."""

import random
from pathlib import Path

from generators.base import BaseGenerator

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    _PILLOW_OK = True
except ImportError:
    _PILLOW_OK = False


def _require_pillow() -> None:
    if not _PILLOW_OK:
        raise ImportError("Pillow is required: uv add pillow")


# Reusable helpers
def _get_font(size: int) -> "ImageFont.FreeTypeFont | ImageFont.ImageFont":
    """Return a font at the given size, falling back to default."""
    try:
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
    except Exception:
        pass
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except Exception:
        pass
    return ImageFont.load_default()


def _new_white(w: int, h: int) -> "Image.Image":
    return Image.new("RGB", (w, h), color=(255, 255, 255))


class ImageGenerator(BaseGenerator):
    category = "images"

    def generate(self, dry_run: bool = False) -> list[dict]:
        _require_pillow()
        out = self.output_dir()
        if not dry_run:
            out.mkdir(parents=True, exist_ok=True)

        entries = []
        entries.append(self._clean_text(out, dry_run))
        entries.append(self._invoice_layout(out, dry_run))
        entries.append(self._two_column(out, dry_run))
        entries.append(self._rotated_text(out, dry_run))
        entries.append(self._low_res(out, dry_run))
        entries.append(self._multilingual(out, dry_run))
        return entries

    # ------------------------------------------------------------------
    def _clean_text(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_clean_text.png"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            img = _new_white(1200, 1600)
            draw = ImageDraw.Draw(img)
            title_font = _get_font(48)
            body_font = _get_font(28)
            draw.text((80, 80), "Technical Report: System Analysis", font=title_font, fill=(0, 0, 0))
            draw.line([(80, 145), (1120, 145)], fill=(0, 0, 0), width=2)
            y = 180
            paragraphs = [
                "1. Executive Summary",
                "This report presents a comprehensive analysis of the system's\n"
                "performance characteristics. The evaluation covers throughput,\n"
                "latency, resource utilization, and reliability metrics.",
                "2. Methodology",
                "Testing was conducted over a 30-day period using standardized\n"
                "benchmarks. All measurements were taken at peak load conditions\n"
                "to ensure worst-case performance data was captured.",
                "3. Results",
                "The system achieved 99.95% uptime during the evaluation period.\n"
                "Average response time was 42ms, well within the 100ms SLA target.\n"
                "Peak throughput reached 15,000 requests per second.",
                "4. Conclusions",
                "Based on the analysis, the system meets all performance\n"
                "requirements. Recommended optimizations are detailed in Appendix A.",
            ]
            for para in paragraphs:
                is_heading = para[0].isdigit() and para[1] == "."
                font = title_font if is_heading else body_font
                color = (20, 20, 120) if is_heading else (0, 0, 0)
                draw.text((80, y), para, font=font, fill=color)
                lines = para.count("\n") + 1
                line_h = 52 if is_heading else 36
                y += lines * line_h + (20 if is_heading else 30)
            img.save(out / filename, dpi=(300, 300))
        return self._entry(filename, "easy",
                           ["png", "clean-text", "300dpi", "structured-report", "ocr-required"],
                           True, "Clean 300 DPI image of a structured text report — easy OCR baseline.")

    def _invoice_layout(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_invoice_layout.png"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            img = _new_white(1400, 1800)
            draw = ImageDraw.Draw(img)
            big = _get_font(52)
            med = _get_font(30)
            sm = _get_font(24)

            # Header
            draw.rectangle([(0, 0), (1400, 130)], fill=(30, 60, 120))
            draw.text((60, 35), "INVOICE", font=big, fill=(255, 255, 255))
            draw.text((900, 40), "Invoice #: INV-2024-00892", font=sm, fill=(200, 220, 255))
            draw.text((900, 75), "Date: March 15, 2024", font=sm, fill=(200, 220, 255))

            # Bill to
            draw.text((60, 160), "Bill To:", font=med, fill=(60, 60, 60))
            draw.text((60, 200), "Acme Corporation", font=med, fill=(0, 0, 0))
            draw.text((60, 235), "123 Business Park, Suite 400", font=sm, fill=(80, 80, 80))
            draw.text((60, 265), "Chicago, IL 60601", font=sm, fill=(80, 80, 80))

            # Table header
            y_table = 360
            cols = [60, 500, 700, 950, 1200]
            draw.rectangle([(50, y_table), (1350, y_table + 45)], fill=(220, 230, 245))
            for label, x in zip(["Description", "Qty", "Unit Price", "Discount", "Total"], cols):
                draw.text((x, y_table + 10), label, font=sm, fill=(30, 60, 120))

            # Table rows
            items = [
                ("Enterprise License (annual)", "1", "$12,000.00", "10%", "$10,800.00"),
                ("Professional Services - Setup", "8 hrs", "$200.00/hr", "0%", "$1,600.00"),
                ("Training Workshop (remote)", "2 days", "$1,500.00/day", "0%", "$3,000.00"),
                ("Support Package (12 months)", "1", "$2,400.00", "15%", "$2,040.00"),
                ("Custom Integration Module", "1", "$4,500.00", "0%", "$4,500.00"),
            ]
            for i, (desc, qty, unit, disc, total) in enumerate(items):
                y_row = y_table + 50 + i * 50
                bg = (250, 250, 250) if i % 2 == 0 else (240, 245, 255)
                draw.rectangle([(50, y_row), (1350, y_row + 45)], fill=bg)
                draw.text((cols[0], y_row + 10), desc, font=sm, fill=(0, 0, 0))
                draw.text((cols[1], y_row + 10), qty, font=sm, fill=(0, 0, 0))
                draw.text((cols[2], y_row + 10), unit, font=sm, fill=(0, 0, 0))
                draw.text((cols[3], y_row + 10), disc, font=sm, fill=(0, 0, 0))
                draw.text((cols[4], y_row + 10), total, font=sm, fill=(0, 0, 0))

            # Totals
            y_tot = y_table + 350
            draw.line([(700, y_tot), (1350, y_tot)], fill=(100, 100, 100), width=1)
            draw.text((900, y_tot + 10), "Subtotal:", font=sm, fill=(60, 60, 60))
            draw.text((1200, y_tot + 10), "$21,940.00", font=sm, fill=(0, 0, 0))
            draw.text((900, y_tot + 45), "Tax (8.5%):", font=sm, fill=(60, 60, 60))
            draw.text((1200, y_tot + 45), "$1,864.90", font=sm, fill=(0, 0, 0))
            draw.rectangle([(880, y_tot + 90), (1350, y_tot + 135)], fill=(30, 60, 120))
            draw.text((900, y_tot + 100), "TOTAL DUE:", font=med, fill=(255, 255, 255))
            draw.text((1130, y_tot + 100), "$23,804.90", font=med, fill=(255, 255, 200))

            img.save(out / filename, dpi=(200, 200))
        return self._entry(filename, "medium",
                           ["png", "invoice", "table-layout", "structured", "ocr-required"],
                           True, "Invoice image with header, itemized table, and totals section — tests table OCR.")

    def _two_column(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_two_column_text.png"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            img = _new_white(1600, 2000)
            draw = ImageDraw.Draw(img)
            title_f = _get_font(44)
            body_f = _get_font(24)

            draw.text((80, 60), "Quarterly Market Analysis — Q1 2024", font=title_f, fill=(0, 0, 0))
            draw.line([(80, 120), (1520, 120)], fill=(0, 0, 0), width=2)
            draw.line([(800, 140), (800, 1960)], fill=(180, 180, 180), width=1)

            left_text = [
                "Market Overview",
                "Global equity markets delivered mixed\n"
                "results in Q1 2024. The S&P 500 gained\n"
                "10.2%, while European indices lagged\n"
                "behind due to ongoing geopolitical\n"
                "uncertainty and energy price pressures.",
                "Technology Sector",
                "Semiconductor stocks led gains, driven\n"
                "by strong AI-related demand. NVIDIA\n"
                "reported record quarterly revenues of\n"
                "$22.1B, a 265% year-over-year increase.\n"
                "Cloud infrastructure spending rose 28%.",
                "Fixed Income",
                "The 10-year Treasury yield rose to 4.35%\n"
                "as the Federal Reserve signaled fewer\n"
                "rate cuts than markets had anticipated.\n"
                "High-yield spreads tightened modestly.",
            ]
            right_text = [
                "Emerging Markets",
                "India emerged as the top-performing\n"
                "major market, with the Nifty 50 up 3.1%.\n"
                "China's CSI 300 fell 2.4% amid continued\n"
                "property sector concerns and deflation\n"
                "fears despite stimulus announcements.",
                "Commodities",
                "Gold surged to record highs above\n"
                "$2,200/oz, supported by central bank\n"
                "buying and safe-haven demand. Oil prices\n"
                "rose 12% to $85/barrel on OPEC+ supply\n"
                "discipline and Middle East tensions.",
                "Outlook",
                "Q2 2024 outlook remains cautiously\n"
                "optimistic. Key risks include persistent\n"
                "inflation, delayed rate cuts, and\n"
                "geopolitical escalations. Investors\n"
                "should focus on quality and diversification.",
            ]

            def draw_column(texts, x_start):
                y = 150
                for t in texts:
                    is_h = not t[0].islower() and len(t) < 40 and "\n" not in t
                    font = title_f if is_h else body_f
                    color = (20, 20, 150) if is_h else (0, 0, 0)
                    draw.text((x_start, y), t, font=font, fill=color)
                    lines = t.count("\n") + 1
                    y += lines * (50 if is_h else 30) + (15 if is_h else 10)

            draw_column(left_text, 80)
            draw_column(right_text, 830)
            img.save(out / filename, dpi=(200, 200))
        return self._entry(filename, "medium",
                           ["png", "two-column", "newspaper-layout", "ocr-required"],
                           True, "Two-column newspaper-style layout — tests column detection in OCR.")

    def _rotated_text(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_rotated_90deg.png"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            # Create normal text first, then rotate 90 degrees
            img = _new_white(1200, 900)
            draw = ImageDraw.Draw(img)
            font = _get_font(32)
            lines = [
                "CONFIDENTIAL DOCUMENT — ROTATED SCAN",
                "",
                "Patient ID: 78432-A",
                "Date of Service: February 14, 2024",
                "Physician: Dr. Sarah Mitchell",
                "",
                "Diagnosis: Routine annual examination",
                "Blood pressure: 118/76 mmHg",
                "Heart rate: 72 bpm",
                "Weight: 168 lbs  Height: 5'9\"",
                "",
                "Next appointment: May 14, 2024",
            ]
            y = 60
            for line in lines:
                draw.text((60, y), line, font=font, fill=(0, 0, 0))
                y += 52
            rotated = img.rotate(90, expand=True)
            rotated.save(out / filename, dpi=(200, 200))
        return self._entry(filename, "hard",
                           ["png", "rotated-90", "scan-artifact", "ocr-required"],
                           True, "Text rotated 90 degrees — simulates a page fed sideways into a scanner.")

    def _low_res(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_low_res_100dpi.png"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            # Create at normal resolution then downscale to simulate low DPI
            img_hi = _new_white(2400, 1800)
            draw = ImageDraw.Draw(img_hi)
            font = _get_font(72)
            sm = _get_font(50)
            draw.text((120, 80), "MEMORANDUM", font=font, fill=(0, 0, 0))
            draw.line([(120, 175), (2280, 175)], fill=(0, 0, 0), width=3)
            draw.text((120, 210), "TO:      All Department Heads", font=sm, fill=(0, 0, 0))
            draw.text((120, 275), "FROM:    Office of the Director", font=sm, fill=(0, 0, 0))
            draw.text((120, 340), "DATE:    January 10, 2024", font=sm, fill=(0, 0, 0))
            draw.text((120, 405), "RE:      Updated Travel Policy", font=sm, fill=(0, 0, 0))
            draw.line([(120, 460), (2280, 460)], fill=(0, 0, 0), width=2)
            body = [
                "Effective February 1, 2024, the company travel policy will be updated.",
                "Key changes include: (1) Economy class required for flights under 4 hours.",
                "(2) Hotel per diem increased to $175/night in Tier 1 cities.",
                "(3) All travel over $2,000 requires VP approval prior to booking.",
                "Please review the full policy document on the intranet portal.",
            ]
            y = 500
            for line in body:
                draw.text((120, y), line, font=sm, fill=(0, 0, 0))
                y += 85

            # Downscale to low-res equivalent (800 x 600 ~ 100 DPI for letter)
            img_lo = img_hi.resize((800, 600), Image.LANCZOS)
            # Add slight noise to simulate scan degradation
            import random as rng
            pixels = img_lo.load()
            for _ in range(2000):
                x = rng.randint(0, 799)
                y_px = rng.randint(0, 599)
                v = rng.randint(180, 220)
                pixels[x, y_px] = (v, v, v)
            img_lo.save(out / filename, dpi=(100, 100))
        return self._entry(filename, "hard",
                           ["png", "low-res", "100dpi", "noisy-scan", "ocr-required"],
                           True, "Low-resolution (100 DPI) scan simulation with noise — tests OCR on degraded images.")

    def _multilingual(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_multilingual.png"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            img = _new_white(1400, 1600)
            draw = ImageDraw.Draw(img)
            # Use default font since custom fonts with full Unicode are hard to guarantee
            font_lg = _get_font(40)
            font_sm = _get_font(28)

            sections = [
                ("English", "Hello! This is a multilingual test document.", font_lg),
                ("", "It contains text in several different languages.", font_sm),
                ("", "", None),
                ("Spanish", "Hola! Este es un documento de prueba multilingüe.", font_lg),
                ("", "Contiene texto en varios idiomas diferentes.", font_sm),
                ("", "", None),
                ("French", "Bonjour! Ceci est un document de test multilingue.", font_lg),
                ("", "Il contient du texte en plusieurs langues.", font_sm),
                ("", "", None),
                ("German", "Hallo! Dies ist ein mehrsprachiges Testdokument.", font_lg),
                ("", "Es enthält Text in verschiedenen Sprachen.", font_sm),
                ("", "", None),
                ("Portuguese", "Olá! Este é um documento de teste multilíngue.", font_lg),
                ("", "Ele contém texto em vários idiomas diferentes.", font_sm),
                ("", "", None),
                ("Numbers", "42 × 3.14 = 131.88   |   100% ≥ 99.9%", font_sm),
                ("", "€1,234.56  •  $9,876.54  •  ¥123,456", font_sm),
            ]

            y = 60
            for label, text, font in sections:
                if font is None:
                    y += 20
                    continue
                if label:
                    draw.text((60, y), f"[{label}]", font=_get_font(30), fill=(100, 100, 200))
                    y += 42
                draw.text((60, y), text, font=font, fill=(0, 0, 0))
                y += 55 if font == font_lg else 42

            img.save(out / filename, dpi=(200, 200))
        return self._entry(filename, "hard",
                           ["png", "multilingual", "unicode", "latin-script", "ocr-required"],
                           True, "Image with text in English, Spanish, French, German, Portuguese — tests multilingual OCR.")
