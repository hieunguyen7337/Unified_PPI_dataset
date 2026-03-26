from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.utils.common import resolve_repo_root


def count_sentences(text: str) -> int:
    if not text:
        return 0

    try:
        import nltk

        try:
            nltk.data.find("tokenizers/punkt")
        except LookupError:
            nltk.download("punkt", quiet=True)
        return len(nltk.sent_tokenize(text))
    except (ImportError, LookupError):
        parts = re.split(r"[.?!]+(?:\s+|$)", text)
        sentences = [part.strip() for part in parts if part.strip()]
        return len(sentences)


def analyze_file(path: Path) -> tuple[int, Counter]:
    distribution: Counter = Counter()
    total_records = 0

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                data = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            distribution[count_sentences(data.get("text", ""))] += 1
            total_records += 1

    return total_records, distribution


def format_distribution(label: str, total_records: int, distribution: Counter) -> list[str]:
    lines = [f"Analyzing: {label}", f"  Total Records: {total_records}", "  Sentence Count Distribution:"]
    for sentence_count in sorted(distribution):
        count = distribution[sentence_count]
        percentage = (count / total_records * 100) if total_records else 0.0
        lines.append(f"    {sentence_count} sentences: {count} ({percentage:.2f}%)")
    lines.append("-" * 30)
    return lines


def default_biored_inputs(repo_root: Path) -> list[Path]:
    return [
        repo_root / "BioRED" / "derived" / "biored_train_ppi_converted.json",
        repo_root / "BioRED" / "derived" / "biored_dev_ppi_converted.json",
        repo_root / "BioRED" / "derived" / "biored_test_ppi_converted.json",
    ]


def run_count_sentence_distribution(biored_inputs: list[Path], reference_input: Path, report_path: Path) -> dict:
    biored_total = 0
    biored_distribution: Counter = Counter()
    for path in biored_inputs:
        total_records, distribution = analyze_file(path)
        biored_total += total_records
        biored_distribution.update(distribution)

    reference_total, reference_distribution = analyze_file(reference_input)
    lines = []
    lines.extend(format_distribution("BioRED converted (all splits)", biored_total, biored_distribution))
    lines.extend(format_distribution(reference_input.name, reference_total, reference_distribution))

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "biored_inputs": [str(path) for path in biored_inputs],
        "reference_input": str(reference_input),
        "report_path": str(report_path),
        "biored_total": biored_total,
        "reference_total": reference_total,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare sentence count distributions across converted datasets.")
    parser.add_argument("--root", help="Override the repository root.")
    parser.add_argument(
        "--biored-input",
        nargs="+",
        help="BioRED converted inputs. Defaults to all three BioRED derived files.",
    )
    parser.add_argument(
        "--reference-input",
        help="Reference input to compare against. Defaults to the base 5_PPI combined dataset.",
    )
    parser.add_argument("--report", help="Output report path.")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.root)
    biored_inputs = [Path(path).resolve() for path in args.biored_input] if args.biored_input else default_biored_inputs(repo_root)
    reference_input = (
        Path(args.reference_input).resolve()
        if args.reference_input
        else repo_root / "5_PPI_dataset" / "derived" / "combined_all_ppi_dataset_0.json"
    )
    report_path = (
        Path(args.report).resolve()
        if args.report
        else repo_root / "BioRED" / "reports" / "sentence_stats.txt"
    )

    run_count_sentence_distribution(biored_inputs, reference_input, report_path)
    print(f"Wrote report to {report_path}")


if __name__ == "__main__":
    main()
