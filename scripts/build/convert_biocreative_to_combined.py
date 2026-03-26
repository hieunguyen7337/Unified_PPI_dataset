"""
Convert Biocreative_VI PMtask_Relations_TrainingSet.json to the combined PPI dataset format.

This script:
1. Loads the BioC format JSON file
2. Segments text into sentences
3. Identifies entity pairs that have relations
4. Creates sentence-level records with entity markers
5. Outputs JSONL format matching combined_all_ppi_dataset_0.json

Output ID format: Biocreative.d{pmid}.s{sent_idx}_Biocreative.d{pmid}.s{sent_idx}.p{pair_idx}
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.utils.common import resolve_repo_root


@dataclass
class Entity:
    """Represents an entity mention in text."""
    text: str
    gene_id: str
    offset: int  # Character offset from document start
    length: int
    entity_type: str = "protein"
    
    @property
    def end_offset(self) -> int:
        return self.offset + self.length


@dataclass
class Sentence:
    """Represents a sentence with its entities."""
    text: str
    start_offset: int  # Character offset from document start
    end_offset: int
    entities: List[Entity] = field(default_factory=list)
    passage_type: str = ""  # "title" or "abstract"


@dataclass
class Relation:
    """Represents a relation between two genes."""
    gene1_id: str
    gene2_id: str
    relation_type: str  # "PPIm" or "PPI"


def simple_sentence_split(text: str) -> List[Tuple[int, int, str]]:
    """
    Simple sentence splitter that handles scientific text.
    Returns list of (start_offset, end_offset, sentence_text).
    """
    # Common abbreviations that don't end sentences
    abbreviations = {'Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Prof.', 'Fig.', 'et al.', 
                     'i.e.', 'e.g.', 'vs.', 'etc.', 'approx.', 'ca.', 'cf.',
                     'no.', 'vol.', 'p.', 'pp.', 'ed.', 'eds.'}
    
    sentences = []
    current_start = 0
    i = 0
    
    while i < len(text):
        char = text[i]
        
        # Check for sentence-ending punctuation
        if char in '.!?':
            # Check if it's followed by space/end and starts with capital (or end of text)
            if i + 1 >= len(text) or (i + 1 < len(text) and text[i + 1] in ' \n\t'):
                # Check if this might be an abbreviation
                is_abbrev = False
                for abbrev in abbreviations:
                    if text[max(0, i - len(abbrev) + 1):i + 1].endswith(abbrev):
                        is_abbrev = True
                        break
                
                # Also check for decimal numbers (e.g., "2.5")
                if not is_abbrev and i > 0 and text[i-1].isdigit():
                    if i + 1 < len(text) and text[i + 1].isdigit():
                        is_abbrev = True
                
                if not is_abbrev:
                    # End of sentence
                    end = i + 1
                    sentence_text = text[current_start:end].strip()
                    if sentence_text:
                        sentences.append((current_start, end, sentence_text))
                    
                    # Skip whitespace for next sentence
                    current_start = i + 1
                    while current_start < len(text) and text[current_start] in ' \n\t':
                        current_start += 1
        i += 1
    
    # Add remaining text as last sentence
    if current_start < len(text):
        remaining = text[current_start:].strip()
        if remaining:
            sentences.append((current_start, len(text), remaining))
    
    return sentences


def find_entities_in_sentence(sentence: Sentence, all_entities: List[Entity]) -> List[Entity]:
    """Find all entities that fall within this sentence's bounds."""
    sentence_entities = []
    for entity in all_entities:
        # Entity is within sentence if its span overlaps
        if entity.offset >= sentence.start_offset and entity.end_offset <= sentence.end_offset:
            sentence_entities.append(entity)
    return sentence_entities


def get_entity_indices_in_sentence(entity: Entity, sentence_start: int) -> List[List[int]]:
    """Get entity character indices relative to sentence start."""
    rel_start = entity.offset - sentence_start
    rel_end = rel_start + entity.length
    return [[rel_start, rel_end]]


