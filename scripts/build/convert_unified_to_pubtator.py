from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.utils.common import resolve_repo_root


def convert_to_pubtator(input_path: Path, output_path: Path) -> None:
    documents: defaultdict[str, list[dict]] = defaultdict(list)

    with input_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                item = json.loads(stripped)
            except json.JSONDecodeError:
                print("Error decoding json line:", stripped[:100])
                continue

            base_id = item["id"].split("_")[0]
            doc_id = base_id.replace(".", "_").replace("_s", "_")
            documents[doc_id].append(item)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as out_handle:
        for doc_id, items in documents.items():
            text = items[0]["text"]
            out_handle.write(f"{doc_id}|t|{text}\n")

            entities = {}
            relations = []
            entity_counter = 1

            for item in items:
                for relation in item.get("relation", []):
                    e1_idx = relation["entity_1_idx"]
                    e2_idx = relation["entity_2_idx"]

                    e1_key = (e1_idx[0][0], e1_idx[-1][1])
                    if e1_key not in entities:
                        entities[e1_key] = {
                            "text": relation["entity_1"],
                            "type": "Gene",
                            "t_id": f"T{entity_counter}",
                        }
                        entity_counter += 1

                    e2_key = (e2_idx[0][0], e2_idx[-1][1])
                    if e2_key not in entities:
                        entities[e2_key] = {
                            "text": relation["entity_2"],
                            "type": "Gene",
                            "t_id": f"T{entity_counter}",
                        }
                        entity_counter += 1

                    if relation.get("relation_type") == "positive":
                        relations.append((entities[e1_key]["t_id"], entities[e2_key]["t_id"]))

            for (start, end), entity in sorted(entities.items()):
                out_handle.write(f"{doc_id}\t{start}\t{end}\t{entity['text']}\t{entity['type']}\t{entity['t_id']}\n")

            seen_relations = set()
            for source_id, target_id in relations:
                relation_key = (source_id, target_id)
                if relation_key in seen_relations:
                    continue
                seen_relations.add(relation_key)
                out_handle.write(f"{doc_id}\tAssociation\t{source_id}\t{target_id}\n")

            out_handle.write("\n")


def run_convert_unified_to_pubtator(input_path: Path, output_path: Path) -> dict[str, str]:
    convert_to_pubtator(input_path, output_path)
    return {"input_path": str(input_path), "output_path": str(output_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert the final unified dataset JSONL into PubTator format.")
    parser.add_argument("--root", help="Override the repository root.")
    parser.add_argument("--input", help="Input unified dataset path.")
    parser.add_argument("--output", help="Output PubTator path.")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.root)
    input_path = (
        Path(args.input).resolve()
        if args.input
        else repo_root / "Unified_PPI_dataset" / "derived" / "Unified_PPI_dataset_clean.json"
    )
    output_path = (
        Path(args.output).resolve()
        if args.output
        else repo_root / "Unified_PPI_dataset" / "derived" / "Unified_PPI_dataset.PubTator"
    )

    run_convert_unified_to_pubtator(input_path, output_path)
    print(f"Conversion complete. Output saved to {output_path}")


if __name__ == "__main__":
    main()
