#!/usr/bin/env python3

"""
Merges non-overlapping/partial (e.g. single subject) BIDS datasets with identically processed derivative data
"""

import argparse
import pandas as pd
import shutil
from typing import List
from pathlib import Path


def merge(outputdir: str, inputdirs: List[str]):

    outputdir = Path(outputdir)
    inputdirs = [Path(inputdir) for inputdir in inputdirs]
    table     = pd.DataFrame().rename_axis('participant_id')

    # Copy all root files except the participants tsv-file
    outputdir.mkdir(exist_ok=True)
    for item in inputdirs[0].iterdir():
        if item.is_file() and item.name != 'participants.tsv':
            shutil.copy(item, outputdir)

    # Copy all root derivative files and recursively merge all derivative sub-folders
    if (inputdirs[0]/'derivatives').is_dir():       # NB: It is assumed that all derivative data is identically present in all input directories
        (outputdir/'derivatives').mkdir()
        for derivative in (inputdirs[0]/'derivatives').iterdir():
            if derivative.is_file():
                print(f"WARNING: merging unexpected file: {derivative}")
                shutil.copy(derivative, outputdir/'derivatives')
            else:
                merge(outputdir/'derivatives'/derivative.name, [inputdir/'derivatives'/derivative.name for inputdir in inputdirs])

    # Copy all participant folders
    for inputdir in inputdirs:

        participants_tsv = inputdir/'participants.tsv'
        if participants_tsv.is_file():
            print(f"Merging: {participants_tsv}")
            table      = pd.concat([table, pd.read_csv(participants_tsv, sep='\t', dtype=str, index_col='participant_id')])
            duplicates = table.index[table.index.duplicated()].unique()
            if not duplicates.empty:
                raise Exception(f"ERROR: Got duplicate participant IDs {duplicates.tolist()} when merging: {inputdir}")

        for subdir in inputdir.glob('sub-*'):
            if subdir.is_dir():
                print(f"Merging: {subdir.name} -> {outputdir}")
                shutil.copytree(subdir, outputdir/subdir.name)

    # Save the merged participants table to disk
    if not table.empty:
        table.replace('', 'n/a').to_csv(outputdir/'participants.tsv', sep='\t', encoding='utf-8', na_rep='n/a')


def main():
    """Console script entry point"""

    parser = argparse.ArgumentParser(description=__doc__,
                                     epilog='examples:\n'
                                            '  merge outputdir singlesubject-1  singlesubject-2  singlesubject-3\n ')
    parser.add_argument('outputdir', help='The output directory with the merged data')
    parser.add_argument('inputdirs', help='The list of BIDS (or BIDS-like) input directories with the partial (e.g. single-subject) data', nargs='+')

    # Parse the input arguments
    args = parser.parse_args()

    # Ensure the output directory exists
    Path(args.outputdir).mkdir(parents=True, exist_ok=True)

    # Execute the merge function
    merge(**vars(args))


if __name__ == '__main__':
    main()
