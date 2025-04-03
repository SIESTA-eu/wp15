#!/usr/bin/env python3

"""
Merges non-overlapping/partial (e.g. single subject) BIDS datasets with identically processed derivative data
"""

import argparse
import pandas as pd
import shutil
from typing import List
from pathlib import Path


def merge(inputdirs: List[str], outputdir: str):

    outputdir = Path(outputdir)
    inputdirs = [Path(inputdir) for inputdir in inputdirs]
    outputdir.mkdir(exist_ok=True)

    if (outputdir/'participants.tsv').is_file():
        table = pd.read_csv(outputdir/'participants.tsv', sep='\t', dtype=str, index_col='participant_id')
    else:
        table = pd.DataFrame().rename_axis('participant_id')

    for inputdir in inputdirs:
        for item in inputdir.iterdir():

            if item.name == 'derivatives':
                (outputdir/'derivatives').mkdir(exist_ok=True)
                for derivative in (inputdir/'derivatives').iterdir():
                    if derivative.is_file():
                        print(f"WARNING: merging unexpected file: {derivative}")
                        shutil.copy(derivative, outputdir/'derivatives')
                    else:
                        merge([derivative], outputdir/'derivatives'/derivative.name)

            elif item.name == 'participants.tsv':
                print(f"Merging: {item}")
                table = pd.concat([table, pd.read_csv(item, sep='\t', dtype=str, index_col='participant_id')])
                duplicates = table.index[table.index.duplicated()].unique()
                if not duplicates.empty:
                    raise Exception(f"ERROR: Got duplicate participant IDs {duplicates.tolist()} when merging: {inputdir}")

            elif item.is_dir():
                print(f"Merging: {item.name} -> {outputdir}")
                shutil.copytree(item, outputdir/item.name, dirs_exist_ok=True)

            elif not (outputdir/item.name).exists():
                print(f"Merging: {item.name} -> {outputdir/item.name}")
                shutil.copyfile(item, outputdir/item.name)

    # Save the merged participants table to disk
    if not table.empty:
        print(f"Saving merged table: {outputdir}/participants.tsv")
        table.replace('', 'n/a').to_csv(outputdir/'participants.tsv', sep='\t', encoding='utf-8', na_rep='n/a')


def main():
    """Console script entry point"""

    parser = argparse.ArgumentParser(description=__doc__,
                                     epilog='examples:\n'
                                            '  merge singlesubject-1  singlesubject-2  singlesubject-3 outputdir\n ')
    parser.add_argument('inputdirs', help='The list of BIDS (or BIDS-like) input directories with the partial (e.g. single-subject) data', nargs='+')
    parser.add_argument('outputdir', help='The output directory with the merged data')

    # Parse the input arguments
    args = parser.parse_args()

    # Ensure the output directory exists
    Path(args.outputdir).mkdir(parents=True, exist_ok=True)

    # Execute the merge function
    merge(**vars(args))


if __name__ == '__main__':
    main()
