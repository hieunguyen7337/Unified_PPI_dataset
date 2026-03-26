"""
Script to verify 10-fold cross-validation structure in AImed dataset.

This script checks:
1. If the dataset is properly split into 10 folds (0-9)
2. If each fold's test and train files are mutually exclusive (no overlap)
3. If combining test and train files of the same fold number forms the complete dataset
4. If all folds contain the same total samples (test + train)
"""

import json
import os
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


def verify_10fold_cv(dataset_path):
    """
    Verify that the dataset follows proper 10-fold cross-validation structure.
    
    Args:
        dataset_path: Path to the dataset folder (e.g., AImed folder)
    
    Returns:
        Dictionary containing verification results
    """
    results = {
        'is_valid_10fold': True,
        'num_folds': 0,
        'fold_details': {},
        'total_unique_samples': 0,
        'issues': []
    }
    
    dataset_path = Path(dataset_path)
    
    # Collect all test and train files
    test_files = sorted(dataset_path.glob('test_*.json'))
    train_files = sorted(dataset_path.glob('train_*.json'))
    
    # Check if we have 10 folds
    test_fold_nums = set()
    train_fold_nums = set()
    
    for f in test_files:
        fold_num = int(f.stem.split('_')[1])
        test_fold_nums.add(fold_num)
    
    for f in train_files:
        fold_num = int(f.stem.split('_')[1])
        train_fold_nums.add(fold_num)
    
    results['num_folds'] = len(test_fold_nums)
    
    if test_fold_nums != train_fold_nums:
        results['is_valid_10fold'] = False
        results['issues'].append(f"Mismatch between test and train fold numbers. Test: {test_fold_nums}, Train: {train_fold_nums}")
        return results
    
    if len(test_fold_nums) != 10:
        results['is_valid_10fold'] = False
        results['issues'].append(f"Expected 10 folds, found {len(test_fold_nums)} folds")
    
    # Load all samples for each fold
    all_fold_ids = []  # Will store the union of test + train for each fold
    all_samples_ever = set()
    
    for fold_num in sorted(test_fold_nums):
        test_file = dataset_path / f'test_{fold_num}.json'
        train_file = dataset_path / f'train_{fold_num}.json'
        
        test_ids = load_ids_from_file(test_file)
        train_ids = load_ids_from_file(train_file)
        
        # Store fold details
        results['fold_details'][fold_num] = {
            'test_count': len(test_ids),
            'train_count': len(train_ids),
            'total_count': len(test_ids) + len(train_ids),
            'test_file': str(test_file),
            'train_file': str(train_file)
        }
        
        # Check for overlap between test and train within the fold
        overlap = test_ids & train_ids
        if overlap:
            results['is_valid_10fold'] = False
            results['issues'].append(f"Fold {fold_num}: {len(overlap)} samples appear in both test and train sets")
            results['fold_details'][fold_num]['overlap_count'] = len(overlap)
            results['fold_details'][fold_num]['overlap_sample'] = list(overlap)[:5]  # Show first 5
        else:
            results['fold_details'][fold_num]['overlap_count'] = 0
        
        # Combine test and train for this fold
        fold_combined = test_ids | train_ids
        all_fold_ids.append(fold_combined)
        all_samples_ever.update(fold_combined)
    
    results['total_unique_samples'] = len(all_samples_ever)
    
    # Check if all folds have the same combined size
    fold_sizes = [len(fold_ids) for fold_ids in all_fold_ids]
    if len(set(fold_sizes)) > 1:
        results['issues'].append(f"Folds have different total sizes: {fold_sizes}")
    
    # Check if all folds combine to form the same complete dataset
    reference_set = all_fold_ids[0]
    for i, fold_ids in enumerate(all_fold_ids[1:], 1):
        if fold_ids != reference_set:
            missing_in_current = reference_set - fold_ids
            extra_in_current = fold_ids - reference_set
            
            if missing_in_current:
                results['issues'].append(f"Fold {i}: {len(missing_in_current)} samples missing compared to fold 0")
            if extra_in_current:
                results['issues'].append(f"Fold {i}: {len(extra_in_current)} extra samples compared to fold 0")
    
    # Check if test samples across folds cover all samples
    all_test_ids = set()
    test_id_counts = defaultdict(int)
    
    for fold_num in sorted(test_fold_nums):
        test_file = dataset_path / f'test_{fold_num}.json'
        test_ids = load_ids_from_file(test_file)
        all_test_ids.update(test_ids)
        for tid in test_ids:
            test_id_counts[tid] += 1
    
    # Check if every sample appears exactly once in test sets across all folds
    samples_not_in_any_test = all_samples_ever - all_test_ids
    if samples_not_in_any_test:
        results['issues'].append(f"{len(samples_not_in_any_test)} samples never appear in any test set")
    
    # Check if any sample appears in multiple test sets
    samples_in_multiple_tests = {k for k, v in test_id_counts.items() if v > 1}
    if samples_in_multiple_tests:
        results['issues'].append(f"{len(samples_in_multiple_tests)} samples appear in multiple test sets")
        # Show which samples and how many times
        multi_count_dist = defaultdict(int)
        for sample_id in samples_in_multiple_tests:
            multi_count_dist[test_id_counts[sample_id]] += 1
        results['multi_test_distribution'] = dict(multi_count_dist)
    
    # Check if all test sets combined equals the full dataset
    if all_test_ids == all_samples_ever:
        results['all_test_sets_cover_full_dataset'] = True
    else:
        results['all_test_sets_cover_full_dataset'] = False
        missing = all_samples_ever - all_test_ids
        extra = all_test_ids - all_samples_ever
        if missing:
            results['samples_missing_from_test_union'] = len(missing)
        if extra:
            results['extra_samples_in_test_union'] = len(extra)
    
    return results


