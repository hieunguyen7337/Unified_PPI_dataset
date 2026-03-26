from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.utils.common import resolve_repo_root


def clean_unified_ppi_json(input_file: Path, output_file: Path) -> dict[str, int]:
    """
    Clean the unified PPI dataset by:
    1. Removing relations whose offsets fall outside the text bounds.
    2. Replacing entity text strings with strict slices from the text.
    3. Dropping items if no valid relations remain.
    """
    cleaned_items = []
    total_items = 0
    items_dropped = 0
    relations_dropped = 0
    relations_cleaned = 0

    with input_file.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue

            total_items += 1
            try:
                item = json.loads(stripped)
            except json.JSONDecodeError:
                items_dropped += 1
                continue

            text = item.get("text", "")
            text_length = len(text)
            valid_relations = []

            for relation in item.get("relation", []):
                e1_idx = relation.get("entity_1_idx")
                e2_idx = relation.get("entity_2_idx")

                if not e1_idx or not e2_idx:
                    relations_dropped += 1
                    continue

                e1_start = e1_idx[0][0]
                e1_end = e1_idx[-1][1]
                e2_start = e2_idx[0][0]
                e2_end = e2_idx[-1][1]

                if e1_start < 0 or e1_end > text_length or e2_start < 0 or e2_end > text_length:
                    relations_dropped += 1
                    continue

                expected_e1 = text[e1_start:e1_end]
                expected_e2 = text[e2_start:e2_end]
                if relation.get("entity_1") != expected_e1 or relation.get("entity_2") != expected_e2:
                    relation["entity_1"] = expected_e1
                    relation["entity_2"] = expected_e2
                    relations_cleaned += 1

                valid_relations.append(relation)

            if valid_relations:
                item["relation"] = valid_relations
                cleaned_items.append(item)
            else:
                items_dropped += 1

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as handle:
        for item in cleaned_items:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")

    return {
        "total_items": total_items,
        "items_dropped": items_dropped,
        "valid_items": len(cleaned_items),
        "relations_dropped": relations_dropped,
        "relations_cleaned": relations_cleaned,
    }


def run_clean_unified(input_path: Path, output_path: Path) -> dict[str, int | str]:
    stats = clean_unified_ppi_json(input_path, output_path)
    return {**stats, "input_path": str(input_path), "output_path": str(output_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean the final unified PPI dataset for downstream use.")
    parser.add_argument("--root", help="Override the repository root.")
    parser.add_argument("--input", help="Input unified dataset path.")
    parser.add_argument("--output", help="Output cleaned dataset path.")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.root)
    input_path = (
        Path(args.input).resolve()
        if args.input
        else repo_root / "Unified_PPI_dataset" / "derived" / "Unified_PPI_dataset.json"
    )
    output_path = (
        Path(args.output).resolve()
        if args.output
        else repo_root / "Unified_PPI_dataset" / "derived" / "Unified_PPI_dataset_clean.json"
    )

    stats = run_clean_unified(input_path, output_path)
    print(f"Total original items: {stats['total_items']}")
    print(f"Items completely dropped (no valid relations left): {stats['items_dropped']}")
    print(f"Total valid items saved: {stats['valid_items']}")
    print(f"Relations dropped due to out-of-bounds offsets: {stats['relations_dropped']}")
    print(f"Relations updated to wipe dirty string markers: {stats['relations_cleaned']}")
    print(f"\nCleaned dataset written to {output_path}")


if __name__ == "__main__":
    main()
