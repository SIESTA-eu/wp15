#!/usr/bin/env python3

import numpy as np
from tqdm import tqdm
from pathlib import Path
from typing import List
from . import get_inputfiles


def scramble_fif(inputdir: str, outputdir: str, select: str, bidsvalidate: bool, method: str='null', dims: List[str]=(), dryrun: bool=False, **_):

    import mne          # MNE is not imported in the root as it is only installed as `extras`

    # Defaults
    inputdir  = Path(inputdir).resolve()
    outputdir = Path(outputdir).resolve()

    # Create pseudo-random out data for all files of each included data type
    inputfiles, _ = get_inputfiles(inputdir, select, '*.fif', bidsvalidate)
    for inputfile in tqdm(inputfiles, unit='file', colour='green', leave=False):

        # Figure out which reader function to use, fif-files with time-series data come in 3 flavours
        isevoked  = any(mne.io.show_fiff(inputfile,output=list,tag=104))
        isepoched = any(mne.io.show_fiff(inputfile,output=list,tag=373))
        israw     = any(mne.io.show_fiff(inputfile,output=list,tag=102))

        # Read the data
        if israw:
            obj = mne.io.read_raw_fif(inputfile, preload=True)
        elif isevoked:
            obj = mne.Evoked(inputfile)
        elif isepoched:
            raise Exception(f"cannot read epoched FIF file: {inputfile}")

        # Apply the scrambling method
        if method == 'permute':
            axis = dict([(d, i) for i, d in enumerate(['channel', 'time'])])

            if not type(dims) is list:
                dims = [dims]

            # scramble the samples across the requested dimension(s)
            rng = np.random.default_rng()
            for dim in range(len(dims)):
                rng.shuffle(obj._data, axis=axis[dims[dim]])

        elif method in ('null', None):
            obj._data *= 0

        else:
            raise ValueError(f"Unknown fif-scramble method: {method}")

        # Save the output data
        outputfile = outputdir/inputfile.relative_to(inputdir)
        tqdm.write(f"Saving: {outputfile}")
        if not dryrun:
            outputfile.parent.mkdir(parents=True, exist_ok=True)
            obj.save(outputfile, overwrite=True)
