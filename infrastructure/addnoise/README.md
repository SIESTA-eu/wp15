# Addnoise

This is a Python script that reads the list of input files from a whitelist file.
For each of those files it adds the corresponding noise values and writes the noisy
results to a file with the same format as the input file format.

## Features

Supported input file formats are:

- tsv
- csv
- nii
- mat

## Requirements

Python 3.x

## Usage

```bash
python addnoise.py <whitelist.txt> <noise.tsv> <outputdir>
```