def print_report(results, dataset_name):
    """Print a formatted report of the verification results."""
    print("=" * 80)
    print(f"10-Fold Cross-Validation Verification Report: {dataset_name}")
    print("=" * 80)
    
    print(f"\nNumber of folds detected: {results['num_folds']}")
    print(f"Total unique samples in dataset: {results['total_unique_samples']}")
    print(f"Valid 10-fold CV structure: {'[PASS] YES' if results['is_valid_10fold'] else '[FAIL] NO'}")
    
    print("\n" + "-" * 40)
    print("Fold Details:")
    print("-" * 40)
    print(f"{'Fold':<6} {'Test':<10} {'Train':<10} {'Total':<10} {'Overlap':<10}")
    print("-" * 46)
    
    for fold_num in sorted(results['fold_details'].keys()):
        details = results['fold_details'][fold_num]
        print(f"{fold_num:<6} {details['test_count']:<10} {details['train_count']:<10} "
              f"{details['total_count']:<10} {details['overlap_count']:<10}")
    
    # Check if all folds have the same total
    totals = [d['total_count'] for d in results['fold_details'].values()]
    if len(set(totals)) == 1:
        print(f"\n[PASS] All folds have the same total count: {totals[0]}")
    else:
        print(f"\n[FAIL] Folds have different total counts: {set(totals)}")
    
    # Report on test coverage
    print("\n" + "-" * 40)
    print("Test Set Coverage Analysis:")
    print("-" * 40)
    
    if results.get('all_test_sets_cover_full_dataset'):
        print("[PASS] All test sets combined cover the entire dataset")
    else:
        print("[FAIL] Test sets do NOT cover the entire dataset")
        if 'samples_missing_from_test_union' in results:
            print(f"  - {results['samples_missing_from_test_union']} samples missing from any test set")
    
    if 'multi_test_distribution' in results:
        print("[FAIL] Some samples appear in multiple test sets:")
        for count, num_samples in sorted(results['multi_test_distribution'].items()):
            print(f"  - {num_samples} samples appear in {count} test sets")
    else:
        print("[PASS] Each sample appears in exactly one test set (proper 10-fold CV)")
    
    if results['issues']:
        print("\n" + "-" * 40)
        print("Issues Found:")
        print("-" * 40)
        for issue in results['issues']:
            print(f"  [!] {issue}")
    else:
        print("\n[PASS] No issues found - dataset is properly structured for 10-fold CV")
    
    print("\n" + "=" * 80)


