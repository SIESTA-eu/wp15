# BIDScramble

The BIDScramble tool generates scrambled or pseudo-random BIDS datasets from existing BIDS datasets, while preserving statistical distributions of user-specified variables and preserving user-specified effects of interest. The output data of this tool is not (or at least minimally) traceable and does not contain personal data.

Having access to pseudo-random datasets allows researchers to interact with the data in detail and develop code to implement and test their pipelines. The pipelines should run on the scrambled data just as it runs on the real input data.

## Software installation

The BIDScramble software runs on multiple platforms (e.g. Linux, MacOS, Windows) that have a Python 3.8+ installation.

It is recommended (but not required) to first create a virtual environment.

```console
python -m venv venv
source venv/bin/activate
```

You can then install the BIDScramble tools using git and pip.

```console
git clone https://github.com/SIESTA-eu/wp15.git     # Or download the code yourself
pip install wp15/BIDScramble                        # Or use an alternative installer
pip install wp15/BIDScramble[fif]                   # Use this if you have fif data
```

## Usage

To scramble BIDS data you can run the command-line tool named ``scramble``. At its base, this tool has an input and output argument, followed by a ``Action`` subcommand. The meaning and usage of these arguments is explained in more detail in the following sections.

### scramble

```console
usage: scramble [-h] inputdir outputdir {stub,tsv,json,nii,fif,brainvision,swap,pseudo} ...

The general workflow to build up a scrambled dataset is by consecutively running `scramble` for actions of your
choice. For instance, you could first run `scramble` with the `stub` action to create a dummy dataset with only
the file structure and some basic files, and then run `scramble` with the `nii` action  to specifically add
scrambled NIfTI data (see examples below). To combine different scrambling actions, simply re-run `scramble` using
the already scrambled data as input directory.

positional arguments:
  inputdir              The BIDS (or BIDS-like) input directory with the original data
  outputdir             The output directory with the scrambled pseudo data

options:
  -h, --help            Show this help message and exit

Action:
  {stub,tsv,json,nii,fif,brainvision,swap,pseudo}
                        Add -h, --help for more information
    stub                Saves a dummy inputdir skeleton in outputdir
    tsv                 Saves scrambled tsv files in outputdir
    json                Saves scrambled json files in outputdir
    nii                 Saves scrambled NIfTI files in outputdir
    fif                 Saves scrambled FIF files in outputdir
    brainvision         Saves scrambled BrainVision files in outputdir
    swap                Saves swapped file contents in outputdir
    pseudo              Saves pseudonymized file names and contents in outputdir

examples:
  scramble inputdir outputdir stub -h
  scramble inputdir outputdir nii -h
```

#### Action: stub

```console
usage: scramble inputdir outputdir stub [-h] [-d] [-b] [-s PATTERN]

Creates a copy of the input directory in which all files are empty stubs. Exceptions to this are the
'dataset_description.json', 'README', 'CHANGES', 'LICENSE' and 'CITATION.cff' files, which are copied over and
updated if possible.

options:
  -h, --help            Show this help message and exit
  -d, --dryrun          Do not save anything, only print the output filenames in the terminal (default: False)
  -b, --bidsvalidate    If given, all input files are checked for BIDS compliance when first indexed, and
                        excluded when non-compliant (as in pybids.BIDSLayout) (default: False)
  -s PATTERN, --select PATTERN
                        A fullmatch regular expression pattern that is matched against the relative path of the
                        input data. Files that match are scrambled and saved in outputdir (default: (?!\.).*)

examples:
  scramble inputdir outputdir stub
  scramble inputdir outputdir stub -s '.*\.(nii|json|tsv)'
  scramble inputdir outputdir stub -s '(?!derivatives(/|$)).*'
  scramble inputdir outputdir stub -s '(?!sub.*scans.tsv|/func/).*'
```

#### Action: tsv

```console
usage: scramble inputdir outputdir tsv [-h] [-d] [-b] [-s PATTERN] {null,permute} ...

Adds scrambled versions of the tsv files in the input directory to the output directory. If no scrambling
method is specified, the default behavior is to null all values.

positional arguments:
  {null,permute}        Scrambling method (default: null). Add -h, --help for more information
    null                Replaces all values with "n/a"
    permute             Randomly permute the column values of the tsv files

options:
  -h, --help            Show this help message and exit
  -d, --dryrun          Do not save anything, only print the output filenames in the terminal (default: False)
  -b, --bidsvalidate    If given, all input files are checked for BIDS compliance when first indexed, and
                        excluded when non-compliant (as in pybids.BIDSLayout) (default: False)
  -s PATTERN, --select PATTERN
                        A fullmatch regular expression pattern that is matched against the relative path of the
                        input data. Files that match are scrambled and saved in outputdir (default: (?!\.).*)

examples:
  scramble inputdir outputdir tsv
  scramble inputdir outputdir tsv permute
  scramble inputdir outputdir tsv permute -s '.*_events.tsv' -p '.*'
  scramble inputdir outputdir tsv permute -s participants.tsv -p (participant_id|SAS.*)
```