def insert_entity_markers(text: str, entity1: Entity, entity2: Entity, sent_start: int) -> str:
    """
    Insert [E1]...[/E1] and [E2]...[/E2] markers around entities.
    Handles the case where entities might overlap or be adjacent.
    """
    # Calculate relative positions
    e1_start = entity1.offset - sent_start
    e1_end = e1_start + entity1.length
    e2_start = entity2.offset - sent_start
    e2_end = e2_start + entity2.length
    
    # Determine order (which entity comes first in text)
    if e1_start <= e2_start:
        first, first_start, first_end = "E1", e1_start, e1_end
        second, second_start, second_end = "E2", e2_start, e2_end
    else:
        first, first_start, first_end = "E2", e2_start, e2_end
        second, second_start, second_end = "E1", e1_start, e1_end
    
    # Build the marked text
    result = text[:first_start]
    result += f"[{first}]" + text[first_start:first_end] + f"[/{first}]"
    result += text[first_end:second_start]
    result += f"[{second}]" + text[second_start:second_end] + f"[/{second}]"
    result += text[second_end:]
    
    return result


def create_record(
    doc_id: str,
    sentence_idx: int,
    pair_idx: int,
    sentence_text: str,
    entity1: Entity,
    entity2: Entity,
    sentence_start: int,
    is_positive: bool
) -> Dict:
    """Create a single record in the target format."""
    
    # Create ID in the same format as AIMed
    base_id = f"Biocreative.d{doc_id}.s{sentence_idx}"
    record_id = f"{base_id}_{base_id}.p{pair_idx}"
    
    # Create text with entity markers
    text_with_markers = insert_entity_markers(
        sentence_text, entity1, entity2, sentence_start
    )
    
    # Get entity indices relative to original sentence
    e1_idx = get_entity_indices_in_sentence(entity1, sentence_start)
    e2_idx = get_entity_indices_in_sentence(entity2, sentence_start)
    
    # Calculate indices in marked text
    e1_start_in_original = entity1.offset - sentence_start
    e2_start_in_original = entity2.offset - sentence_start
    
    # Adjust for marker insertions
    if e1_start_in_original < e2_start_in_original:
        # E1 comes first
        e1_idx_marker = [e1_start_in_original + 4, e1_start_in_original + 4 + entity1.length]  # +4 for "[E1]"
        e2_idx_marker = [e2_start_in_original + 4 + 5 + 4, e2_start_in_original + 4 + 5 + 4 + entity2.length]  # +4+5+4 for "[E1]...[/E1]...[E2]"
    else:
        # E2 comes first  
        e2_idx_marker = [e2_start_in_original + 4, e2_start_in_original + 4 + entity2.length]
        e1_idx_marker = [e1_start_in_original + 4 + 5 + 4, e1_start_in_original + 4 + 5 + 4 + entity1.length]
    
    # Map relation type based on is_positive flag
    mapped_relation_type = "positive" if is_positive else "negative"
    
    record = {
        "id": record_id,
        "text": sentence_text,
        "text_with_entity_marker": text_with_markers,
        "relation": [{
            "relation_type": mapped_relation_type,
            "relation_id": 0,
            "entity_1": entity1.text,
            "entity_1_idx": e1_idx,
            "entity_1_idx_in_text_with_entity_marker": e1_idx_marker[0],
            "entity_1_type": entity1.entity_type,
            "entity_1_type_id": 0,
            "entity_2": entity2.text,
            "entity_2_idx": e2_idx,
            "entity_2_idx_in_text_with_entity_marker": e2_idx_marker[0],
            "entity_2_type": entity2.entity_type,
            "entity_2_type_id": 0
        }],
        "directed": False,
        "reverse": False
    }
    
    return record


