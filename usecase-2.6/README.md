# SIESTA - work package 15 - use case 2.6 (4D imaging space * time)

This is a specific use case that serves as a prototype for development and testing the SIESTA computational strategy for sensitive medical imaging data on representative BIDS datasets. The general outline is provided in the [documentation](docs/README.md). In short, it consists of these steps:

1. the _data rights holder_ transferring the data onto the platform and making a scrambled version
2. the _data user_ implementing and testing the pipeline on the scrambled version
3. the _platform operator_ running the differential private computation on the resampled version of the original data

In the absence of a complete implementation of the SIESTA platform, this prototype use case requires that we bootstrap the whole process. The data transfer, the pipeline development, and the pipeline execution are all performed by wp15 members.

In the following it is assumed that the wp15 repository with the code for all use cases is as `wp15` and that the data for all use cases is stored in a directory called `data` with subdirectories for each use case. Depending on where you store the code and the data on your computer, you may have to change some paths in the instructions below.

## Data rights holder

### Summary of the input data

> [!NOTICE]  
> The input data set is the same as that for [use case 2.5](../usecase-2.5/README.md). Hence the data transfer and scrambling are also identical.

The input data is freely available from "OpenNeuro" with the Accession Number [ds004934](https://doi.org/10.18112/openneuro.ds004934.v1.0.0). The dataset includes 44 subjects who are divided into two experiments: 17 subjects undergo fMRIs dedicated to experiment 1, whereas 29 subjects undergo fMRIs dedicated to experiment 2.

The input data consists of about 1548 files with a combined size of 18.63G.

### Data transfer

The data can be downloaded using the Amazon [AWS command-line interface](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) or using [datalad](https://www.datalad.org/).

```console
mkdir data/usecase-2.5
cd data/usecase-2.5

aws s3 cp --recursive --no-sign-request s3://openneuro.org/ds004934/ input
```

To resume a partially complete download that was interrupted you can do

```console
aws s3 sync --no-sign-request s3://openneuro.org/ds004934/ input
```

Alternatively, you can download the data with the openneuro [cli](https://docs.openneuro.org/packages/openneuro-cli.html) (requires Node.js v18 or higher to be installed). To install a specific (latest) version of Node.js you can [install nvm](https://github.com/nvm-sh/nvm?tab=readme-ov-file#installing-and-updating) and manage your node installation(s) from there:

```console
wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
nvm install node    # "node" is an alias for the latest version
```

If your node installation is up-to-date and working then make sure you have an openneuro account and in a new termminal run:

```console
npm install -g @openneuro/cli

mkdir data/usecase-2.5
cd data/usecase-2.5

openneuro login
openneuro download ds004934 -s 1.0.0 input
```

Tip: Use e.g. Node.js version 21.7.3 if you get errors from the openneuro client

### Constructing the scrambled data

As in SIESTA the data is assumed to be sensitive, the analysis is conceived to be designed and implemented on a scrambled version of the dataset. Note that that is not needed here, as the original input and output data can be accessed directly.

 A scrambled version of the data can be generated using [BIDScramble](https://bidscramble.readthedocs.io).

```console
cd data/usecase-2.5
scramble input scrambled stub
scramble input scrambled json -p '(?!AcquisitionTime).*'
scramble input scrambled nii permute y -i
```

### Privacy assessment on the scrambled data

To be discussed and documented here.

### Data citation

The dataset itself can be cited with

- Shari Liu and Kirsten Lydic and Lingjie Mei and Rebecca Saxe (2024). fMRI dataset: Violations of psychological and physical expectations in human adult brains. OpenNeuro. [Dataset] [doi:10.18112/openneuro.ds004934.v1.0.0](https://doi.org/10.18112/openneuro.ds004934.v1.0.0).

The publication that describes the study in more detail is

- Liu, S., Lydic, K., Mei, L., & Saxe, R. (2024). Violations of physical and psychological expectations in the human adult brain. Imaging Neuroscience. [doi:10.1162/imag_a_00068](https://doi.org/10.1162/imag_a_00068).

### Legal aspects of the input data

The input dataset has been released under the [CC0](https://spdx.org/licenses/CC0-1.0.html) license.

## Data user

TBD

### Computational requirements for the participant level

TBD

### Computational requirements for the group level

The execution of the group-level pipeline takes XX GB of RAM, XX seconds, and results in XX GB of temporary data per leave-one-out sample.

### Output data

TBD

### Software installation

TBD

### Testing the pipeline

TBD

### Legal aspects of the software

TBD

## Platform operator

TBD

### Transferring the data

TBD

### Containerizing the pipeline

TBD

### Executing the pipeline as container

TBD