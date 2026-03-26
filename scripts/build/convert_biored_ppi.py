"""
Convert BioRED PPI Data to Unified PPI Dataset Format

This script converts the extracted BioRED PPI data to the format used in
the 5_PPI_dataset (e.g., combined_test_0.json).

Output format (JSONL - one JSON per line):
{
    "id": "BioRED.{pmid}.p{pair_idx}",
    "text": "sentence text",
    "text_with_entity_marker": "text with [E1]...[/E1] and [E2]...[/E2] markers",
    "relation": [{
        "relation_type": "positive",
        "relation_id": 0,
        "original_relation_type": "Bind",  # BioRED original type
        "entity_1": "gene1_name",
        "entity_1_idx": [[start, end]],
        "entity_1_idx_in_text_with_entity_marker": [start, end],
        "entity_1_type": "protein",
        "entity_1_type_id": 0,
        "entity_2": "gene2_name",
        "entity_2_idx": [[start, end]],
        "entity_2_idx_in_text_with_entity_marker": [start, end],
        "entity_2_type": "protein",
        "entity_2_type_id": 0
    }],
    "directed": false,
    "reverse": false
}

Note: BioRED dataset only contains positive PPI relations (all relation types 
like Association, Bind, Positive_Correlation, Negative_Correlation indicate 
the EXISTENCE of an interaction, hence relation_type is always "positive").
The "original_relation_type" field preserves the BioRED-specific relation subtype.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.utils.common import resolve_repo_root


def find_entity_positions(text: str, entity_name: str) -> List[List[int]]:
    """
    Find all positions of an entity in the text.
    Returns list of [start, end] positions.
    """
    positions = []
    # Escape special regex characters
    pattern = re.escape(entity_name)
    
    for match in re.finditer(pattern, text, re.IGNORECASE):
        positions.append([match.start(), match.end()])
    
    return positions


def insert_entity_markers(text: str, e1_start: int, e1_end: int, 
                          e2_start: int, e2_end: int) -> Tuple[str, int, int]:
    """
    Insert entity markers into text.
    Assumes e1_start < e2_start and no overlap.
    
    Returns:
        - marked text
        - e1 end position in marked text
        - e2 end position in marked text
    """
    marked = (text[:e1_start] + 
              "[E1]" + text[e1_start:e1_end] + "[/E1]" + 
              text[e1_end:e2_start] +
              "[E2]" + text[e2_start:e2_end] + "[/E2]" +
              text[e2_end:])
              
    e1_end_marked = e1_start + 4 + (e1_end - e1_start)  # after [E1]entity
    
    # E2 position shifted by [E1] and [/E1] markers attached to E1
    e2_start_marked = e2_start + 9  # +4 for [E1] +5 for [/E1]
    e2_end_marked = e2_start_marked + 4 + (e2_end - e2_start)
    
    return marked, e1_end_marked, e2_end_marked


def extract_ppi_from_bioc_json(file_path: str | Path) -> List[Dict]:
    """
    Extract PPI data from BioC.JSON and convert to unified format.
    """
    with Path(file_path).open('r', encoding='utf-8') as f:
        data = json.load(f)
    
    converted_records = []
    pair_counter = 0
    
    for doc in data.get("documents", []):
        pmid = doc.get("id", "")
        
        # Collect all gene entities and their text positions
        gene_entities = {}  # identifier -> {names: [], positions: [(start, end, text)]}
        
        # Get full text from passages
        passages = doc.get("passages", [])
        title_text = ""
        abstract_text = ""
        title_offset = 0
        abstract_offset = 0
        
        for passage in passages:
            offset = passage.get("offset", 0)
            p_text = passage.get("text", "")
            
            if offset == 0:
                title_text = p_text
                title_offset = 0
            else:
                abstract_text = p_text
                abstract_offset = offset
            
            # Collect annotations
            for annotation in passage.get("annotations", []):
                entity_type = annotation.get("infons", {}).get("type", "")
                if entity_type == "GeneOrGeneProduct":
                    identifier = annotation.get("infons", {}).get("identifier", "")
                    entity_text = annotation.get("text", "")
                    locations = annotation.get("locations", [])
                    
                    if identifier:
                        if identifier not in gene_entities:
                            gene_entities[identifier] = {"names": [], "positions": []}
                        
                        if entity_text not in gene_entities[identifier]["names"]:
                            gene_entities[identifier]["names"].append(entity_text)
                        
                        for loc in locations:
                            loc_offset = loc.get("offset", 0)
                            loc_length = loc.get("length", len(entity_text))
                            gene_entities[identifier]["positions"].append({
                                "offset": loc_offset,
                                "length": loc_length,
                                "text": entity_text,
                                "passage_offset": offset,
                                "passage_text": p_text
                            })
        
        # Full document text
        full_text = title_text + " " + abstract_text if abstract_text else title_text
        
        # Process relations
        for relation in doc.get("relations", []):
            infons = relation.get("infons", {})
            entity1_id = infons.get("entity1", "")
            entity2_id = infons.get("entity2", "")
            relation_type = infons.get("type", "")
            
            # Check if both entities are genes (numeric IDs)
            if not (entity1_id and entity2_id):
                continue
            
            # Check if entities are Gene IDs (numeric)
            def is_gene_id(identifier):
                if not identifier or identifier == "-":
                    return False
                parts = identifier.split(",")
                return all(part.strip().isdigit() for part in parts)
            
            if not (is_gene_id(entity1_id) and is_gene_id(entity2_id)):
                continue
            
            # Get entity information
            e1_info = gene_entities.get(entity1_id, {"names": [entity1_id], "positions": []})
            e2_info = gene_entities.get(entity2_id, {"names": [entity2_id], "positions": []})
            
            e1_name = e1_info["names"][0] if e1_info["names"] else entity1_id
            e2_name = e2_info["names"][0] if e2_info["names"] else entity2_id
            
            # Find positions in full text
            e1_positions = find_entity_positions(full_text, e1_name)
            e2_positions = find_entity_positions(full_text, e2_name)
            
            # If no positions found, use the first mention from annotations
            if not e1_positions and e1_info["positions"]:
                pos = e1_info["positions"][0]
                # Calculate position relative to full text
                if pos["passage_offset"] == 0:
                    start = pos["offset"] - pos["passage_offset"]
                else:
                    start = len(title_text) + 1 + (pos["offset"] - pos["passage_offset"])
                e1_positions = [[start, start + pos["length"]]]
            
            if not e2_positions and e2_info["positions"]:
                pos = e2_info["positions"][0]
                if pos["passage_offset"] == 0:
                    start = pos["offset"] - pos["passage_offset"]
                else:
                    start = len(title_text) + 1 + (pos["offset"] - pos["passage_offset"])
                e2_positions = [[start, start + pos["length"]]]
            
            # Skip if we can't find positions
            if not e1_positions or not e2_positions:
                # Create a synthetic sentence with the entities
                synthetic_text = f"The interaction between {e1_name} and {e2_name} was reported."
                e1_start = synthetic_text.find(e1_name)
                e1_end = e1_start + len(e1_name)
                e2_start = synthetic_text.find(e2_name)
                e2_end = e2_start + len(e2_name)
                
                text_to_use = synthetic_text
                e1_pos = [e1_start, e1_end]
                e2_pos = [e2_start, e2_end]
            else:
                text_to_use = full_text
                e1_pos = e1_positions[0]
                e2_pos = e2_positions[0]
            
            # Create text with entity markers
            # Check for overlaps and enforce order
            p1_start, p1_end = e1_pos
            p2_start, p2_end = e2_pos
            
            # 1. Start Check overlap
            # Intersection: max(start1, start2) < min(end1, end2)
            if max(p1_start, p2_start) < min(p1_end, p2_end):
                # Overlap detected, skip this pair
                continue
            
            # 2. Enforce order: [E1] must be the first entity in text
            if p1_start < p2_start:
                # e1 is already first
                final_e1_name = e1_name
                final_e1_id = entity1_id
                final_e1_pos = e1_pos
                
                final_e2_name = e2_name
                final_e2_id = entity2_id
                final_e2_pos = e2_pos
            else:
                # e2 is first, swap them
                final_e1_name = e2_name
                final_e1_id = entity2_id
                final_e1_pos = e2_pos
                
                final_e2_name = e1_name
                final_e2_id = entity1_id
                final_e2_pos = e1_pos
            
            # Create text with entity markers using the ordered entities
            # Now we know final_e1_pos is before final_e2_pos and no overlap
            text_with_markers, e1_end_marked, e2_end_marked = insert_entity_markers(
                text_to_use, 
                final_e1_pos[0], final_e1_pos[1],
                final_e2_pos[0], final_e2_pos[1]
            )
            
            e1_idx_in_marked = [e1_end_marked - (final_e1_pos[1] - final_e1_pos[0]), e1_end_marked]
            e2_idx_in_marked = [e2_end_marked - (final_e2_pos[1] - final_e2_pos[0]), e2_end_marked]
            
            # Create the record in unified format
            record = {
                "id": f"BioRED.d{pmid}.s0_BioRED.d{pmid}.s0.p{pair_counter}",
                "text": text_to_use,
                "text_with_entity_marker": text_with_markers,
                "relation": [{
                    "relation_type": "positive",  # All BioRED PPI are positive (interaction exists)
                    "relation_id": 0,
                    "original_relation_type": relation_type,  # BioRED specific type
                    "entity_1": final_e1_name,
                    "entity_1_idx": [final_e1_pos],
                    "entity_1_idx_in_text_with_entity_marker": e1_idx_in_marked,
                    "entity_1_type": "protein",
                    "entity_1_type_id": 0,
                    "entity_1_ncbi_id": final_e1_id,  # Additional BioRED-specific info
                    "entity_2": final_e2_name,
                    "entity_2_idx": [final_e2_pos],
                    "entity_2_idx_in_text_with_entity_marker": e2_idx_in_marked,
                    "entity_2_type": "protein",
                    "entity_2_type_id": 0,
                    "entity_2_ncbi_id": final_e2_id  # Additional BioRED-specific info
                }],
                "directed": False,
                "reverse": False,
                "source": "BioRED",
                "pmid": pmid
            }
            
            converted_records.append(record)
            pair_counter += 1
    
    return converted_records


def save_converted_data(records: List[Dict], output_path: str | Path):
    """Save converted records in JSONL format (one JSON per line)."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')