def process_document(doc: Dict, negative_multiplier: float = 3.0) -> Tuple[List[Dict], int, int]:
    """
    Process a single document and return all records.
    
    Returns:
        Tuple of (records, positive_count, negative_count)
    """
    records = []
    doc_id = doc["id"]
    positive_count = 0
    negative_count = 0
    
    # Extract all entities from all passages
    all_entities: List[Entity] = []
    full_text = ""
    passage_offsets = []
    
    for passage in doc.get("passages", []):
        passage_offset = passage.get("offset", 0)
        passage_text = passage.get("text", "")
        passage_type = passage.get("infons", {}).get("type", "")
        
        passage_offsets.append((passage_offset, passage_offset + len(passage_text), passage_type))
        
        for annot in passage.get("annotations", []):
            locations = annot.get("locations", [])
            if locations:
                loc = locations[0]
                entity = Entity(
                    text=annot.get("text", ""),
                    gene_id=annot.get("infons", {}).get("NCBI GENE", ""),
                    offset=loc.get("offset", 0),
                    length=loc.get("length", 0),
                    entity_type="protein"
                )
                all_entities.append(entity)
    
    # Build gene_id to entities mapping
    gene_to_entities: Dict[str, List[Entity]] = defaultdict(list)
    for entity in all_entities:
        gene_to_entities[entity.gene_id].append(entity)
    
    # Extract relations and build a set of positive gene pairs
    relations: List[Relation] = []
    positive_gene_pairs: Set[Tuple[str, str]] = set()
    for rel in doc.get("relations", []):
        infons = rel.get("infons", {})
        gene1 = infons.get("Gene1", "")
        gene2 = infons.get("Gene2", "")
        relations.append(Relation(
            gene1_id=gene1,
            gene2_id=gene2,
            relation_type=infons.get("relation", "")
        ))
        # Store both orderings since relations are undirected
        positive_gene_pairs.add((gene1, gene2))
        positive_gene_pairs.add((gene2, gene1))
    
    # Store all sentences with entities for cross-sentence pair generation
    all_sentences: List[Tuple[int, str, List[Entity]]] = []
    
    # Process each passage
    for passage in doc.get("passages", []):
        passage_offset = passage.get("offset", 0)
        passage_text = passage.get("text", "")
        passage_type = passage.get("infons", {}).get("type", "")
        
        # Split passage into sentences
        sentence_splits = simple_sentence_split(passage_text)
        
        for sent_rel_start, sent_rel_end, sent_text in sentence_splits:
            # Calculate absolute offsets
            sent_abs_start = passage_offset + sent_rel_start
            sent_abs_end = passage_offset + sent_rel_end
            
            # Find entities in this sentence
            sent_entities = [
                e for e in all_entities 
                if e.offset >= sent_abs_start and e.end_offset <= sent_abs_end
            ]
            
            # Sort entities by offset to ensure E1 is always textually before E2
            sent_entities.sort(key=lambda x: (x.offset, x.end_offset))
            
            if len(sent_entities) < 2:
                # Still store sentences with 1+ entity for cross-sentence pairs
                if sent_entities:
                    all_sentences.append((sent_abs_start, sent_text, sent_entities))
                continue
            
            # Store for cross-sentence processing
            all_sentences.append((sent_abs_start, sent_text, sent_entities))
            
            # Create a sentence object with relative text
            sentence = Sentence(
                text=sent_text,
                start_offset=sent_abs_start,
                end_offset=sent_abs_end,
                entities=sent_entities,
                passage_type=passage_type
            )
            
            # Generate sentence index based on passage and position
            sent_idx = hash(f"{doc_id}_{sent_abs_start}") % 100000
            
            # Track all entity pairs and which are positive
            pair_idx = 0
            processed_pairs: Set[Tuple[int, int]] = set()  # Track by offsets to avoid duplicates
            
            # Generate ALL entity pairs in this sentence
            for i, e1 in enumerate(sent_entities):
                for j, e2 in enumerate(sent_entities):
                    if i >= j:  # Avoid self-pairs and duplicate orderings
                        continue
                    
                    # Skip if same entity instance (same offset and text)
                    if e1.offset == e2.offset and e1.text == e2.text:
                        continue
                    
                    # Create a canonical pair key (smaller offset first)
                    pair_key = (min(e1.offset, e2.offset), max(e1.offset, e2.offset))
                    if pair_key in processed_pairs:
                        continue
                    processed_pairs.add(pair_key)
                    
                    # Check if this pair has a positive relation
                    is_positive = (e1.gene_id, e2.gene_id) in positive_gene_pairs
                    
                    try:
                        record = create_record(
                            doc_id=doc_id,
                            sentence_idx=sent_idx,
                            pair_idx=pair_idx,
                            sentence_text=sent_text,
                            entity1=e1,
                            entity2=e2,
                            sentence_start=sent_abs_start,
                            is_positive=is_positive
                        )
                        records.append(record)
                        pair_idx += 1
                        if is_positive:
                            positive_count += 1
                        else:
                            negative_count += 1
                    except Exception as e:
                        print(f"Error processing pair in doc {doc_id}: {e}")
                        continue
    
    # Calculate how many more negatives we need (target: negative_multiplier * positive)
    target_negatives = int(positive_count * negative_multiplier)
    needed_negatives = target_negatives - negative_count
    
    # Generate cross-sentence negative pairs if needed
    if needed_negatives > 0 and len(all_sentences) >= 2:
        import random
        cross_sent_negatives = []
        
        # Generate cross-sentence pairs (entities from different sentences)
        for i, (sent_start1, sent_text1, entities1) in enumerate(all_sentences):
            for j, (sent_start2, sent_text2, entities2) in enumerate(all_sentences):
                if i >= j:  # Avoid duplicates
                    continue
                
                # Create pairs between entities in different sentences
                for e1 in entities1:
                    for e2 in entities2:
                        # Skip if same gene (could be co-reference)
                        if e1.gene_id == e2.gene_id:
                            continue
                        # Skip if this is a positive relation
                        if (e1.gene_id, e2.gene_id) in positive_gene_pairs:
                            continue
                        
                        # Use the first sentence as the context
                        cross_sent_negatives.append((sent_start1, sent_text1, e1, e2))
        
        # Randomly sample needed negatives
        if len(cross_sent_negatives) > needed_negatives:
            cross_sent_negatives = random.sample(cross_sent_negatives, needed_negatives)
        
        # Create records for cross-sentence negatives
        cross_pair_idx = 0
        for sent_start, sent_text, e1, e2 in cross_sent_negatives:
            sent_idx = hash(f"{doc_id}_{sent_start}_cross") % 100000
            
            # For cross-sentence pairs, we use the first entity's sentence
            # and create a synthetic text with markers for context
            try:
                record = create_record(
                    doc_id=doc_id,
                    sentence_idx=sent_idx,
                    pair_idx=cross_pair_idx,
                    sentence_text=sent_text,
                    entity1=e1,
                    entity2=e2,
                    sentence_start=sent_start,
                    is_positive=False
                )
                records.append(record)
                negative_count += 1
                cross_pair_idx += 1
            except Exception as e:
                continue
    
    return records, positive_count, negative_count


