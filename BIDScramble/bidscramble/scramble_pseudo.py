import shutil
import re
import random
import tempfile
from tqdm import tqdm
from pathlib import Path
from . import get_inputfiles, prune_participants_tsv

def scramble_pseudo(bidsfolder: str, outputfolder: str, select: str, bidsvalidate: bool, method: str, pattern: str, rootfiles: str, dryrun: bool=False, **_):

    # Defaults
    inputdir   = Path(bidsfolder).resolve()
    outputdir  = Path(outputfolder).resolve()
    outputdir_ = outputdir/'tmpdir_swap' if method != 'original' else outputdir

    # Create pseudonyms for all selected subject identifiers
    rootfiles  = [rootfile for rootfile in inputdir.iterdir() if rootfiles=='yes' and rootfile.is_file() and not (outputdir/rootfile.name).is_file()]
    inputfiles = get_inputfiles(inputdir, select, '*', bidsvalidate)
    inputfiles += [rootfile for rootfile in rootfiles if rootfile not in inputfiles]
    subjectids = sorted(set(subid for inputfile in inputfiles for subid in re.findall(pattern, str(inputfile.relative_to(inputdir)))))
    if method == 'random':
        pseudonyms = [next(tempfile._get_candidate_names()).replace('_','x') for _ in subjectids]
    elif method == 'permute':
        pseudonyms = random.sample(subjectids, len(subjectids))
    elif method == 'original':
        pseudonyms = subjectids
    else:
        raise ValueError(f"Invalid pseudonymization method '{method}'")

    # Copy the input data
    if inputdir != outputdir:
        print(f"Copying the data of {len(subjectids)} subjects to: {outputdir}")
        for inputfile in tqdm(inputfiles, unit='file', colour='green', leave=False):
            outputfile = outputdir_/inputfile.relative_to(inputdir)
            if not dryrun:
                outputfile.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(inputfile, outputfile)

    # Adjust the participants.tsv file for the selected subjects
    if not dryrun:
        prune_participants_tsv(outputdir_)

    # Pseudonymize the filenames and content of all selected subjects
    if method != 'original':
        print(f"Pseudonymizing the data of {len(subjectids)} subjects in: {outputdir}")
        for inputfile in tqdm(inputfiles, unit='file', colour='green', leave=False):

            # Read the non-binary file content
            outputfile = outputdir_/inputfile.relative_to(inputdir)
            pseudofile = outputdir/inputfile.relative_to(inputdir)
            try:
                newtext = outputfile.read_text()
            except UnicodeDecodeError:
                newtext = ''

            # Replace each subjectid with its pseudonym
            for subjectid, pseudonym in zip(subjectids, pseudonyms):

                # Pseudonymize the filepath
                if (subjectid in re.findall(pattern, str(inputfile.relative_to(inputdir))) or inputfile.parent==inputdir) and outputfile.is_file():  # NB: This does not support the inheritance principle (sub-* files in root)
                    pseudofile = outputdir/str(inputfile.relative_to(inputdir)).replace(f"sub-{subjectid}", f"sub-{pseudonym}")
                    print(f"\tRenaming sub-{subjectid} -> {pseudofile}")
                    if not dryrun:
                        pseudofile.parent.mkdir(parents=True, exist_ok=True)
                        outputfile.rename(pseudofile)

                # Pseudonymize the file content
                newtext = newtext.replace(f"sub-{subjectid}", f"sub-^#^{pseudonym}")    # Add temporary `^#^` characters to avoid recursive replacements

            # Write the non-binary pseudonymized file content
            if newtext:
                print(f"\tRewriting -> {pseudofile}")
                if not dryrun:
                    pseudofile.write_text(newtext.replace('sub-^#^','sub-'))            # Remove the temporary characters

        shutil.rmtree(outputdir_)