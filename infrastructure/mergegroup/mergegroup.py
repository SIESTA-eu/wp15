#!/usr/bin/env python3

import csv
import os
import sys
import time

from tqdm import tqdm
from more_itertools import collapse

# Importing necessary modules from the mergegroup/lib directory
from lib.filetype import filetype as filetype
from lib import txt, csv, tsv, nii, mat


def main(args=None):
    start_time = time.time()
    
    if args is None:
        args = sys.argv
    
    if len(args) < 4:
        print("Usage: mergegroup.py <input dir 1> <input dir 2> ... <output dir> <whitelist.txt>", file=sys.stderr)
        sys.exit(1)

    whitelist_path = args[-1]
    if not os.path.exists(whitelist_path):
        raise FileNotFoundError(f"Whitelist file not found at {whitelist_path}")
        
    if not os.path.isfile(whitelist_path):
        raise ValueError(f"{whitelist_path} is not a regular file")
        
    with open(whitelist_path, "r") as file:
        whitelist = [line.strip() for line in file if line.strip() and not line.startswith("#")]
        
    if not whitelist:
        raise ValueError("Whitelist file is empty or contains no valid entries")

    output_dir = args[-2]
    os.makedirs(output_dir, exist_ok=True)
    if not os.path.isdir(output_dir):
        raise NotADirectoryError(f"{output_dir} is not a valid directory")

    output_file = f"{output_dir}/group-merged.tsv"
    if os.path.exists(output_file):
        os.remove(output_file)
    
    input_dirs = args[1:-2]
    if not input_dirs:
        raise ValueError("No input directories provided")

    # loop across files in the whitelist
    data_values = {}
    file_types = {wl_file: filetype(wl_file) for wl_file in whitelist}
    all_data = []

    for wl_file in whitelist:

        # loop across the input directories
        temp_aux = []
        for i, item in tqdm(enumerate(input_dirs), desc=f"Processing whitelisted file '{wl_file}': "):
            try:
                if not os.path.exists(item):
                    print(f"Warning: Input directory {item} does not exist", file=sys.stderr)
                    continue

                if not os.path.isdir(item):
                    print(f"Warning: {item} is not a directory", file=sys.stderr)
                    continue

                input_path = os.path.join(item, wl_file)
                if not os.path.exists(input_path):
                    print(
                        f"Warning: File '{os.path.basename(input_path)}' not found in {os.path.dirname(input_path)}",
                        file=sys.stderr)
                    continue

                file_type = file_types[wl_file]

                content = None
                if file_type == "txt":
                    content, structure = txt.read(input_path)
                elif file_type == "tsv":
                    content, structure = tsv.read(input_path)
                elif file_type == "csv":
                    content, structure = csv.read(input_path)
                elif file_type == "nii":
                    content, structure = nii.read(input_path)
                elif file_type == "mat":
                    content, structure = mat.read(input_path)
                else:
                    print(f"Warning: Unsupported file type {file_type} for {input_path}", file=sys.stderr)

                all_data.append(content)

            except Exception as e:
                raise RuntimeError("Error processing file %s" % wl_file)

    # Save the result
    tsv.write(output_file, all_data, {})

    # Give feedback to the user
    total_time = time.time() - start_time
    total_time = f"{time.strftime('%H:%M:%S', time.gmtime(int(total_time)))}.{int((total_time - int(total_time)) * 1000):03d}"
    print(f"\nTotal time taken: {total_time}")

if __name__ == "__main__":
    main()