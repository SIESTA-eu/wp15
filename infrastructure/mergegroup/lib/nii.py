import sys, os
import nibabel as nib
from more_itertools import collapse

def read(filepath):
    structure = {}
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File {filepath} does not exist")
        
    if not os.path.isfile(filepath):
        raise ValueError(f"{filepath} is not a regular file")
        
    img = nib.load(filepath)
    if img is None:
        raise ValueError("Failed to load NIfTI image")
        
    content = img.get_fdata()
    if content is None:
        raise ValueError("Failed to get content from NIfTI image")
        
    content = list(collapse(content))
    return content, structure
    

def write(filepath, content, structure):
    raise NotImplementedError("Writing to .nii files is not implemented yet.")
    return

