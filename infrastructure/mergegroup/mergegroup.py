import os, csv, re, sys, json, h5py, scipy.io  
import numpy as np
import nibabel as nib
from more_itertools import collapse
from itertools import zip_longest

def filetype(filename):
    filename = filename.strip()  
    extensions = {".txt": "txt", ".csv": "csv", ".tsv": "tsv", ".nii": "nii", ".nii.gz": "nii", ".mat": "mat"}
    for ext, file_type in extensions.items():
        if filename.lower().endswith(ext): 
            return file_type
    return "unknown"



def parse_ctsv(filepath, delimiter):
    data = list()
    with open(filepath, 'r') as file:
        reader = csv.reader(file, delimiter=delimiter)
        for row in reader:
            line = list()
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
                
    return data

def parse_txt(filepath, delimiter=' '):
    data = list()
    with open(filepath, 'r') as file:
        for line in file:
            row = line.strip().split(delimiter)
            line = list()
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
    return data

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
    file_types = {key: filetype(key) for key in whitelist}
    txt_values, ctsv_values ,mat_values, nii_values = list(), list(), list(), list()
    
    for key in whitelist:
        input_dirs = sorted([f"{item}/{key}" for item in sys.argv[1:-2]], key=lambda x: [int(text) if text.isdigit() else text for text in re.split(r'(\d+)', x)])
        txt_aux, ctsv_aux,mat_aux, nii_aux = list(), list(), list(), list()
        for input_dir in input_dirs:  
            if os.path.exists(input_dir):
                try:
                    if file_types[key] == "txt":
                        data = parse_txt(input_dir)
                        txt_aux.append(list(collapse(data)))
                        print(f"Merging: {input_dir} -> {output_dir}/group-merged.tsv")
                    if file_types[key] in ["csv", "tsv"]:
                        delimiter = "," if file_types[key] == "csv" else "\t"
                        data = parse_ctsv(input_dir, delimiter)
                        ctsv_aux.append(list(collapse(data)))              
                        print(f"Merging: {input_dir} -> {output_dir}/group-merged.tsv")
                    if file_types[key] == "nii":
                        nii_aux.append(parse_nii(input_dir).flatten())
                        print(f"Merging: {input_dir} -> {output_dir}/group-merged.tsv")
                    if file_types[key] == "mat":
                        mat_aux.append(parse_mat(input_dir))
                        print(f"Merging: {input_dir} -> {output_dir}/group-merged.tsv")
                    else: 
                        pass
                        #print(f"Unsupported file type: {key}")
                except Exception as e:
                    print(f"Error processing {input_dir}: {e}")
            else:
                print(f"Expected file '{input_dir.split('/')[-1]}' does not exist in directory {'/'.join(input_dir.split('/')[:-1])}")        
        if txt_aux:
            txt_values.append(txt_aux)
        if ctsv_aux:
            ctsv_values.append(ctsv_aux)
        if nii_aux:
            nii_values.append(nii_aux)
        if mat_aux:
            mat_values.append([prep_(i) for i in mat_aux])
    
    #txt_values = list(np.array(txt_values).T)
    ctsv_values= list(np.array(ctsv_values).T)    
    #nii_values= list(np.array(nii_values).T)
    mat_values= list(np.array(mat_values).T)
 
    merged_lists = [list(filter(lambda x: x is not None, sublist)) for sublist in zip_longest(
    [[list(pair)] for pair in zip(*[sublist for sublist in txt_values])],#[i for i in txt_values], 
    [[list(pair)] for pair in zip(*[sublist for sublist in ctsv_values])],#[list(i) for i in ctsv_values], 
    [[list(pair)] for pair in zip(*[sublist for sublist in nii_values])],#[i for i in nii_values], 
    [[list(pair)] for pair in zip(*[sublist for sublist in mat_values])],#[prep_(i) for i in mat_values]
    fillvalue=None)]
    
    if os.path.exists(f"{output_dir}/group-merged.tsv"):
        os.remove(f"{output_dir}/group-merged.tsv")
    for i in merged_lists:
         save_(f"{output_dir}/group-merged.tsv", list(collapse(i)))
    
if __name__ == "__main__":
    main()
