import json
import re
from tqdm import tqdm
from pathlib import Path
from . import get_inputfiles


def clearvalues(data: dict, preserve: str):

    for key, value in data.items():
        if isinstance(value, dict):
            clearvalues(value, preserve)        # Recursively clear the dictionary
        elif re.fullmatch(preserve, str(key or 'unspecified')):
            pass                                # Preserve the value
        else:
            data[key] = type(value)()           # Clear the value


def scramble_json(inputdir: str, outputdir: str, select: str, bidsvalidate: bool, preserve: str='^$', dryrun: bool=False, **_):

    # Defaults
    inputdir  = Path(inputdir).resolve()
    outputdir = Path(outputdir).resolve()

    # Create pseudo-random out data for all selected json files
    inputfiles, _ = get_inputfiles(inputdir, select, '*.json', bidsvalidate)
    for inputfile in tqdm(inputfiles, unit='file', colour='green', leave=False):

        # Load the json data
        with open(inputfile, 'r') as f:
            jsondata = json.load(f)

        # Clear values that are not of interest
        clearvalues(jsondata, preserve or '^$')

        # Save the output data
        outputfile = outputdir/inputfile.relative_to(inputdir)
        tqdm.write(f"Saving: {outputfile}")
        if not dryrun:
            outputfile.parent.mkdir(parents=True, exist_ok=True)
            with outputfile.open('w') as fid:
                json.dump(jsondata, fid, indent=4)
