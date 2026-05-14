"""
Merges ScopusAuthorIDs from the 2025 Excel sheet into the 2026 scraped CSVs.

For each faculty in the new CSV:
  1. Exact name match  → copy Scopus ID directly
  2. Fuzzy name match  → copy if similarity is high enough, flag for review
  3. No match found    → leave blank, print for manual lookup

Usage (standalone):
  python merge.py                          # process all CSVs in output/
  python merge.py --index 01              # process one university
"""

import argparse
import csv
import json
import os
from pathlib import Path

import openpyxl

EXCEL_PATH  = Path(__file__).parent / "2025 Faculty List With SCOPUS IDs.xlsx"
OUTPUT_DIR  = Path(__file__).parent / "output"
CONFIG_PATH = Path(__file__).parent / "config" / "universities.json"

FUZZY_THRESHOLD = 0.82  # similarity score to auto-accept a fuzzy match


# ---------------------------------------------------------------------------
# Simple name similarity (no external library needed)
# ---------------------------------------------------------------------------
def normalize(name: str) -> str:
    return name.lower().strip()


def similarity(a: str, b: str) -> float:
    """Jaccard similarity on character bigrams."""
    def bigrams(s):
        s = normalize(s)
        return set(s[i:i+2] for i in range(len(s) - 1))
    ba, bb = bigrams(a), bigrams(b)
    if not ba or not bb:
        return 0.0
    return len(ba & bb) / len(ba | bb)


# ---------------------------------------------------------------------------
# Load 2025 Scopus IDs: {university_index: {full_name: scopus_id}}
# ---------------------------------------------------------------------------
def load_2025_scopus() -> dict[str, dict[str, int]]:
    wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)
    ws = wb["2025 Master Copy"]
    data: dict[str, dict[str, int]] = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        univ_idx, scopus_id, name = row[1], row[3], row[4]
        if univ_idx and name and scopus_id and str(scopus_id).strip() not in ("", "N/A"):
            data.setdefault(str(univ_idx), {})[str(name)] = scopus_id
    return data


# ---------------------------------------------------------------------------
# Match and merge for one CSV file
# ---------------------------------------------------------------------------
def merge(csv_path: Path, scopus_by_name: dict[str, int]):
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    fieldnames = list(rows[0].keys()) if rows else []
    if "scopus_id" not in fieldnames:
        fieldnames = ["scopus_id"] + fieldnames

    exact = fuzzy = missing = 0
    needs_review = []
    needs_lookup = []

    for row in rows:
        name = row["name"]

        # 1. Exact match
        if name in scopus_by_name:
            row["scopus_id"] = int(float(scopus_by_name[name]))
            exact += 1
            continue

        # 2. Fuzzy match
        best_score, best_name = 0.0, ""
        for candidate in scopus_by_name:
            s = similarity(name, candidate)
            if s > best_score:
                best_score, best_name = s, candidate

        if best_score >= FUZZY_THRESHOLD:
            row["scopus_id"] = int(scopus_by_name[best_name])
            fuzzy += 1
            needs_review.append((name, best_name, round(best_score, 2), row["scopus_id"]))
        else:
            row["scopus_id"] = ""
            missing += 1
            needs_lookup.append(name)

    # Write enriched CSV back
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Exact matches:  {exact}")
    print(f"  Fuzzy matches:  {fuzzy}")
    print(f"  Missing (new):  {missing}")

    if needs_review:
        print(f"\n  Fuzzy matches — please verify these:")
        print(f"  {'2026 name':<35s} {'matched to (2025)':<35s} {'score':>5}  {'scopus_id'}")
        for new, old, score, sid in needs_review:
            print(f"  {new:<35s} {old:<35s} {score:>5}  {sid}")

    if needs_lookup:
        print(f"\n  New faculty — Scopus ID needed (look up at scopus.com):")
        for n in needs_lookup:
            print(f"    {n}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def run(indexes: list[str] | None = None):
    print("Loading 2025 Scopus IDs...")
    all_scopus = load_2025_scopus()

    with open(CONFIG_PATH, encoding="utf-8") as f:
        universities = json.load(f)["universities"]

    if indexes:
        universities = [u for u in universities if u["index"] in indexes]

    for univ in universities:
        idx = univ["index"]
        safe_name = univ["name"].replace(" ", "_").replace("/", "-")[:40]
        csv_path = OUTPUT_DIR / f"{idx}_{safe_name}.csv"

        if not csv_path.exists():
            print(f"\n[{idx}] {univ['name']} — CSV not found, run main.py first")
            continue

        scopus_by_name = all_scopus.get(idx, {})
        print(f"\n[{idx}] {univ['name']} — {len(scopus_by_name)} names in 2025 sheet")
        merge(csv_path, scopus_by_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", nargs="+", metavar="IDX")
    args = parser.parse_args()
    run(indexes=args.index)
