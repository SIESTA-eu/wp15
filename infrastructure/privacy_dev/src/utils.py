import numpy as np
import os
import nibabel as nib
from sklearn.neighbors import BallTree
from nilearn.input_data import NiftiMasker

def searchlight_cov(fmri_path, mask_path, radius=2, output_path="sl_cov_map.nii.gz"):
    fmri_img = nib.load(fmri_path)
    mask_img = nib.load(mask_path)

    masker = NiftiMasker(mask_img=mask_img, standardize=True)
    ts = masker.fit_transform(fmri_img).T

    n_vox, _ = ts.shape
    coords = np.array(np.where(mask_img.get_fdata())).T
    tree = BallTree(coords)
    neighbors = tree.query_radius(coords, r=radius)

    values = np.zeros(n_vox)
    for c, idx in enumerate(neighbors):
        if len(idx) < 2:
            continue
        X = ts[idx] - ts[idx].mean(axis=1, keepdims=True)
        cov = np.cov(X)
        d = np.sqrt(np.diag(cov))
        corr = cov / np.outer(d, d)
        mean_corr = (np.sum(corr) - np.trace(corr)) / (corr.size - len(d))
        values[c] = mean_corr

    cov_map = masker.inverse_transform(values.reshape(1, -1))
    cov_map.to_filename(output_path)
    return cov_map


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

