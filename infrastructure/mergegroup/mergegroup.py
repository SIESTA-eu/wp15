#!/usr/bin/env python3

import csv
import os
import sys
import time

import h5py
import nibabel as nib
import numpy as np
import scipy.io
from nibabel.filebasedimages import FileBasedImage
from tqdm import tqdm


def filetype(filename):
    try:
        if not isinstance(filename, str):
            raise ValueError("Filename must be a string")
            
        filename = filename.strip()
        if not filename:
            raise ValueError("Empty filename provided")
            
        extensions = {".txt": "txt", ".csv": "csv", ".tsv": "tsv", 
                     ".nii": "nii", ".nii.gz": "nii", ".mat": "mat"}
        
        for ext, file_type in extensions.items():
            if filename.lower().endswith(ext): 
                return file_type
        return "unknown"
    except Exception as e:
        print(f"Error determining file type for {filename}: {str(e)}", file=sys.stderr)
        return "error"

def is_numeric_array(obj):
    return isinstance(obj, np.ndarray) and np.issubdtype(obj.dtype, np.number)

def is_mat_struct(obj):
    return hasattr(obj, '__dict__') and not isinstance(obj, np.ndarray)

def extract_numeric_data(data, prefix=''):
    numeric_data = {}

    if isinstance(data, dict):
        for wl_file, value in data.items():
            if wl_file.startswith('__'):
                continue
            sub_prefix = f"{prefix}.{wl_file}" if prefix else wl_file
            numeric_data.update(extract_numeric_data(value, sub_prefix))

    elif is_mat_struct(data):
        for field, value in vars(data).items():
            sub_prefix = f"{prefix}.{field}" if prefix else field
            numeric_data.update(extract_numeric_data(value, sub_prefix))

    elif isinstance(data, np.ndarray):
        if is_numeric_array(data):
            numeric_data[prefix] = data
        elif data.dtype.names:
            # structured numpy array (e.g., MATLAB struct array)
            for i in range(data.shape[0] if data.ndim > 0 else 1):
                item = data[i] if data.ndim > 0 else data
                for field_name in data.dtype.names:
                    try:
                        value = item[field_name]
                        sub_prefix = f"{prefix}.{field_name}"
                        numeric_data.update(extract_numeric_data(value, sub_prefix))
                    except Exception:
                        continue
        else:
            # General ndarray (could be an array of structs)
            for i, item in np.ndenumerate(data):
                sub_prefix = f"{prefix}[{i}]"
                numeric_data.update(extract_numeric_data(item, sub_prefix))

    return numeric_data