#### Action: json

```console
usage: scramble inputdir outputdir json [-h] [-d] [-b] [-s PATTERN] [-p PATTERN]

Adds scrambled key-value versions of the json files in the input directory to the output directory. If no
preserve expression is specified, the default behavior is to null all values.

options:
  -h, --help            Show this help message and exit
  -d, --dryrun          Do not save anything, only print the output filenames in the terminal (default: False)
  -b, --bidsvalidate    If given, all input files are checked for BIDS compliance when first indexed, and
                        excluded when non-compliant (as in pybids.BIDSLayout) (default: False)
  -s PATTERN, --select PATTERN
                        A fullmatch regular expression pattern that is matched against the relative path of the
                        input data. Files that match are scrambled and saved in outputdir (default: (?!\.).*)
  -p PATTERN, --preserve PATTERN
                        A fullmatch regular expression pattern that is matched against all keys in the json
                        files. The json values are copied over when a key matches positively (default: None)

examples:
  scramble inputdir outputdir json
  scramble inputdir outputdir json participants.json -p '.*'
  scramble inputdir outputdir json 'sub-.*.json' -p '(?!AcquisitionTime|Date).*'
```

#### Action: nii

```console
usage: scramble inputdir outputdir nii [-h] [-d] [-b] [-s PATTERN] [-c [SPECS]]
                                       {null,blur,permute,scatter,wobble} ...

Adds scrambled versions of the NIfTI files in the input directory to the output directory. If no
scrambling method is specified, the default behavior is to null all image values.

positional arguments:
  {null,blur,permute,scatter,wobble}
                        Scrambling method (default: null). Add -h, --help for more information
    null                Replaces all values with zeros
    blur                Apply a 3D Gaussian smoothing filter
    permute             Perform random permutations along one or more image dimensions
    scatter             Perform random permutations using a sliding 3D permutation kernel
    wobble              Deform the images using 3D random waveforms

options:
  -h, --help            Show this help message and exit
  -d, --dryrun          Do not save anything, only print the output filenames in the terminal (default: False)
  -b, --bidsvalidate    If given, all input files are checked for BIDS compliance when first indexed, and
                        excluded when non-compliant (as in pybids.BIDSLayout) (default: False)
  -s PATTERN, --select PATTERN
                        A fullmatch regular expression pattern that is matched against the relative path of the
                        input data. Files that match are scrambled and saved in outputdir (default: (?!\.).*)
  -c [SPECS], --cluster [SPECS]
                        Use the DRMAA library to submit the scramble jobs to a high-performance compute (HPC)
                        cluster. You can add an opaque DRMAA argument with native specifications for your HPC
                        resource manager (NB: Use quotes and include at least one space character to prevent
                        premature parsing -- see examples) (default: None)

examples:
  scramble inputdir outputdir nii
  scramble inputdir outputdir nii scatter -h
  scramble inputdir outputdir nii scatter 2 -s 'sub-.*_MP2RAGE.nii.gz' -c '--mem=5000 --time=0:20:00'
  scramble inputdir outputdir nii wobble -a 2 -f 1 8 -s 'sub-.*_T1w.nii'
```

#### Action: fif

```console
usage: scramble inputdir outputdir fif [-h] [-d] [-b] [-s PATTERN] {null,permute} ...

Adds scrambled versions of the FIF files in the input directory to the output directory. If no scrambling method
is specified, the default behavior is to null the data.

positional arguments:
  {null,permute}        Scrambling method (default: null). Add -h, --help for more information
    null                Replaces all values with zeros
    permute             Randomly permute the MEG samples in each channel

options:
  -h, --help            Show this help message and exit
  -d, --dryrun          Do not save anything, only print the output filenames in the terminal (default: False)
  -b, --bidsvalidate    If given, all input files are checked for BIDS compliance when first indexed, and
                        excluded when non-compliant (as in pybids.BIDSLayout) (default: False)
  -s PATTERN, --select PATTERN
                        A fullmatch regular expression pattern that is matched against the relative path of the
                        input data. Files that match are scrambled and saved in outputdir (default: (?!\.).*)

examples:
  scramble inputdir outputdir fif
  scramble inputdir outputdir fif permute
```

#### Action brainvision