def main():
    # Path to the datasets
    base_path = Path(__file__).parent / 'original'
    
    # List of datasets to check
    datasets = ['AImed', 'BioInfer', 'HPRD50', 'IEPA', 'LLL']
    
    # Open output file
    output_file = Path(__file__).parent / 'verification_report.txt'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("10-FOLD CROSS-VALIDATION VERIFICATION\n")
        f.write("=" * 80 + "\n")
        
        all_valid = True
        for dataset in datasets:
            dataset_path = base_path / dataset
            if dataset_path.exists():
                f.write(f"\nChecking {dataset}...\n")
                results = verify_10fold_cv(dataset_path)
                write_report(results, dataset, f)
                if not results['is_valid_10fold'] or results['issues']:
                    all_valid = False
            else:
                f.write(f"\n[WARN] Dataset not found: {dataset_path}\n")
                all_valid = False
        
        f.write("\n" + "=" * 80 + "\n")
        if all_valid:
            f.write("SUMMARY: All datasets are properly structured for 10-fold cross-validation!\n")
        else:
            f.write("SUMMARY: Some datasets have issues. Please review the reports above.\n")
        f.write("=" * 80 + "\n")
    
    print(f"Report saved to: {output_file}")


def write_report(results, dataset_name, f):
    """Write a formatted report of the verification results to file."""
    f.write("=" * 80 + "\n")
    f.write(f"10-Fold Cross-Validation Verification Report: {dataset_name}\n")
    f.write("=" * 80 + "\n")
    
    f.write(f"\nNumber of folds detected: {results['num_folds']}\n")
    f.write(f"Total unique samples in dataset: {results['total_unique_samples']}\n")
    f.write(f"Valid 10-fold CV structure: {'[PASS] YES' if results['is_valid_10fold'] else '[FAIL] NO'}\n")
    
    f.write("\n" + "-" * 40 + "\n")
    f.write("Fold Details:\n")
    f.write("-" * 40 + "\n")
    f.write(f"{'Fold':<6} {'Test':<10} {'Train':<10} {'Total':<10} {'Overlap':<10}\n")
    f.write("-" * 46 + "\n")
    
    for fold_num in sorted(results['fold_details'].keys()):
        details = results['fold_details'][fold_num]
        f.write(f"{fold_num:<6} {details['test_count']:<10} {details['train_count']:<10} "
              f"{details['total_count']:<10} {details['overlap_count']:<10}\n")
    
    # Check if all folds have the same total
    totals = [d['total_count'] for d in results['fold_details'].values()]
    if len(set(totals)) == 1:
        f.write(f"\n[PASS] All folds have the same total count: {totals[0]}\n")
    else:
        f.write(f"\n[FAIL] Folds have different total counts: {set(totals)}\n")
    
    # Report on test coverage
    f.write("\n" + "-" * 40 + "\n")
    f.write("Test Set Coverage Analysis:\n")
    f.write("-" * 40 + "\n")
    
    if results.get('all_test_sets_cover_full_dataset'):
        f.write("[PASS] All test sets combined cover the entire dataset\n")
    else:
        f.write("[FAIL] Test sets do NOT cover the entire dataset\n")
        if 'samples_missing_from_test_union' in results:
            f.write(f"  - {results['samples_missing_from_test_union']} samples missing from any test set\n")
    
    if 'multi_test_distribution' in results:
        f.write("[FAIL] Some samples appear in multiple test sets:\n")
        for count, num_samples in sorted(results['multi_test_distribution'].items()):
            f.write(f"  - {num_samples} samples appear in {count} test sets\n")
    else:
        f.write("[PASS] Each sample appears in exactly one test set (proper 10-fold CV)\n")
    
    if results['issues']:
        f.write("\n" + "-" * 40 + "\n")
        f.write("Issues Found:\n")
        f.write("-" * 40 + "\n")
        for issue in results['issues']:
            f.write(f"  [!] {issue}\n")
    else:
        f.write("\n[PASS] No issues found - dataset is properly structured for 10-fold CV\n")
    
    f.write("\n" + "=" * 80 + "\n")


if __name__ == '__main__':
    main()
