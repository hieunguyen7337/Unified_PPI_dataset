from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build.clean_unified_ppi_dataset import run_clean_unified
from scripts.build.combine_datasets import default_inputs as default_combination_inputs
from scripts.build.combine_datasets import run_combine_datasets
from scripts.build.convert_biocreative_to_combined import convert_biocreative_to_combined
from scripts.build.convert_biored_ppi import run_biored_conversion
from scripts.build.convert_unified_to_pubtator import run_convert_unified_to_pubtator
from scripts.build.deduplicate_ppi import run_deduplicate
from scripts.utils.common import resolve_repo_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the full conversion/build pipeline end to end.")
    parser.add_argument("--root", help="Override the repository root.")
    parser.add_argument("--force", action="store_true", help="Recompute outputs even if the canonical files already exist.")
    return parser


def should_run(output_path: Path, force: bool) -> bool:
    return force or not output_path.exists()


def main() -> None:
    args = build_parser().parse_args()
    repo_root = resolve_repo_root(args.root)

    biocreative_input = repo_root / "Biocreative_VI" / "raw" / "PMtask_Relations_TrainingSet.json"
    biocreative_output = repo_root / "Biocreative_VI" / "derived" / "biocreative_vi_converted.json"
    biored_datasets = [
        (repo_root / "BioRED" / "raw" / "Train.BioC.JSON", repo_root / "BioRED" / "derived" / "biored_train_ppi_converted.json"),
        (repo_root / "BioRED" / "raw" / "Dev.BioC.JSON", repo_root / "BioRED" / "derived" / "biored_dev_ppi_converted.json"),
        (repo_root / "BioRED" / "raw" / "Test.BioC.JSON", repo_root / "BioRED" / "derived" / "biored_test_ppi_converted.json"),
    ]
    combined_output = repo_root / "Unclean_combined_dataset" / "derived" / "combined_all_ppi.json"
    unified_output = repo_root / "Unified_PPI_dataset" / "derived" / "Unified_PPI_dataset.json"
    clean_output = repo_root / "Unified_PPI_dataset" / "derived" / "Unified_PPI_dataset_clean.json"
    pubtator_output = repo_root / "Unified_PPI_dataset" / "derived" / "Unified_PPI_dataset.PubTator"

    if should_run(biocreative_output, args.force):
        stats = convert_biocreative_to_combined(biocreative_input, biocreative_output)
        print(f"[build] BioCreative -> {stats['total_records']} records")
    else:
        print(f"[skip] {biocreative_output}")

    biored_outputs = [output for _, output in biored_datasets]
    if args.force or any(not path.exists() for path in biored_outputs):
        results = run_biored_conversion(biored_datasets)
        total_records = sum(item["record_count"] for item in results)
        print(f"[build] BioRED -> {total_records} records across {len(results)} splits")
    else:
        print("[skip] BioRED derived conversions")

    if should_run(combined_output, args.force):
        stats = run_combine_datasets(default_combination_inputs(repo_root), combined_output)
        print(f"[build] Combined dataset -> {stats['total_records']} records")
    else:
        print(f"[skip] {combined_output}")

    if should_run(unified_output, args.force):
        stats = run_deduplicate(combined_output, unified_output)
        print(f"[build] Unified pre-clean dataset -> {stats['final_count']} records")
    else:
        print(f"[skip] {unified_output}")

    if should_run(clean_output, args.force):
        stats = run_clean_unified(unified_output, clean_output)
        print(f"[build] Unified final-for-use dataset -> {stats['valid_items']} records")
    else:
        print(f"[skip] {clean_output}")

    if should_run(pubtator_output, args.force):
        run_convert_unified_to_pubtator(clean_output, pubtator_output)
        print(f"[build] PubTator export -> {pubtator_output}")
    else:
        print(f"[skip] {pubtator_output}")


if __name__ == "__main__":
    main()
