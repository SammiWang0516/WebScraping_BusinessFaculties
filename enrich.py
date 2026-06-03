"""
Looks up ScopusAuthorIDs for faculty rows that have no scopus_id yet.
Calls the Scopus Author Search API with first name + last name + affiliation.

Results:
  - 1 match found   → auto-filled
  - Multiple matches → printed for manual review
  - 0 matches        → flagged as not found

Usage (standalone):
  python enrich.py                        # process all CSVs in output/
  python enrich.py --index 01            # one university
"""

import argparse
import csv
import json
import os
import time
from pathlib import Path

import requests

CONFIG_PATH = Path(__file__).parent / "config" / "universities.json"
OUTPUT_DIR  = Path(__file__).parent / "output"
SCOPUS_URL  = "https://api.elsevier.com/content/search/author"


class QuotaExhaustedError(Exception):
    pass


# ---------------------------------------------------------------------------
# Load API key from environment (set in .venv/bin/activate)
# ---------------------------------------------------------------------------
def load_api_key() -> str:
    key = os.environ.get("SCOPUS_API_KEY", "")
    if not key:
        raise RuntimeError(
            "SCOPUS_API_KEY not found. Make sure your .venv is activated: "
            "source .venv/bin/activate"
        )
    return key


# ---------------------------------------------------------------------------
# Scopus Author Search
# ---------------------------------------------------------------------------
def search_author(first: str, last: str, affiliation: str, api_key: str) -> list[dict]:
    query = f'AUTHFIRST("{first}") AND AUTHLAST("{last}") AND AFFIL("{affiliation}")'
    params = {"query": query, "count": 5, "field": "identifier,preferred-name,affiliation-current"}
    headers = {"X-ELS-APIKey": api_key, "Accept": "application/json"}

    try:
        resp = requests.get(SCOPUS_URL, params=params, headers=headers, timeout=15)
        if resp.status_code == 429:
            raise QuotaExhaustedError()
        resp.raise_for_status()
        data = resp.json()
        entries = data.get("search-results", {}).get("entry", [])
        if entries and "error" in entries[0]:
            return []
        return entries
    except requests.RequestException as e:
        print(f"    API error for {first} {last}: {e}")
        return []


def parse_author_id(entry: dict) -> str:
    raw = entry.get("dc:identifier", "")
    return raw.replace("AUTHOR_ID:", "").strip()


def parse_affil(entry: dict) -> str:
    affil = entry.get("affiliation-current", {})
    if isinstance(affil, list):
        affil = affil[0] if affil else {}
    return affil.get("affiliation-name", "")


def parse_display_name(entry: dict) -> str:
    pn = entry.get("preferred-name", {})
    return f"{pn.get('given-name', '')} {pn.get('surname', '')}".strip()


# ---------------------------------------------------------------------------
# Process one CSV
# ---------------------------------------------------------------------------
def enrich(csv_path: Path, affiliation: str, api_key: str):
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    fieldnames = list(rows[0].keys()) if rows else []
    missing = [r for r in rows if not r.get("scopus_id")]

    if not missing:
        print("  All rows already have Scopus IDs — nothing to do.")
        return

    print(f"  Looking up {len(missing)} faculty without Scopus ID...")

    auto_filled = 0
    multi_match = []
    not_found   = []

    for row in missing:
        first = row["first_name"]
        last  = row["last_name"]
        entries = search_author(first, last, affiliation, api_key)

        if len(entries) == 1:
            row["scopus_id"] = parse_author_id(entries[0])
            auto_filled += 1

        elif len(entries) > 1:
            candidates = [
                (parse_author_id(e), parse_display_name(e), parse_affil(e))
                for e in entries
            ]
            multi_match.append((row["name"], candidates))

        else:
            not_found.append(row["name"])

        time.sleep(1.0)  # stay within API rate limit

    # Write updated CSV (partial progress saved even if quota hits later)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Auto-filled:    {auto_filled}")
    print(f"  Multiple hits:  {len(multi_match)} (pick manually below)")
    print(f"  Not found:      {len(not_found)}")

    if multi_match:
        print(f"\n  --- Multiple candidates — open the CSV and fill scopus_id manually ---")
        for name, candidates in multi_match:
            print(f"\n  Faculty: {name}")
            for sid, dname, aff in candidates:
                print(f"    ID={sid:>15s}  name={dname:<30s}  affil={aff}")

    if not_found:
        print(f"\n  --- Not found in Scopus (may have no publications yet) ---")
        for n in not_found:
            print(f"    {n}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def run(indexes: list[str] | None = None):
    api_key = load_api_key()

    with open(CONFIG_PATH, encoding="utf-8") as f:
        universities = json.load(f)["universities"]

    if indexes:
        universities = [u for u in universities if u["index"] in indexes]

    for univ in universities:
        idx       = univ["index"]
        safe_name = univ["name"].replace(" ", "_").replace("/", "-")[:40]
        csv_path  = OUTPUT_DIR / f"{idx}_{safe_name}.csv"

        if not csv_path.exists():
            print(f"\n[{idx}] {univ['name']} — CSV not found, run main.py first")
            continue

        print(f"\n[{idx}] {univ['name']}")
        try:
            enrich(csv_path, affiliation=univ["name"], api_key=api_key)
        except QuotaExhaustedError:
            print(f"\n  QUOTA EXHAUSTED — Scopus daily limit reached at [{idx}] {univ['name']}.")
            print(f"  Re-run with: python enrich.py --index {idx} (and all remaining indexes)")
            print(f"  Quota typically resets at midnight UTC.")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", nargs="+", metavar="IDX")
    args = parser.parse_args()
    run(indexes=args.index)
