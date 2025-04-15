import sys
import re
import pandas as pd
from pathlib import Path
from importlib import metadata
from typing import List, Tuple, Set
from bids_validator import BIDSValidator

__version__     = metadata.version('bidscramble')
__description__ = metadata.metadata('bidscramble')['Summary']
__url__         = metadata.metadata('bidscramble')['Project-URL']
validator       = BIDSValidator()


def is_bids(filepath: Path):
    """Returns True if the (relative) filepath has a BIDS-valid naming"""

    filepath = filepath.as_posix()
    if not filepath.startswith('/'):
        filepath = '/' + filepath

    return validator.is_bids(filepath) or filepath == '/.bidsignore'


def get_inputfiles(inputdir: Path, select: str, pattern: str='*', bidsvalidate: bool=False) -> Tuple[List[Path], List[Path]]:
    """
    Recursively get the (modality specific) files from the input directory

    :param inputdir:     The input directory from which files are retrieved using rglob
    :param select:       The fullmatch regular expression pattern to select the files of interest
    :param pattern:      The rglob search pattern (e.g. useful for additional filtering on file extension)
    :param bidsvalidate: Filters out BIDS files if True
    :return:             The input files and directories of interest
    """

    inputitems = [item for item in inputdir.rglob(pattern) if re.fullmatch(select, str(item.relative_to(inputdir)))]
    inputfiles = [fpath  for fpath  in inputitems if fpath.is_file() and (not bidsvalidate or is_bids(fpath.relative_to(inputdir)))]
    inputdirs  = [folder for folder in inputitems if folder.is_dir() and folder.name not in ('.', '..')]

    print(f"Found {len(inputfiles)} input files and {len(inputdirs)} directories using '{select}'")

    return sorted(inputfiles), sorted(inputdirs)       # TODO: create a class and return input objects?


def get_extrafiles(inputdir: Path, bidsvalidate: bool=False) -> Set[Path]:
    """
    Recursively get the modality agnostic from the BIDS root, sourcedata, stimuli, phenotype, code and derivatives directories

    :param inputdir:     The path to the input dataset
    :param bidsvalidate: Filters out BIDS files if True
    :return:             The set of modality agnostic files
    """

    extrafiles = set(extrafile for extrafile in inputdir.iterdir() if extrafile.is_file())
    for extra in ('stimuli', 'phenotype', 'code'):
        if (extradir := inputdir/extra).is_dir():
            extrafiles.update(extrafile for extrafile in extradir.rglob('*') if extrafile.is_file())
    if (derivatives := inputdir/'derivatives').is_dir():
        for derivativedir in [item for item in derivatives.iterdir() if item.is_dir()]:
            extrafiles.update(get_extrafiles(derivativedir))
    if (sourcedata := inputdir/'sourcedata').is_dir():
        extrafiles.update(get_extrafiles(sourcedata))

    if bidsvalidate:
        for invalid in [extrafile for extrafile in extrafiles if not is_bids(extrafile.relative_to(inputdir))]:
            extrafiles.remove(invalid)

    return extrafiles


def prune_participants_tsv(rootdir: Path):
    """
    Recursively remove rows from the participants tsv file if their subject directories do not exist

    :param rootdir: The BIDS (or BIDS-like) input directory with the participants.tsv file and, optionally, derivatives and sourcedata directories
    :return:
    """

    for participants_tsv in [rootdir/'participants.tsv'] + (list((rootdir/'phenotype').glob('*.tsv')) if (rootdir/'phenotype').is_dir() else []):
        if participants_tsv.is_file():

            print(f"--> {participants_tsv}")
            table = pd.read_csv(participants_tsv, sep='\t', dtype=str, index_col='participant_id')
            for subid in table.index:
                if not isinstance(subid, str):  # Can happen with anonymized data
                    return
                if not (rootdir/subid).is_dir():
                    print(f"Pruning {subid} record from {participants_tsv}")
                    table.drop(subid, inplace=True)

            table.to_csv(participants_tsv, sep='\t', encoding='utf-8', na_rep='n/a')

    if (derivatives := rootdir/'derivatives').is_dir():
        for derivativedir in [item for item in derivatives.iterdir() if item.is_dir()]:
            prune_participants_tsv(derivativedir)
    if (sourcedata := rootdir/'sourcedata').is_dir():
        prune_participants_tsv(sourcedata)


def console_scripts(show: bool=False) -> list:
    """
    :param show:    Print the installed console scripts if True
    :return:        List of BIDScramble console scripts
    """

    if show: print('Executable tools:')

    scripts = []
    if sys.version_info.major == 3 and sys.version_info.minor < 10:
        console_scripts = metadata.entry_points()['console_scripts']                 # Raises DeprecationWarning for python >= 3.10: SelectableGroups dict interface is deprecated
    else:
        console_scripts = metadata.entry_points().select(group='console_scripts')    # The select method was introduced in python = 3.10
    for script in console_scripts:
        if script.value.startswith('bidscramble'):
            scripts.append(script.name)
            if show: print(f"- {script.name}")

    return scripts


def drmaa_nativespec(specs: str, session) -> str:
    """
    Converts (CLI default) native Torque walltime and memory specifications to the DRMAA implementation (currently only Slurm is supported)

    :param specs:   Native Torque walltime and memory specifications, e.g. '-l walltime=00:10:00,mem=2gb' from argparse CLI
    :param session: The DRMAA session
    :return:        The converted native specifications
    """

    jobmanager: str = session.drmaaImplementation

    if '-l ' in specs and 'pbs' not in jobmanager.lower():

        if 'slurm' in jobmanager.lower():
            specs = (specs.replace('-l ', '')
                          .replace(',', ' ')
                          .replace('walltime', '--time')
                          .replace('mem', '--mem')
                          .replace('gb','000'))
        else:
            print(f"WARNING: Default `--cluster` native specifications are not (yet) provided for {jobmanager}. Please add them to your command if you get DRMAA errors")
            specs = ''

    return specs.strip()
