# Data user

The data user is the researcher that aims to answer a specific research question using the data that is made available for analysis on the SIESTA platform. We assume that the SIESTA data user is working in a different institute than the data rights holder; if they were working in the same institution, they could share directly and the SIESTA platform would not be needed.

As the data on SIESTA is considered to be sensitive, it is not directly available for download by the data user. The SIESTA platform allows the data user to interactively implement an analysis, which eventually is converted to a container and executed by the platform operator on the data of behalf of the data user.

SIESTA wp15 makes use of the [BIDS](https://bids.neuroimaging.io) (Brain Imaging Data Structure) standard, which is a formalized framework for organizing and describing neuroimaging and behavioral data in a consistent, machine-readable manner to facilitate data sharing and reproducibility.

## Developing and testing the analysis

A scrambled version of the data is provided by the data rights holder that shows what the dataset contains and how it is organized, so that the data user can implement the analysis pipeline. The scrambled version has been reviewed by the data rights holder and is anonymous, hence it can also be downloaded and used outside of the SIESTA platform for pipeline development.

The data analysis can be implemented on the basis of any analysis tool and/or analysis environment, given that it is possible to run the analysis in batch mode without user input. Graphical user interface dialogs that ask a question are not possible during batch execution.

### Implementing the container

The final implementation should be containerized and implemented as a [BIDS app](https://doi.org/10.1371/journal.pcbi.1005209) with a participant- and a group-level step (see below).

The motivation for containerizing the analysis pipeline is:

- to be able to run the analysis pipeline in the cloud (i.e., on someone else's computer)
- to ensure that all software dependencies are identified and installed properly
- to protect the sensitive data that is processed from being disclosed

In general the sharing of an analysis pipeline with other researchers would not require to contanerise it, you only have to share your code, a specification of its requirements, and documentation how to execute it. However, containerizing a data analysis pipeline ensures **reproducibility** (same environment everywhere), **portability** (runs on any system), and **scalability** (easy cloud deployment). It isolates dependencies, avoids setup conflicts, and simplifies sharing with others. Plus, it integrates with continuous-integration, continuous-deployment and **orchestration** tools for automation and scaling (like Docker Swarm or Kubernetes).

> [!IMPORTANT]  
> It is as of yet unclear whether it is the data use or the platform operator (or both) that writes the container definition file to encapsulate the analysis pipeline. The container definition is stored in the SIESTA [container registry](https://goharbor.io) and the building of the container image is the responsibility of the platform operator.

### General recommendations

Install all software and all dependencies from the command line, as that will facilitate the implementation of the container.

Once the container is built, it will be read only and always run without internet connectivity. Installing additional software dependencies from within the analysis environment (for example downloading and installing "plug-ins" on the fly) will not work. If software dependencies need to be installed from within the analysis environment, this must be done in the container definition file, not in the analysis pipeline. See for an example the usecase-2.1 container with `r-base` and the call to `install.packages` for the dependencies.

The only two directories that are shared with the analysis pipeline are directory with the input and the output data. The input directory is to be assumed to be read-only. The output directory can be used in any way you like, but only the files in the `whitelist.txt` with group-level aggregate data will be shared with the data user.

During development and testing, the data user has access to an anonymous scrambled version of the original dataset. This scrambled dataset has all the technical features of the original data, but the results of the analysis on this data should be assumed to be meaningless.

To facilitate debugging, the data user's analysis scripts should give explicit error messages. Rather than a try-except statement that print that "something went wrong", the analysis script should show _where_ in the analysis it went wrong (i.e., in which step, and on which subject) and _what_ went wrong. When possible, show a full stack trace of the error.

### Input data handling

Input data to the analysis pipeline is formatted as a [BIDS](https://bids.neuroimaging.io) dataset. If the input data provided by the data rights holder is a "derivatives" dataset (as specified by `DatasetType` in the `dataset_description.json` file), it is expected to still follow the folder organization of a "raw" dataset, as that is required for the shuffling and resampling.

The input directory can optionally also include nested derivatives that are provided by the data rights holder, such as MaxFiltered data, or FreeSurfer cortical sheets. These would be in the `input/derivative/pipelinename` directory, where the pipeline name is for example `maxfilter` or `freesurfer`. Again, these derivatives should follow the folder organization of a "raw" dataset.

The input is, for example, formatted as

```console
input
├── dataset_description.json
├── participants.tsv
├── participants.json
├── README.md
├── sub-01
|   | ses-01/...
|   └ ses-02/...
├── sub-02
|   | ses-01/...
|   └ ses-02/...
...
├── sub-NN
|   | ses-01/...
|   └ ses-02/...
└── derivatives
    ├ maxfilter
    | ├── dataset_description.json
    | ├── README.md
    | ├── sub-01
    | ├── sub-02
    | ...
    | └── sub-NN
    └ freesurfer
      ├── dataset_description.json
      ├── README.md
      ├── sub-01
      ├── sub-02
      ...
      └── sub-NN
```

### Output data handling

A requirement for the resampling implemented in SIESTA wp15 is that the output data from the analysis pipeline must be formatted as a [BIDS](https://bids.neuroimaging.io) derivative dataset, i.e., a BIDS compliant dataset with a `dataset_description.json` that specifies `"DatasetType": "derivative"`. The output directory holds both the intermediate results from the participant-level analysis _and_ the final results from the group-level analysis.

The participant-level analysis must write its results in `sub-xxx` directories that are placed directly underneath the output directory. You should _not_ place the participant-level results in a subdirectory named `derivatives` inside the output directory.

The group-level analysis has access to the original input data and to these intermediate participant-level output results. The output data for the group-level analysis should be written inside a `derivatives` subsirectory in the output. We recommend to place group results in a `derivatives/group` or a `derivatives/pipelinename` subdirectory.

The output is for example formatted as

```console
output
├── dataset_description.json (with "DatasetType" specified as "derivative")
├── sub-01
|   └ ...
├── sub-02
|   └ ...
├── sub-03
|   └ ...
...
└── derivatives
    └── group
        ├── someresults.tsv
        └── otherresults.nii.gz
```

#### Whitelisting

The participant and group-level analysis result in a number of files, some of which are only temporary work-in-progress, whereas others represent the primary research outcomes of the analysis pipeline. The data user has to provide a text file `whitelist.txt` that lists all the desired outcomes, i.e., all files resulting from the group-level analysis that are to be retained. Noise calibration will be done on the numerical data in these files, and a differentially private version of these files will be shared with the data user.

An example for the whitelist is

```console
derivatives/group/someresults.tsv
derivatives/group/otherresults.nii.gz
```

Files that are not in the `whitelist.txt` will never be shared with the data user.

## Storage requirements

The data user must specify to the platform operator what the storage requirements are for the participant- and group-level analyses. How many file are created, how much storage does that require, what is the retention period of the intermediate data, and what data files comprise the final results for the data user.

The original dataset is not directly accessible to the data user and should remain read-only. The analysis pipeline should not write any results to the original input dataset. If temporary results are to be written to the input dataset, it is required to make a copy of the input dataset to the output directory and use that as the input.

## Computational requirements

The data user must specify to the platform operator what the computational requirements for the analysis are. Preferably, the data user would specify the computational requirements for the participant-level and the group-level separately, as that allows the platform operator to decide whether the participant-level analysis can be executed in parallel.

For development and testing we recommend to use a Linux-based environment where the data user has full administrative rights to install software and dependencies. The steps for software and dependency installation must be transferred to a container definition file.

### Participant level

[BIDS apps](https://doi.org/10.1371/journal.pcbi.1005209) make the distinction between participant- and group-level analyses. The participant-level analysis can be considered as a sort of pre-processing step prior to the actual analysis. Examples include FreeSurfer reconstruction of the cortical sheet, or computing first-level statistical estimates.

The participant-level analysis can be done one subject at the time, but can also be executed in parallel. As such, the analysis of one participant's data does not have access to the data of any other participant, i.e. the participant-level analysis is implemented on single-subject versions of the input dataset.

### Group level

During the group-level analysis, the data from multiple participants is combined into an aggregate group-level output that provides the answer to the data user's research question. The group level analysis might require access to the original input data, and might also require access to intermediate results that are computed during the participant-level analysis.

### Software licenses

The SIESTA platform or its platform operators does not provide the software and/or licenses for the software that you may want to use in your analysis pipeline. When implementing the container that runs the analysis pipeline, you should take the appropriate measures such that the software can be installed and that it can be both legally and technically used.

For instance, if the data user want to make use of MATLAB in the analysis, they should give the platform operator access to the MATLAB license server and provide the `LM_LICENSE_FILE` environment variable. If there are license restriction, e.g. the institutional license does not allow for use of the MATLAB license on hardware that is not from the institute, the data user can consider to create a compiled executable from the pipeline, and containerize this executable.

If the data user want to make use other non-free software in the analysis (for example for [FreeSurfer](https://surfer.nmr.mgh.harvard.edu/fswiki/License)), they should provide the platform operator with that software and with the license to use that software on their behalf.

## Data transfer out from the system (export)

The data user may want to download the scrambled version of the data for local development and testing of the analysis pipeline.

The data user will also want to download the differentially private results of the application of their pipeline to the original sensitive data.

> [!IMPORTANT]
> It is as of yet unclear how data transfer out of the system will be implemented. This is to be done with [WP11](https://confluence.ifca.es/spaces/SIESTA/pages/160956465/WP10+WP11+-+Data+privacy+and+anonymization+tools+Data+stage+out+and+risk+control).