def read_mat_file(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    mat_data = scipy.io.loadmat(filepath, struct_as_record=False, squeeze_me=True)
    return extract_numeric_data(mat_data)

def concatenate_common_fields(dicts):
    if not dicts:
        return {}

    # Find keys that are common to all dictionaries
    common_keys = set(dicts[0].keys())
    for d in dicts[1:]:
        common_keys &= d.keys()

    result = {}
    for key in common_keys:
        lengths = [len(d[key]) for d in dicts]
        if all(length == lengths[0] for length in lengths):
            try:
                concatenated = np.stack([np.ravel(np.asarray(d[key])) for d in dicts])
            except Exception as e:
                print(f"Error concatenating {key}: {str(e)}", file=sys.stderr)
            result[key] = concatenated

    return result

def dicts_to_list(dicts, n):

    result = []
    for outer_dict in dicts.values():
        for arr in outer_dict.values():
            arr = np.asarray(arr)
            if arr.shape[0] != n:
                raise ValueError(f"Expected {n} rows, got {arr.shape[0]} rows")
            result.append(arr)

    return result

def parse_ctsv(filepath, delimiter):
    data = []
    try:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File {filepath} does not exist")
            
        if not os.path.isfile(filepath):
            raise ValueError(f"{filepath} is not a regular file")
            
        with open(filepath, 'r') as file:
            reader = csv.reader(file, delimiter=delimiter)
            for row_num, row in enumerate(reader, 1):
                try:
                    line = []
                    for item in row:
                        try:
                            val = float(item)
                            if val.is_integer():
                                val = int(val)
                            line.append(val)
                        except ValueError:
                            continue
                    if line:
                        data.append(line)

                    # Flatten the list of lists
                    data = [it for sublist in data for it in sublist]
                    data = {os.path.basename(filepath): data}
                    return data

                except Exception as e:
                    print(f"Error processing row {row_num} in {filepath}: {str(e)}", file=sys.stderr)
    except Exception as e:
        print(f"Error parsing CSV/TSV file {filepath}: {str(e)}", file=sys.stderr)
        return None

def parse_txt(filepath, delimiter=' '):
    data = []
    try:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File {filepath} does not exist")
            
        if not os.path.isfile(filepath):
            raise ValueError(f"{filepath} is not a regular file")
            
        with open(filepath, 'r') as file:
            for line_num, line in enumerate(file, 1):
                try:
                    row = line.strip().split(delimiter)
                    processed_line = []
                    for item in row:
                        try:
                            val = float(item)
                            if val.is_integer():
                                val = int(val)
                            processed_line.append(val)
                        except ValueError:
                            continue
                    if processed_line:
                        data.append(processed_line)
                except Exception as e:
                    print(f"Error processing line {line_num} in {filepath}: {str(e)}", file=sys.stderr)

                # Flatten the list of lists
                data = [it for sublist in data for it in sublist]
                data = {os.path.basename(filepath): data}
                return data
    except Exception as e:
        print(f"Error opening/reading text file {filepath}: {str(e)}", file=sys.stderr)
        return None

def parse_nii(filepath):
    try:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File {filepath} does not exist")
            
        if not os.path.isfile(filepath):
            raise ValueError(f"{filepath} is not a regular file")
            
        img: FileBasedImage = nib.load(filepath)
        if img is None:
            raise ValueError("Failed to load NIfTI image")
        data = img.get_fdata(caching='unchanged')
        data = {os.path.basename(filepath): data.flatten()}
        if data is None:
            raise ValueError("Failed to get data from NIfTI image")
            
        return data
    except Exception as e:
        print(f"Error loading NIfTI file {filepath}: {str(e)}", file=sys.stderr)
        return None

def parse_mat(filepath):   
    meta_keys = {'__header__', '__version__', '__globals__', '#refs#'}
    try:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File {filepath} does not exist")
            
        if not os.path.isfile(filepath):
            raise ValueError(f"{filepath} is not a regular file")
            
        try:
            mat_data = scipy.io.loadmat(filepath, struct_as_record=False, squeeze_me=True)
            return extract_numeric_data(mat_data)

        except NotImplementedError:
            try:
                with h5py.File(filepath, 'r') as file:
                    result = {}
                    for key, dataset in file.items():
                        if key == "#refs#":
                            continue
                        try:
                            if isinstance(dataset, h5py.Dataset):
                                result[key] = dataset[()]
                            else:
                                result[key] = {subkey: dataset[subkey][()] for subkey in dataset.keys()}
                        except Exception as e:
                            print(f"Error processing dataset {key} in MAT file {filepath}: {str(e)}", file=sys.stderr)
                    return result
            except Exception as e:
                print(f"Error reading MAT file {filepath}: {str(e)}", file=sys.stderr)
                return None
    except Exception as e:
        print(f"Error processing MAT file {filepath}: {str(e)}", file=sys.stderr)
        return None

def main(args=None):
    start_time = time.time()
    
    if args is None:
        args = sys.argv
    
    if len(args) < 4:
        print("Usage: mergegroup.py <input dir 1> <input dir 2> ... <output dir> <whitelist.txt>", file=sys.stderr)
        sys.exit(1)

    try:
        try:
            whitelist_path = args[-1]
            if not os.path.exists(whitelist_path):
                raise FileNotFoundError(f"Whitelist file not found at {whitelist_path}")
                
            if not os.path.isfile(whitelist_path):
                raise ValueError(f"{whitelist_path} is not a regular file")
                
            with open(whitelist_path, "r") as file:
                whitelist = [line.strip() for line in file if line.strip() and not line.startswith("#")]
                
            if not whitelist:
                raise ValueError("Whitelist file is empty or contains no valid entries")
        except Exception as e:
            print(f"Error reading whitelist file: {str(e)}", file=sys.stderr)
            sys.exit(1)

        output_dir = args[-2]
        try:
            os.makedirs(output_dir, exist_ok=True)
            if not os.path.isdir(output_dir):
                raise NotADirectoryError(f"{output_dir} is not a valid directory")
        except Exception as e:
            print(f"Error creating output directory {output_dir}: {str(e)}", file=sys.stderr)
            sys.exit(1)

        output_file = f"{output_dir}/group-merged.tsv"
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except Exception as e:
                print(f"Error removing existing output file: {str(e)}", file=sys.stderr)
                sys.exit(1)

        input_dirs = args[1:-2]
        if not input_dirs:
            raise ValueError("No input directories provided")

        # loop across files in the whitelist
        data_values = {}
        file_types = {wl_file: filetype(wl_file) for wl_file in whitelist}

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

                    data = None
                    if file_type == "txt":
                        data = parse_txt(input_path)
                    elif file_type in ["csv", "tsv"]:
                        delimiter = "," if file_type == "csv" else "\t"
                        data = parse_ctsv(input_path, delimiter)
                    elif file_type == "nii":
                        data = parse_nii(input_path)
                    elif file_type == "mat":
                        data = parse_mat(input_path)
                    else:
                        print(f"Warning: Unsupported file type {file_type} for {input_path}", file=sys.stderr)

                    if data is not None:
                        temp_aux.append(data)

                except Exception as e:
                    print(f"Error processing file {input_path}: {str(e)}", file=sys.stderr)
                    continue

            # store the data per whitelisted file in dictionaries => perhapsß for bookkeeping, we may want to create a list of nested keys, so that we can put back noise-calibrated data where it belongs eventually?
            # keeping only the fields that are shared across files, and that have the same size
            data_values[wl_file] = concatenate_common_fields(temp_aux)

        # Concatenate all arrays horizontally
        all_data = dicts_to_list(data_values, len(input_dirs))
        all_data = np.concatenate(all_data, axis=1)

        # Save the result
        np.savetxt(output_file, all_data, delimiter="\t", fmt="%s")

    finally:
        total_time = time.time() - start_time
        total_time = f"{time.strftime('%H:%M:%S', time.gmtime(int(total_time)))}.{int((total_time - int(total_time)) * 1000):03d}"
        print(f"\nTotal time taken: {total_time}")

if __name__ == "__main__":
    main()
