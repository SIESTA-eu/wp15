# Addnoise

This is a Python script that reads the list of input files from a whitelist file.
For each of those files it adds the corresponding noise values and writes the noisy
results to a file in the output directory with the same file name and format as
the input file.

## Features

Supported input file formats are:

- tsv
- csv
- txt
- nii
- mat

## Requirements

Python 3.x

## Usage

```bash
addnoise.py <inputdir> <outputdir> <whitelist.txt> <noise.tsv>
```
