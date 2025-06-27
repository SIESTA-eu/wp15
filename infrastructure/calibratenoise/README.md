# Calibratenoise

This is a Python script that computes the standard deviation over the rows of the
input `.tsv` file. Each row is a LOO sample, and each column is one of the variables
that results from the group-level pipeline. 

## Features

- Handles TSV (Tab-Separated Values) files
- Computes sample standard deviation (using N-1 in denominator)
- Skips non-numeric values with a warning
- Handles rows with inconsistent column counts
- Outputs standard deviations in the same order as input columns

The input file should not have any column headers.

## Requirements

Python 3.x

## Usage

```bash
calibratenoise.py <input.tsv> <output.tsv>
```
