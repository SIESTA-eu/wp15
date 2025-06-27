# Cleanup

This is a Python script that recursively removes files and directories, while
preserving the files that are listed in the whitelist file.

## Features

- Recursively cleans a directory while keeping specified files/directories
- Supports exclusion files with whitelisted paths (one per line)
- Handles both files and directories in the exclusion list
- Dry-run mode to preview changes without actual deletion
- Preserves parent directories of excluded files
- Comments in exclusion file (lines starting with #) are ignored

## Requirements

Python 3.x

## Usage

```bash
cleanup.py <directory> [whitelist_file] [--dry-run]
```

## Arguments

- `directory`: The directory to clean (required)
- `whitelist_file`: Text file containing paths to exclude (optional)
- `--dry-run`: Preview changes without deleting (optional)

## Example

Create an exclusion file that is named `whitelist.txt`:

    # Keep these files/directories, comments are ignored
    important_file.txt
    protected_dir/

Run the cleaner:

```bash
cleanup.py /path/to/clean whitelist.txt
```

For a dry run (preview only):

```bash
cleanup.py /path/to/clean whitelist.txt --dry-run
```

## Exclusion File Format

- One path per line
- Paths can be files or directories
- It is recommended but not required that directories end with `/`
- Lines starting with `#` are treated as comments
- Paths are relative to the directory being cleaned
