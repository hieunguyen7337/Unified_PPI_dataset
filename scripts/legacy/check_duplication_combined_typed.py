"""
Script to check for duplication between the combined 5 datasets and the Typed_PPI dataset.
Compares fold 0 only.
"""

import json
from pathlib import Path
from collections import defaultdict


def load_ids_from_file(file_path):
    """Load all sample IDs from a JSON lines file."""
    ids = set()
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data = json.loads(line)
                ids.add(data['id'])
    return ids


def load_samples_from_file(file_path):
    """Load all samples as a dict keyed by ID."""
    samples = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data = json.loads(line)
                samples[data['id']] = data
    return samples


def main():
    base_path = Path(__file__).parent
    fold_num = 0
    
    # Paths
    combined_test = base_path / 'combined_datasets' / f'combined_test_{fold_num}.json'
    combined_train = base_path / 'combined_datasets' / f'combined_train_{fold_num}.json'
    combined_all = base_path / 'combined_datasets' / f'combined_all_{fold_num}.json'
    
    typed_ppi_path = base_path / 'type_annotation' / 'Typed_PPI'
    typed_test = typed_ppi_path / f'test_{fold_num}.json'
    typed_train = typed_ppi_path / f'train_{fold_num}.json'
    
    print("=" * 80)
    print(f"DUPLICATION CHECK: Combined 5 Datasets vs Typed_PPI (Fold {fold_num})")
    print("=" * 80)
    
    # Load IDs from combined datasets
    print("\nLoading Combined Datasets...")
    combined_test_ids = load_ids_from_file(combined_test)
    combined_train_ids = load_ids_from_file(combined_train)
    combined_all_ids = combined_test_ids | combined_train_ids
    print(f"  Combined Test: {len(combined_test_ids):,} samples")
    print(f"  Combined Train: {len(combined_train_ids):,} samples")
    print(f"  Combined All: {len(combined_all_ids):,} unique samples")
    
    # Load IDs from Typed_PPI
    print("\nLoading Typed_PPI Dataset...")
    typed_test_ids = load_ids_from_file(typed_test)
    typed_train_ids = load_ids_from_file(typed_train)
    typed_all_ids = typed_test_ids | typed_train_ids
    print(f"  Typed_PPI Test: {len(typed_test_ids):,} samples")
    print(f"  Typed_PPI Train: {len(typed_train_ids):,} samples")
    print(f"  Typed_PPI All: {len(typed_all_ids):,} unique samples")
    
    # Check for overlaps
    print("\n" + "=" * 80)
    print("OVERLAP ANALYSIS")
    print("=" * 80)
    
    # Test vs Test overlap
    test_test_overlap = combined_test_ids & typed_test_ids
    print(f"\n1. Combined Test vs Typed_PPI Test:")
    print(f"   Overlapping IDs: {len(test_test_overlap):,}")
    if test_test_overlap:
        print(f"   Sample overlapping IDs: {list(test_test_overlap)[:5]}")
    
    # Train vs Train overlap
    train_train_overlap = combined_train_ids & typed_train_ids
    print(f"\n2. Combined Train vs Typed_PPI Train:")
    print(f"   Overlapping IDs: {len(train_train_overlap):,}")
    if train_train_overlap:
        print(f"   Sample overlapping IDs: {list(train_train_overlap)[:5]}")
    
    # Combined Test vs Typed_PPI Train
    test_train_overlap = combined_test_ids & typed_train_ids
    print(f"\n3. Combined Test vs Typed_PPI Train:")
    print(f"   Overlapping IDs: {len(test_train_overlap):,}")
    if test_train_overlap:
        print(f"   Sample overlapping IDs: {list(test_train_overlap)[:5]}")
    
    # Combined Train vs Typed_PPI Test
    train_test_overlap = combined_train_ids & typed_test_ids
    print(f"\n4. Combined Train vs Typed_PPI Test:")
    print(f"   Overlapping IDs: {len(train_test_overlap):,}")
    if train_test_overlap:
        print(f"   Sample overlapping IDs: {list(train_test_overlap)[:5]}")
    
    # Overall overlap
    all_overlap = combined_all_ids & typed_all_ids
    print(f"\n5. Combined All vs Typed_PPI All (Total Overlap):")
    print(f"   Overlapping IDs: {len(all_overlap):,}")
    if all_overlap:
        print(f"   Sample overlapping IDs: {list(all_overlap)[:10]}")
    
    # Calculate percentages
    print("\n" + "=" * 80)
    print("OVERLAP PERCENTAGES")
    print("=" * 80)
    
    if combined_all_ids:
        pct_combined_in_typed = (len(all_overlap) / len(combined_all_ids)) * 100
        print(f"\n  {len(all_overlap):,} / {len(combined_all_ids):,} Combined samples found in Typed_PPI")
        print(f"  = {pct_combined_in_typed:.2f}% of Combined dataset")
    
    if typed_all_ids:
        pct_typed_in_combined = (len(all_overlap) / len(typed_all_ids)) * 100
        print(f"\n  {len(all_overlap):,} / {len(typed_all_ids):,} Typed_PPI samples found in Combined")
        print(f"  = {pct_typed_in_combined:.2f}% of Typed_PPI dataset")
    
    # Unique samples in each
    only_in_combined = combined_all_ids - typed_all_ids
    only_in_typed = typed_all_ids - combined_all_ids
    
    print("\n" + "=" * 80)
    print("UNIQUE SAMPLES")
    print("=" * 80)
    print(f"\n  Samples ONLY in Combined (not in Typed_PPI): {len(only_in_combined):,}")
    print(f"  Samples ONLY in Typed_PPI (not in Combined): {len(only_in_typed):,}")
    print(f"  Samples in BOTH datasets: {len(all_overlap):,}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if len(all_overlap) == 0:
        print("\n[RESULT] NO DUPLICATES FOUND between Combined and Typed_PPI datasets!")
        print("         The datasets are completely independent.")
    else:
        print(f"\n[RESULT] DUPLICATES FOUND: {len(all_overlap):,} samples exist in both datasets.")
        print(f"         This represents {pct_combined_in_typed:.2f}% of combined and {pct_typed_in_combined:.2f}% of Typed_PPI.")
    
    # Save report
    report_path = base_path / 'duplication_check_report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write(f"DUPLICATION CHECK REPORT: Combined 5 Datasets vs Typed_PPI (Fold {fold_num})\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("Dataset Sizes:\n")
        f.write(f"  Combined Test: {len(combined_test_ids):,}\n")
        f.write(f"  Combined Train: {len(combined_train_ids):,}\n")
        f.write(f"  Combined All: {len(combined_all_ids):,}\n\n")
        f.write(f"  Typed_PPI Test: {len(typed_test_ids):,}\n")
        f.write(f"  Typed_PPI Train: {len(typed_train_ids):,}\n")
        f.write(f"  Typed_PPI All: {len(typed_all_ids):,}\n\n")
        
        f.write("Overlap Analysis:\n")
        f.write(f"  Combined Test vs Typed_PPI Test: {len(test_test_overlap):,}\n")
        f.write(f"  Combined Train vs Typed_PPI Train: {len(train_train_overlap):,}\n")
        f.write(f"  Combined Test vs Typed_PPI Train: {len(test_train_overlap):,}\n")
        f.write(f"  Combined Train vs Typed_PPI Test: {len(train_test_overlap):,}\n")
        f.write(f"  Total Overlap: {len(all_overlap):,}\n\n")
        
        f.write("Unique Samples:\n")
        f.write(f"  Only in Combined: {len(only_in_combined):,}\n")
        f.write(f"  Only in Typed_PPI: {len(only_in_typed):,}\n")
        f.write(f"  In Both: {len(all_overlap):,}\n\n")
        
        if all_overlap:
            f.write("Overlapping IDs (first 50):\n")
            for i, id_ in enumerate(sorted(list(all_overlap))[:50]):
                f.write(f"  {i+1}. {id_}\n")
    
    print(f"\nReport saved to: {report_path}")
    print("=" * 80)


if __name__ == '__main__':
    main()
