# Pipeline

This repository now exposes two public entrypoints:

- `python scripts/run_conversion_pipeline.py`
- `python scripts/run_analysis_pipeline.py`

## Conversion pipeline

The conversion pipeline runs these stages in order:

1. Convert BioCreative VI to the shared JSONL schema.
2. Convert BioRED to the shared JSONL schema.
3. Combine the base 5-PPI dataset with the converted source datasets.
4. Deduplicate the merged dataset into the pre-clean unified dataset.
5. Clean the unified dataset for downstream use.
6. Export the cleaned dataset to PubTator.

Canonical outputs:

- `Unclean_combined_dataset/derived/combined_all_ppi.json`
- `Unified_PPI_dataset/derived/Unified_PPI_dataset.json`
- `Unified_PPI_dataset/derived/Unified_PPI_dataset_clean.json`
- `Unified_PPI_dataset/derived/Unified_PPI_dataset.PubTator`

## Analysis pipeline

The analysis pipeline runs these stages in order:

1. Base 5-PPI reports
2. BioCreative VI report
3. BioRED relation report
4. BioRED sentence-distribution report
5. Combined duplicate report
6. Combined duplicate-consistency report
7. Final cleaned dataset report

Canonical reports:

- `5_PPI_dataset/reports/final_report.txt`
- `5_PPI_dataset/reports/dataset_stats.txt`
- `Biocreative_VI/reports/biocreative_stats.txt`
- `BioRED/reports/biored_relation_stats.txt`
- `BioRED/reports/sentence_stats.txt`
- `reports/combined/duplicate_source_analysis.txt`
- `reports/combined/consistency_analysis.txt`
- `Unified_PPI_dataset/reports/dataset_analysis.md`

## Notes

- `Unified_PPI_dataset_clean.json` is the final-for-use dataset.
- `Unified_PPI_dataset.json` is retained as the pre-clean unified output.
- Legacy helpers for older fold-level verification remain under `scripts/legacy/`.
