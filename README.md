# Unified PPI Pipeline

This repository builds and analyzes a unified protein-protein interaction dataset from several source corpora. The normal workflow is now centered on two commands:

1. `python scripts/run_conversion_pipeline.py`
2. `python scripts/run_analysis_pipeline.py`

## Dataset Sources

- `5_PPI_dataset/`: legacy five-corpus PPI bundle assembled from commonly used benchmark corpora. [https://github.com/BNLNLP/PPI-Relation-Extraction/tree/main/datasets/PPI]([https://link.springer.com/article/10.1186/1471-2105-9-S3-S6](https://github.com/BNLNLP/PPI-Relation-Extraction/tree/main/datasets/PPI)).
- `Biocreative_VI/`: [BioCreative VI Precision Medicine Track](https://biocreative.bioinformatics.udel.edu/tasks/biocreative-vi/track-4/) and [track overview paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC6348314/)
- `BioRED/`: [NCBI BioRED FTP release](https://ftp.ncbi.nlm.nih.gov/pub/lu/BioRED/), [BioRED GitHub repository](https://github.com/ncbi/BioRED), and [dataset paper](https://arxiv.org/abs/2204.04263)

## Quickstart

Run from the repo root:

```bash
python scripts/run_conversion_pipeline.py
python scripts/run_analysis_pipeline.py
```

To recompute outputs even if the canonical files already exist:

```bash
python scripts/run_conversion_pipeline.py --force
python scripts/run_analysis_pipeline.py --force
```

## What Each Entrypoint Does

### Conversion pipeline

`scripts/run_conversion_pipeline.py` runs the full build path in this order:

1. Convert BioCreative VI into the shared JSONL schema.
2. Convert BioRED into the shared JSONL schema.
3. Combine the 5-PPI base dataset, BioCreative, and BioRED into the unclean merged dataset.
4. Deduplicate the merged dataset into the pre-clean unified dataset.
5. Clean the unified dataset for downstream use.
6. Export the cleaned dataset to PubTator format.

### Analysis pipeline

`scripts/run_analysis_pipeline.py` runs the reporting path in this order:

1. Base 5-PPI dataset statistics.
2. BioCreative VI statistics.
3. BioRED relation counts.
4. BioRED sentence-distribution analysis.
5. Duplicate analysis on the unclean combined dataset.
6. Duplicate consistency analysis on the unclean combined dataset.
7. Final cleaned dataset analysis.

## Canonical Outputs

- Pre-clean unified dataset: `Unified_PPI_dataset/derived/Unified_PPI_dataset.json`
- Final-for-use unified dataset: `Unified_PPI_dataset/derived/Unified_PPI_dataset_clean.json`
- Final PubTator export: `Unified_PPI_dataset/derived/Unified_PPI_dataset.PubTator`
- Unclean intermediate dataset: `Unclean_combined_dataset/derived/combined_all_ppi.json`

`Unified_PPI_dataset_clean.json` is the canonical downstream final-for-use dataset.

## Folder Roles

Source dataset folders:

- `5_PPI_dataset/`
- `Biocreative_VI/`
- `BioRED/`
- `Typed_PPI_dataset/`

These keep `raw/`, `derived/`, `reports/`, and `archive/`.

Build-output folders:

- `Unclean_combined_dataset/`
- `Unified_PPI_dataset/`

These intentionally keep only `derived/`, `reports/`, and `archive/`.

## Documentation

- `docs/pipeline.md`: stage-by-stage build and analysis flow
- `docs/code_overview.md`: what the code does, what each stage reads/writes, and why it exists
- `docs/data_sources.md`: placeholder template for dataset source information
- `docs/file-migration.md`: historical path migration notes from the cleanup/refactor
