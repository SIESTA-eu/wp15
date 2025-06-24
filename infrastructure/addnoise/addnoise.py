import csv
import sys

# FIXME FIXME FIXME FIXME FIXME FIXME FIXME 
# This should start with the whitelist file, which is not implemented yet.
# FIXME FIXME FIXME FIXME FIXME FIXME FIXME

def addnoise(result_file, noise_file, output_file):
    """
    Reads two TSV files, one with the results of the pipeline and the other with the calibrated noise_file, 
    adds the corresponding numeric values (noise_file to result_file), and writes the result_file to an output TSV file.
    """
    try:
        # Read the first file
        with open(result_file, 'r', newline='') as f1:
            reader1 = csv.reader(f1, delimiter='\t')
            result = [row for row in reader1]
        
        # Read the second file
        with open(noise_file, 'r', newline='') as f2:
            reader2 = csv.reader(f2, delimiter='\t')
            noise = [row for row in reader2]
        
        # Check if files have the same dimensions
        if len(result) != len(noise):
            raise ValueError("Files have different number of rows")
        
        result_file = []
        for row1, row2 in zip(result, noise):
            if len(row1) != len(row2):
                raise ValueError("Rows have different number of columns")
            
            new_row = []
            for val1, val2 in zip(row1, row2):
                # Try to convert to float and add if both are numeric
                try:
                    num1 = float(val1)
                    num2 = float(val2)
                    new_val = num1 + num2
                    # Keep as integer if possible for cleaner output
                    if new_val.is_integer():
                        new_row.append(str(int(new_val)))
                    else:
                        new_row.append(str(new_val))
                except ValueError:
                    # If not numeric, keep the value from result_file
                    new_row.append(val1)
            
            result_file.append(new_row)
        
        # Write the result_file to output file
        with open(output_file, 'w', newline='') as out_file:
            writer = csv.writer(out_file, delimiter='\t')
            writer.writerows(result_file)
        
        print(f"Successfully added the noise to the results and wrote {output_file}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python addnoise.py <result_file.tsv> <noise_file.tsv> <output_file.tsv>")
        sys.exit(1)
    
    result_file = sys.argv[1]
    noise_file = sys.argv[2]
    output_file = sys.argv[3]
    
    addnoise(result_file, noise_file, output_file)