def run_biored_conversion(datasets: List[Tuple[Path, Path]]) -> List[Dict]:
    results: List[Dict] = []
    for input_file, output_file in datasets:
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        records = extract_ppi_from_bioc_json(input_file)
        save_converted_data(records, output_file)
        type_counts = {}
        for record in records:
            orig_type = record["relation"][0].get("original_relation_type", "Unknown")
            type_counts[orig_type] = type_counts.get(orig_type, 0) + 1

        results.append(
            {
                "input_path": str(input_file),
                "output_path": str(output_file),
                "record_count": len(records),
                "unique_pmids": len({record.get("pmid", "") for record in records}),
                "original_relation_types": type_counts,
            }
        )
    return results


def print_summary(records: List[Dict]):
    """Print summary statistics."""
    print("\n" + "="*60)
    print("BioRED PPI Conversion Summary")
    print("="*60)
    print(f"Total converted records: {len(records)}")
    
    # Count by original relation type
    type_counts = {}
    for record in records:
        orig_type = record["relation"][0].get("original_relation_type", "Unknown")
        type_counts[orig_type] = type_counts.get(orig_type, 0) + 1
    
    print("\nOriginal Relation Types Distribution:")
    for rel_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {rel_type}: {count}")
    
    # Count unique PMIDs
    unique_pmids = set(r.get("pmid", "") for r in records)
    print(f"\nUnique PMIDs: {len(unique_pmids)}")
    
    print("\n" + "-"*60)
    print("Sample Records (first 3):")
    print("-"*60)
    
    for i, record in enumerate(records[:3]):
        print(f"\n[{i+1}] ID: {record['id']}")
        print(f"    Text: {record['text'][:100]}...")
        rel = record["relation"][0]
        print(f"    Entities: {rel['entity_1']} <-> {rel['entity_2']}")
        print(f"    Original Type: {rel['original_relation_type']}")
        print(f"    Relation Type: {rel['relation_type']}")


