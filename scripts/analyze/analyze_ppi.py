from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.utils.common import resolve_repo_root


def analyze_file(path: Path) -> dict:
    positive = 0
    negative = 0
    total_rows = 0
    unique_sentences: set[str] = set()
    e1_before_e2 = 0
    e2_before_e1 = 0
    missing_markers = 0

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                data = json.loads(stripped)
            except json.JSONDecodeError:
                continue

            total_rows += 1
            unique_sentences.add(data.get("text", ""))

            for relation in data.get("relation", []):
                relation_type = relation.get("relation_type")
                if relation_type == "positive":
                    positive += 1
                elif relation_type == "negative":
                    negative += 1

            text_with_marker = data.get("text_with_entity_marker", "")
            e1_index = text_with_marker.find("[E1]")
            e2_index = text_with_marker.find("[E2]")
            if e1_index != -1 and e2_index != -1:
                if e1_index < e2_index:
                    e1_before_e2 += 1
                else:
                    e2_before_e1 += 1
            else:
                missing_markers += 1

    return {
        "file": path.name,
        "total_rows": total_rows,
        "unique_sentences": len(unique_sentences),
        "positive": positive,
        "negative": negative,
        "e1_before_e2": e1_before_e2,
        "e2_before_e1": e2_before_e1,
        "missing_markers": missing_markers,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze the base 5-PPI dataset files.")
    parser.add_argument("--root", help="Override the repository root.")
    parser.add_argument(
        "--input",
        nargs="+",
        help="Dataset files to analyze. Defaults to the canonical 5_PPI_dataset derived files.",
    )
    parser.add_argument("--report", help="Detailed report path.")
    parser.add_argument("--summary-report", help="Compact summary report path.")
    return parser


def run_analyze_ppi(input_paths: list[Path], report_path: Path, summary_path: Path) -> dict:
    analyses = [analyze_file(path) for path in input_paths]

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as handle:
        for item in analyses:
            handle.write(f"Analyzing: {item['file']}\n")
            handle.write(f"  Total Data Points (rows): {item['total_rows']}\n")
            handle.write(f"  Total Unique Sentences: {item['unique_sentences']}\n")
            handle.write(f"  Positive Relations: {item['positive']}\n")
            handle.write(f"  Negative Relations: {item['negative']}\n")
            handle.write(f"  [E1] before [E2]: {item['e1_before_e2']}\n")
            handle.write(f"  [E2] before [E1]: {item['e2_before_e1']}\n")
            if item["missing_markers"]:
                handle.write(f"  Rows with missing markers: {item['missing_markers']}\n")
            handle.write("-" * 30 + "\n")

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", encoding="utf-8") as handle:
        for item in analyses:
            handle.write(f"File: {item['file']}\n")
            handle.write(f"Positive: {item['positive']}\n")
            handle.write(f"Negative: {item['negative']}\n")
            handle.write(f"Total Entries: {item['total_rows']}\n\n")

    return {
        "input_paths": [str(path) for path in input_paths],
        "report_path": str(report_path),
        "summary_report_path": str(summary_path),
        "analyses": analyses,
    }


def default_inputs(repo_root: Path) -> list[Path]:
    return [
        repo_root / "5_PPI_dataset" / "derived" / "combined_train_0.json",
        repo_root / "5_PPI_dataset" / "derived" / "combined_test_0.json",
        repo_root / "5_PPI_dataset" / "derived" / "combined_all_ppi_dataset_0.json",
    ]


def main() -> None:
    args = build_parser().parse_args()
    repo_root = resolve_repo_root(args.root)
    input_paths = [Path(path).resolve() for path in args.input] if args.input else default_inputs(repo_root)
    report_path = Path(args.report).resolve() if args.report else repo_root / "5_PPI_dataset" / "reports" / "final_report.txt"
    summary_path = (
        Path(args.summary_report).resolve()
        if args.summary_report
        else repo_root / "5_PPI_dataset" / "reports" / "dataset_stats.txt"
    )

    run_analyze_ppi(input_paths, report_path, summary_path)

    print(f"Wrote detailed report to {report_path}")
    print(f"Wrote summary report to {summary_path}")


if __name__ == "__main__":
    main()
