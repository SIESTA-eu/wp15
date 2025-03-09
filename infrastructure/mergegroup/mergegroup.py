import os, csv, re, sys
import numpy as np
import nibabel as nib

def filetype(filename):
    if filename.endswith(".csv"):
        return "csv"
    elif filename.endswith(".tsv"):
        return "tsv"
    elif filename.endswith(".nii") or filename.endswith(".nii.gz"):
        return "nii"
    else:
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

def save_nii(outp, nii_data, affine):

    nii_data = np.stack(nii_list, axis=-1)  
    nib.save(nib.Nifti1Image(nii_data, affine), outp)

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
        print("Usage: apptainer run mergegroup.sif <input dir 1> <input dir 2> <input dir 3> ... <output dir> <whitelist.txt>")
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
    nii_values = list()
    for key in whitelist:
        input_dirs = sorted([f"{item}/{key}" for item in sys.argv[1:-2]],
                             key=lambda x: [int(text) if text.isdigit() else text for text in re.split(r'(\d+)', x)])
        
        for input_dir in input_dirs:
            if os.path.exists(input_dir):
                try:
                    if file_types[key] in ["csv", "tsv"]:
                        delimiter = "," if file_types[key] == "csv" else "\t"
                        header, data = parse_ctsv(input_dir, delimiter)
                        print(f"Merging: {input_dir} -> {output_dir}/group-merged.{file_types[key]}")
                        if headers[key] is None:
                            headers[key] = header
                        data_dict[key].extend(data)
                    elif file_types[key] == "nii":
                        nii_data = parse_nii(input_dir)
                        nii_values.append(nii_data.flatten())
                        print(f"Merging: {input_dir} -> {output_dir}/group-merged.npy")
                    else:
                        print(f"Unsupported file type: {key}")
                except Exception as e:
                    print(f"Error processing {input_dir}: {e}")
    
    if nii_values:
        np.savetxt(output_dir+"/group-merged.txt", np.array(nii_values), fmt="%.15f") 
        np.save(output_dir+"/group-merged.npy", np.array(nii_values))

    if data_dict:
    	output_file = f"{output_dir}/group-merged.csv" if any(ft == "csv" for ft in file_types.values()) else f"{output_dir}/group-merged.tsv"
    	delimiter = "," if output_file.endswith(".csv") else "\t"
    	save_ctsv(output_file, data_dict, headers, delimiter)
    else: print("No valid data found.")
    
if __name__ == "__main__":
    main()
