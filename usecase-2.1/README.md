# SIESTA - work package 15 - use case 2.1 (tabular data)

This is a specific use case that serves as a prototype for development and testing the SIESTA computational strategy for sensitive medical imaging data on representative BIDS datasets. The general outline is provided in the [documentation](../docs/README.md). In short, it consists of these steps:

1. the _data rights holder_ transferring the data onto the platform and making a scrambled version
2. the _data user_ implementing and testing the pipeline on the scrambled version
3. the _platform operator_ running the differential private computation on the resampled version of the original data

In the absence of a complete implementation of the SIESTA platform, this prototype use case requires that we bootstrap the whole process. The data transfer, the pipeline development, and the pipeline execution are all performed by wp15 members.

In the following it is assumed that the wp15 repository with the code for all use cases is as `wp15` and that the data for all use cases is stored in a directory called `data` with subdirectories for each use case. Depending on where you store the code and the data on your computer, you may have to change some paths in the instructions below.

## Data rights holder

### Summary of the input data

The [input dataset](https://doi.org/10.18112/openneuro.ds004148.v1.0.1) contains resting (eyes closed, eyes open) and cognitive (subtraction, music, memory) state EEG recordings with 60 participants during three experimental sessions together with sleep, emotion, mental health, and mind-wandering related measures. The data is described in more detail in an [accompanying paper](https://doi.org/10.1038/s41597-022-01607-9).

The analysis pipeline demonstrated here only uses the tabular data that is included in the BIDS dataset. The tabular data contains biometric information, i.e. indirect personal identifiers (age, height and weight, as well as outcomes from various questionnaires). With some minor modifications the pipeline should also work with many other BIDS datasets from [OpenNeuro](https://openneuro.org).

The complete input data consists of 5585 files with a combined size of 30.67GB. The analysis only requires a few of those files to be downloaded.

### Data transfer

```console
mkdir data/usecase-2.1/input
cd data/usecase-2.1/input

wget https://s3.amazonaws.com/openneuro.org/ds004148/participants.tsv
wget https://s3.amazonaws.com/openneuro.org/ds004148/participants.json
wget https://s3.amazonaws.com/openneuro.org/ds004148/dataset_description.json
wget https://s3.amazonaws.com/openneuro.org/ds004148/README
wget https://s3.amazonaws.com/openneuro.org/ds004148/CHANGES
for SUBJ in `seq -w 60`; do mkdir sub-${SUBJ} ; done
```

### Constructing the scrambled data

As in SIESTA the data is assumed to be sensitive, the analysis is conceived to be designed and implemented on a scrambled version of the dataset. Note that that is not needed here, as the original input and output data can be accessed directly.

 A scrambled version of the data can be generated using [BIDScramble](https://github.com/SIESTA-eu/wp15/tree/main/BIDScramble).

```console
cd data/usecase-2.1
scramble input scrambled stub
scramble input scrambled tsv permute -s participants.tsv
scramble input scrambled json -p '.*' -s participants.json
```

### Privacy assessment on the scrambled data

For the scrambled data you can ensure to what degree intended patterns or information are leaked from the original dataset. You can use [DatLeak](https://github.com/SIESTA-eu/DatLeak) to test for potential data leakage, checking whether the scrambled variables still contain any identifiable patterns that could be traced back to the original participants. DatLeak detects data leakage in anonymized datasets by comparing the original data with the scrambled version. It calculates percentage of full leakage (where all variables in a row match) and partial leakage (where some, but not all, variables match). These calculation help assess the effectiveness of the anonymization process. Running DatLeak on scrambled datasets helps confirm that the anonymization process is robust and protects participant privacy.

Installing DatLeak is done by cloning its repository.

```console
git clone https://github.com/SIESTA-eu/DatLeak.git
```
#### Usage 

```
python DatLeak.py <original_file> <scrambled_file> [ignore_value] [ignore_col]
```
DatLeak is executed using the following, where you should make sure that the `input` and `scrambled` directory correspond to the actual path for them on your computer. You can see some practical usage down here:


```console
python ./DatLeak/DatLeak.py input/participants.tsv scrambled/participants.tsv -999 0
python ./DatLeak/DatLeak.py input/participants.tsv scrambled/participants.tsv None 0
python ./DatLeak/DatLeak.py input/participants.tsv scrambled/participants.tsv
```

This will print a report on screen with the percentage of rows with partial leakage, the percentage of rows with full leakage, the average matching cells per row, and the standard deviation of the matching cells per row.

```console
 - Full Leakage (identical row/participant): 0.00%
 - Partial Leakage (rows/participants have data partially identical): 100.00%
 - Average portion of row/participants that are identical: 46.73
 - Standard Deviation of row/participants that are identical: 6.26
```

If full leakage is not at 0%, the scrambler should be re-run. Partial leakage is left at the appreciation of the data right holder.

### Data citation

Yulin Wang and Wei Duan and Debo Dong and Lihong Ding and Xu Lei (2022). A test-retest resting and cognitive state EEG dataset. OpenNeuro. [Dataset] doi: doi:10.18112/openneuro.ds004148.v1.0.1

### Legal aspects of the input data

The input dataset has been released under the [CC0](https://spdx.org/licenses/CC0-1.0.html) license.

## Data user

The data user's pipeline implements a very simple analysis of the tabular data that accompanies a neuroimaging dataset. Specifically, it computes the mean age, height and weight over a group of participants.

This specific use case implements the same pipeline based on R, MATLAB, Python and Julia. In the subsequent documentation we only describe the version based on R.

The pipeline is expected to be executed on a Linux computer, although it might also work on macOS or Windows.

### Computational requirements for the participant level

There is no real computation done at the participant level, so this takes barely any time (except for data handling). The execution of the pipeline for each participant takes XX GB of RAM and XX seconds per subject.

There are 60 subjects.

### Computational requirements for the group level

The execution of the group-level pipeline takes XX GB of RAM, XX seconds, and results in XX GB of temporary data per leave-one-out sample.

### Output data

The output data consist of a `results.tsv` file that contains the averaged age, height and weight of the participants.

The `whitelist.txt` file contains a complete list of the output data that is to be shared.

```console
cd data/usecase-2.1
mkdir output
```

### Software installation

The R-software can be installed on a Linux, MacOS or Windows computer, specifically including the `Rscript` binary. The `optparse` and `dplyr` packages are ideally installed and on the path. If these packages are not available, they will be downloaded and installed in a temporary directory.

### Testing the pipeline

Executing the pipeline from the Linux terminal is done like this:

```console
cd wp15/usecase-2.1
Rscript work/pipeline.R input output participant
Rscript work/pipeline.R input output group
```

Note that this specific analysis pipeline does not have any computations at the participant level, but the participant step is included for completeness.

You should replace the `input` and `output` directories in the instructions above with the ones where the actual data is located or should be written. For the prototype you can test the pipeline both on the original input data and on the scrambled data in the `scrambled` directory.

### Legal aspects of the software

The R-package and the optparse package are Open Source and licensed under GPL-2 or GPL-3.

MATLAB is commercial software and requires a license.

The Julia software is Open Source and licensed under the MIT License.

The Python software is Open Source and licensed under the PSL License.

The Apptainer software is licensed under the [BSD-3-Clause](https://apptainer.org/docs/admin/main/license.html).

The code that is specific to the analysis pipeline is shared under the CC0 license.

## Platform operator

The platform operator should be assumed to have no domain specific knowledge about the data, about the software, about the analysis pipeline, or about the results that it generates. The platform operator just executes the required containers following the [computational workflow](docs/workflow.md).

The documentation provided here is for Apptainer imagines, which allows wp15 members to develop and test. Once the use case is past the prototype stage, Docker images might be used instead.

The documentation provided here is also just for a minimal test that does not consider differential privacy yet.

### Transferring the data

The platform operator can download the data using the corresponding container (only for testing purposes) and the following instructions:

```console
cd wp15/usecase-2.1
apptainer build download.sif download.def
apptainer run download.sif ../../data/usecase-2.1/input
```

You may have to replace the `input` directory in the example above with the desired location on your computer.

### Containerizing the pipeline

You can install the software in an Apptainer container image like this:

```console
cd wp15/usecase-2.1
apptainer build pipeline.sif container-r.def
```

### Executing the pipeline as container

Executing the pipeline from the Apptainer image is done like this:

```console
cd wp15/usecase-2.1
apptainer run pipeline.sif input output participant
apptainer run pipeline.sif input output group
```

You should replace the `input` and `output` directories in the instructions above with the ones where the actual data is located or should be written.
