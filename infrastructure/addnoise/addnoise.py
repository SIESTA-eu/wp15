#!/usr/bin/env python3

import sys, os
from pathlib import Path
from more_itertools import collapse

# Ensure the script can find the mergegroup/lib directory
current_dir = Path(__file__).resolve().parent
shared_dir = current_dir.parent / 'mergegroup'
if shared_dir not in sys.path:
    sys.path.append(str(shared_dir))

# Importing necessary modules from the mergegroup/lib directory
from lib.filetype import filetype as filetype
from lib import txt, csv, tsv, nii, mat


def main(args=None):
    if args is None:
        args = sys.argv
    
    if len(args) != 5:
        print("Usage: addnoise.py <inputdir> <outputdir> <whitelist.txt>  <noise.tsv>")
        sys.exit(1)
    
    input_dir      = args[1]
    output_dir     = args[2]
    whitelist_path = args[3]
    noise_path     = args[4]

    if not os.path.exists(whitelist_path):
        raise FileNotFoundError("Whitelist file not found")
        
    if not os.path.isfile(whitelist_path):
        raise ValueError(f"Whitelist file is not a regular file_name")
        
    with open(whitelist_path, "r") as file_name:
        whitelist = [line.strip() for line in file_name if line.strip() and not line.startswith("#")]
    
    if not whitelist:
        raise ValueError("Whitelist file is empty or contains no valid entries")

    # Check if the output directory exists, if not create it
    os.makedirs(output_dir, exist_ok=True)

    # Read the noise file_name, this is expected to be a TSV file_name
    file_type = filetype(noise_path)
    if file_type == "txt":
        noise, structure = txt.read(noise_path)
    elif file_type == "tsv":
        noise, structure = tsv.read(noise_path)
    elif file_type == "csv":
        noise, structure = csv.read(noise_path)
    elif file_type == "nii":
        noise, structure = nii.read(noise_path)
    elif file_type == "mat":
        noise, structure = mat.read(noise_path)

    offset = 0
    for file_name in whitelist:
        input_file  = os.path.join(input_dir, file_name)
        output_file = os.path.join(output_dir, file_name)
        
        if not os.path.exists(input_file):
            raise FileExistsError("file_name not found: " + input_file)
            
        file_type = filetype(input_file)
        
        if file_type == "txt":
            content, structure = txt.read(input_file)
        elif file_type == "tsv":
            content, structure = tsv.read(input_file)
        elif file_type == "csv":
            content, structure = csv.read(input_file)
        elif file_type == "nii":
            content, structure = nii.read(input_file)
        elif file_type == "mat":
            content, structure = mat.read(input_file)
        else:
            print(f"Warning: Unsupported file type {file_type} for {input_file}", file=sys.stderr)
            continue

        # Add the noise to the results
        for i in range(len(content)):
            content[i] += noise[i]
        offset += len(content)

        # Write the noisy result to the output file        
        if file_type == "txt":
            txt.write(output_file, content, structure)
        elif file_type == "tsv":
            tsv.write(output_file, content, structure)
        elif file_type == "csv":
            csv.write(output_file, content, structure)
        elif file_type == "nii":
            nii.write(output_file, content, structure)
        elif file_type == "mat":
            mat.write(output_file, content, structure)  
        else:
            print(f"Warning: Unsupported file type {file_type} for {output_file}", file_name=sys.stderr)
            continue
        
        print(f"Successfully added the noise to the results and wrote {output_file}")
    

if __name__ == "__main__":
    main()