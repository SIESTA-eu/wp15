#!/usr/bin/env python3

import argparse
import textwrap
from pathlib import Path
from .scramble_stub import scramble_stub
from .scramble_tsv import scramble_tsv
from .scramble_json import scramble_json
from .scramble_nii import scramble_nii
from .scramble_fif import scramble_fif
from .scramble_brainvision import scramble_brainvision
from .scramble_swap import scramble_swap
from .scramble_pseudo import scramble_pseudo

# Use parent parsers to inherit optional arguments (https://macgregor.gitbooks.io/developer-notes/content/python/argparse-basics.html#inheriting-arguments)
parent = argparse.ArgumentParser(add_help=False)
parent.add_argument('-d','--dryrun', help='Do not save anything, only print the output filenames in the terminal', action='store_true')
parent.add_argument('-b','--bidsvalidate', help='If given, all input files are checked for BIDS compliance when first indexed, and excluded when non-compliant (as in pybids.BIDSLayout)', action='store_true')
parent.add_argument('-s','--select', metavar='PATTERN', help='A fullmatch regular expression pattern that is matched against the relative path of the input data. Files that match are scrambled and saved in outputdir', default=r'(?!\.).*')
parent_nii = argparse.ArgumentParser(add_help=False, parents=[parent])
parent_nii.add_argument('-c','--cluster', help='Use the DRMAA library to submit the scramble jobs to a high-performance compute (HPC) cluster. You can add an opaque DRMAA argument with native specifications for your HPC resource manager (NB: Use quotes and include at least one space character to prevent premature parsing -- see examples)',
                        metavar='SPECS', nargs='?', const='-l mem=4gb,walltime=0:15:00', type=str)


class DefaultsFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter): pass


def addparser_stub(parsers, _help: str):

    description = textwrap.dedent("""
    Creates a copy of the input directory tree in which all files are empty stubs. Optionally, modality-agnostic BIDS
    files from the input directory are copied over (with content), such as the README, dataset_descrption and
    participants rootfiles, as well as files in phenotype, code, and similar files in sourcedata and derivatives. In
    this way you can create a richer BIDS output folder without the modality specific content.""")

    epilog = ('examples:\n'
              '  scramble inputdir outputdir stub\n'
             r"  scramble inputdir outputdir stub -s '.*\.(nii|json|tsv)'"'\n'
             r"  scramble inputdir outputdir stub -s '(?!derivatives(/|$)).*'"'\n'
             r"  scramble inputdir outputdir stub -s '(?!sub.*scans.tsv|/func/).*'"'\n ')

    parser = parsers.add_parser('stub', parents=[parent], formatter_class=DefaultsFormatter, description=description, epilog=epilog, help=_help)
    parser.add_argument('-a','--agnostics', help='If yes, in addition to the included files (see `--select` for usage), add modality-agnostic BIDS files', choices=['yes','no'], default='yes')
    parser.set_defaults(func=scramble_stub)


def addparser_tsv(parsers, _help: str):

    description = textwrap.dedent("""
    Adds scrambled versions of the tsv files in the input directory to the output directory. If no scrambling
    method is specified, the default behavior is to null all values.""")

    epilog = ('examples:\n'
              '  scramble inputdir outputdir tsv\n'
              '  scramble inputdir outputdir tsv permute\n'
              "  scramble inputdir outputdir tsv permute -s '.*_events.tsv' -p '.*'\n"
              '  scramble inputdir outputdir tsv permute -s participants.tsv -p (participant_id|SAS.*)\n ')

    parser = parsers.add_parser('tsv', parents=[parent], formatter_class=DefaultsFormatter, description=description, epilog=epilog, help=_help)
    parser.set_defaults(func=scramble_tsv)

    subparsers = parser.add_subparsers(dest='method', help='Scrambling method (default: null). Add -h, --help for more information')
    subparser  = subparsers.add_parser('null', parents=[parent], description=description, help='Replaces all values with "n/a"')
    subparser  = subparsers.add_parser('permute', parents=[parent], description=description, help='Randomly permute the column values of the tsv files')
    subparser.add_argument('-p','--preserve', metavar='PATTERN', help='A regular expression pattern that is matched against tsv column names. The exact relationship (row order) between the matching columns is then preserved, i.e. they are permuted in conjunction instead of independently')


def addparser_json(parsers, _help: str):

    description = textwrap.dedent("""
    Adds scrambled key-value versions of the json files in the input directory to the output
    directory. If no preserve expression is specified, the default behavior is to null all
    values.""")

    epilog = ('examples:\n'
              '  scramble inputdir outputdir json\n'
              "  scramble inputdir outputdir json participants.json -p '.*'\n"
              "  scramble inputdir outputdir json 'sub-.*.json' -p '(?!AcquisitionTime|Date).*'\n ")

    parser = parsers.add_parser('json', parents=[parent], formatter_class=DefaultsFormatter, description=description, epilog=epilog, help=_help)
    parser.add_argument('-p','--preserve', metavar='PATTERN', help='A fullmatch regular expression pattern that is matched against all keys in the json files. The json values are copied over when a key matches positively')
    parser.set_defaults(func=scramble_json)


