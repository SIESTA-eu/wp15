import os, csv, re, sys, json, h5py, scipy.io  
import numpy as np
import nibabel as nib
from more_itertools import collapse

def filetype(filename):
    filename = filename.strip()  
    extensions = {".txt": "txt", ".csv": "csv", ".tsv": "tsv", ".nii": "nii", ".nii.gz": "nii", ".mat": "mat"}
    for ext, file_type in extensions.items():
        if filename.lower().endswith(ext): 
            return file_type
    return "unknown"

def parse_ctsv(filepath, delimiter):
    data = []
    header = None
    with open(filepath, 'r') as f:
        reader = csv.reader(f, delimiter=delimiter)
        l = next(reader, None)
        if any(not c.isdigit() for c in l):
            header = l
        else:
            data.append([float(x) for x in l])
        for row in reader:
            data.append([float(x) for x in row])
    return header, data

def parse_nii(filepath):
    return nib.load(filepath).get_fdata()

def parse_mat(filepath):    
    try:
        return scipy.io.loadmat(filepath)
    except NotImplementedError:
        with h5py.File(filepath, 'r') as file:
            return {key: (dataset[()] if isinstance(dataset, h5py.Dataset) else {subkey: dataset[subkey][()] for subkey in dataset.keys()})
                    for key, dataset in file.items() if key != "#refs#"}


def prep_(dict_):
    def flatten(lst):
        if isinstance(lst, list):
            return [item for sublist in lst for item in flatten(sublist)]
        return [lst]

    result = []
    for v in dict_.values():
        if isinstance(v, dict):
            result.extend(prep_(v))
        else:
            result.extend(flatten(v))
    return list(collapse(result))

def save_(filename, data):
    with open(filename, "a") as f:
        f.write("\t".join(map(str, data)) + "\n")

def main():
    if len(sys.argv) < 4:
        print("Usage: apptainer run mergegroup.sif <input dir 1> <input dir 2> ... <output dir> <whitelist.txt>")
        sys.exit(1)

    try:
        with open(sys.argv[-1], "r") as file:
            whitelist = [line.strip() for line in file if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        print("Please provide a valid path to whitelist.txt")
        sys.exit(1)

    output_dir = sys.argv[-2]
    os.makedirs(output_dir, exist_ok=True)
    data_dict = {key: list() for key in whitelist}
    headers = {key: None for key in whitelist}
    file_types = {key: filetype(key) for key in whitelist}
    txt_values, mat_values, nii_values = list(), list(), list()
    for key in whitelist:
        input_dirs = sorted([f"{item}/{key}" for item in sys.argv[1:-2]], key=lambda x: [int(text) if text.isdigit() else text for text in re.split(r'(\d+)', x)])
        
        for input_dir in input_dirs:
            if os.path.exists(input_dir):
                try:
                    if file_types[key] == "txt":
                        with open(input_dir, "r") as file:
                            txt_values.append(file.readline().strip())
                        print(f"Merging: {input_dir} -> {output_dir}/group-merged.tsv")
                    if file_types[key] in ["csv", "tsv"]:
                        delimiter = "," if file_types[key] == "csv" else "\t"
                        header, data = parse_ctsv(input_dir, delimiter)
                        if headers[key] is None:
                            headers[key] = header
                        data_dict[key].extend(data)
                        print(f"Merging: {input_dir} -> {output_dir}/group-merged.tsv")
                    if file_types[key] == "nii":
                        nii_values.append(parse_nii(input_dir).flatten())
                        print(f"Merging: {input_dir} -> {output_dir}/group-merged.tsv")
                    if file_types[key] == "mat":
                        mat_values.append(parse_mat(input_dir))
                        print(f"Merging: {input_dir} -> {output_dir}/group-merged.tsv")
                    else: 
                        pass
                        #print(f"Unsupported file type: {key}")
                except Exception as e:
                    print(f"Error processing {input_dir}: {e}")
            else:
                print(f"Expected file '{input_dir.split('/')[-1]}' does not exist in directory {'/'.join(input_dir.split('/')[:-1])}")        


    if os.path.exists(f"{output_dir}/group-merged.tsv"):
        os.remove(f"{output_dir}/group-merged.tsv")
    if txt_values:
        for i in txt_values:
            save_(f"{output_dir}/group-merged.tsv", i)
    if data_dict:
        for i in list(data_dict.values())[0]:
            save_(f"{output_dir}/group-merged.tsv",list(collapse(i)))
    if nii_values:
        for i in nii_values:
            save_(f"{output_dir}/group-merged.tsv",list(collapse(i))) 
    if mat_values:
        for i in mat_values:
            save_(f"{output_dir}/group-merged.tsv",prep_(i))  
    else:
        pass
        #print("No valid data found.")

if __name__ == "__main__":
    main()
