# Singlesubject

This tool extracts the data for a specified single participant in a BIDS dataset, while excluding all other participants' data.

## Features

- Extracts data for a single specified participant from a dataset
- Handles both TSV files (extracting participant rows) and other file types (copying as-is)
- Maintains the original directory structure in the output
- Supports participant specification by either:
    - Direct participant ID (e.g., sub-01)
    - Numerical index (e.g., 1 for the first participant)
- Preserves participant-specific directory structure

## Requirements

- Python 3.x
- Pandas

## Usage

```bash
singlesubject.py <inputdir> <outputdir> <participant_nr>
```

Where:
- `<input_dir>`: Path to the input directory containing participant data
- `<output_dir>`: Name of the output directory (will be created in current working directory)
- `<participant_nr>`: The participant ID string (e.g., sub-01), or a numerical index (e.g., 1 for first participant)

## Behavior

- Scans the input directory for participant folders (starting with `sub-`)
- For TSV files:
    - Extracts only rows containing the specified participant ID
    - Excludes all other participant data
- For other files it copies them unchanged to the output directory
- Only includes directories relevant to the specified participant

## Notes

- The script assumes a BIDS-like structure with participant folders prefixed with `sub-`
- Output directory will be created in the current working directory
- TSV files are expected to have participant IDs in their first column
- Provides clear error messages for invalid inputs or missing files
- Preserves the directory structure of the extracted participant