def addparser_nii(parsers, _help: str):

    description = textwrap.dedent("""
    Adds scrambled versions of the NIfTI files in the input directory to the output directory.
    If no scrambling method is specified, the default behavior is to null all image values.""")

    epilog = ('examples:\n'
              '  scramble inputdir outputdir nii\n'
              '  scramble inputdir outputdir nii scatter -h\n'
              "  scramble inputdir outputdir nii scatter 2 -s 'sub-.*_MP2RAGE.nii.gz' -c '--mem=5000 --time=0:20:00'\n"
              "  scramble inputdir outputdir nii wobble -a 2 -f 1 8 -s 'sub-.*_T1w.nii'\n ")

    parser = parsers.add_parser('nii', parents=[parent_nii], formatter_class=DefaultsFormatter, description=description, epilog=epilog, help=_help)
    parser.set_defaults(func=scramble_nii)

    subparsers = parser.add_subparsers(dest='method', help='Scrambling method (default: null). Add -h, --help for more information')
    subparser  = subparsers.add_parser('null', parents=[parent_nii], description=description, help='Replaces all values with zeros')
    subparser  = subparsers.add_parser('blur', parents=[parent_nii], description=description, help='Apply a 3D Gaussian smoothing filter')
    subparser.add_argument('fwhm', help='The FWHM (in mm) of the isotropic 3D Gaussian smoothing kernel', type=float)
    subparser  = subparsers.add_parser('permute', parents=[parent_nii], formatter_class=DefaultsFormatter, description=description, help='Perform random permutations along one or more image dimensions')
    subparser.add_argument('dims', help='The dimensions along which the images will be permuted', nargs='+', choices=['x','y','z','t','u','v','w'])
    subparser.add_argument('-i','--independent', help='Make all permutations along a dimension independent (instead of permuting slices as a whole)', action='store_true')
    subparser  = subparsers.add_parser('scatter', parents=[parent_nii], formatter_class=DefaultsFormatter, description=description, help='Perform random permutations using a sliding 3D permutation kernel')
    subparser.add_argument('radius', help='The radius (in mm) of the 3D/cubic permutation kernel', type=float, nargs='?', default=3)
    subparser  = subparsers.add_parser('wobble', parents=[parent_nii], formatter_class=DefaultsFormatter, description=description, help='Deform the images using 3D random waveforms')
    subparser.add_argument('-a','--amplitude', metavar='GAIN', help='The amplitude of the random waveform', type=float, default=2)
    subparser.add_argument('-f','--freqrange', metavar='FREQ', help='The lowest and highest spatial frequency (in mm) of the random waveform', nargs=2, type=float, default=[1, 5])


def addparser_fif(parsers, _help: str):

    description = textwrap.dedent("""
    Adds scrambled versions of the FIF files in the input directory to the output directory. If
    no scrambling method is specified, the default behavior is to null the data.""")

    epilog = ('examples:\n'
              '  scramble inputdir outputdir fif\n'
              '  scramble inputdir outputdir fif permute time\n')

    parser = parsers.add_parser('fif', parents=[parent], formatter_class=DefaultsFormatter, description=description, epilog=epilog, help=_help)
    parser.set_defaults(func=scramble_fif)

    subparsers = parser.add_subparsers(dest='method', help='Scrambling method (default: null). Add -h, --help for more information')
    subparser  = subparsers.add_parser('null', parents=[parent], description=description, help='Replaces all values with zeros')
    subparser  = subparsers.add_parser('permute', parents=[parent], formatter_class=DefaultsFormatter, description=description, help='Perform random permutations along one or more MEG data dimensions')
    subparser.add_argument('dims', help='The dimensions along which the data will be permuted', nargs='+', choices=['channel', 'time'])


def addparser_brainvision(parsers, _help: str):

    description = textwrap.dedent("""
    Adds scrambled versions of the BrainVision EEG files in the input directory to the output
    directory. If no scrambling method is specified, the default behavior is to null the data.""")

    epilog = ('examples:\n'
              '  scramble inputdir outputdir brainvision\n'
              '  scramble inputdir outputdir brainvision permute\n')

    parser = parsers.add_parser('brainvision', parents=[parent], formatter_class=DefaultsFormatter, description=description, epilog=epilog, help=_help)
    parser.set_defaults(func=scramble_brainvision)

    subparsers = parser.add_subparsers(dest='method', help='Scrambling method (default: null). Add -h, --help for more information')
    subparser  = subparsers.add_parser('null', parents=[parent], description=description, help='Replaces all values with zeros')
    subparser  = subparsers.add_parser('permute', parents=[parent], description=description, help='Randomly permute the EEG samples in each channel')


