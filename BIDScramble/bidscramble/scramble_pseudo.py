import shutil
import re
import random
import tempfile
from tqdm import tqdm
from pathlib import Path
from . import get_inputfiles, get_extrafiles, prune_participants_tsv


def scramble_pseudo(inputdir: str, outputdir: str, select: str, bidsvalidate: bool, method: str, participant: str, agnostics: str, dryrun: bool=False, **_):
    """
    Adds pseudonymized versions of the input directory to the output directory, such that the subject label is replaced by a pseudonym
    anywhere in the filepath as well as inside all text files (such as json and tsv-files).

    :param inputdir:     The path to the input dataset
    :param outputdir:    The path to the output dataset
    :param select:       The fullmatch regular expression pattern to select the files of interest
    :param bidsvalidate: If True, BIDS files are skipped if they do not validate
    :param method:       The method to generate the pseudonyms
    :param participant:  The findall() regular expression pattern that is used to extract the subject label from the relative filepath
    :param agnostics:    If 'yes', include all modality agnostic files in the root of the input directory (such as participants.tsv, code, etc.)
    :param dryrun:       If True, do not modify anything

    Examples
    --------
    scramble data/bids data/synthetic pseudo
    scramble data/bids data/synthetic_remove1 pseudo random  -s '(?!sub-003(/|$)).*'
    scramble data/bids data/synthetic_keep1 pseudo original -s 'sub-003(/|$).*'
    """

    # Resolve the input and output paths
    inputdir   = Path(inputdir).resolve()
    outputdir  = Path(outputdir).resolve()
    outputdir_ = outputdir/'tmpdir_swap' if method != 'original' else outputdir

    # Create pseudonyms for all selected subject identifiers
    inputfiles, inputdirs = get_inputfiles(inputdir, select, '*', bidsvalidate)
    subjectids            = sorted(set(subid for item in inputfiles + inputdirs for subid in re.findall(participant, str(item.relative_to(inputdir))) if subid))
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
        for inputitem in tqdm(inputdirs + inputfiles, unit='file', colour='green', leave=False):
            outputitem = outputdir_/inputitem.relative_to(inputdir)
            if not dryrun:
                if inputitem.is_dir():
                    outputitem.mkdir(parents=True, exist_ok=True)
                else:
                    outputitem.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(inputitem, outputitem)

    # Adjust the participants.tsv file for the selected subjects
    if not dryrun:
        prune_participants_tsv(outputdir_)

    # Pseudonymize the filenames and content of all selected subjects
    if method != 'original':
        print(f"Pseudonymizing the data of {len(subjectids)} subjects in: {outputdir}")
        extrafiles = sorted(get_extrafiles(inputdir, bidsvalidate)) if agnostics == 'yes' else []
        for inputitem in tqdm(inputdirs + inputfiles + extrafiles, unit='file', colour='green', leave=False):

            # Read the non-binary file content
            outputitem = outputdir_/inputitem.relative_to(inputdir)
            pseudoitem = outputdir/inputitem.relative_to(inputdir)
            try:
                newtext = outputitem.read_text() if outputitem.is_file() else ''
            except Exception:
                newtext = ''

            # Replace each subjectid with its pseudonym
            inputid = re.findall(participant, str(inputitem.relative_to(inputdir)))
            for subjectid, pseudonym in zip(subjectids, pseudonyms):

                # Pseudonymize the filepath
                if (subjectid in inputid) and outputitem.exists():          # NB: This does not support the inheritance principle (sub-* files in root)
                    pseudoitem = outputdir/re.sub(f"sub-{re.escape(subjectid)}(?=[._/]|$)", f"sub-{pseudonym}", inputitem.relative_to(inputdir).as_posix())
                    print(f"\t{'Renaming' if outputitem.is_file() else 'Making'} sub-{subjectid} -> {pseudoitem}")
                    if not dryrun:
                        if outputitem.is_file():
                            pseudoitem.parent.mkdir(parents=True, exist_ok=True)
                            outputitem.rename(pseudoitem)
                        else:
                            pseudoitem.mkdir(parents=True, exist_ok=True)

                # Pseudonymize the file content (for **all** subject ids)
                newtext = re.sub(f"sub-{re.escape(subjectid)}(?=[._/\t\n]|$)", f"sub-^#^{pseudonym}", newtext)    # Add temporary `^#^` characters to avoid recursive replacements

            # Write the non-binary pseudonymized file content
            if newtext:
                print(f"\tRewriting -> {pseudoitem}")
                if not dryrun:
                    pseudoitem.write_text(newtext.replace('sub-^#^','sub-'))            # Remove the temporary characters

        shutil.rmtree(outputdir_)
