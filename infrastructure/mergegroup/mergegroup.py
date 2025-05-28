#!/usr/bin/env python3

import os, csv, re, sys, json, h5py, scipy.io, itertools, time
import numpy as np
import nibabel as nib
from more_itertools import collapse
from itertools import zip_longest
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
            
        img = nib.load(filepath)
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
    meta_keys = {'__header__', '__version__', '__globals__', '#refs#'}
    try:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File {filepath} does not exist")
            
        if not os.path.isfile(filepath):
            raise ValueError(f"{filepath} is not a regular file")
            
        try:
            val = scipy.io.loadmat(filepath)
            val = {k: v for k, v in val.items() if k not in meta_keys and not k.startswith('__')}
            val = [list(collapse(val[k])) for k in list(val.keys())][0]
            f_val = []
            #print(set([type(i) for i in val]))
            for v in val:
                if isinstance(v, np.str_) or v is None:
                    pass
                else:
                    f_val.append(v)
            return f_val
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

        data_dict = {key: list() for key in whitelist}
        file_types = {key: filetype(key) for key in whitelist}
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
            
        for item in tqdm(input_dirs, desc=f"Processing: "):
            try:
                if not os.path.exists(item):
                    print(f"Warning: Input directory {item} does not exist", file=sys.stderr)
                    continue
                    
                if not os.path.isdir(item):
                    print(f"Warning: {item} is not a directory", file=sys.stderr)
                    continue
                    
                txt_aux, ctsv_aux, mat_aux, nii_aux = list(), list(), list(), list()
                print()
                for key in whitelist:
                    try:
                        input_dir = os.path.join(item, key)
                        if not os.path.exists(input_dir):
                            print(f"Warning: File '{os.path.basename(input_dir)}' not found in {os.path.dirname(input_dir)}", file=sys.stderr)
                            continue
                            
                        file_type = file_types[key]
                        
                        if file_type == "txt":
                            data = parse_txt(input_dir)
                            if data:
                                txt_aux.append(list(collapse(data)))
                                print(f"Merging: {input_dir} -> {output_file}")
                            
                        elif file_type in ["csv", "tsv"]:
                            delimiter = "," if file_type == "csv" else "\t"
                            data = parse_ctsv(input_dir, delimiter)
                            if data:
                                ctsv_aux.append(list(collapse(data)))
                                print(f"Merging: {input_dir} -> {output_file}")
                            
                        elif file_type == "nii":
                            data = parse_nii(input_dir)
                            if data is not None:
                                nii_aux.append(data.flatten())
                                print(f"Merging: {input_dir} -> {output_file}")
                            
                        elif file_type == "mat":
                            data = parse_mat(input_dir)
                            if data is not None:
                                mat_aux.append(data)
                                print(f"Merging: {input_dir} -> {output_file}")
                            
                        else:
                            print(f"Warning: Unsupported file type {file_type} for {input_dir}", file=sys.stderr)
                            
                    except Exception as e:
                        print(f"Error processing file {input_dir}: {str(e)}", file=sys.stderr)
                        continue

                if txt_aux:
                    txt_values.append(txt_aux)
                if ctsv_aux:
                    ctsv_values.append(ctsv_aux)
                if nii_aux:
                    nii_values.append(nii_aux)
                if mat_aux:
                    mat_values.append(list(collapse([i for i in mat_aux])))
                
                try:
                    if ctsv_values:
                        ctsv_values = list(np.array(ctsv_values).T)
                    if mat_values:
                        mat_values = list(np.array(mat_values).T)

                    merged_lists = [list(filter(lambda x: x is not None, sublist)) 
                                  for sublist in zip_longest(
                                      [[list(pair)] for pair in zip(*[sublist for sublist in txt_values])],
                                      [[list(pair)] for pair in zip(*[sublist for sublist in ctsv_values])],
                                      [[list(pair)] for pair in zip(*[sublist for sublist in nii_values])],
                                      [[list(pair)] for pair in zip(*[sublist for sublist in mat_values])],
                                      fillvalue=None)]
                    
                    if merged_lists:
                        save_(output_file, list(collapse(sum(merged_lists, []))))
                        
                except Exception as e:
                    print(f"Error merging data: {str(e)}", file=sys.stderr)
                    
                nii_values, txt_values, mat_values, ctsv_values, merged_lists = list(), list(), list(), list(), list()
                
            except Exception as e:
                print(f"Error processing directory {item}: {str(e)}", file=sys.stderr)
                continue
                
    except Exception as e:
        print(f"Fatal error: {str(e)}", file=sys.stderr)
        sys.exit(1)
        
    finally:
        total_time = time.time() - start_time
        total_time = f"{time.strftime('%H:%M:%S', time.gmtime(int(total_time)))}.{int((total_time - int(total_time)) * 1000):03d}"
        print(f"\nTotal time taken: {total_time}")

if __name__ == "__main__":
    main()
