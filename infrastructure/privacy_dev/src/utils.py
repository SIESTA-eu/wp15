import numpy as np
import os
import nibabel as nib
from sklearn.neighbors import BallTree
from nilearn.input_data import NiftiMasker
from joblib import Parallel, delayed

def searchlight_cov(fmri_path, mask_path, radius=2, output_path=None, n_jobs=-1):

    fmri_img = nib.load(fmri_path)
    mask_img = nib.load(mask_path)

    masker = NiftiMasker(mask_img=mask_img, standardize=True)
    ts = masker.fit_transform(fmri_img).T  

    n_vox, _ = ts.shape
    coords = np.array(np.where(mask_img.get_fdata())).T
    tree = BallTree(coords)
    neighbors_list = tree.query_radius(coords, r=radius)

    def voxel_mean_cov(idx):
        if len(idx) < 2:
            return 0.0
        X = ts[idx] - ts[idx].mean(axis=1, keepdims=True)
        cov = np.cov(X)
        mean_cov = (np.sum(cov) - np.trace(cov)) / (cov.size - len(idx))
        return mean_cov

    values = Parallel(n_jobs=n_jobs, backend="loky")(
        delayed(voxel_mean_cov)(idx) for idx in neighbors_list
    )
    values = np.array(values)
    out_data = np.zeros(mask_img.shape)
    mask_indices = tuple(coords.T)
    out_data[mask_indices] = values

    out_img = nib.Nifti1Image(out_data, affine=mask_img.affine)
    if not output_path:
        nib.save(out_img, output_path)
    
    return out_data


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

