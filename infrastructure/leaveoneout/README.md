# Leaveoneout

This script creates **leave-one-out** (LOO) datasets by excluding the data from a specified participant in a BIDS dataset, while preserving the data from all other participants.

## Features

- Excludes a specified participant from a directory structure
- Handles both TSV files (removing participant rows) and other file types (copying as-is)
- Maintains the original directory structure in the output
- Supports participant specification by either:
  - Direct participant ID (e.g., sub-01)
  - Numerical index (e.g., 1 for the first participant)

## Requirements

- Python 3.x
- Pandas

## Usage

```bash
leaveoneout.py <inputdir> <outputdir> <participant_nr>
```

Where:

  - `<input_dir>`: Path to the input directory containing participant data
  - `<output_dir>`: Name of the output directory (will be created in current working directory)
  - `<participant_nr>`: Either the participant ID (e.g., sub-01) or numerical index (e.g., 1)

## Behaviour

1. Scans the input directory for participant folders (starting with `sub-`)
2. Creates an output directory structure mirroring the input
3. For TSV files:
   - Removes rows containing the specified participant ID
   - Preserves all other data
4. For other files:
   - Copies them unchanged to the output directory
5. Skips directories containing the participant ID to be excluded

## Notes

- Handles BIDS-like structure (participant folders prefixed with `sub-`)
- Output directory created in current working directory
- TSV files should have participant IDs in first column
