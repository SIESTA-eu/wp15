import sys, csv, os
from more_itertools import collapse


def read(filepath, delimiter='\t'):
    """
    Reads a TSV file and returns its content as a vector 
    and its structure as the number of rows and columns.
    """
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
                content += line
                # store the number of columns in the structure
                structure['ncols'] = len(line)
    # store the number of rows in the structure
    structure['nrows'] = int(len(content) / structure['ncols'])

    return content, structure


def write(filepath, content, structure, delimiter='\t'):
    nrows = structure.get('nrows', 0)
    ncols = structure.get('ncols', 0)
    if nrows>1 or ncols>1:
        # reformat the vectorized content into a table with rows and columns
        if len(content) != nrows * ncols:
            raise ValueError("Content length does not match structure dimensions")
        content = [[ content[i * ncols + j] for j in range(ncols) ] for i in range(nrows)]

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

