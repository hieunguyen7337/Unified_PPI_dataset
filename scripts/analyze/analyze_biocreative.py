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


def run_analyze_biocreative(input_path: Path, report_path: Path) -> dict:
    analysis = analyze_file(input_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as handle:
        handle.write(f"Analyzing: {analysis['file']}\n")
        handle.write(f"  Total Data Points (rows): {analysis['total_rows']}\n")
        handle.write(f"  Total Unique Sentences: {analysis['unique_sentences']}\n")
        handle.write(f"  Positive Relations: {analysis['positive']}\n")
        handle.write(f"  Negative Relations: {analysis['negative']}\n")
        handle.write(f"  [E1] before [E2]: {analysis['e1_before_e2']}\n")
        handle.write(f"  [E2] before [E1]: {analysis['e2_before_e1']}\n")
        if analysis["missing_markers"]:
            handle.write(f"  Rows with missing markers: {analysis['missing_markers']}\n")
        handle.write("-" * 30 + "\n")
    return {"input_path": str(input_path), "report_path": str(report_path), "analysis": analysis}


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze the converted BioCreative VI dataset.")
    parser.add_argument("--root", help="Override the repository root.")
    parser.add_argument("--input", help="Input JSONL file to analyze.")
    parser.add_argument("--report", help="Output report path.")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.root)
    input_path = (
        Path(args.input).resolve()
        if args.input
        else repo_root / "Biocreative_VI" / "derived" / "biocreative_vi_converted.json"
    )
    report_path = (
        Path(args.report).resolve()
        if args.report
        else repo_root / "Biocreative_VI" / "reports" / "biocreative_stats.txt"
    )

    run_analyze_biocreative(input_path, report_path)

    print(f"Wrote report to {report_path}")


if __name__ == "__main__":
    main()
