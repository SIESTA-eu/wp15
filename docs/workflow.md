# Computational workflow

This document outlines the computational workflow and the handling of input data, intermedate or work-in-progress data, and output data.

Whenever `filename.sif` is mentioned below, it is assumed that this might be either an Apptainer or Singularity container (for wp15 development and testing), or a Docker container (for execution in Kubernetes). Arguments that are specified to the containers correspond to the input and the output directories (for wp15 development and testing) or the encrypted volumes that are to be mounted. The Apptainer or Docker containers do not take additional command-line options that are to be specified by the data rights holder or by the data user. The interaction of the data rights holder or data user with tools and data happens _inside_ the container. For this purpose, some of the containers will need to provide an interactive graphical desktop with VNC or ThinLinc.

Whenever a directory for input or output data is mentioned below, it is assumed that this corresponds to a secure and encrypted volume that is mounted into the container being executed. We anticipate that many volumes will be created, most of them only to hold the single-subject or leave-one-out datasets and the work-in-progress results of the pipelines on these subsets. These volumes can be short-lived and removed after their content has been merged for the next step in the workflow.

## Data rights holder

Transfer the data to the platform and provide a scrambled version.

    ./download.sif input
    ./privacy.sif input scrambled  # this includes the interactive scrambling process and the privacy review

## Data user

Develop the pipeline and test it on the scrambled data.

    ./pipeline.sif scrambled output participant
    ./pipeline.sif scrambled output group
    
## Platform operator

Run the particpant-level analysis on the single subjects.

    for SUBJ in `seq $NSUBJ`; do
        ./singlesubject.sif input singlesubject-$SUBJ $SUBJ
    done

    for SUBJ in `seq $NSUBJ`; do
        ./pipeline.sif singlesubject-$SUBJ singlesubject-$SUBJ/derivatives/output participant
    done

_The call above assumes that the `singlesubject-$SUBJ` directory is writable and that the pipeline writes results in a subdirectory `singlesubject-$SUBJ/derivatives/output`. This is probably not realistic in a Docker scenario that accesses only volumes, not directories. In that case a separate `mergederivatives.sif` step might be needed to merge the singlesubject input data with the singlesubject derivative data. The resulting volumes for all participants are then merged in the next step. See [issue #61](https://github.com/SIESTA-eu/wp15/issues/61)._

    ./mergesubjects.sif subjects-merged $(eval echo singlesubject-{1..$NSUBJ})

Run the group-level analysis on the leave-one-out resampled datasets.

    for SUBJ in `seq $NSUBJ`; do
        ./leaveoneout.sif subjects-merged leaveoneout-$SUBJ $SUBJ
    done

    for SUBJ in `seq $NSUBJ`; do
        ./pipeline.sif leaveoneout-$SUBJ group-$SUBJ group
    done

    ./mergegroup.sif $(eval echo group-{1..$NSUBJ}) group-merged
    ./calibratenoise.sif group-merged noise

Run the group-level analysis on all subjects together and add the calibrated noise.

    ./pipeline.sif subjects-merged group-all group
    ./addnoise.sif group-all noise group-with-noise

## Data rights holder

Review the group-level results with the calibrated noise and release them to the data user.

    ./privacy.sif input group-with-noise

# Required applications or containers

- download.sif
- privacy.sif (for the interactive scrambling process and the privacy review)
- singlesubject.sif
- pipeline.sif (participant-level, on single-subject data)
- mergederivatives.sif
- mergesubjects.sif
- leaveoneout.sif
- pipeline.sif (group-level, on resampled data)
- mergegroup.sif
- pipeline.sif (group-level, on all data, not resampled)
- compare.sif
- calibratenoise.sif
- addnoise.sif
- privacy.sif (for the privacy review on the output data)

# Required data directories or volumes

- input
- scrambled
- output
- singlesubject-xxx
- subjects-merged
- leaveoneout-xxx
- group-xxx
- group-merged
- noise
- group-all
- group-with-noise
