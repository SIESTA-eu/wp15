# SIESTA - work package 15 - use case 2.3

This is a specific use case that serves as a prototype for development and testing the SIESTA computational strategy for sensitive medical imaging data on representative BIDS datasets. The general outline is provided in the [documentation](docs/README.md). In short it consists of these steps:

1. the _data rights holder_ transferring the data onto the platform and making a scrambled version
2. the _data user_ implementing and testing the pipeline on the scrambled version
3. the _platform operator_ running the differential private computation on the resampled version of the original data

In the absence of a complete implementation of the SIESTA platform, this prototype use case requires that we bootstrap the whole process. The data transfer, the pipeline development, and the pipeline execution are all performed by wp15 members.

In the following it is assumed that the wp15 repository with the code for all use cases is as `wp15` and that the data for all use cases is stored in a directory called `data` with subdirectories for each use case. Depending on where you store the code and the data on your computer, you may have to change some paths in the instructions below.

## Data rights holder

### Summary of the input data

The [input dataset](https://doi.org/10.18112/openneuro.ds000117.v1.0.6) is a multi-subject, multi-modal neuroimaging dataset that is described in detail in the accompanying [data publication](https://doi.org/10.1038/sdata.2015.1). It includes structural and functional MRI, MEG, and EEG data that was recorded during an experimental task on face processing.

The input data consists of 1671 files with a combined size of 84.82GB and can be downloaded using [datalad](https://www.datalad.org). 

### Data transfer

In order to be able to use datalad, a sufficiently recent version of git is required. The older CentOS nodes on the DCCN cluster, running git version 1.8.3.1 could not do the job. The newer AlmaLinux nodes run git version 2.39.3. This worked.

```console
python -m venv venv
source venv/bin/activate
pip install datalad datalad-installer

datalad-installer git-annex -m datalad/git-annex:release --install-dir venv
mv venv/usr/lib/* venv/lib/.
mv venv/usr/bin/* venv/bin/.

mkdir data/usecase-2.3
cd data/usecase-2.3

git clone https://github.com/OpenNeuroDatasets/ds000117.git input

cd input

# get the MEG data for all subjects
datalad get sub-*/ses-meg/meg/*

# get the MaxFiltered MEG data for all subjects
datalad get derivatives/meg_derivatives/sub-*/ses-meg/meg/*

# get the anatomical MRI data for all subjects
datalad get sub-*/ses-mri/anat/*mprage_T1w.nii.gz
```

### Constructing the scrambled data

As in SIESTA the data is assumed to be sensitive, the analysis is conceived to be designed and implemented on a scrambled version of the dataset. Note that that is not needed here, as the original input and output data can be accessed directly.

 A scrambled version of the data can be generated using [BIDScramble](https://github.com/SIESTA-eu/wp15/tree/main/BIDScramble).

```console
cd data/usecase-2.3
scramble input scrambled stub
scramble input scrambled json -p '.*'
scramble input scrambled fif -s 'sub-../.*_meg\.fif'
```

### Privacy assessment on the scrambled data

To be discussed and documented here.

### Data citation

Wakeman, DG and Henson, RN (2024). Multisubject, multimodal face processing. OpenNeuro. [Dataset] doi: doi:10.18112/openneuro.ds000117.v1.0.6

### Legal aspects of the input data

The input dataset has been released under the [CC0](https://spdx.org/licenses/CC0-1.0.html) license.

## Data user

The data user's pipeline implements an Event-Related Field (ERF) analysis on [Magnetoencephalography](https://en.wikipedia.org/wiki/Magnetoencephalography) (MEG) data.

The pipeline is expected to be executed on a Linux computer, although it might also work on macOS or Windows.

### Output data

The output data that is to be shared consists of folders and files that represent group-level aggregated data. Many more individual-subject files are generated but these should not be shared with the researcher.

The `whitelist.txt` file contains a complete list of the output data that is to be shared. 

```console
cd wp15/usecase-2.3
mkdir output
```

### Software installation

This requires the GitHub wp15 repository, MATLAB, and a recent FieldTrip version.

```console
git clone https://github.com/SIESTA-eu/wp15.git
wget wget https://github.com/fieldtrip/fieldtrip/archive/refs/heads/master.zip
unzip master.zip
mv fieldtrip-master fieldtrip
rm master.zip
```

### Testing the pipeline

Executing the pipeline from the MATLAB command window is done like this:

```console
cd wp15/usecase-2.3
restoredefaultpath
addpath fieldtrip
addpath work
analyze_participant('input', 'output')
analyze_group('input', 'output')
```

Executing the pipeline from the Linux terminal is done like this:

```console
cd wp15/usecase-2.3
matlab -batch "restoredefaultpath; addpath fieldtrip source; bidsapp input output participant
matlab -batch "restoredefaultpath; addpath fieldtrip source; bidsapp input output group
```

You should replace the `input` and `output` directories in the instructions above with the ones where the actual data is located or should be written. For the prototype you can test the pipeline both on the original input data and on the scrambled data in the `scrambled` directory.

### Legal aspects of the software

MATLAB is commercial software and requires a license.

FieldTrip is open source and released under the GPLv3 license.

The code that is specific to the analysis pipeline is shared under the CC0 license.

## Platform operator

The platform operator should be assumed to have no domain specific knowledge about the data, about the software, about the analysis pipeline, or about the results that it generates. The platform operator just executes the required containers following the [computational workflow](docs/workflow.md).

The documention provided here is for Apptainer imagines, which allows wp15 members to develop and test. Once the use case is past the prototype stage, Docker images might be used instead.

The documentation provided here is also just for a minimal test that does not consider differential privacy yet.

### Containerizing the pipeline

You can install the software in an Apptainer container image like this:

```console
cd wp15/usecase-2.3
apptainer build pipeline.sif pipeline.def
```

### Executing the pipeline as container

Executing the pipeline from the Apptainer image is done like this:

```console
cd wp15/usecase-2.3
apptainer run --env MLM_LICENSE_FILE=port@server pipeline.sif input output participant
apptainer run --env MLM_LICENSE_FILE=port@server pipeline.sif input output group
```

You should replace the `input` and `output` directories in the instructions above with the ones where the actual data is located or should be written.
