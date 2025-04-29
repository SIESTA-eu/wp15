#!/usr/bin/env python3

import numpy as np
import scipy as sp
import nibabel as nib
import time
import os
import sys
import ast
from tqdm import tqdm
from pathlib import Path
from typing import List
from . import get_inputfiles, drmaa_nativespec


def scramble_nii(inputdir: str, outputdir: str, select: str, bidsvalidate: bool, method: str='null', fwhm: float=0, dims: List[str]=(), independent: bool=False,
                 radius: float=1, freqrange: List[float]=(0,0), amplitude: float=1, cluster: str='', dryrun: bool=False, **_):

    # Defaults
    inputdir  = Path(inputdir).resolve()
    outputdir = Path(outputdir).resolve()

    # Create pseudo-random out data for all files of each included data type
    inputfiles, _ = get_inputfiles(inputdir, select, '*.nii*', bidsvalidate)
    if not inputfiles:
        return

    # Submit scramble jobs on the DRMAA-enabled HPC
    if cluster:

        # Lazy import to avoid import errors on non-HPC systems
        from drmaa import Session as DrmaaSession

        with DrmaaSession() as pbatch:
            jobids                  = []
            job                     = pbatch.createJobTemplate()
            job.jobEnvironment      = os.environ
            job.remoteCommand       = 'python'      # Call `python -m __name__` because `__file__` is not executable (NB: calling the scramble parent instead of self would be much more complicated)
            job.nativeSpecification = drmaa_nativespec(cluster, pbatch)
            job.joinFiles           = True
            (outputdir/'logs').mkdir(exist_ok=True, parents=True)

            for inputfile in inputfiles:
                subid          = inputfile.name.split('_')[0].split('-')[1]
                sesid          = inputfile.name.split('_')[1].split('-')[1] if '_ses-' in inputfile.name else ''
                job.args       = ['-m', __name__, inputdir, outputdir, inputfile.relative_to(inputdir), bidsvalidate, method, fwhm, dims, independent, radius, freqrange, amplitude, '', dryrun]
                job.jobName    = f"scramble_nii_sub-{subid}_ses-{sesid}"
                job.outputPath = f"{os.getenv('HOSTNAME')}:{outputdir/'logs'/job.jobName}.out"
                jobids.append(pbatch.runJob(job))
            print(f"HPC output logs are written to: {outputdir/'logs'}")

            watchjobs(pbatch, jobids)
            pbatch.deleteJobTemplate(job)

        return

    # Scramble the included input files
    for inputfile in tqdm(inputfiles, unit='file', colour='green', leave=False):

        # Load the (zipped) nii data
        inputimg: nib.ni1.Nifti1Image = nib.load(inputfile)
        data   = inputimg.get_fdata()
        voxdim = inputimg.header['pixdim'][1:4]
        if data.ndim < 3 and method in ('scatter', 'wobble'):
            tqdm.write(f"WARNING: {inputfile} only has {data.ndim} image dimensions (must be 3 or more), aborting '{method}' scrambling...")
            continue

        # Apply the scrambling method
        if method == 'permute':
            axis = dict([(d,i) for i,d in enumerate(['x','y','z','t','u','v','w'])])    # NB: Assumes data is oriented in a standard way (i.e. no dim-flips, no rotations > 45 deg)
            for dim in dims:
                if independent:
                    np.random.default_rng().permuted(data, axis=axis[dim], out=data)
                else:
                    np.random.default_rng().shuffle(data, axis=axis[dim])

        elif method == 'blur':
            sigma = list(abs(fwhm/voxdim/2.355)) + [0]*4         # No smoothing over any further dimensions such as time (Nifti supports up to 7 dimensions)
            data  = sp.ndimage.gaussian_filter(data, sigma[0:data.ndim], mode='nearest')

        elif method == 'scatter':
            window = abs(np.int16(2 * radius / voxdim))                     # Size of the sliding window
            step   = [int(d/2) or 1 for d in window]                        # Sliding step (NB: int >= 1): e.g. 1/4 of the size of the sliding window (to speed up)
            tqdm.write(f"window: {window}\nstep: {step}")
            for x in range(0, data.shape[0] - window[0], step[0]):
                for y in range(0, data.shape[1] - window[1], step[1]):
                    for z in range(0, data.shape[2] - window[2], step[2]):
                        box = data[0+x:window[0]+x, 0+y:window[1]+y, 0+z:window[2]+z]
                        np.random.default_rng().permuted(box, out=box)
                        box = None
                        if x == data.shape[0] - window[0] - 1:              # We are at the edge, permute the remaining part
                            box = data[-step[0]:, 0+y:window[1]+y, 0+z:window[2]+z]
                        if y == data.shape[1] - window[1] - 1:
                            box = data[0+x:window[0]+x, -step[1]:, 0+z:window[2]+z]
                        if y == data.shape[2] - window[2] - 1:
                            box = data[0+x:window[0]+x, 0+y:window[1]+y, -step[2]:]
                        if box is not None:
                            np.random.default_rng().permuted(box, out=box)

        elif method == 'reface':
            pass

        elif method == 'wobble':
            # Implementation ideas:
            # 1. Add random k-space phase gradients in a mid-range frequency band while using a sliding window in image space
            # 2. Use a random deformation/warp field (see e.g. https://antspy.readthedocs.io/en/latest/registration.html)
            # 3. Apply random wavy (tapered wrap-around?) translations (https://numpy.org/doc/stable/reference/generated/numpy.roll.html) in x, y and z (repeatedly if that is still reversible?)
            for dim in (0,1,2,1,0):
                for axis in [ax for ax in (0,1,2) if ax != dim]:
                    index  = np.arange(data.shape[dim], dtype=np.float64)
                    wobble = 0 * index
                    lowfreq, highfreq = abs(np.float64(freqrange) * voxdim[dim] / index[-1])
                    if highfreq > 0.5:
                        tqdm.write(f"WARNING: the high-frequency in {freqrange} is higher than the Nyquist / maximum possible frequency: {0.5*index[-1] / voxdim[dim]}")
                    for f in np.arange(0, 0.5, 1 / index[-1]):
                        if lowfreq <= f <= highfreq:
                            wobble += np.sin(2*np.pi * (f * index + np.random.rand()))
                    for i in index.astype(int):
                        slab = (slice(None),) * dim + (i,)   # https://stackoverflow.com/questions/42817508/get-the-i-th-slice-of-the-k-th-dimension-in-a-numpy-array
                        data[slab] = np.roll(data[slab], round(amplitude * wobble[i]), axis=axis if axis < dim else axis - 1)

        elif method in ('null', None):
            data = data * 0

        else:
            raise ValueError(f"Unknown nii-scramble method: {method}")

        # Save the output data
        outputfile = outputdir/inputfile.relative_to(inputdir)
        tqdm.write(f"Saving: {outputfile}")
        if not dryrun:
            outputfile.parent.mkdir(parents=True, exist_ok=True)
            outputimg = nib.Nifti1Image(data, inputimg.affine, inputimg.header)
            nib.save(outputimg, outputfile)


