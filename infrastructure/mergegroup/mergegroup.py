import os, csv, re, sys
import numpy as np

if len(sys.argv) < 4:
    print("Usage: apptainer run mergegroup.sif <input dir 1> <input dir 2> <input dir 3> ... <output dir> <whitelist.txt>")
    sys.exit(1)

try:
    with open(sys.argv[-1], "r") as file:
        whitelist = [line.strip() for line in file if not line.startswith("#")]
except FileNotFoundError:
    print("Please provide a valid path to whitelist.txt")
    sys.exit(1)
    
output_dir = sys.argv[-2]
os.makedirs(output_dir, exist_ok=True)

for i in range(len(whitelist)):
	input_dirs = sorted([f"{item}/{whitelist[i]}" for item in sys.argv[1:-2]], 
			 key=lambda x:[int(text) if text.isdigit() else text for text in re.split(r'(\d+)', x)])

	print(input_dirs)
	data_matrix = []

	for input_dir in input_dirs:
		if os.path.exists(input_dir):
		    try:
		        with open(input_dir, 'r') as f:
		            print(f"Merging: {input_dir} -> {output_dir}/group-merged.tsv")
		            reader = csv.reader(f, delimiter='\t')
		            row = [float(x) for x in next(reader)]
		            data_matrix.append(row)
		            
		    except (ValueError, StopIteration) as e:
		        print(e)
		        continue
		else:
		    print(f"File not found: {input_dir}")
		    

if data_matrix:
    with open(output_dir+"/group-merged.tsv", "w") as file:
        for row in data_matrix:
            val = "\t".join(f"{value}" for value in row)
            file.write(val + "\n")
else:
    print("No valid data found.")