def addparser_swap(parsers, _help: str):

    description = textwrap.dedent("""
    Randomly swaps the content of data files between a group of similar files in the input
    directory and save them as output.""")

    epilog = ('examples:\n'
              '  scramble inputdir outputdir swap\n'
             r"  scramble inputdir outputdir swap -s '.*\.(nii|json|tsv)'"'\n'
             r"  scramble inputdir outputdir swap -s '(?!derivatives(/|$)).*' -b"'\n'
             r"  scramble inputdir outputdir swap -g subject session run"'\n ')

    parser = parsers.add_parser('swap', parents=[parent], formatter_class=DefaultsFormatter, description=description, epilog=epilog, help=_help)
    parser.add_argument('-g','--grouping', metavar='ENTITY', help='A list of (full-name) BIDS entities that make up a group between which file contents are swapped. See: https://bids-specification.readthedocs.io/en/stable/appendices/entities.html', nargs='+', default=['subject'], type=str)
    parser.set_defaults(func=scramble_swap)


def addparser_pseudo(parsers, _help: str):

    description = textwrap.dedent("""
    Adds pseudonymized versions of the input directory to the output directory, such that the subject label is
    replaced by a pseudonym anywhere in the filepath as well as inside all text files (such as json and tsv-files).""")

    epilog = ('examples:\n'
              '  scramble inputdir outputdir pseudo\n'
             r"  scramble inputdir outputdir_remove1 pseudo random  -s '(?!sub-003(/|$)).*'"'\n'
             r"  scramble inputdir outputdir_keep1 pseudo original -s 'sub-003(/|$).*'"'\n ')

    parser = parsers.add_parser('pseudo', parents=[parent], formatter_class=DefaultsFormatter, description=description, epilog=epilog, help=_help)
    parser.add_argument('method', help='The method to generate the pseudonyms', choices=['random','permute','original'], default='permute')
    parser.add_argument('-p','--participant', metavar='PATTERN', help='The findall() regular expression pattern that is used to extract the subject label from the relative filepath. NB: Do not change this if the input data is in BIDS format', default='^sub-(.*?)(?:/|$).*')
    parser.add_argument('-a','--agnostics', help='If yes, in addition to the included files (see `--select` for usage), pseudomymize all modality agnostic files in the input directory (such as participants.tsv, code, etc.)', choices=['yes','no'], default='yes')
    parser.set_defaults(func=scramble_pseudo)


def main():
    """Console script entry point"""

    description = textwrap.dedent("""
    The general workflow to build up a scrambled dataset is by consecutively running `scramble`
    for actions of your choice. For instance, you could first run `scramble` with the `stub`
    action to create a dummy dataset with only the file structure and some basic files, and
    then run `scramble` with the `nii` action  to specifically add scrambled NIfTI data (see
    examples below). To combine different scrambling actions, simply re-run `scramble` using
    the already scrambled data as input directory.""")

    # Add the baseparser
    parser = argparse.ArgumentParser(formatter_class=DefaultsFormatter, description=description,
                                     epilog='examples:\n'
                                            '  scramble inputdir outputdir stub -h\n'
                                            '  scramble inputdir outputdir nii -h\n ')
    parser.add_argument('inputdir',  help='The BIDS (or BIDS-like) input directory with the original data')
    parser.add_argument('outputdir', help='The output directory with the scrambled pseudo data')

    # Add the subparsers
    subparsers = parser.add_subparsers(title='Action', help='Add -h, --help for more information', required=True)
    addparser_stub(subparsers, _help='Saves a dummy inputdir skeleton in outputdir')
    addparser_tsv(subparsers, _help='Saves scrambled tsv files in outputdir')
    addparser_json(subparsers, _help='Saves scrambled json files in outputdir')
    addparser_nii(subparsers, _help='Saves scrambled NIfTI files in outputdir')
    addparser_fif(subparsers, _help='Saves scrambled FIF files in outputdir')
    addparser_brainvision(subparsers, _help='Saves scrambled BrainVision files in outputdir')
    addparser_swap(subparsers, _help='Saves swapped file contents in outputdir')
    addparser_pseudo(subparsers, _help='Saves pseudonymized file names and contents in outputdir')

    # Parse the input arguments
    args = parser.parse_args()

    # Ensure the output directory exists
    Path(args.outputdir).mkdir(parents=True, exist_ok=True)

    # Execute the scramble function
    args.func(**vars(args))


if __name__ == '__main__':
    main()
