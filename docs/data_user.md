# Data user

The data user is the researcher that aims to answer a specific research question using the data that is made available for analysis on the SIESTA platform. We assume that the SIESTA data user is working in a different institute than the data rights holder; if they were working in the same institution, they could share directly and the SIESTA platform would not be needed.

As the data on SIESTA is considered to be sensitive, it is not directly available for download by the data user. The SIESTA platform allows the data user to interactively implement an analysis, which eventually is converted to a container and executed by the platform operator on the data of behalf of the data user.

## Developing and testing the analysis

The data analysis can be implemented on basis of any analysis tool and/or analysis environment, given that it is possible to run the analysis in batch mode without user input. Graphical user interface dialogs that ask a question are not possible during batch execution.

The final implementation should be containerized and implemented as a [BIDS app](https://doi.org/10.1371/journal.pcbi.1005209) with a participant- and a group-level step (see below).

### General recommendations

Install all software and all dependencies from the command line, as that will facilitate the implementation of the container.

Once the container is built, it will be read only. Installing additional software dependencies from within the analysis environment (for example downloading and installing "plug-ins" on the fly) will not work. If software dependencies need to be installed from within the analysis environment, this must be done in the container definition file, not in the analysis pipeline. See for an example the usecase-2.1 container with `r-base` and the the call to `install.packages` for the dependencies.

The only two directories that are shared with the analysis pipeline are directory with the input and the output data. The input directory is to be assumed to be read-only. The output directory can be used in any way you like, but only the files in the `whitelist.txt` with group-level aggregate data will be shared with the data user.

During development and testing, the data user has access to an anonymous scrambled version of the original dataset. This scrambled dataset has all the technical features of the original data, but the results of the analysis on this data should be assumed to be meaningless.

To facilitate debugging, the data user's analysis scripts should give explicit error messages. Rather than a try-except statement that print that "something went wrong", the analysis script should show _where_ in the analysis it went wrong (i.e., in which step, and on which subject) and _what_ went wrong. When possible, show a full stack trace of the error.

## Storage requirements

The data user must specify to the platform operator what the storage requirements are for the participant- and group-level analyses. How many file are created, how much storage does that require, what is the retention period of the intermediate data, and what data files comprise the final results for the data user.

The original dataset is not directly accessible to the data user and should remain read-only. The analysis pipeline should not write any results to the original dataset. There is a single "BIDS derivative" output directory to hold the intermediate results of the participant-level analysis _and_ the group-level results. It is up to the data user how to organize the data in this directory, but we recommend that the participant-level data is organized in subdirectories named `sub-<label>` and that the group results are stored in a subdirectory named `group`.

## Computational requirements

The data user must specify to the platform operator what the computational requirements for the analysis are. Preferably, the data user would specify the computational requirements for the participant-level and the group-level separately, as that allows the platform operator to decide whether the participant-level analysis can be executed in parallel.

For development and testing we recommend to use a Linux-based environment where the data user has full administrative rights to install software and dependencies. The steps for software and dependency installation must be transferred to a container definition file.

If the data user want to make use of MATLAB in the analysis, they should give the platform operator access to the MATLAB license server and provide the `LM_LICENSE_FILE` environment variable.

If the data user want to make use other non-free software in the analysis, they should provide the platform operator with that software and with the license to use that software on their behalf.

### Participant level

[BIDS apps](https://doi.org/10.1371/journal.pcbi.1005209) make the distinction between participant- and group-level analyses. The participant-level analysis can be considered as a sort of pre-processing step prior to the actual analysis. Examples include FreeSurfer reconstruction of the cortical sheet, or computing first-level statistical estimates.

The participant-level analysis can be done one subject at the time, but can also be executed in parallel. The analysis of one participant's data does not require access to the data of any other participant.

To ensure that no targeted attacks are possible by singling out any given subject, the participant-level analysis is implemented on single-subject versions of the input dataset.

### Group level

During the group-level analysis, the data from multiple participants is combined into an aggregate group-level output that provides the answer to the data user's research question. The group level analysis might require access to the original input data, and might also require access to intermediate results that are computed during the participant-level analysis.

### Software licenses

The SIESTA platform or its platform operators does not provide the software and/or licenses for the software that you may want to use in your analysis pipeline. When implementing the container that runs the analysis pipeline, you should take the appropriate measures such that the software can be installed and that it can be both legally and technically used. This may mean that you have to apply for a license key (for example for [FreeSurfer](https://surfer.nmr.mgh.harvard.edu/fswiki/License)) or that you have to provide network access to a license server (for example [MATLAB](https://nl.mathworks.com/help/install/ug/use-existing-on-premises-license-manager-with-matlab-running-on-the-cloud.html)).

### Computational efficiency

The participant- and group-level analysis can in principle be computed sequentially in a single step, but for efficiency reasons with the leave-one-out resampling scheme, we have implemented these explicitly as separate steps, so that the participant-level analyses don't have to be repeated for each leave-one-out sample. 

Since the participant-level analysis is done separately for each subject, it can be executed in parallel by the platform operator. The data user does not have to implement anything special for parallel execution.

## Data transfer out from the system (export)

The data user may want to download the scrambled version of the data for local development and testing of the analysis pipeline.

The data user will also want to download the results of the application of their pipeline to the original sensitive data.
