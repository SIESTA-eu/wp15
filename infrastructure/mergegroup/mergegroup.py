import os, csv, re, sys, json, h5py, scipy.io  
import numpy as np
import nibabel as nib

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

def save_mat(data, filepath):
    with open(filepath, 'w') as f:
        for entry in data:
            json.dump(entry, f, default=lambda o: o.tolist() if isinstance(o, np.ndarray) else o)
            f.write('\n')

def save_txt(output_path, data):
    with open(output_path, "w") as file:
        file.writelines("\t".join(map(str, row)) + "\n" for row in data)

def save_ctsv(output_path, data_dict, headers, delimiter):
    with open(output_path, "w", newline='') as file:
        writer = csv.writer(file, delimiter=delimiter)
        if any(headers.values()):
            combined_header = []
            for key in headers:
                if headers[key]:
                    combined_header.extend(headers[key])
            writer.writerow(combined_header)
        max_rows = max(len(rows) for rows in data_dict.values())
        for i in range(max_rows):
            row_values = []
            for key in data_dict:
                if i < len(data_dict[key]):
                    row_values.extend(data_dict[key][i])
                else:
                    row_values.extend(["" for _ in range(len(headers[key]) if headers[key] else len(data_dict[key][0]))])
            writer.writerow(row_values)

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
                        print(f"Merging: {input_dir} -> {output_dir}/group-merged.{file_types[key]}")
                    elif file_types[key] in ["csv", "tsv"]:
                        delimiter = "," if file_types[key] == "csv" else "\t"
                        header, data = parse_ctsv(input_dir, delimiter)
                        if headers[key] is None:
                            headers[key] = header
                        data_dict[key].extend(data)
                        print(f"Merging: {input_dir} -> {output_dir}/group-merged.{file_types[key]}")
                    elif file_types[key] == "nii":
                        nii_values.append(parse_nii(input_dir).flatten())
                        print(f"Merging: {input_dir} -> {output_dir}/group-merged.npy")
                    elif file_types[key] == "mat":
                        mat_values.append(parse_mat(input_dir))
                        print(f"Merging: {input_dir} -> {output_dir}/group-merged.jsonl")
                    else:
                        print(f"Unsupported file type: {key}")
                except Exception as e:
                    print(f"Error processing {input_dir}: {e}")
            else:
                print(f"Expected file '{input_dir.split('/')[-1]}' does not exist in directory {'/'.join(input_dir.split('/')[:-1])}")        

    if file_types[key] == "txt":
        save_txt(f"{output_dir}/group-merged.txt", txt_values)
    elif file_types[key] in ["csv", "tsv"]:
        save_ctsv(f"{output_dir}/group-merged.{file_types[key]}", data_dict, headers, "," if file_types[key] == "csv" else "\t")
    elif file_types[key] == "nii":
        np.savetxt(f"{output_dir}/group-merged.txt", np.array(nii_values), fmt="%.15f") 
        np.save(f"{output_dir}/group-merged.npy", np.array(nii_values))
    elif file_types[key] == "mat":
        save_mat(mat_values, f"{output_dir}/group-merged.jsonl")
    else:
        print("No valid data found.")

if __name__ == "__main__":
    main()
