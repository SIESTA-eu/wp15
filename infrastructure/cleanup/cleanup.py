#!/usr/bin/env python3

"""
This script recursively removes files and directories from a specified directory,
except those listed in an exclusion file. The exclusion file can contain files or directories to be kept.
The script can be run in dry-run mode to show what would be removed without actually deleting anything.
Usage:
    python cleanup.py <directory> [<exclusion_file>] [--dry-run]
"""

import os
import shutil
import argparse

def load_exclusions(path, exclusion_file):
    """Load the list of files/directories to exclude from removal."""
    exclusions = set()
    if exclusion_file is None:
        # If no exclusion file is provided, return an empty set
        return exclusions
    elif not os.path.exists(exclusion_file):
        raise FileNotFoundError(f"Exclusion file {exclusion_file} does not exist.")
    elif not os.path.isfile(exclusion_file):
        raise ValueError(f"Exclusion file {exclusion_file} is not a valid file.")

    with open(exclusion_file, 'r') as f:
        # Read the exclusion file line by line
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if os.path.isfile(os.path.join(path, line)):
                    # If the line is a file, add the file and its directory to the exclusions
                    exclusions.add(os.path.dirname(line))
                    exclusions.add(line)
                else:
                    # Otherwise, add the directory
                    exclusions.add(line)
    return exclusions

def should_exclude(path, exclusions, root_dir):
    """Check if the given path should be excluded from removal."""
    # Get relative path from the root directory
    rel_path = os.path.relpath(path, root_dir)
    
    # Check if this path or any of its parents is in the exclusion list
    parts = rel_path.split(os.sep)
    for i in range(len(parts)):
        partial_path = os.sep.join(parts[:i+1])
        if partial_path in exclusions:
            return True
    return False

def clean_directory(directory, exclusions):
    """Recursively remove all files and directories except the excluded ones."""
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory")
        return
        
    # Walk through the directory tree bottom-up (so we can delete directories)
    for root, dirs, files in os.walk(directory, topdown=False):
        # Process files first
        for file in files:
            file_path = os.path.join(root, file)
            if not should_exclude(file_path, exclusions, directory):
                try:
                    os.remove(file_path)
                    print(f"Removing file: {file_path}")
                except Exception as e:
                    print(f"Error removing file {file_path}: {e}")
            else:
                print(f"Keeping file: {file_path}")
        
        # Process directories
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if not should_exclude(dir_path, exclusions, directory):
                try:
                    os.rmdir(dir_path)
                    print(f"Removing directory: {dir_path}")
                except Exception as e:
                    print(f"Error removing directory {dir_path}: {e}")
            else:
                print(f"Keeping directory: {dir_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Recursively remove files and directories except those listed in exclusion file."
    )
    parser.add_argument("directory", help="Directory to clean")
    parser.add_argument("whitelist_file", help="Optional text file containing the files to exclude (one per line)", nargs='?')
    parser.add_argument("--dry-run", action="store_true", help="Show what would be removed without actually deleting")
    
    args = parser.parse_args()
    
    exclusions = load_exclusions(args.directory, args.whitelist_file)
    if len(exclusions) == 0:
        print("No exclusions")
    else:
        print(f"Exclusions loaded: {exclusions}")
    
    if args.dry_run:
        print("Dry run mode - no files will be deleted")
        # Simulate the cleaning process
        for root, dirs, files in os.walk(args.directory):
            for file in files:
                file_path = os.path.join(root, file)
                if not should_exclude(file_path, exclusions, args.directory):
                    print(f"[Dry run] Would remove file: {file_path}")
                else:
                    print(f"[Dry run] Would keep file: {file_path}")
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                if not should_exclude(dir_path, exclusions, args.directory):
                    print(f"[Dry run] Would remove directory: {dir_path}")
                else:
                    print(f"[Dry run] Would keep directory: {dir_path}")
    else:
        clean_directory(args.directory, exclusions)

if __name__ == "__main__":
    main()
