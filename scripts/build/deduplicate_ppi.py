from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.utils.common import load_json_lines, resolve_repo_root, write_json_lines


def deduplicate_records(records: list[dict]) -> tuple[list[dict], dict[str, int]]:
    marker_groups: defaultdict[str, list[dict]] = defaultdict(list)
    entries_without_marker: list[dict] = []

    for entry in records:
        marker = entry.get("text_with_entity_marker", "")
        if marker and len(marker) > 10:
            marker_groups[marker].append(entry)
        else:
            entries_without_marker.append(entry)

    cleaned_records: list[dict] = []
    conflicting_groups = 0
    duplicate_groups_consolidated = 0

    for entries in marker_groups.values():
        if len(entries) == 1:
            cleaned_records.append(entries[0])
            continue

        type_sets = {
            tuple(sorted({relation.get("relation_type") for relation in entry.get("relation", [])}))
            for entry in entries
        }
        if len(type_sets) > 1:
            conflicting_groups += 1
            continue

        cleaned_records.append(entries[0])
        duplicate_groups_consolidated += 1

    cleaned_records.extend(entries_without_marker)
    stats = {
        "original_count": len(records),
        "entries_without_marker": len(entries_without_marker),
        "conflicting_groups": conflicting_groups,
        "duplicate_groups_consolidated": duplicate_groups_consolidated,
        "final_count": len(cleaned_records),
    }
    return cleaned_records, stats


def run_deduplicate(input_path: Path, output_path: Path) -> dict[str, int | str]:
    records = load_json_lines(input_path)
    cleaned_records, stats = deduplicate_records(records)
    write_json_lines(cleaned_records, output_path)
    return {**stats, "input_path": str(input_path), "output_path": str(output_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Deduplicate the merged dataset by text_with_entity_marker.")
    parser.add_argument("--root", help="Override the repository root.")
    parser.add_argument("--input", help="Input merged dataset path.")
    parser.add_argument("--output", help="Output cleaned dataset path.")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.root)
    input_path = (
        Path(args.input).resolve()
        if args.input
        else repo_root / "Unclean_combined_dataset" / "derived" / "combined_all_ppi.json"
    )
    output_path = (
        Path(args.output).resolve()
        if args.output
        else repo_root / "Unified_PPI_dataset" / "derived" / "Unified_PPI_dataset.json"
    )

    stats = run_deduplicate(input_path, output_path)

    print(f"Original Count: {stats['original_count']}")
    print(f"Entries without valid marker kept: {stats['entries_without_marker']}")
    print(f"Conflicting groups discarded: {stats['conflicting_groups']}")
    print(f"Duplicate groups consolidated: {stats['duplicate_groups_consolidated']}")
    print(f"Final Count: {stats['final_count']}")
    print(f"Wrote cleaned dataset to {output_path}")


if __name__ == "__main__":
    main()
