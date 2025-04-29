#!/usr/bin/env python3

"""This pipeline computes averages from the participants.tsv file

This code is shared under the CC0 license

Copyright (C) 2024-2025, SIESTA workpackage 15 team
"""

import pandas as pd
import argparse
from pathlib import Path
import json

##########################################################################
# Compute the averages of the age, height, and weight of the participants
##########################################################################

def main(options: dict):
    """
    This function computes averages from the participants.tsv file

    :param options: The commandline input arguments parsed to a dictionary

    The ``options`` keys:
    ---------------------
      - inputdir:   Directory containing the BIDS input dataset (str)
      - outputdir:  Directory to save the derived BIDS output dataset (str)
      - level:      Analysis level, either "group" or "participant" (str)
      - verbose:    Enable verbose output (bool)
      - start-idx:  Start index for participant selection (int)
      - stop-idx:   Stop index for participant selection (int)
    """

    if options.get('verbose'):
        print('options =')
        print(options)

    dataset_description_json = Path(options['inputdir']) / 'dataset_description.json'
    with open(dataset_description_json, 'r', encoding='utf-8') as f:
        input_dataset_description = json.load(f)
        if options.get('verbose'):
            print(f"dataset_description = {dataset_description}")

    # Create the output directory and its parents if they don't exist
    Path(options['outputdir']).mkdir(parents=True, exist_ok=True)

    # Write the metadata about the dataset to a JSON file in line with the BIDS standard
    # https://bids-specification.readthedocs.io/en/stable/modality-agnostic-files.html#dataset-description
    dataset_description = {
        "Name": "SIESTA Use Case 2.1",
        "BIDSVersion": "1.10.0",
        "DatasetType": "derivative",
        "License": input_dataset_description['License'],
        "Authors": ["SIESTA workpackage 15 team"],
        "Acknowledgements": ["SIESTA workpackage 15 team"],
        "HowToAcknowledge": ["Please cite the SIESTA paper"],
        "Funding": ["Horizon Europe research and innovation programme grant agreement No. 101131957"],
        "ReferencesAndLinks": ["https://eosc-siesta.eu", "https://github.com/SIESTA-eu/wp15"],
        "SourceDatasets": [
            {
                "DOI": input_dataset_description['DatasetDOI'],
            }    
        ],
        "GeneratedBy": [
            {
                "Name": "Python version of SIESTA use case 2.1",
                "Description": "This code computes averages from the participants.tsv file",
                "Version": "x.y.z", # FIXME, the tagged version number should be inserted here 
                "Container": {
                    "Type": "apptainer",
                    "Tag": "latest", # FIXME, the tagged version number should be inserted here
                    "URI": "oras://ghcr.io/siesta-eu/pipeline-2.1.sif:latest"
                }
            }
        ],
    }

    dataset_description_json = Path(options['outputdir']) / 'dataset_description.json'
    with open(dataset_description_json, 'w', encoding='utf-8') as f:
        json.dump(dataset_description, f, ensure_ascii=False, indent=4)    
    
    # Read the participants.tsv input file into a DataFrame
    inputfile  = Path(options['inputdir']) / 'participants.tsv'
    if not inputfile.is_file():
        print(f"WARNING: input file does not exist: {inputfile}")
        return
    participants = pd.read_csv(inputfile, sep='\t')
    if options.get('verbose'):
        print(f"data contains {len(participants)} participants")

    # Select participants based on start_idx and stop_idx, these are specified using 1-indexing
    if options.get('stop_idx') is not None:
        if options.get('verbose'):
            print('stop_idx = ', options.get('stop_idx'))
        participants = participants.iloc[:(options['stop_idx'])]
    if options.get('start_idx') is not None:
        if options.get('verbose'):
            print('start_idx = ', options.get('start_idx'))
        participants = participants.iloc[(options['start_idx']-1):]
    if options.get('verbose'):
        print(f"selected {len(participants)} participants")

    if options.get('level') == 'participant':
        print("nothing to do at the participant level, only creating participant-level output directories")

        for sub in participants['participant_id']:
            outputdir = Path(options['outputdir'])/f'{sub}'
            Path(outputdir).mkdir(parents=True, exist_ok=True)

    elif options.get('level') == 'group':
        outputfile = Path(options['outputdir']) / 'derivatives' / 'group' / 'results.tsv'

        # Create the group output directory and its parents if they don't exist
        outputdir = Path(options['outputdir']) / 'derivatives' / 'group' 
        outputdir.mkdir(parents=True, exist_ok=True)

        # Compute averages
        averaged_age    = participants['age'].mean(skipna=True)
        averaged_height = participants['Height'].mean(skipna=True)
        averaged_weight = participants['Weight'].mean(skipna=True)

        # Put the results in a DataFrame
        result = pd.DataFrame({
            'averagedAge': [averaged_age],
            'averagedHeight': [averaged_height],
            'averagedWeight': [averaged_weight]
        })
        if options.get('verbose'):
            print(result)

        # Write the results to a TSV file
        result.to_csv(outputfile, sep='\t', index=False, header=False)


##########################################################################
# execute the code if it is run as a script
##########################################################################

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputdir', type=str, help='Directory containing the BIDS input dataset')
    parser.add_argument('outputdir', type=str, help='Directory to save the derived BIDS output dataset')
    parser.add_argument('level', type=str, help='The analysis level', choices=['participant', 'group'])
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--start-idx', type=int, default=None, help='Start index for participant selection')
    parser.add_argument('--stop-idx', type=int, default=None, help='Stop index for participant selection')

    main(vars(parser.parse_args()))
