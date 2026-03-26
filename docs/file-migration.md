# File Migration

This cleanup preserved the top-level dataset folders while relocating files into `raw/`, `derived/`, `reports/`, and `archive/`.

Exception: `Unclean_combined_dataset/` and `Unified_PPI_dataset/` are output-only folders, so they intentionally do not contain `raw/`.

## Scripts

- `analyze_cleaned_combined_dataset.py` -> `scripts/analyze/analyze_cleaned_combined_dataset.py`
- `analyze_duplicates.py` -> `scripts/analyze/analyze_duplicates.py`
- `analyze_duplicate_consistency.py` -> `scripts/analyze/analyze_duplicate_consistency.py`
- `combine_datasets.py` -> `scripts/build/combine_datasets.py`
- `clean_unified_ppi_dataset.py` -> `scripts/build/clean_unified_ppi_dataset.py`
- `deduplicate_ppi.py` -> `scripts/build/deduplicate_ppi.py`
- `print_results.py` -> `scripts/utils/print_results.py`
- `5_PPI_dataset/analyze_ppi.py` -> `scripts/analyze/analyze_ppi.py`
- `5_PPI_dataset/extract_missing.py` -> `scripts/analyze/extract_missing_markers.py`
- `Biocreative_VI/analyze_biocreative.py` -> `scripts/analyze/analyze_biocreative.py`
- `Biocreative_VI/convert_biocreative_to_combined.py` -> `scripts/build/convert_biocreative_to_combined.py`
- `BioRED/convert_biored_ppi.py` -> `scripts/build/convert_biored_ppi.py`
- `BioRED/count_biored_stats.py` -> `scripts/analyze/count_biored_stats.py`
- `BioRED/count_sentences.py` -> `scripts/analyze/count_sentence_distribution.py`
- `Unified_PPI_dataset/convert_unified_to_pubtator.py` -> `scripts/build/convert_unified_to_pubtator.py`
- `PPI/combine_datasets.py` -> `scripts/legacy/combine_datasets.py`
- `PPI/verify_10fold_cv.py` -> `scripts/legacy/verify_10fold_cv.py`
- `PPI/verify_typed_ppi.py` -> `scripts/legacy/verify_typed_ppi.py`
- `PPI/check_duplication_combined_typed.py` -> `scripts/legacy/check_duplication_combined_typed.py`

## Key Data and Reports

- `PPI/original/AImed` -> `5_PPI_dataset/raw/AImed`
- `PPI/original/BioInfer` -> `5_PPI_dataset/raw/BioInfer`
- `PPI/original/HPRD50` -> `5_PPI_dataset/raw/HPRD50`
- `PPI/original/IEPA` -> `5_PPI_dataset/raw/IEPA`
- `PPI/original/LLL` -> `5_PPI_dataset/raw/LLL`
- `5_PPI_dataset/combined_train_0.json` -> `5_PPI_dataset/derived/combined_train_0.json`
- `5_PPI_dataset/combined_test_0.json` -> `5_PPI_dataset/derived/combined_test_0.json`
- `5_PPI_dataset/combined_all_ppi_dataset_0.json` -> `5_PPI_dataset/derived/combined_all_ppi_dataset_0.json`
- `5_PPI_dataset/overlap_markers_extracted.json` -> `5_PPI_dataset/derived/missing_markers_extracted.json`
- `PPI/combined_datasets/*` -> `5_PPI_dataset/archive/legacy_combined_datasets/*`
- `PPI/5_dataset_verification_report.txt` -> `5_PPI_dataset/archive/legacy_reports/5_dataset_verification_report.txt`
- `PPI/duplication_check_report.txt` -> `5_PPI_dataset/archive/legacy_reports/duplication_check_report.txt`
- `PPI/type_annotation/Typed_PPI/*` -> `Typed_PPI_dataset/raw/Typed_PPI/*`
- `PPI/type_annotation/annotation_resources/*` -> `Typed_PPI_dataset/raw/annotation_resources/*`
- `PPI/typed_ppi_verification_report.txt` -> `Typed_PPI_dataset/reports/typed_ppi_verification_report.txt`
- `Biocreative_VI/PMtask_Relations_TrainingSet.json` -> `Biocreative_VI/raw/PMtask_Relations_TrainingSet.json`
- `Biocreative_VI/biocreative_vi_converted.json` -> `Biocreative_VI/derived/biocreative_vi_converted.json`
- `BioRED/PPI_converted/biored_train_ppi_converted.json` -> `BioRED/derived/biored_train_ppi_converted.json`
- `BioRED/PPI_converted/biored_dev_ppi_converted.json` -> `BioRED/derived/biored_dev_ppi_converted.json`
- `BioRED/PPI_converted/biored_test_ppi_converted.json` -> `BioRED/derived/biored_test_ppi_converted.json`
- `Unclean_combined_dataset/combined_all_ppi.json` -> `Unclean_combined_dataset/derived/combined_all_ppi.json`
- `Unified_PPI_dataset/Unified_PPI_dataset.json` -> `Unified_PPI_dataset/derived/Unified_PPI_dataset.json`
- `Unified_PPI_dataset/Unified_PPI_dataset.PubTator` -> `Unified_PPI_dataset/derived/Unified_PPI_dataset.PubTator`
- `Unified_PPI_dataset/README.md` -> `Unified_PPI_dataset/reports/dataset_analysis.md`
- `consistency_analysis.txt` -> `reports/combined/consistency_analysis.txt`
- `duplicate_source_analysis.txt` -> `reports/combined/duplicate_source_analysis.txt`
- `final_analysis.txt` -> `reports/combined/final_analysis.txt`
- `test.txt` -> `archive/manual/test.txt`
