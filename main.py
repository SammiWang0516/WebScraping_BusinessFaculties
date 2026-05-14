"""
Full pipeline — scrape → merge → enrich for one or more universities.

Usage:
  python main.py                   # run all configured universities
  python main.py --index 01        # run one university
  python main.py --index 01 02     # run several universities

To run individual stages only:
  python scrape.py  --index 01     # scrape only
  python merge.py   --index 01     # merge 2025 Scopus IDs only
  python enrich.py  --index 01     # API lookup only
"""

import argparse
import importlib
import sys


def run_stage(module_name: str, indexes: list[str] | None):
    mod = importlib.import_module(module_name.replace(".py", ""))
    mod.run(indexes=indexes)


def run(indexes: list[str] | None = None):
    for stage in ("scrape", "merge", "enrich"):
        print(f"\n{'='*50}")
        print(f"  STAGE: {stage.upper()}")
        print(f"{'='*50}")
        run_stage(stage, indexes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", nargs="+", metavar="IDX")
    args = parser.parse_args()
    run(indexes=args.index)