def main():
    """Main function to convert BioRED PPI data."""

    import argparse

    parser = argparse.ArgumentParser(description="Convert BioRED BioC JSON files into the shared PPI JSONL format.")
    parser.add_argument("--root", help="Override the repository root.")
    parser.add_argument("--input", help="Single input BioC JSON file to convert.")
    parser.add_argument("--output", help="Output path for a single conversion.")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.root)
    if args.input or args.output:
        if not (args.input and args.output):
            raise SystemExit("Use --input and --output together for a single-file conversion.")
        datasets = [(Path(args.input).resolve(), Path(args.output).resolve())]
    else:
        datasets = [
            (repo_root / "BioRED" / "raw" / "Train.BioC.JSON", repo_root / "BioRED" / "derived" / "biored_train_ppi_converted.json"),
            (repo_root / "BioRED" / "raw" / "Dev.BioC.JSON", repo_root / "BioRED" / "derived" / "biored_dev_ppi_converted.json"),
            (repo_root / "BioRED" / "raw" / "Test.BioC.JSON", repo_root / "BioRED" / "derived" / "biored_test_ppi_converted.json"),
        ]

    print("BioRED PPI Data Converter")
    print("=" * 60)
    results = run_biored_conversion(datasets)
    for item in results:
        print(f"\nProcessed: {item['input_path']}")
        print(f"Output: {item['output_path']}")
        print(f"Records: {item['record_count']}")
        print(f"Unique PMIDs: {item['unique_pmids']}")
    print("\n" + "=" * 60)
    print("All conversions complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