def convert_biocreative_to_combined(input_path: str | Path, output_path: str | Path) -> Dict:
    """
    Main conversion function.
    
    Args:
        input_path: Path to PMtask_Relations_TrainingSet.json
        output_path: Path for output JSONL file
    
    Returns:
        Statistics dictionary
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    print(f"Loading {input_path}...")
    with input_path.open('r', encoding='utf-8') as f:
        data = json.load(f)
    
    documents = data.get("documents", [])
    print(f"Found {len(documents)} documents")
    
    all_records = []
    docs_with_records = 0
    total_positive = 0
    total_negative = 0
    
    for i, doc in enumerate(documents):
        if (i + 1) % 100 == 0:
            print(f"Processing document {i + 1}/{len(documents)}...")
        
        records, pos_count, neg_count = process_document(doc)
        if records:
            docs_with_records += 1
            all_records.extend(records)
            total_positive += pos_count
            total_negative += neg_count
    
    print(f"\nWriting {len(all_records)} records to {output_path}...")
    
    # Write as JSONL (one JSON per line, matching target format)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8') as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    # Count positive and negative
    positive_count = sum(1 for r in all_records if r['relation'][0]['relation_type'] == 'positive')
    negative_count = sum(1 for r in all_records if r['relation'][0]['relation_type'] == 'negative')
    
    stats = {
        "total_documents": len(documents),
        "documents_with_records": docs_with_records,
        "total_records": len(all_records),
        "positive_records": total_positive,
        "negative_records": total_negative,
        "output_file": str(output_path)
    }
    
    print(f"\nConversion complete!")
    print(f"  Documents processed: {stats['total_documents']}")
    print(f"  Documents with records: {stats['documents_with_records']}")
    print(f"  Total records generated: {stats['total_records']}")
    print(f"  Positive records: {stats['positive_records']}")
    print(f"  Negative records: {stats['negative_records']}")
    
    return stats


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert BioCreative VI to the shared PPI JSONL format.")
    parser.add_argument("--root", help="Override the repository root.")
    parser.add_argument("--input", "-i", help="Input JSON file path.")
    parser.add_argument("--output", "-o", help="Output JSONL file path.")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.root)
    input_path = (
        Path(args.input).resolve()
        if args.input
        else repo_root / "Biocreative_VI" / "raw" / "PMtask_Relations_TrainingSet.json"
    )
    output_path = (
        Path(args.output).resolve()
        if args.output
        else repo_root / "Biocreative_VI" / "derived" / "biocreative_vi_converted.json"
    )

    convert_biocreative_to_combined(input_path, output_path)
