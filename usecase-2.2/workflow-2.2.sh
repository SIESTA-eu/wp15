#!/bin/bash

export PS4='\[\e[1;33m\][DEBUG] \[\e[95m\]$(date "+%H:%M:%S") ${BASH_SOURCE}:${LINENO}|\[\e[0m\] '
set -e  # Exit on any error
set -u  # Treat unset variables as an error
set -x  # Print all executed commands to the terminal

VER=latest
USECASE=2.2
URLORAS=oras://ghcr.io/siesta-eu
WHITELIST=./whitelist.txt
PIPELINE=./pipeline-${USECASE}.sif
# PIPELINE=${URLORAS}/pipeline-${USECASE}.sif:${VER}

# DOWNLOAD
apptainer run ${URLORAS}/download-${USECASE}.sif:${VER} input

# SCRAMBLE
apptainer run ${URLORAS}/scramble.sif:${VER} input scrambled-input stub
apptainer run ${URLORAS}/scramble.sif:${VER} input scrambled-input tsv permute -s participants.tsv
apptainer run ${URLORAS}/scramble.sif:${VER} input scrambled-input nii wobble
apptainer run ${URLORAS}/scramble.sif:${VER} input scrambled-input json -p '.*'

# DO SOMETHING WITH PRIVACY
# apptainer run ${URLORAS}/privacy.sif:${VER} input scrambled-input

# RUN PIPELINE
apptainer run $PIPELINE input           output           participant
apptainer run $PIPELINE input           output           group
apptainer run $PIPELINE scrambled-input scrambled-output participant
apptainer run $PIPELINE scrambled-input scrambled-output group

# CREATE SINGLESUBJECT AND RUN THE PIPELINE ON SINGLESUBJECTS
count=1             # NB: ((count++)) evaluates to 0 if count==0, which is a falsey value in bash, causing set -e to exit
for SUBJ in input/sub-*/; do
   apptainer run ${URLORAS}/singlesubject.sif:${VER} input singlesubject-$count-input $count
   apptainer run $PIPELINE singlesubject-$count-input singlesubject-$count-output participant
   ((count++))
done
((count--))

# MERGE
apptainer run ${URLORAS}/mergesubjects.sif:${VER} $(eval echo singlesubject-{1..$count}-input)  singlesubject-merged-input
apptainer run ${URLORAS}/mergesubjects.sif:${VER} $(eval echo singlesubject-{1..$count}-output) singlesubject-merged-output

# CREATE LOO SAMPLES AND RUN THE GROUP PIPELINE ON THE INPUT AND ON THE LOO SAMPLES
count=1
for SUBJ in input/sub-*/; do
    leaveout="$count: $SUBJ"
    apptainer run ${URLORAS}/leaveoneout.sif:${VER} singlesubject-merged-input  leaveoneout-$count-input  $count
    apptainer run ${URLORAS}/leaveoneout.sif:${VER} singlesubject-merged-output leaveoneout-$count-output $count
    rm -rf leaveoneout-$count-output/.bids_db/      # Somehow this database makes the last subject iteration fail
    apptainer run $PIPELINE                         leaveoneout-$count-input    leaveoneout-$count-output group
    ((count++))
done
((count--))

# MERGE
apptainer run ${URLORAS}/mergegroup.sif:${VER} $(eval echo leaveoneout-{1..$count}-output) leaveoneout-merged-output $WHITELIST

# apptainer run oras://ghcr.io/siesta-eu/calibratenoise.sif:${VER}      leaveoneout-merged-output noise
# apptainer run oras://ghcr.io/siesta-eu/mergesubjects.sif:${VER}       singlesubject-merged $(eval echo singlesubject-{1..$NSUBJ})  # this should result in the same as "input"
# apptainer run oras://ghcr.io/siesta-eu/pipeline-${USECASE}.sif:${VER} singlesubject-merged singlesubject-merged-output group       # this should result in the same as "input-output"
# apptainer run oras://ghcr.io/siesta-eu/addnoise.sif:${VER}            singlesubject-merged-output noise result-with-noise
# apptainer run oras://ghcr.io/siesta-eu/privacy.sif:${VER}             result-with-noise
