import numpy as np
import os
import nibabel as nib
from sklearn.neighbors import BallTree
from nilearn.input_data import NiftiMasker
from joblib import Parallel, delayed


def searchlight_cov(fmri_path, mask_path=None, radius=2.0, output_path=None, n_jobs=-1):

    fmri_img = nib.load(fmri_path)
    fmri_data = fmri_img.get_fdata()

    if mask_path is None:
        mask_data = (fmri_data.mean(axis=-1) > 0.0).astype(bool)
        affine = fmri_img.affine
    else:
        mask_img = nib.load(mask_path)
        mask_data = mask_img.get_fdata().astype(bool)
        affine = mask_img.affine

    coords_voxel = np.array(np.where(mask_data)).T
    coords_mm = nib.affines.apply_affine(affine, coords_voxel)
    ts = fmri_data[mask_data]  
    ts = ts - ts.mean(axis=1, keepdims=True)
    tree = BallTree(coords_mm)
    neighbors_list = tree.query_radius(
        coords_mm,
        r=np.linalg.norm(affine[:3, :3], axis=0).mean() * radius
    )

    def voxel_mean_cov(idx):
        k = len(idx)
        if k < 2:
            return 0.0
        X = ts[idx] 
        cov_sum = X @ X.T 
        mean_cov = (np.sum(cov_sum) - np.trace(cov_sum)) / (k*(k-1)*X.shape[1])
        return mean_cov

    values = Parallel(n_jobs=n_jobs, backend="loky")(
        delayed(voxel_mean_cov)(idx) for idx in neighbors_list
    )

    out_data = np.zeros(mask_data.shape)
    for v, val in zip(coords_voxel, values):
        out_data[tuple(v)] = val

    out_img = nib.Nifti1Image(out_data, affine=affine)
    if output_path:
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

