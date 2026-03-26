from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.utils.common import load_json_lines, resolve_repo_root


def analyze_duplicates(path: Path) -> tuple[dict[str, list[str]], Counter]:
    data = load_json_lines(path)
    marker_groups: defaultdict[str, list[str]] = defaultdict(list)

    for entry in data:
        marker = entry.get("text_with_entity_marker", "")
        if marker:
            marker_groups[marker].append(entry.get("id", "Unknown"))

    duplicates = {marker: ids for marker, ids in marker_groups.items() if len(ids) > 1}
    source_overlap_counts: Counter = Counter()

    for ids in duplicates.values():
        sources = []
        for identifier in ids:
            sources.append(identifier.split(".")[0] if "." in identifier else identifier)
        source_overlap_counts[" & ".join(sorted(sources))] += 1

    return duplicates, source_overlap_counts


def run_analyze_duplicates(input_path: Path, report_path: Path) -> dict:
    duplicates, source_overlap_counts = analyze_duplicates(input_path)
    lines = [
        "Duplicate Analysis Report",
        f"Total Duplicate Groups: {len(duplicates)}",
        "",
        "Source Combinations:",
    ]
    for key, count in source_overlap_counts.most_common():
        lines.append(f"  - {key}: {count}")
    lines.extend(["", "=" * 50, "", "Detailed Duplicate Entries:"])
    for marker, ids in duplicates.items():
        lines.append(f"Text with Marker: {marker}")
        lines.append(f"Found in IDs: {', '.join(ids)}")
        lines.append("-" * 20)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "input_path": str(input_path),
        "report_path": str(report_path),
        "duplicate_group_count": len(duplicates),
        "source_overlap_counts": dict(source_overlap_counts),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze duplicate text_with_entity_marker values.")
    parser.add_argument("--root", help="Override the repository root.")
    parser.add_argument("--input", help="Input dataset path.")
    parser.add_argument("--report", help="Output report path.")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.root)
    input_path = (
        Path(args.input).resolve()
        if args.input
        else repo_root / "Unclean_combined_dataset" / "derived" / "combined_all_ppi.json"
    )
    report_path = (
        Path(args.report).resolve()
        if args.report
        else repo_root / "reports" / "combined" / "duplicate_source_analysis.txt"
    )

    run_analyze_duplicates(input_path, report_path)
    print(f"Wrote report to {report_path}")


if __name__ == "__main__":
    main()
