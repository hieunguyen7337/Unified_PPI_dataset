from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.utils.common import load_json_lines, resolve_repo_root


def are_relations_equal(left: list[dict], right: list[dict]) -> bool:
    def sort_key(item: dict) -> tuple:
        return (item.get("relation_id", 0), item.get("entity_1", ""), item.get("entity_2", ""))

    return sorted(left, key=sort_key) == sorted(right, key=sort_key)


def analyze_consistency(path: Path) -> tuple[int, int, int, int, list[dict]]:
    data = load_json_lines(path)
    marker_groups: defaultdict[str, list[dict]] = defaultdict(list)

    for entry in data:
        marker = entry.get("text_with_entity_marker", "")
        if marker:
            marker_groups[marker].append(entry)

    duplicates = {marker: entries for marker, entries in marker_groups.items() if len(entries) > 1}
    identical_groups = 0
    different_groups = 0
    different_relation_types = 0
    detailed_diffs: list[dict] = []

    for marker, entries in duplicates.items():
        reference = entries[0]
        group_is_identical = True
        relation_type_diff = False

        for other in entries[1:]:
            fields_match = True
            if reference.get("text") != other.get("text"):
                fields_match = False
            if reference.get("directed") != other.get("directed"):
                fields_match = False
            if reference.get("reverse") != other.get("reverse"):
                fields_match = False
            if not are_relations_equal(reference.get("relation", []), other.get("relation", [])):
                fields_match = False
                if {
                    relation.get("relation_type") for relation in reference.get("relation", [])
                } != {relation.get("relation_type") for relation in other.get("relation", [])}:
                    relation_type_diff = True

            if not fields_match:
                group_is_identical = False

        if group_is_identical:
            identical_groups += 1
        else:
            different_groups += 1
            if relation_type_diff:
                different_relation_types += 1
                detailed_diffs.append(
                    {
                        "marker": marker,
                        "ids": [entry.get("id") for entry in entries],
                        "types": [
                            sorted({relation.get("relation_type") for relation in entry.get("relation", [])})
                            for entry in entries
                        ],
                    }
                )

    return len(duplicates), identical_groups, different_groups, different_relation_types, detailed_diffs


def run_analyze_duplicate_consistency(input_path: Path, report_path: Path) -> dict:
    total_groups, identical_groups, different_groups, different_relation_types, detailed_diffs = analyze_consistency(
        input_path
    )
    lines = [
        "Consistency Analysis Report",
        f"Total Duplicate Groups: {total_groups}",
        f"Identical Groups: {identical_groups}",
        f"Different Groups: {different_groups}",
        f"Different Relation Types: {different_relation_types}",
        "",
    ]
    if detailed_diffs:
        lines.append("Details of groups with different relation types:")
        for item in detailed_diffs:
            lines.append("-" * 20)
            lines.append(f"Text with Marker: {item['marker']}")
            lines.append(f"IDs: {item['ids']}")
            lines.append(f"Relation Types: {item['types']}")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "input_path": str(input_path),
        "report_path": str(report_path),
        "total_groups": total_groups,
        "identical_groups": identical_groups,
        "different_groups": different_groups,
        "different_relation_types": different_relation_types,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check whether duplicate marker strings agree on labels/content.")
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
        else repo_root / "reports" / "combined" / "consistency_analysis.txt"
    )

    run_analyze_duplicate_consistency(input_path, report_path)
    print(f"Wrote report to {report_path}")


if __name__ == "__main__":
    main()
