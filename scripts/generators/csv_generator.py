"""Generate synthetic CSV test files."""

import csv
import io
from pathlib import Path

from generators.base import BaseGenerator


class CsvGenerator(BaseGenerator):
    category = "csv"

    def generate(self, dry_run: bool = False) -> list[dict]:
        out = self.output_dir()
        if not dry_run:
            out.mkdir(parents=True, exist_ok=True)

        entries = []

        # 1. Simple comma-separated, ASCII, 20 rows x 5 cols
        entries.append(self._simple_comma(out, dry_run))

        # 2. UTF-8 BOM encoding with international characters
        entries.append(self._utf8_bom(out, dry_run))

        # 3. Semicolon-delimited (European style)
        entries.append(self._semicolon(out, dry_run))

        # 4. Tab-delimited (TSV with .csv extension)
        entries.append(self._tab_delimited(out, dry_run))

        # 5. Quoted fields containing commas and newlines
        entries.append(self._quoted_fields(out, dry_run))

        # 6. Very wide: 100 columns, 500 rows
        entries.append(self._wide_sheet(out, dry_run))

        return entries

    # ------------------------------------------------------------------
    def _simple_comma(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_simple_comma.csv"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            rows = [["id", "name", "department", "salary", "start_date"]]
            people = [
                ("Alice Johnson", "Engineering", 95000, "2021-03-15"),
                ("Bob Smith", "Marketing", 72000, "2019-07-01"),
                ("Carol White", "Finance", 88000, "2020-11-20"),
                ("David Brown", "Engineering", 102000, "2018-04-10"),
                ("Eve Davis", "HR", 65000, "2022-01-08"),
            ]
            for i in range(1, 21):
                p = people[(i - 1) % len(people)]
                rows.append([i, p[0], p[1], p[2] + i * 500, p[3]])
            self._write_csv(out / filename, rows, encoding="utf-8")
        return self._entry(filename, "easy",
                           ["csv", "comma-separated", "ascii", "tabular-data"],
                           False, "Simple comma-separated file, 20 rows x 5 columns, ASCII only.")

    def _utf8_bom(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_utf8_bom.csv"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            rows = [
                ["country", "capital", "population_m", "currency"],
                ["Germany", "Berlin", 83.2, "Euro €"],
                ["Japan", "Tōkyō", 125.7, "Yen ¥"],
                ["France", "Paris", 67.4, "Euro €"],
                ["Brazil", "Brasília", 214.3, "Real R$"],
                ["Russia", "Москва", 144.1, "Ruble ₽"],
                ["China", "北京", 1412.0, "Yuan ¥"],
                ["Egypt", "القاهرة", 102.3, "Pound £"],
                ["India", "नई दिल्ली", 1380.0, "Rupee ₹"],
            ]
            self._write_csv(out / filename, rows, encoding="utf-8-sig")
        return self._entry(filename, "medium",
                           ["csv", "utf8-bom", "international-characters", "unicode"],
                           False, "UTF-8 BOM encoded CSV with international characters and currency symbols.")

    def _semicolon(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_semicolon_delimited.csv"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            rows = [
                ["Artikelnummer", "Beschreibung", "Preis (€)", "Menge", "Lager"],
                ["A001", "Schreibtisch", "299,99", 15, "Berlin"],
                ["A002", "Bürostuhl", "149,50", 42, "München"],
                ["A003", "Aktenschrank", "189,00", 8, "Hamburg"],
                ["A004", "Whiteboard", "89,95", 20, "Frankfurt"],
                ["A005", "Tischlampe", "45,00", 67, "Berlin"],
            ]
            self._write_csv(out / filename, rows, encoding="utf-8", delimiter=";")
        return self._entry(filename, "medium",
                           ["csv", "semicolon-delimited", "european-format", "german"],
                           False, "Semicolon-delimited CSV in European format with German content and comma decimal separators.")

    def _tab_delimited(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_tab_delimited.csv"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            rows = [
                ["gene_id", "symbol", "chromosome", "start_bp", "end_bp", "strand"],
                ["ENSG00000139618", "BRCA2", "13", 32315086, 32400266, "+"],
                ["ENSG00000012048", "BRCA1", "17", 41196312, 41277500, "-"],
                ["ENSG00000141510", "TP53", "17", 7661779, 7687550, "-"],
                ["ENSG00000134323", "MYCN", "2", 15940550, 15947007, "+"],
                ["ENSG00000146648", "EGFR", "7", 55019017, 55211628, "+"],
                ["ENSG00000157764", "BRAF", "7", 140719327, 140924764, "-"],
            ]
            self._write_csv(out / filename, rows, encoding="utf-8", delimiter="\t")
        return self._entry(filename, "easy",
                           ["csv", "tab-delimited", "tsv", "genomics-data"],
                           False, "Tab-delimited file (.csv extension) with genomic coordinate data.")

    def _quoted_fields(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_quoted_fields.csv"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            content = (
                'id,title,description,tags,price\n'
                '1,"Widget, Standard","A basic widget, suitable for most uses.","tools,hardware",9.99\n'
                '2,"Gadget Pro","Multi-line description:\nLine 1: High performance.\nLine 2: Durable build.","gadgets,pro",49.99\n'
                '3,"Kit ""Deluxe""","Contains 5 pieces: nuts, bolts, washers, screws, and a wrench.","kits,hardware",24.50\n'
                '4,"Service Pack","Includes:\n- Installation\n- Training\n- 1-year support","services",299.00\n'
                '5,"Combo, Special","Pairs well with item #1, #2, or #3.","bundles,sale",79.95\n'
            )
            (out / filename).write_text(content, encoding="utf-8")
        return self._entry(filename, "medium",
                           ["csv", "quoted-fields", "embedded-commas", "embedded-newlines"],
                           False, "CSV with quoted fields containing commas, embedded newlines, and escaped quotes.")

    def _wide_sheet(self, out: Path, dry_run: bool) -> dict:
        filename = "syn_wide_100cols.csv"
        if dry_run:
            print(f"  [dry-run] would create {self.category}/{filename}")
        else:
            headers = ["record_id"] + [f"metric_{i:03d}" for i in range(1, 100)]
            rows = [headers]
            for r in range(1, 501):
                row = [r] + [round((r * i * 0.01) % 1000, 2) for i in range(1, 100)]
                rows.append(row)
            self._write_csv(out / filename, rows, encoding="utf-8")
        return self._entry(filename, "hard",
                           ["csv", "wide-format", "100-columns", "500-rows", "numeric-data"],
                           False, "Very wide CSV: 100 columns x 500 rows of numeric metric data.")

    @staticmethod
    def _write_csv(path: Path, rows: list, encoding: str, delimiter: str = ",") -> None:
        buf = io.StringIO()
        writer = csv.writer(buf, delimiter=delimiter)
        writer.writerows(rows)
        path.write_text(buf.getvalue(), encoding=encoding)
