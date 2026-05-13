"""
Faculty scraper — tiered config approach.

Usage:
  python main.py                  # scrape all universities in config
  python main.py --index 01       # scrape only university index 01
  python main.py --index 01 02    # scrape specific universities
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

from scrapers import get_scraper

CONFIG_PATH = Path(__file__).parent / "config" / "universities.json"
OUTPUT_DIR = Path(__file__).parent / "output"


def load_config() -> list[dict]:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)["universities"]


def save_csv(university: dict, rows: list[dict]) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    idx = university["index"]
    safe_name = university["name"].replace(" ", "_").replace("/", "-")[:40]
    out_path = OUTPUT_DIR / f"{idx}_{safe_name}.csv"

    fieldnames = [
        "name", "first_name", "last_name", "original_title",
        "department", "area", "university", "email", "rank",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return out_path


def run(indexes: list[str] | None = None):
    universities = load_config()

    if indexes:
        universities = [u for u in universities if u["index"] in indexes]
        if not universities:
            print(f"No universities found for indexes: {indexes}")
            sys.exit(1)

    for univ in universities:
        print(f"\n[{univ['index']}] {univ['name']} ({univ['school']})")
        print(f"  Scraper: {univ['scraper_type']} | Departments: {len(univ['departments'])}")

        scraper = get_scraper(univ)
        rows = scraper.scrape()

        if not rows:
            print("  No data collected — check selectors or URLs.")
            continue

        out_path = save_csv(univ, rows)
        print(f"  Saved {len(rows)} faculty → {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--index", nargs="+", metavar="IDX",
        help="University index(es) to scrape (e.g. --index 01 02)"
    )
    args = parser.parse_args()
    run(indexes=args.index)