def watchjobs(pbatch, jobids: list):
    """
    Shows tqdm progress bars for queued and running DRMAA jobs. Waits until all jobs have finished

    :param pbatch: The DRMAA session
    :param jobids: The job ids
    :return:
    """

    qbar = tqdm(total=len(jobids), desc='Queued ', unit='job', leave=False, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]')
    rbar = tqdm(total=len(jobids), desc='Running', unit='job', leave=False, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]', colour='green')
    done = 0
    while done < len(jobids):
        jobs   = [pbatch.jobStatus(jobid) for jobid in jobids]
        done   = sum([status in ('done', 'failed', 'undetermined') for status in jobs])
        qbar.n = sum([status == 'queued_active'                    for status in jobs])
        rbar.n = sum([status == 'running'                          for status in jobs])
        qbar.refresh(), rbar.refresh()
        time.sleep(2)
    qbar.close(), rbar.close()
    print(f"Finished processing all {len(jobids)} jobs")

    failedjobs = [jobid for jobid in jobids if pbatch.jobStatus(jobid) == 'failed']
    if failedjobs:
        print(f"ERROR: {len(failedjobs)} HPC jobs failed to run:\n{failedjobs}\nThis may well be due to an underspecified `--cluster` input option (e.g. not enough memory)")


if __name__ == '__main__':
    """drmaa usage: python -m __name__ args"""

    args = sys.argv[1:]
    """ Non-str scramble_nii() arguments indices (zero-based) that are passed as strings:
    3  bidsvalidate: bool=False
    5  fwhm: float
    6  dims: List[str]=()
    7  independent: bool=False
    8  radius: float=1
    9  freqrange: List[float]=(0,0)
    10 amplitude: float=1
    12 dryrun: bool=False
    """
    print('Running scramble_nii with commandline args:', args)
    for n in [3, 5, 7, 8, 9, 10, 12]:
        args[n] = ast.literal_eval(args[n])
    args[6] = args[6][1:-1].replace(' ','').split(',') if args[6] else []

    scramble_nii(*args)
