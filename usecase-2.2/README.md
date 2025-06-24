# SIESTA - work package 15 - use case 2.2 (3D medical images)

This is a specific use case that serves as a prototype for development and testing the SIESTA computational strategy for sensitive medical imaging data on representative BIDS datasets. The general outline is provided in the [documentation](../docs/README.md). In short, it consists of these steps:

1. the _data rights holder_ transferring the data onto the platform and making a scrambled version
2. the _data user_ implementing and testing the pipeline on the scrambled version
3. the _platform operator_ running the differential private computation on the resampled version of the original data

In the absence of a complete implementation of the SIESTA platform, this prototype use case requires that we bootstrap the whole process. The data transfer, the pipeline development, and the pipeline execution are all performed by wp15 members.

In the following it is assumed that the wp15 repository with the code for all use cases is as `wp15` and that the data for all use cases is stored in a directory called `data` with subdirectories for each use case. Depending on where you store the code and the data on your computer, you may have to change some paths in the instructions below.

## Data rights holder

### Summary of the input data

The [input dataset](https://doi.org/10.18112/openneuro.ds003826.v3.0.1) contains structural T1-weighted MRI brain scans from 136 young individuals (87 females; age range from 18 to 35 years old) along with questionnaire-assessed measurements of trait-like chronotype, sleep quality and daytime sleepiness. The data is organized according to the BIDS standard (combined size of 1.18GB) and mostly useful to scientists interested in circadian rhythmicity, structural brain correlates of chronotypes in humans and the effects of sleeping habits and latitude on brain anatomy. The dataset is described in more detail in an [accompanying publication](https://doi.org/10.1080/09291016.2021.1990501).

### Data transfer

Downloading the data with the [cli](https://docs.openneuro.org/packages/openneuro-cli.html) requires Node.js (version 18 or higher) to be installed. To install a specific (latest) version of Node.js you can [install nvm](https://github.com/nvm-sh/nvm?tab=readme-ov-file#installing-and-updating) and manage your node installation(s) from there:

```console
wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
nvm install node    # "node" is an alias for the latest version
```

If your node installation is up-to-date and working then make sure you have an openneuro account and in a new termminal run:

```console
npm install -g @openneuro/cli

mkdir data/usecase-2.2
cd data/usecase-2.2

openneuro login
openneuro download ds003826 -s 3.0.1 input
```

Tip: Use e.g. Node.js version 21.7.3 if you get errors from the openneuro client

### Constructing the scrambled data

As in SIESTA the data is assumed to be sensitive, the analysis is conceived to be designed and implemented on a scrambled version of the dataset. Note that that is not needed here, as the original input and output data can be accessed directly.

 A scrambled version of the data can be generated using [BIDScramble](https://bidscramble.readthedocs.io).

```console
cd data/usecase-2.2
scramble input scrambled stub
scramble input scrambled json -p '(?!AcquisitionTime).*'
scramble input scrambled nii permute y -i
```

### Privacy assessment on the scrambled data

For the scrambled data you can ensure to what degree intended patterns or information are leaked from the original dataset. You can use [DatLeak](https://github.com/SIESTA-eu/DatLeak) to test for potential data leakage, checking whether the scrambled variables still contain any identifiable patterns that could be traced back to the original participants. DatLeak detects data leakage in anonymized datasets by comparing the original data with the scrambled version. It calculates **full leakage** (where all voxels are identical in an array) and partial leakage (where some, but not all, variables match). These calculation help assess the effectiveness of the anonymization process. Running DatLeak on scrambled datasets helps confirm that the anonymization process is robust and protects participant privacy.

#### Installing DatLeak is done by cloning its repository.

```console
git clone https://github.com/SIESTA-eu/DatLeak.git
```
#### Usage 

```
python run.py <base dir original> <base dir scrambled> [report]
# example
python run.py usecase-2.2/input usecase-2.2/scrambled True/False
```
#### Output
The output will be:
- A brief information of the subject
- Full/Partial leakage in different axis
- Total full/partial leakage of the image
   - Partial leakage will be assessed by numerical values [0: 0.999] where the max value indicates the maximum information leaked
   - Full leakage will be assessed by True/False indicating whether or not the image needs to be re-scrambled.
```
########################################
 - Subject ID: sub-02
 - Shape: (176, 248, 256)
########################################
 - Spatial Analysis
	 - Dimension[X]: 	Full Leakage: 0/176 slices	Average Partial Leakage: 0.563
	 - Dimension[Y]: 	Full Leakage: 0/248 slices	Average Partial Leakage: 0.515
	 - Dimension[Z]: 	Full Leakage: 0/256 slices	Average Partial Leakage: 0.535
 - Partial Leakage: 0.6614
 - Full Leakage: False

```


**NOTE:** 
- DatLeak is divided into two branches of **Tabular** and **NeuroImaging** folders, where anything related to BIDS dataset are stored in NeuroImaging folders.
- All subjects are expected to be right in **base dir original/scrambled** folders.
```
original/scrambled
├── sub-02
├── sub-03
├── ...
├── ...
```

### Data citation

Michal Rafal Zareba and Magdalena Fafrowicz and Tadeusz Marek and Ewa Beldzik and Halszka Oginska and Aleksandra Domagalik (2022). Structural (t1) images of 136 young healthy adults; study of effects of chronotype, sleep quality and daytime sleepiness on brain structure. OpenNeuro. [Dataset] doi: doi:10.18112/openneuro.ds003826.v3.0.1

### Legal aspects of the input data

The input dataset has been released under the [CC0](https://spdx.org/licenses/CC0-1.0.html) license.

## Data user

This implements the [MRIQC](https://mriqc.readthedocs.io/en/latest/) pipeline for obtaining standard QC measures from an MRI dataset.

The pipeline is expected to be executed on a Linux computer, although it might also work on macOS or Windows.

### Computational requirements for the participant level

The execution of the pipeline for each participant takes about 8 GB of RAM, 15 minutes per subject, and results in 250 MB of temporary data per subject.

There are 136 subjects.

### Computational requirements for the group level

The execution of the group-level pipeline takes less than 1 GB of RAM, 10 seconds, and results in less than 1 MB of temporary data per leave-one-out sample.

### Output data

The output data consists of MRI QC parameters of each participant

The `whitelist.txt` file contains a complete list of the output data that is to be shared.

```console
cd data/usecase-2.2
mkdir output
```

### Software installation

Running the analysis pipeline requires a working [Apptainer installation](https://apptainer.org/docs/admin/main/installation.html#installation-on-linux) (version >= 2.5). Next the [MRIQC](https://mriqc.readthedocs.io/en/latest/) container needs to be downloaded:

```console
cd wp15/usecase-2.2
apptainer pull mriqc-24.0.0.sif docker://nipreps/mriqc:24.0.0
```

### Testing the pipeline

Executing the pipeline from the Apptainer image is done like this:

```console
cd wp15/usecase-2.2
apptainer run --cleanenv mriqc-24.0.0.sif input output participant
apptainer run --cleanenv mriqc-24.0.0.sif input output group
```

You should replace the `input` and `output` directories in the instructions above with the ones where the actual data is located or should be written. For the prototype you can test the pipeline both on the original input data and on the scrambled data in the `scrambled` directory.

### Legal aspects of the software

The Apptainer software is licensed under [BSD-3-Clause](https://apptainer.org/docs/admin/main/license.html).

The MRIQC software is licensed under [Apache-2.0](https://spdx.org/licenses/Apache-2.0.html).

## Platform operator

The platform operator should be assumed to have no domain specific knowledge about the data, about the software, about the analysis pipeline, or about the results that it generates. The platform operator just executes the required containers following the [computational workflow](docs/workflow.md).

The documentation provided here is for Apptainer imagines, which allows wp15 members to develop and test. Once the use case is past the prototype stage, Docker images might be used instead.

The documentation provided here is also just for a minimal test that does not consider differential privacy yet.

### Transferring the data

The platform operator can download the data using the corresponding container (only for testing purposes) and the following instructions:

```console
cd wp15/usecase-2.2
apptainer build download.sif download.def
apptainer run download.sif ../../data/usecase-2.2/input
```

You may have to replace the `input` directory in the example above with the desired location on your computer.

### Containerizing the pipeline

This is not needed, since the pipeline is natively distributed as a container. You can download it as follows:

```console
cd wp15/usecase-2.2
apptainer pull mriqc-24.0.0.sif docker://nipreps/mriqc:24.0.0
```

### Executing the pipeline as container

Executing the pipeline from the Apptainer image is done like this:

```console
cd wp15/usecase-2.2
apptainer run --cleanenv mriqc-24.0.0.sif input output participant
apptainer run --cleanenv mriqc-24.0.0.sif input output group
```

You should replace the `input` and `output` directories in the instructions above with the ones where the actual data is located or should be written.
