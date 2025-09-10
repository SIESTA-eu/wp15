import numpy as np
import os

def detect_file(folder):
    has_fif = False
    has_nii = False
    has_vhdr = False
    
    for root, _, files in os.walk(folder):
        for f in files:
            if f.endswith(".fif") or f.endswith(".fif.gz"):
                has_fif = True
                break 
            elif f.endswith(".vhdr") or f.endswith(".vhdr.gz"):
                has_vhdr = True
                break  
            elif f.endswith(".nii.gz") or "_T1w.nii.gz" in f:
                has_nii = True
        if has_fif:
            break  
    if has_fif:
        return "fif"
    if has_vhdr:
        return "vhdr"
    elif has_nii:
        return "nii"
    else:
        return None 

