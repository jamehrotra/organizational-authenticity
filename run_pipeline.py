"""
Master pipeline runner. Runs all stages in order, or individual stages by name.

Stages:
  1  cdx          Query Wayback CDX API for all company-year URLs
  2  download     Download archived HTML snapshots
  3  extract      Extract clean text from HTML
  4  analyze1     LLM analysis of About Us pages -> part1_dataset.csv
  5  fetch_sec    Download DEF 14A proxy statements from SEC EDGAR
  6  extract2     Extract clean text from proxy statements
  7  analyze2     LLM analysis of proxy statements -> part2_dataset.csv
  8  vectors      Build theme vectors for Part 3
  9  index        Compute authenticity index -> part3_authenticity_index.csv
  10 validity     Run validity checks and produce plots
  11 part4        Part 4 sector drift and values volatility analysis

Usage:
  python run_pipeline.py                   # run all stages
  python run_pipeline.py cdx download      # run specific stages
  python run_pipeline.py --from index      # run from a given stage onward
  python run_pipeline.py --force           # ignore all caches
"""

import argparse
import sys

STAGES = [
    "cdx",
    "download",
    "extract",
    "analyze1",
    "fetch_sec",
    "extract2",
    "analyze2",
    "vectors",
    "index",
    "validity",
    "part4",
]


def run_stage(name: str, force: bool):
    print(f"\n{'='*60}")
    print(f"  STAGE: {name.upper()}")
    print(f"{'='*60}")

    if name == "cdx":
        from src.part1_wayback.query_cdx import run_all
        run_all(force=force)

    elif name == "download":
        from src.part1_wayback.download_snapshots import run_all
        run_all(force=force)

    elif name == "extract":
        from src.part1_wayback.extract_about_text import run_all
        run_all(force=force)

    elif name == "analyze1":
        from src.part1_wayback.analyze_about_pages import run_all
        run_all(force=force)

    elif name == "fetch_sec":
        from src.part2_disclosures.fetch_sec_filings import run_all
        run_all(force=force)

    elif name == "extract2":
        from src.part2_disclosures.extract_disclosure_text import run_all
        run_all(force=force)

    elif name == "analyze2":
        from src.part2_disclosures.analyze_disclosures import run_all
        run_all(force=force)

    elif name == "vectors":
        from src.part3_index.construct_theme_vectors import run
        run()

    elif name == "index":
        from src.part3_index.compute_authenticity_index import run
        run()

    elif name == "validity":
        from src.part3_index.validity_checks import run
        run()

    elif name == "part4":
        from src.part4_exploratory.sector_drift_analysis import run
        run()

    else:
        print(f"Unknown stage: {name}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Organizational Authenticity Pipeline")
    parser.add_argument("stages", nargs="*", help="Stages to run (default: all)")
    parser.add_argument("--from", dest="from_stage", help="Run from this stage onward")
    parser.add_argument("--force", action="store_true", help="Ignore all caches")
    args = parser.parse_args()

    if args.from_stage:
        if args.from_stage not in STAGES:
            print(f"Unknown stage: {args.from_stage}. Valid: {STAGES}")
            sys.exit(1)
        idx = STAGES.index(args.from_stage)
        to_run = STAGES[idx:]
    elif args.stages:
        invalid = [s for s in args.stages if s not in STAGES]
        if invalid:
            print(f"Unknown stages: {invalid}. Valid: {STAGES}")
            sys.exit(1)
        to_run = args.stages
    else:
        to_run = STAGES

    print(f"Running stages: {to_run}")
    print(f"Force re-run: {args.force}")

    for stage in to_run:
        run_stage(stage, force=args.force)

    print(f"\n{'='*60}")
    print("  PIPELINE COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
