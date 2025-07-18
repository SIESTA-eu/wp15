# Mergesubjects

This tool merges multiple single-subject BIDS datasets into a single BIDS dataset containing all subjects, combining TSV files while preserving all other file types.

## Features

- Merges multiple input directories into a single output directory
- Concatenates TSV files with matching names/paths across input directories
- Preserves all non-TSV files in their original structure
- Maintains directory hierarchy from source to destination
- Comprehensive error handling throughout the merging process

## Requirements

- Python 3.x
- Pandas

## Usage

```bash
mergesubjects.py <inputdir1> <inputdir2> ... <inputdirN> <outputdir>
```

Where:
- `<inputdir_1>`, **<inputdir_2>`, ... , `<inputdir_N>`: Paths to input directories containing participant data
- `<output_dir>`: Path for the output directory (will be created if it doesn't exist)

## Behavior

1. Creates the specified output directory structure
2. For each input directory:
   - Copies all non-TSV files to output directory
3. Merges TSV files with matching relative paths:
   - Concatenates rows while preserving headers
   - Saves merged versions to output directory
4. Preserves original directory structure throughout

## Notes

- Handles BIDS-like directory structures
- Output directory will be created if it doesn't exist
- TSV files are merged based on matching filenames and relative paths
- Provides detailed error messages for troubleshooting
- Skips files that already exist in output directory (no overwriting)
