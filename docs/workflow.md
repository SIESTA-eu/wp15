# Computational workflow

This document outlines the computational workflow and the handling of input data, intermedate or work-in-progress data, and output data.

Whenever `filename.sif` is mentioned below, it is assumed that this might be either an Apptainer or Singularity container (for wp15 development and testing), or a Docker container (for execution in Kubernetes). Arguments that are specified to the containers correspond to the input and the output directories (for wp15 development and testing) or the encrypted volumes that are to be mounted. The Apptainer or Docker containers do not take additional command-line options that are to be specified by the data rights holder or by the data user. The interaction of the data rights holder or data user with tools and data happens _inside_ the container. For this purpose, some of the containers will need to provide an interactive graphical desktop with VNC or ThinLinc.

Whenever a directory for input or output data is mentioned below, it is assumed that this corresponds to a secure and encrypted volume that is mounted into the container being executed. We anticipate that many volumes will be created, most of them only to hold the single-subject or leave-one-out datasets and the work-in-progress results of the pipelines on these subsets. These volumes can be short-lived and removed after their content has been merged for the next step in the workflow.

The following workflow includes a number of steps that are not needed for the final output. These have been added to validate the consistency of the implementation and to help with testing during platform development. They can be removed at a later stage.

## Data rights holder

Transfer the data to the platform, provide a scrambled version, and do a privacy review.

    ./download.sif  input
    ./scramble      input scrambled-input
    ./privacy.sif   input scrambled-input

## Data user

Develop the pipeline and test it on the scrambled data.

    ./pipeline.sif scrambled-input scrambled-output participant
    ./pipeline.sif scrambled-input scrambled-output group
    
## Platform operator

Run the particpant- and group-level analysis on the original input data.

    ./pipeline.sif input output participant
    ./pipeline.sif input output group

Run the particpant-level analysis on the single subjects.

    for SUBJ in `seq $NSUBJ`; do
        ./singlesubject.sif input singlesubject-$SUBJ-input $SUBJ
        ./pipeline.sif singlesubject-$SUBJ-input singlesubject-$SUBJ-output participant
    done

Combine the single subject input and results into merged datasets.

    ./mergesubjects.sif singlesubject-merged-input  $(eval echo singlesubject-{1..$NSUBJ}-input)  # this should result in the same as "input"
    ./mergesubjects.sif singlesubject-merged-output $(eval echo singlesubject-{1..$NSUBJ}-output)

Run the group-level analysis on the leave-one-out resampled datasets.

    for SUBJ in `seq $NSUBJ`; do
        ./leaveoneout.sif input                       leaveoneout-$SUBJ-input  $SUBJ
        ./leaveoneout.sif singlesubject-merged-output leaveoneout-$SUBJ-output $SUBJ
        ./pipeline.sif    leaveoneout-$SUBJ-input     leaveoneout-$SUBJ-output group
    done

Merge the leave-one-out results and calibrate the noise.

    ./mergegroup.sif $(eval echo leaveoneout-{1..$NSUBJ}-output) leaveoneout-merged-output ./whitelist.txt
    ./calibratenoise.sif leaveoneout-merged-output noise

Run the group-level analysis on all subjects together and add the calibrated noise.

    ./pipeline.sif singlesubject-merged-input singlesubject-merged-output group  # this should result in the same as "output"
    ./addnoise.sif singlesubject-merged-output noise singlesubject-merged-output-noise
    ./addnoise.sif output noise output-noise    # this should result in the same "singlesubject-merged-output-noise"

## Data rights holder

Review the group-level results with the calibrated noise and release them to the data user.

    ./privacy.sif input output-noise

# Required applications or containers

- download.sif
- scramble.sif
- privacy.sif
- pipeline.sif
- singlesubject.sif
- leaveoneout.sif
- mergesubjects.sif
- mergegroup.sif
- calibratenoise.sif
- addnoise.sif

# Required data directories or volumes

- input
- output
- scrambled-input
- scrambled-output
- singlesubject-xxx-input
- singlesubject-xxx-output
- singlesubject-merged-input
- singlesubject-merged-output
- leaveoneout-xxx-input
- leaveoneout-xxx-output
- leaveoneout-merged-output
- noise
- singlesubject-merged-output-noise
- output-noise
