from __future__ import annotations

import argparse
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.utils.common import load_json_lines, resolve_repo_root


def calculate_stats(values: list[int]) -> tuple[str, str, str]:
    if not values:
        return "N/A", "N/A", "N/A"
    return f"{statistics.mean(values):.2f}", str(min(values)), str(max(values))


def analyze_dataset(path: Path) -> str:
    data = load_json_lines(path)
    source_relation_types: defaultdict[str, Counter] = defaultdict(Counter)
    overall_relation_types: Counter = Counter()
    source_marker_patterns: defaultdict[str, Counter] = defaultdict(Counter)
    overall_marker_patterns: Counter = Counter()
    source_text_stats: defaultdict[str, dict[str, list[int]]] = defaultdict(lambda: {"words": [], "sentences": []})
    overall_text_stats = {"words": [], "sentences": []}
    source_texts: defaultdict[str, list[str]] = defaultdict(list)
    overall_texts: list[str] = []

    marker_pattern = re.compile(r"\[/?E\d+(?:-E\d+)?\]")
    sentence_pattern = re.compile(r"[.!?]+(?:\s+|$)")

    for entry in data:
        identifier = entry.get("id", "")
        source = identifier.split(".")[0] if "." in identifier else "Unknown"

        for relation in entry.get("relation", []):
            relation_type = relation.get("relation_type", "unknown")
            overall_relation_types[relation_type] += 1
            source_relation_types[source][relation_type] += 1

        marker_text = entry.get("text_with_entity_marker", "")
        signature = " - ".join(marker_pattern.findall(marker_text)) or "No Markers"
        overall_marker_patterns[signature] += 1
        source_marker_patterns[source][signature] += 1

        text = entry.get("text", "")
        word_count = len(text.split())
        sentence_count = len(sentence_pattern.findall(text))
        if sentence_count == 0 and text:
            sentence_count = 1

        overall_text_stats["words"].append(word_count)
        overall_text_stats["sentences"].append(sentence_count)
        source_text_stats[source]["words"].append(word_count)
        source_text_stats[source]["sentences"].append(sentence_count)
        source_texts[source].append(text)
        overall_texts.append(text)

    def uniqueness_stats(values: list[str]) -> tuple[int, int]:
        unique = len(set(values))
        return unique, len(values) - unique

    ordered_sources = sorted(source_relation_types)
    lines = [
        "# Dataset Analysis: Combined PPI",
        "",
        f"**File Analyzed**: `{path}`",
        "",
        f"**Total Entries**: **{len(data):,}**",
        "",
        "## Source Statistics & Relations",
        "",
        "| Source | Total | Positive | Negative | Text Unique | Text Duplicates |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for source in ordered_sources:
        positive = source_relation_types[source].get("positive", 0)
        negative = source_relation_types[source].get("negative", 0)
        total = sum(source_relation_types[source].values())
        text_unique, text_duplicates = uniqueness_stats(source_texts[source])
        lines.append(f"| **{source}** | {total} | {positive} | {negative} | {text_unique} | {text_duplicates} |")

    overall_unique, overall_duplicates = uniqueness_stats(overall_texts)
    lines.append(
        f"| **OVERALL** | **{sum(overall_relation_types.values())}** | **{overall_relation_types.get('positive', 0)}** | "
        f"**{overall_relation_types.get('negative', 0)}** | **{overall_unique}** | **{overall_duplicates}** |"
    )
    lines.extend(["", "## Entity Marker Patterns", "", "| Pattern | Count |", "| --- | --- |"])
    for pattern, count in overall_marker_patterns.most_common():
        lines.append(f"| `{pattern}` | {count} |")

    lines.extend(
        [
            "",
            "## Text & Linguistic Statistics",
            "",
            "| Source | Avg. Words | Range (Words) | Avg. Sents | Range (Sents) |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for source in ordered_sources:
        words_mean, words_min, words_max = calculate_stats(source_text_stats[source]["words"])
        sent_mean, sent_min, sent_max = calculate_stats(source_text_stats[source]["sentences"])
        lines.append(f"| **{source}** | {words_mean} | {words_min} - {words_max} | {sent_mean} | {sent_min} - {sent_max} |")

    overall_words_mean, overall_words_min, overall_words_max = calculate_stats(overall_text_stats["words"])
    overall_sent_mean, overall_sent_min, overall_sent_max = calculate_stats(overall_text_stats["sentences"])
    lines.append(
        f"| **OVERALL** | **{overall_words_mean}** | **{overall_words_min} - {overall_words_max}** | "
        f"**{overall_sent_mean}** | **{overall_sent_min} - {overall_sent_max}** |"
    )
    return "\n".join(lines) + "\n"


def run_analyze_cleaned_dataset(input_path: Path, report_path: Path) -> dict:
    report_text = analyze_dataset(input_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_text, encoding="utf-8")
    return {"input_path": str(input_path), "report_path": str(report_path), "report_text": report_text}


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze the cleaned unified dataset and emit a Markdown summary.")
    parser.add_argument("--root", help="Override the repository root.")
    parser.add_argument("--input", help="Input dataset path.")
    parser.add_argument("--report", help="Output Markdown report path.")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.root)
    input_path = (
        Path(args.input).resolve()
        if args.input
        else repo_root / "Unified_PPI_dataset" / "derived" / "Unified_PPI_dataset_clean.json"
    )
    report_path = (
        Path(args.report).resolve()
        if args.report
        else repo_root / "Unified_PPI_dataset" / "reports" / "dataset_analysis.md"
    )

    run_analyze_cleaned_dataset(input_path, report_path)
    print(f"Wrote report to {report_path}")


if __name__ == "__main__":
    main()
