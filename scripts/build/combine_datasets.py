from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.utils.common import load_json_lines, resolve_repo_root, write_json_lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Combine canonical converted datasets into the unclean merged dataset.")
    parser.add_argument("--root", help="Override the repository root.")
    parser.add_argument(
        "--input",
        nargs="+",
        help="Input JSONL files. Defaults to the canonical 5_PPI, BioCreative, and BioRED derived files.",
    )
    parser.add_argument("--output", help="Output path for the combined JSONL dataset.")
    return parser


def run_combine_datasets(input_paths: list[Path], output_path: Path) -> dict:
    combined_records: list[dict] = []
    per_input_counts: list[dict] = []
    for input_path in input_paths:
        records = load_json_lines(input_path)
        combined_records.extend(records)
        per_input_counts.append({"path": str(input_path), "count": len(records)})

    write_json_lines(combined_records, output_path)
    return {
        "input_paths": [str(path) for path in input_paths],
        "per_input_counts": per_input_counts,
        "output_path": str(output_path),
        "total_records": len(combined_records),
    }


def default_inputs(repo_root: Path) -> list[Path]:
    return [
        repo_root / "5_PPI_dataset" / "derived" / "combined_all_ppi_dataset_0.json",
        repo_root / "Biocreative_VI" / "derived" / "biocreative_vi_converted.json",
        repo_root / "BioRED" / "derived" / "biored_dev_ppi_converted.json",
        repo_root / "BioRED" / "derived" / "biored_test_ppi_converted.json",
        repo_root / "BioRED" / "derived" / "biored_train_ppi_converted.json",
    ]


def main() -> None:
    args = build_parser().parse_args()
    repo_root = resolve_repo_root(args.root)
    input_paths = [Path(path).resolve() for path in args.input] if args.input else default_inputs(repo_root)
    output_path = (
        Path(args.output).resolve()
        if args.output
        else repo_root / "Unclean_combined_dataset" / "derived" / "combined_all_ppi.json"
    )

    stats = run_combine_datasets(input_paths, output_path)
    for item in stats["per_input_counts"]:
        print(f"Loaded {item['count']} records from {item['path']}")
    print(f"Saved {stats['total_records']} records to {stats['output_path']}")


if __name__ == "__main__":
    main()
