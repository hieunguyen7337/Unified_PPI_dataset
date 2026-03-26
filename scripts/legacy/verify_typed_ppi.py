"""
Script to verify 10-fold cross-validation structure in Typed_PPI dataset.
This verifies the type_annotation/Typed_PPI folder.
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


def verify_10fold_cv(dataset_path):
    """
    Verify that the dataset follows proper 10-fold cross-validation structure.
    
    Args:
        dataset_path: Path to the dataset folder
    
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
    all_fold_ids = []
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
            results['fold_details'][fold_num]['overlap_sample'] = list(overlap)[:5]
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


def main():
    # Path to the Typed_PPI dataset
    base_path = Path(__file__).parent / 'type_annotation'
    dataset_path = base_path / 'Typed_PPI'
    
    # Output file
    output_file = Path(__file__).parent / 'typed_ppi_verification_report.txt'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("10-FOLD CROSS-VALIDATION VERIFICATION FOR TYPED_PPI\n")
        f.write("=" * 80 + "\n\n")
        
        if dataset_path.exists():
            f.write(f"Checking Typed_PPI dataset...\n")
            results = verify_10fold_cv(dataset_path)
            write_report(results, 'Typed_PPI', f)
            
            f.write("\n" + "=" * 80 + "\n")
            if results['is_valid_10fold'] and not results['issues']:
                f.write("SUMMARY: Typed_PPI dataset is properly structured for 10-fold cross-validation!\n")
            else:
                f.write("SUMMARY: Typed_PPI dataset has issues. Please review the report above.\n")
            f.write("=" * 80 + "\n")
        else:
            f.write(f"\n[ERROR] Dataset not found: {dataset_path}\n")
    
    print(f"Report saved to: {output_file}")


if __name__ == '__main__':
    main()
