import sys, csv, os
from more_itertools import collapse


def read(filepath, delimiter='\t'):
    content = []
    structure = {}
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File {filepath} does not exist")
        
    if not os.path.isfile(filepath):
        raise ValueError(f"{filepath} is not a regular file")
        
    with open(filepath, 'r') as file:
        reader = csv.reader(file, delimiter=delimiter)
        for row_num, row in enumerate(reader, 1):
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
                content.append(line)

    content = list(collapse(content))
    return content, structure


def write(filepath, content, structure, delimiter='\t'):
    # FIXME the structure should contain information about the number of rows and columns, and about the header
    with open(filepath, 'w', newline='') as file:
        writer = csv.writer(file, delimiter=delimiter)
        if isinstance(content, list) and all(isinstance(row, list) for row in content):
            # If content is a list of lists, write each row
            for row in content:
                writer.writerow(row)
        elif isinstance(content, list):
            # If content is a single list, write it as a single row
            writer.writerow(content)
        else:
            # If content is not a list, write it as a single value
            writer.writerow([content])
    return
