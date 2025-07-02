# Mergesubjects

This tool merges multiple BIDS-like datasets into a single output directory, combining TSV files while preserving all other file types.

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
- **<inputdir1>**, **<inputdir2>**, ... , **<inputdirN>**: Paths to input directories containing participant data
- **<outputdir>**: Path for the output directory (will be created if it doesn't exist)

## Behavior
1. Creates the specified output directory structure
2. For each input directory:
   - Copies all non-TSV files to output directory
   - Identifies TSV files for later merging
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
