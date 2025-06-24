import csv
import math
import sys

def calibratenoise(input_file, output_file):
    """
    Reads a TSV file, computes standard deviation for each column,
    and writes the results to another TSV file.
    """
    # Initialize variables
    columns = []
    column_sums = []
    column_sums_sq = []
    row_count = 0
    
    # Read input file and compute sums
    with open(input_file, 'r', newline='') as tsv_in:
        reader = csv.reader(tsv_in, delimiter='\t')
        
        # Read header if exists (we'll assume first row is header)
        try:
            first_row = next(reader)
            num_columns = len(first_row)
            # jump back to the start of the file
            tsv_in.seek(0)
        except StopIteration:
            print(f"Error: Empty input file {input_file}")
            return
        
        # Initialize data structures
        columns = [[] for _ in range(num_columns)]
        column_sums = [0.0] * num_columns
        column_sums_sq = [0.0] * num_columns
        
        # Process each row
        for row in reader:
            if len(row) != num_columns:
                print(f"Warning: Row {row_count+1} has {len(row)} columns, expected {num_columns}. Skipping.")
                continue
            
            for i in range(num_columns):
                try:
                    value = float(row[i])
                    columns[i].append(value)
                    column_sums[i] += value
                    column_sums_sq[i] += value * value
                except ValueError:
                    print(f"Warning: Non-numeric value '{row[i]}' in column {i+1}, row {row_count+1}. Skipping.")
            
            row_count += 1
    
    if row_count < 2:
        print("Error: Need at least 2 data points to calculate standard deviation")
        return
    
    # Calculate standard deviations
    std_devs = []
    for i in range(num_columns):
        if len(columns[i]) < 2:
            std_dev = float('nan')  # not enough data
        else:
            mean = column_sums[i] / len(columns[i])
            variance = (column_sums_sq[i] - (column_sums[i]**2)/len(columns[i])) / (len(columns[i]) - 1)
            std_dev = math.sqrt(variance)
            # Scale the noise with the number of columns
            std_dev *= math.sqrt(num_columns)
        std_devs.append(std_dev)
    
    # Write results to output file
    with open(output_file, 'w', newline='') as tsv_out:
        writer = csv.writer(tsv_out, delimiter='\t')
        
        # Write standard deviations
        writer.writerow(std_devs)
    
    print(f"Standard deviations written to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python calibratenoise.py <input.tsv> <output.tsv>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    calibratenoise(input_file, output_file)