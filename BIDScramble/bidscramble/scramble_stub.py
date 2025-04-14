import shutil
import json
from tqdm import tqdm
from pathlib import Path
from . import get_inputfiles, get_extrafiles, __version__, __description__, __url__


def scramble_stub(inputdir: str, outputdir: str, select: str, bidsvalidate: bool, bidsagnostics: str='yes', dryrun: bool=False, **_):

    # Defaults
    inputdir  = Path(inputdir).resolve()
    outputdir = Path(outputdir).resolve()

    # Create placeholder output files for selected input files
    print(f"Creating BIDS stub data in: {outputdir}")
    inputfiles, inputdirs = get_inputfiles(inputdir, select, '*', bidsvalidate)        # NB: this skips empty directories
    for inputitem in tqdm(inputdirs + inputfiles, unit='file', colour='green', leave=False):
        outputitem = outputdir/inputitem.relative_to(inputdir)
        tqdm.write(f"--> {outputitem}")
        if inputitem.is_dir() and not dryrun:
            outputitem.mkdir(parents=True, exist_ok=True)
        elif not dryrun:
            outputitem.touch()

    # Copy the modality agnostic BIDS(-valid) root files
    if bidsagnostics == 'yes':
        for inputfile in get_extrafiles(inputdir, bidsvalidate):
            outputfile = outputdir/inputfile.relative_to(inputdir)
            print(f"Copying: {inputfile} -> {outputfile}")
            if not dryrun:
                outputfile.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(inputfile, outputfile)

        # Create a dataset description file
        description = {}
        if (description_file := inputdir/'dataset_description.json').is_file():
            with description_file.open('r') as fid:
                description = json.load(fid)
        description['GeneratedBy'] = [{'Name':'BIDScramble', 'Version':__version__, 'Description:':__description__, 'CodeURL':__url__}]
        description['DatasetType'] = 'derivative'
        print(f"Writing: {description_file.name} -> {outputdir}")
        if not dryrun:
            with (outputdir/description_file.name).open('w') as fid:
                json.dump(description, fid, indent=4)
