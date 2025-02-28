import os, csv, re, sys
import numpy as np

if len(sys.argv) < 3:
    print("Usage: apptainer run mergegroup.sif <output dir> <output file>")
    sys.exit(1)


output_file = sys.argv[2]
output_dir = sys.argv[1]
os.makedirs(output_dir, exist_ok=True)

folders = sorted(
    [f for f in os.listdir() if re.match(r"group-\d+", f)], 
    key=lambda x: int(x.split('-')[1])
)

data_matrix = []
for folder in folders:
    file_path = os.path.join(folder, "group", "results.tsv")
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                print(f"Processing: {file_path} -> {output_dir}/{output_file}")
                reader = csv.reader(f, delimiter='\t')
                row = [float(x) for x in next(reader)]
                data_matrix.append(row)
        except (ValueError, StopIteration) as e:
            print(e)
            continue
    else:
        print(f"File not found: {file_path}")

if data_matrix:
    if output_file:
        np.savetxt(output_dir+"/"+output_file, np.array(data_matrix), delimiter='\t', fmt='%.15f')
    else:
        np.savetxt(output_dir+"/"+"whitelist.txt", np.array(data_matrix), delimiter='\t', fmt='%.15f')
else:
    print("No valid data found.")