```console
usage: scramble inputdir outputdir brainvision [-h] [-d] [-b] [-s PATTERN] {null,permute} ...

Adds scrambled versions of the BrainVision EEG files in the input directory to the output directory. If no
scrambling method is specified, the default behavior is to null the data.

positional arguments:
  {null,permute}        Scrambling method (default: null). Add -h, --help for more information
    null                Replaces all values with zeros
    permute             Randomly permute the EEG samples in each channel

options:
  -h, --help            Show this help message and exit
  -d, --dryrun          Do not save anything, only print the output filenames in the terminal (default: False)
  -b, --bidsvalidate    If given, all input files are checked for BIDS compliance when first indexed, and
                        excluded when non-compliant (as in pybids.BIDSLayout) (default: False)
  -s PATTERN, --select PATTERN
                        A fullmatch regular expression pattern that is matched against the relative path of the
                        input data. Files that match are scrambled and saved in outputdir (default: (?!\.).*)

examples:
  scramble inputdir outputdir brainvision
  scramble inputdir outputdir brainvision permute
```

#### Action: swap

```console
usage: scramble inputdir outputdir swap [-h] [-d] [-b] [-s PATTERN] [-g ENTITY [ENTITY ...]]

Randomly swaps the content of data files between a group of similar files in the input directory and save
them as output.

options:
  -h, --help            Show this help message and exit
  -d, --dryrun          Do not save anything, only print the output filenames in the terminal (default: False)
  -b, --bidsvalidate    If given, all input files are checked for BIDS compliance when first indexed, and
                        excluded when non-compliant (as in pybids.BIDSLayout) (default: False)
  -s PATTERN, --select PATTERN
                        A fullmatch regular expression pattern that is matched against the relative path of the
                        input data. Files that match are scrambled and saved in outputdir (default: (?!\.).*)
  -g ENTITY [ENTITY ...], --grouping ENTITY [ENTITY ...]
                        A list of (full-name) BIDS entities that make up a group between which file contents are
                        swapped. See: https://bids-
                        specification.readthedocs.io/en/stable/appendices/entities.html (default: ['subject'])

examples:
  scramble inputdir outputdir swap
  scramble inputdir outputdir swap -s '.*\.(nii|json|tsv)'
  scramble inputdir outputdir swap -s '(?!derivatives(/|$)).*' -b
  scramble inputdir outputdir swap -g subject session run
```

#### Action: pseudo

```console
usage: scramble inputdir outputdir pseudo [-h] [-d] [-b] [-s PATTERN] [-p PATTERN] [-r {yes,no}]
                                          {random,permute,original}

Adds pseudonymized versions of the input directory to the output directory, such that the subject label is
replaced by a pseudonym anywhere in the filepath as well as inside all text files (such as json and tsv-files).

positional arguments:
  {random,permute,original}
                        The method to generate the pseudonyms

options:
  -h, --help            Show this help message and exit
  -d, --dryrun          Do not save anything, only print the output filenames in the terminal (default: False)
  -b, --bidsvalidate    If given, all input files are checked for BIDS compliance when first indexed, and
                        excluded when non-compliant (as in pybids.BIDSLayout) (default: False)
  -s PATTERN, --select PATTERN
                        A fullmatch regular expression pattern that is matched against the relative path of the
                        input data. Files that match are scrambled and saved in outputdir (default: (?!\.).*)
  -p PATTERN, --participant PATTERN
                        The findall() regular expression pattern that is used to extract the subject label from
                        the relative filepath. NB: Do not change this if the input data is in BIDS (default:
                        ^sub-(.*?)(?:/|$).*
  -r {yes,no}, --rootfiles {yes,no}
                        In addition to the included files (see `--select` for usage), include all files in the
                        root of the input directory (such as participants.tsv, etc) (default: yes)

examples:
  scramble inputdir outputdir         pseudo
  scramble inputdir outputdir_remove1 pseudo random   -s '(?!sub-003(/|$)).*' 
  scramble inputdir outputdir_keep1   pseudo original -s 'sub-003/.*'
```

### merge

```console
usage: merge [-h] outputdir inputdirs [inputdirs ...]

Merges non-overlapping/partial (e.g. single subject) BIDS datasets with identically processed derivative data

positional arguments:
  outputdir   The output directory with the merged data
  inputdirs   The list of BIDS (or BIDS-like) input directories with the partial (e.g. single- subject) data

options:
  -h, --help  show this help message and exit

examples: merge outputdir singlesubject-1 singlesubject-2 singlesubject-3
```

## Legal Aspects

This code is released under the GPLv3 license.

## Related tools

- https://github.com/PennLINC/CuBIDS
- https://peerherholz.github.io/BIDSonym
- https://arx.deidentifier.org
