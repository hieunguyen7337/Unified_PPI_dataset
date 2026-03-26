# Code Overview

This document explains what the pipeline code does, what each stage reads and writes, and how the pieces fit together.

## Public entrypoints

### `scripts/run_conversion_pipeline.py`

Purpose: build the canonical datasets and exports used downstream.

Stages:

1. BioCreative conversion
   - Reads the raw BioCreative VI relation dataset.
   - Writes the converted BioCreative JSONL dataset.
2. BioRED conversion
   - Reads the raw BioRED BioC JSON files.
   - Writes the converted BioRED JSONL datasets for train/dev/test.
3. Dataset combination
   - Reads the base 5-PPI combined dataset and the converted BioCreative/BioRED datasets.
   - Writes the unclean combined dataset.
4. Deduplication
   - Reads the unclean combined dataset.
   - Writes the pre-clean unified dataset.
5. Final cleaning
   - Reads the pre-clean unified dataset.
   - Removes out-of-bounds relations and normalizes entity strings from the text.
   - Writes the final-for-use unified dataset.
6. PubTator export
   - Reads the final-for-use unified dataset.
   - Writes the final PubTator export.

### `scripts/run_analysis_pipeline.py`

Purpose: regenerate the canonical reports that describe the source datasets, intermediate dataset quality, and final cleaned dataset.

Stages:

1. Base 5-PPI stats
2. BioCreative stats
3. BioRED relation stats
4. BioRED sentence-distribution report
5. Duplicate analysis on the unclean combined dataset
6. Duplicate consistency analysis on the unclean combined dataset
7. Final cleaned dataset analysis

## Internal stage modules

The wrappers call the existing stage modules under:

- `scripts/build/`
- `scripts/analyze/`

These modules are still callable directly for debugging, but they are no longer the primary interface for normal use.

## How to run

From the repo root:

```bash
python scripts/run_conversion_pipeline.py
python scripts/run_analysis_pipeline.py
```

Force recomputation:

```bash
python scripts/run_conversion_pipeline.py --force
python scripts/run_analysis_pipeline.py --force
```

## Final dataset model

- `Unified_PPI_dataset.json`: pre-clean unified dataset after deduplication
- `Unified_PPI_dataset_clean.json`: final-for-use unified dataset after downstream cleaning

Downstream exports and final analysis should use `Unified_PPI_dataset_clean.json`.
