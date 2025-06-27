import sys

def filetype(filename):
    if not isinstance(filename, str):
        raise ValueError("Filename must be a string")
        
    filename = filename.strip()
    if not filename:
        raise ValueError("Empty filename provided")
        
    extensions = {".txt": "txt", ".csv": "csv", ".tsv": "tsv", 
                    ".nii": "nii", ".nii.gz": "nii", ".mat": "mat"}
    
    for ext, file_type in extensions.items():
        if filename.lower().endswith(ext): 
            return file_type

    # in case there is no match
    return "unknown"
