"""
Compares 2026_master.csv against 2025 Faculty List With SCOPUS IDs.xlsx.
Produces output/2026_master.xlsx with two sheets:
  - "2026 Master"  : all 2026 faculty data
  - "comparison"   : faculty present in one year but not the other

Matching key: normalized full name + normalized university base name.
"""

import csv
import re
from pathlib import Path

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

BASE_DIR   = Path(__file__).parent
EXCEL_2025 = BASE_DIR / "2025 Faculty List With SCOPUS IDs.xlsx"
CSV_2026   = BASE_DIR / "output" / "2026_master.csv"
OUT_XLSX   = BASE_DIR / "output" / "2026_master.xlsx"

COMPARISON_COLS = [
    "status", "scopus_id", "name", "first_name", "last_name",
    "original_title", "department", "area", "university", "rank",
]


def norm_name(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower().strip())


def norm_univ(s: str) -> str:
    """Strip school/college suffix in parentheses, lowercase, strip."""
    base = re.sub(r"\s*\(.*", "", s or "")
    return base.lower().strip()


def load_2025() -> dict[tuple, dict]:
    wb = openpyxl.load_workbook(EXCEL_2025, read_only=True, data_only=True)
    ws = wb["2025 Master Copy"]
    faculty = {}
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            continue
        raw_sid = str(row[3]).strip() if row[3] is not None else ""
        try:
            scopus_id = str(int(float(raw_sid))) if raw_sid and raw_sid not in ("None", "N/A", "") else ""
        except (ValueError, OverflowError):
            scopus_id = raw_sid
        full_name    = str(row[4] or "").strip()
        original_title = str(row[5] or "").strip()
        university   = str(row[6] or "").strip()
        department   = str(row[7] or "").strip()  # OriginalArea used as dept
        first_name   = str(row[8] or "").strip()
        last_name    = str(row[9] or "").strip()
        rank         = str(row[10] or "").strip()
        if not full_name:
            continue
        key = (norm_name(full_name), norm_univ(university))
        faculty[key] = {
            "scopus_id":     scopus_id,
            "name":          full_name,
            "first_name":    first_name,
            "last_name":     last_name,
            "original_title": original_title,
            "department":    department,
            "area":          department,  # 2025 has no separate area col
            "university":    university,
            "rank":          rank,
        }
    wb.close()
    return faculty


def load_2026() -> tuple[list[dict], dict[tuple, dict]]:
    rows = []
    index = {}
    with open(CSV_2026, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
            key = (norm_name(row["name"]), norm_univ(row["university"]))
            index[key] = row
    return rows, index


def style_header(ws, row_num: int, ncols: int, fill_hex: str):
    fill = PatternFill("solid", fgColor=fill_hex)
    for col in range(1, ncols + 1):
        cell = ws.cell(row=row_num, column=col)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = fill
        cell.alignment = Alignment(horizontal="center")


def write_xlsx(rows_2026: list[dict], comparison_rows: list[dict]):
    wb = openpyxl.Workbook()

    # ── Sheet 1: 2026 Master ─────────────────────────────────────────────────
    ws1 = wb.active
    ws1.title = "2026 Master"
    master_cols = ["scopus_id", "name", "first_name", "last_name",
                   "original_title", "department", "area", "university",
                   "email", "rank"]
    ws1.append(master_cols)
    style_header(ws1, 1, len(master_cols), "2E75B6")
    for r in rows_2026:
        ws1.append([r.get(c, "") for c in master_cols])

    # ── Sheet 2: comparison ──────────────────────────────────────────────────
    ws2 = wb.create_sheet("comparison")
    ws2.append(COMPARISON_COLS)
    style_header(ws2, 1, len(COMPARISON_COLS), "70AD47")

    green_fill = PatternFill("solid", fgColor="E2EFDA")  # new in 2026
    red_fill   = PatternFill("solid", fgColor="FCE4D6")  # left / not in 2026

    for r in comparison_rows:
        ws2.append([r.get(c, "") for c in COMPARISON_COLS])
        row_idx = ws2.max_row
        fill = green_fill if r["status"] == "New in 2026" else red_fill
        for col in range(1, len(COMPARISON_COLS) + 1):
            ws2.cell(row=row_idx, column=col).fill = fill

    # Auto-width (approximate) for both sheets
    for ws in [ws1, ws2]:
        for col_cells in ws.columns:
            max_len = max((len(str(c.value or "")) for c in col_cells), default=10)
            ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 2, 50)

    wb.save(OUT_XLSX)
    print(f"Saved → {OUT_XLSX}")


def main():
    print("Loading 2025 data...")
    faculty_2025 = load_2025()
    print(f"  {len(faculty_2025)} faculty in 2025")

    print("Loading 2026 data...")
    rows_2026, faculty_2026 = load_2026()
    print(f"  {len(rows_2026)} faculty in 2026")

    # New in 2026 (in 2026 but not 2025)
    new_in_2026 = []
    for key, row in faculty_2026.items():
        if key not in faculty_2025:
            new_in_2026.append({"status": "New in 2026", **row})

    # Left / not in 2026 (in 2025 but not 2026)
    not_in_2026 = []
    for key, row in faculty_2025.items():
        if key not in faculty_2026:
            not_in_2026.append({"status": "Not in 2026", **row})

    # Sort each group by university then last name
    new_in_2026.sort(key=lambda r: (r["university"], r["last_name"]))
    not_in_2026.sort(key=lambda r: (r["university"], r["last_name"]))

    comparison_rows = new_in_2026 + not_in_2026

    print(f"\nNew in 2026 (not in 2025): {len(new_in_2026)}")
    print(f"Not in 2026 (was in 2025): {len(not_in_2026)}")
    print(f"Total comparison rows:     {len(comparison_rows)}")

    print("\nWriting Excel file...")
    write_xlsx(rows_2026, comparison_rows)


if __name__ == "__main__":
    main()
