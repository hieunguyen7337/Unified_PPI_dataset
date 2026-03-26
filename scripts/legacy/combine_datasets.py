"""
Script to combine test_0.json and train_0.json files from all 5 datasets.

This script will:
1. Combine all test_0.json files from AImed, BioInfer, HPRD50, IEPA, and LLL
2. Combine all train_0.json files from the same 5 datasets
3. Create a fully combined dataset (test_0 + train_0 from all 5 datasets)
"""

import json
from pathlib import Path
from collections import defaultdict


def load_samples_from_file(file_path):
    """Load all samples from a JSON lines file."""
    samples = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data = json.loads(line)
                samples.append(data)
    return samples


def write_samples_to_file(samples, output_path):
    """Write samples to a JSON lines file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')


def combine_datasets(base_path, datasets, fold_num=0):
    """
    Combine test and train files from multiple datasets.
    
    Args:
        base_path: Path to the original folder containing datasets
        datasets: List of dataset names
        fold_num: Fold number to combine (default: 0)
    
    Returns:
        Dictionary with combined test, train, and all samples
    """
    combined = {
        'test': [],
        'train': [],
        'all': []
    }
    
    stats = {
        'test_counts': {},
        'train_counts': {},
        'total_counts': {}
    }
    
    for dataset in datasets:
        dataset_path = base_path / dataset
        test_file = dataset_path / f'test_{fold_num}.json'
        train_file = dataset_path / f'train_{fold_num}.json'
        
        if test_file.exists():
            test_samples = load_samples_from_file(test_file)
            combined['test'].extend(test_samples)
            combined['all'].extend(test_samples)
            stats['test_counts'][dataset] = len(test_samples)
            print(f"  Loaded {len(test_samples):,} test samples from {dataset}")
        else:
            print(f"  WARNING: Test file not found: {test_file}")
            stats['test_counts'][dataset] = 0
        
        if train_file.exists():
            train_samples = load_samples_from_file(train_file)
            combined['train'].extend(train_samples)
            combined['all'].extend(train_samples)
            stats['train_counts'][dataset] = len(train_samples)
            print(f"  Loaded {len(train_samples):,} train samples from {dataset}")
        else:
            print(f"  WARNING: Train file not found: {train_file}")
            stats['train_counts'][dataset] = 0
        
        stats['total_counts'][dataset] = stats['test_counts'][dataset] + stats['train_counts'][dataset]
    
    return combined, stats


def check_for_duplicates(samples):
    """Check for duplicate IDs in the samples."""
    ids = [s['id'] for s in samples]
    unique_ids = set(ids)
    
    if len(ids) != len(unique_ids):
        duplicates = defaultdict(int)
        for id_ in ids:
            duplicates[id_] += 1
        
        duplicate_ids = {k: v for k, v in duplicates.items() if v > 1}
        return True, len(duplicate_ids), duplicate_ids
    
    return False, 0, {}


def main():
    # Configuration
    base_path = Path(__file__).parent / 'original'
    output_dir = Path(__file__).parent / 'combined_datasets'
    datasets = ['AImed', 'BioInfer', 'HPRD50', 'IEPA', 'LLL']
    fold_num = 0
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 80)
    print(f"COMBINING DATASETS FROM FOLD {fold_num}")
    print("=" * 80)
    print(f"\nDatasets to combine: {', '.join(datasets)}")
    print(f"Output directory: {output_dir}\n")
    
    # Combine datasets
    print("Loading and combining files...")
    combined, stats = combine_datasets(base_path, datasets, fold_num)
    
    # Print statistics
    print("\n" + "=" * 80)
    print("COMBINATION STATISTICS")
    print("=" * 80)
    print(f"\n{'Dataset':<15} {'Test Samples':<15} {'Train Samples':<15} {'Total':<15}")
    print("-" * 60)
    
    for dataset in datasets:
        print(f"{dataset:<15} {stats['test_counts'][dataset]:>14,} {stats['train_counts'][dataset]:>14,} {stats['total_counts'][dataset]:>14,}")
    
    print("-" * 60)
    print(f"{'COMBINED':<15} {len(combined['test']):>14,} {len(combined['train']):>14,} {len(combined['all']):>14,}")
    
    # Check for duplicates
    print("\n" + "=" * 80)
    print("DUPLICATE CHECK")
    print("=" * 80)
    
    has_dup_test, num_dup_test, dup_ids_test = check_for_duplicates(combined['test'])
    has_dup_train, num_dup_train, dup_ids_train = check_for_duplicates(combined['train'])
    has_dup_all, num_dup_all, dup_ids_all = check_for_duplicates(combined['all'])
    
    if has_dup_test:
        print(f"[WARNING] Combined test set has {num_dup_test} duplicate IDs")
        if num_dup_test <= 10:
            for id_, count in list(dup_ids_test.items())[:10]:
                print(f"  - {id_}: appears {count} times")
    else:
        print("[PASS] Combined test set has no duplicate IDs")
    
    if has_dup_train:
        print(f"[WARNING] Combined train set has {num_dup_train} duplicate IDs")
        if num_dup_train <= 10:
            for id_, count in list(dup_ids_train.items())[:10]:
                print(f"  - {id_}: appears {count} times")
    else:
        print("[PASS] Combined train set has no duplicate IDs")
    
    if has_dup_all:
        print(f"[WARNING] Combined full dataset has {num_dup_all} duplicate IDs")
    else:
        print("[PASS] Combined full dataset has no duplicate IDs")
    
    # Write combined files
    print("\n" + "=" * 80)
    print("WRITING OUTPUT FILES")
    print("=" * 80)
    
    test_output = output_dir / f'combined_test_{fold_num}.json'
    train_output = output_dir / f'combined_train_{fold_num}.json'
    all_output = output_dir / f'combined_all_{fold_num}.json'
    
    write_samples_to_file(combined['test'], test_output)
    print(f"[SAVED] Combined test file: {test_output}")
    print(f"        {len(combined['test']):,} samples")
    
    write_samples_to_file(combined['train'], train_output)
    print(f"[SAVED] Combined train file: {train_output}")
    print(f"        {len(combined['train']):,} samples")
    
    write_samples_to_file(combined['all'], all_output)
    print(f"[SAVED] Combined full dataset: {all_output}")
    print(f"        {len(combined['all']):,} samples")
    
    # Write summary report
    report_path = output_dir / f'combination_report_fold_{fold_num}.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write(f"DATASET COMBINATION REPORT - FOLD {fold_num}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Datasets combined: {', '.join(datasets)}\n\n")
        
        f.write("Individual Dataset Statistics:\n")
        f.write("-" * 60 + "\n")
        f.write(f"{'Dataset':<15} {'Test Samples':<15} {'Train Samples':<15} {'Total':<15}\n")
        f.write("-" * 60 + "\n")
        
        for dataset in datasets:
            f.write(f"{dataset:<15} {stats['test_counts'][dataset]:>14,} "
                   f"{stats['train_counts'][dataset]:>14,} {stats['total_counts'][dataset]:>14,}\n")
        
        f.write("-" * 60 + "\n")
        f.write(f"{'COMBINED':<15} {len(combined['test']):>14,} "
               f"{len(combined['train']):>14,} {len(combined['all']):>14,}\n")
        f.write("-" * 60 + "\n\n")
        
        f.write("Output Files:\n")
        f.write(f"  - Combined test: {test_output.name} ({len(combined['test']):,} samples)\n")
        f.write(f"  - Combined train: {train_output.name} ({len(combined['train']):,} samples)\n")
        f.write(f"  - Combined all: {all_output.name} ({len(combined['all']):,} samples)\n\n")
        
        f.write("Duplicate Check:\n")
        f.write(f"  - Test set duplicates: {'Yes' if has_dup_test else 'No'}\n")
        f.write(f"  - Train set duplicates: {'Yes' if has_dup_train else 'No'}\n")
        f.write(f"  - Full dataset duplicates: {'Yes' if has_dup_all else 'No'}\n")
    
    print(f"\n[SAVED] Summary report: {report_path}")
    
    print("\n" + "=" * 80)
    print("COMBINATION COMPLETE!")
    print("=" * 80)


if __name__ == '__main__':
    main()
