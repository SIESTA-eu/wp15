#!/usr/bin/env python3

import os, csv, re, sys, json, h5py, scipy.io, itertools, time
import numpy as np
import nibabel as nib
from more_itertools import collapse
from itertools import zip_longest

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

import numpy as np

def concatenate_common_fields(dicts):
    if not dicts:
        return {}

    # Step 1: Find keys that are common to all dictionaries
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
                except Exception as e:
                    print(f"Error processing row {row_num} in {filepath}: {str(e)}", file=sys.stderr)
    except Exception as e:
        print(f"Error parsing CSV/TSV file {filepath}: {str(e)}", file=sys.stderr)
    return data

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
    except Exception as e:
        print(f"Error opening/reading text file {filepath}: {str(e)}", file=sys.stderr)
    return data

def parse_nii(filepath):
    try:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File {filepath} does not exist")
            
        if not os.path.isfile(filepath):
            raise ValueError(f"{filepath} is not a regular file")
            
        img: FileBasedImage = nib.load(filepath)
        if img is None:
            raise ValueError("Failed to load NIfTI image")
            
        data = img.get_fdata()
        if data is None:
            raise ValueError("Failed to get data from NIfTI image")
            
        return data
    except Exception as e:
        print(f"Error loading NIfTI file {filepath}: {str(e)}", file=sys.stderr)
        return None

def parse_mat(filepath):   
    meta_wl_files = {'__header__', '__version__', '__globals__', '#refs#'}
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
                    for wl_file, dataset in file.items():
                        if wl_file == "#refs#":
                            continue
                        try:
                            if isinstance(dataset, h5py.Dataset):
                                result[wl_file] = dataset[()]
                            else:
                                result[wl_file] = {subwl_file: dataset[subwl_file][()] for subwl_file in dataset.wl_files()}
                        except Exception as e:
                            print(f"Error processing dataset {wl_file} in MAT file {filepath}: {str(e)}", file=sys.stderr)
                    return result
            except Exception as e:
                print(f"Error reading MAT file {filepath}: {str(e)}", file=sys.stderr)
                return None
    except Exception as e:
        print(f"Error processing MAT file {filepath}: {str(e)}", file=sys.stderr)
        return None

def prep_(dict_):
    def flatten(lst):
        try:
            if not isinstance(lst, (list, np.ndarray)):
                return [lst]
            return [item for sublist in lst for item in flatten(sublist)]
        except Exception as e:
            print(f"Error flattening data: {str(e)}", file=sys.stderr)
            return []

    result = []
    try:
        if not isinstance(dict_, dict):
            raise ValueError("Input must be a dictionary")
            
        for v in dict_.values():
            try:
                if isinstance(v, dict):
                    result.extend(prep_(v))
                else:
                    result.extend(flatten(v))
            except Exception as e:
                print(f"Error processing dictionary value: {str(e)}", file=sys.stderr)
    except Exception as e:
        print(f"Error preparing data structure: {str(e)}", file=sys.stderr)
    return list(collapse(result))

def save_(filename, data):
    try:
        if not isinstance(data, (list, np.ndarray)):
            raise ValueError("Data must be a list or array")
            
        with open(filename, "a") as f:
            try:
                line = "\t".join(map(str, data)) + "\n"
                f.write(line)
            except Exception as e:
                print(f"Error writing data to file {filename}: {str(e)}", file=sys.stderr)
    except Exception as e:
        print(f"Error opening output file {filename}: {str(e)}", file=sys.stderr)

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

        data_dict = {wl_file: list() for wl_file in whitelist}
        file_types = {wl_file: filetype(wl_file) for wl_file in whitelist}
        txt_values, ctsv_values, mat_values, nii_values = list(), list(), list(), list()
        
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

        txt_values, ctsv_values, mat_values, nii_values = {}, {}, {}, {}

        # loop across files in the whitelist in the outer-loop, so that we can do diagnostics per file type
        for wl_file in whitelist:
            txt_aux, ctsv_aux, mat_aux, nii_aux = {}, {}, [], {}

            # loop across the input directories
            for i, item in tqdm(enumerate(input_dirs), desc=f"Processing wl_file '{wl_file}': "):
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

                    if file_type == "txt":
                        data = parse_txt(input_path)
                        if data:
                            txt_aux[i] = list(collapse(data))
                            print(f"Merging: {input_path} -> {output_file}")

                    elif file_type in ["csv", "tsv"]:
                        delimiter = "," if file_type == "csv" else "\t"
                        data = parse_ctsv(input_path, delimiter)
                        if data:
                            ctsv_aux[i] = list(collapse(data))
                            print(f"Merging: {input_path} -> {output_file}")

                    elif file_type == "nii":
                        data = parse_nii(input_path)
                        if data is not None:
                            #nii_aux[i] = data.flatten()
                            nii_aux.append(data)
                            print(f"Merging: {input_path} -> {output_file}")

                    elif file_type == "mat":
                        data = parse_mat(input_path)
                        if data is not None:
                            mat_aux.append(data)
                            print(f"Merging: {input_path} -> {output_file}")

                    else:
                        print(f"Warning: Unsupported file type {file_type} for {input_path}", file=sys.stderr)

                except Exception as e:
                    print(f"Error processing file {input_path}: {str(e)}", file=sys.stderr)
                    continue

            # temporarily store the data in outer dictionaries => TODO for bookkeeping?
            if txt_aux:
                txt_values[wl_file] = txt_aux
            if ctsv_aux:
                ctsv_values[wl_file] = ctsv_aux
            if nii_aux:
                nii_values[wl_file] = nii_aux
            if mat_aux:
                mat_concat = concatenate_common_fields(mat_aux)
                mat_values[wl_file] = mat_concat

        # Collect all arrays from the nested dicts
        mat_data = []
        for outer_dict in mat_values.values():
            for arr in outer_dict.values():
                arr = np.asarray(arr)
                if arr.shape[0] != 3:
                    raise ValueError(f"Expected shape (3, N), got {arr.shape}")
                mat_data.append(arr)

        # Concatenate all arrays horizontally
        result = np.concatenate(mat_data, axis=1)


    finally:
        total_time = time.time() - start_time
        total_time = f"{time.strftime('%H:%M:%S', time.gmtime(int(total_time)))}.{int((total_time - int(total_time)) * 1000):03d}"
        print(f"\nTotal time taken: {total_time}")




            #merged_lists = [list(filter(lambda x: x is not None, sublist))
            #                      for sublist in zip_longest(
            #                          [[list(pair)] for pair in zip(*[sublist for sublist in txt_values])],
            #                          [[list(pair)] for pair in zip(*[sublist for sublist in ctsv_values])],
            #                          [[list(pair)] for pair in zip(*[sublist for sublist in nii_values])],
            #                          [[list(pair)] for pair in zip(*[sublist for sublist in mat_values])],
            #                          fillvalue=None)]
            #
            #if merged_lists:
            #            save_(output_file, list(collapse(sum(merged_lists, []))))




if __name__ == "__main__":
    main()
