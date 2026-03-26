from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.utils.common import resolve_repo_root


def extract_missing(path: Path) -> list[dict]:
    missing_rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                data = json.loads(stripped)
            except json.JSONDecodeError:
                continue

            text_with_marker = data.get("text_with_entity_marker", "")
            if "[E1]" not in text_with_marker or "[E2]" not in text_with_marker:
                data["source_file"] = path.name
                missing_rows.append(data)
    return missing_rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract rows missing [E1] or [E2] markers.")
    parser.add_argument("--root", help="Override the repository root.")
    parser.add_argument(
        "--input",
        nargs="+",
        help="Dataset files to scan. Defaults to the canonical 5_PPI_dataset derived files.",
    )
    parser.add_argument("--output", help="Output JSON path for the extracted rows.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    repo_root = resolve_repo_root(args.root)

    default_inputs = [
        repo_root / "5_PPI_dataset" / "derived" / "combined_train_0.json",
        repo_root / "5_PPI_dataset" / "derived" / "combined_test_0.json",
        repo_root / "5_PPI_dataset" / "derived" / "combined_all_ppi_dataset_0.json",
    ]
    input_paths = [Path(path).resolve() for path in args.input] if args.input else default_inputs
    output_path = (
        Path(args.output).resolve()
        if args.output
        else repo_root / "5_PPI_dataset" / "derived" / "missing_markers_extracted.json"
    )

    extracted: list[dict] = []
    for input_path in input_paths:
        extracted.extend(extract_missing(input_path))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(extracted, handle, indent=2, ensure_ascii=False)

    print(f"Extracted {len(extracted)} rows to {output_path}")


if __name__ == "__main__":
    main()
