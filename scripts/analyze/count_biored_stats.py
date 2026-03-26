from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.utils.common import resolve_repo_root


def count_relations(path: Path) -> dict:
    positive = 0
    negative = 0
    total_rows = 0

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
            for relation in data.get("relation", []):
                relation_type = relation.get("relation_type")
                if relation_type == "positive":
                    positive += 1
                elif relation_type == "negative":
                    negative += 1

    return {"file": path.name, "total_rows": total_rows, "positive": positive, "negative": negative}


def default_inputs(repo_root: Path) -> list[Path]:
    return [
        repo_root / "BioRED" / "derived" / "biored_train_ppi_converted.json",
        repo_root / "BioRED" / "derived" / "biored_dev_ppi_converted.json",
        repo_root / "BioRED" / "derived" / "biored_test_ppi_converted.json",
    ]


def run_count_biored_stats(input_paths: list[Path], report_path: Path | None = None) -> dict:
    analyses = [count_relations(path) for path in input_paths]
    lines = []
    for item in analyses:
        lines.extend(
            [
                f"File: {item['file']}",
                f"Total Rows: {item['total_rows']}",
                f"Positive Relations: {item['positive']}",
                f"Negative Relations: {item['negative']}",
                "",
            ]
        )

    text = "\n".join(lines).rstrip() + "\n"
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(text, encoding="utf-8")
    return {"input_paths": [str(path) for path in input_paths], "report_path": str(report_path) if report_path else None, "analyses": analyses, "text": text}


def main() -> None:
    parser = argparse.ArgumentParser(description="Count positive and negative relations in BioRED converted files.")
    parser.add_argument("--root", help="Override the repository root.")
    parser.add_argument(
        "--input",
        nargs="+",
        help="Input BioRED converted files. Defaults to all three canonical derived files.",
    )
    parser.add_argument("--report", help="Optional output report path.")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.root)
    input_paths = [Path(path).resolve() for path in args.input] if args.input else default_inputs(repo_root)
    report_path = Path(args.report).resolve() if args.report else None

    result = run_count_biored_stats(input_paths, report_path)
    if report_path:
        print(f"Wrote report to {report_path}")
    else:
        print(result["text"], end="")


if __name__ == "__main__":
    main()
