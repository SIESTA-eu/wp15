import pandas as pd
import numpy as np
import re
from tqdm import tqdm
from pathlib import Path
from . import get_inputfiles


def scramble_tsv(inputdir: str, outputdir: str, select: str, bidsvalidate: bool, method: str='null', preserve: str= '^$', dryrun: bool=False, **_):

    # Defaults
    inputdir  = Path(inputdir).resolve()
    outputdir = Path(outputdir).resolve()

    # Create pseudo-random out data for all files of each included data type
    inputfiles, _ = get_inputfiles(inputdir, select, '*.tsv', bidsvalidate)
    for inputfile in tqdm(inputfiles, unit='file', colour='green', leave=False):

        # Load the (zipped) tsv data
        tsvdata = pd.read_csv(inputfile, sep='\t')

        # Permute the data in each of the columns of no interest, preserve the order of the data in the columns of interest
        if method == 'permute':
            for column in tsvdata.columns:
                if not re.fullmatch(preserve or '^$', column or 'unspecified'):
                    tsvdata[column] = np.random.permutation(tsvdata[column])
        elif method in ('null', None):
            tsvdata = pd.DataFrame(columns=tsvdata.columns, index=tsvdata.index)
        else:
            raise ValueError(f"Unknown tsv-scramble method: {method}")

        # Permute the rows
        tsvdata = tsvdata.sample(frac=1).reset_index(drop=True)

        # Save the output data
        outputfile = outputdir/inputfile.relative_to(inputdir)
        tqdm.write(f"Saving: {outputfile}")
        if not dryrun:
            outputfile.parent.mkdir(parents=True, exist_ok=True)
            tsvdata.to_csv(outputfile, sep='\t', index=False, encoding='utf-8', na_rep='n/a')
