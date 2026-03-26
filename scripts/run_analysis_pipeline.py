from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.analyze.analyze_biocreative import run_analyze_biocreative
from scripts.analyze.analyze_cleaned_combined_dataset import run_analyze_cleaned_dataset
from scripts.analyze.analyze_duplicate_consistency import run_analyze_duplicate_consistency
from scripts.analyze.analyze_duplicates import run_analyze_duplicates
from scripts.analyze.analyze_ppi import default_inputs as default_ppi_inputs
from scripts.analyze.analyze_ppi import run_analyze_ppi
from scripts.analyze.count_biored_stats import default_inputs as default_biored_stat_inputs
from scripts.analyze.count_biored_stats import run_count_biored_stats
from scripts.analyze.count_sentence_distribution import default_biored_inputs
from scripts.analyze.count_sentence_distribution import run_count_sentence_distribution
from scripts.utils.common import resolve_repo_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the full analysis/report pipeline end to end.")
    parser.add_argument("--root", help="Override the repository root.")
    parser.add_argument("--force", action="store_true", help="Recompute reports even if the canonical files already exist.")
    return parser


def should_run(output_path: Path, force: bool) -> bool:
    return force or not output_path.exists()


def main() -> None:
    args = build_parser().parse_args()
    repo_root = resolve_repo_root(args.root)

    ppi_report = repo_root / "5_PPI_dataset" / "reports" / "final_report.txt"
    ppi_summary = repo_root / "5_PPI_dataset" / "reports" / "dataset_stats.txt"
    biocreative_report = repo_root / "Biocreative_VI" / "reports" / "biocreative_stats.txt"
    biored_relation_report = repo_root / "BioRED" / "reports" / "biored_relation_stats.txt"
    biored_sentence_report = repo_root / "BioRED" / "reports" / "sentence_stats.txt"
    duplicate_report = repo_root / "reports" / "combined" / "duplicate_source_analysis.txt"
    consistency_report = repo_root / "reports" / "combined" / "consistency_analysis.txt"
    final_dataset_report = repo_root / "Unified_PPI_dataset" / "reports" / "dataset_analysis.md"

    if args.force or not (ppi_report.exists() and ppi_summary.exists()):
        result = run_analyze_ppi(default_ppi_inputs(repo_root), ppi_report, ppi_summary)
        print(f"[analyze] 5-PPI -> {len(result['analyses'])} files")
    else:
        print("[skip] 5-PPI reports")

    if should_run(biocreative_report, args.force):
        result = run_analyze_biocreative(
            repo_root / "Biocreative_VI" / "derived" / "biocreative_vi_converted.json",
            biocreative_report,
        )
        print(f"[analyze] BioCreative -> {result['analysis']['total_rows']} rows")
    else:
        print("[skip] BioCreative report")

    if should_run(biored_relation_report, args.force):
        result = run_count_biored_stats(default_biored_stat_inputs(repo_root), biored_relation_report)
        total_rows = sum(item["total_rows"] for item in result["analyses"])
        print(f"[analyze] BioRED relation stats -> {total_rows} rows")
    else:
        print("[skip] BioRED relation stats")

    if should_run(biored_sentence_report, args.force):
        result = run_count_sentence_distribution(
            default_biored_inputs(repo_root),
            repo_root / "5_PPI_dataset" / "derived" / "combined_all_ppi_dataset_0.json",
            biored_sentence_report,
        )
        print(f"[analyze] BioRED sentence distribution -> {result['biored_total']} BioRED rows")
    else:
        print("[skip] BioRED sentence stats")

    if should_run(duplicate_report, args.force):
        result = run_analyze_duplicates(
            repo_root / "Unclean_combined_dataset" / "derived" / "combined_all_ppi.json",
            duplicate_report,
        )
        print(f"[analyze] Duplicate groups -> {result['duplicate_group_count']}")
    else:
        print("[skip] duplicate report")

    if should_run(consistency_report, args.force):
        result = run_analyze_duplicate_consistency(
            repo_root / "Unclean_combined_dataset" / "derived" / "combined_all_ppi.json",
            consistency_report,
        )
        print(f"[analyze] Consistency groups -> {result['total_groups']}")
    else:
        print("[skip] consistency report")

    if should_run(final_dataset_report, args.force):
        result = run_analyze_cleaned_dataset(
            repo_root / "Unified_PPI_dataset" / "derived" / "Unified_PPI_dataset_clean.json",
            final_dataset_report,
        )
        print(f"[analyze] Final cleaned dataset report -> {len(result['report_text'].splitlines())} lines")
    else:
        print("[skip] final cleaned dataset report")


if __name__ == "__main__":
    main()
