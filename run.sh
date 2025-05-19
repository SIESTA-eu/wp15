export NSUBJ=3
export VER=v0.6.12
export USECASE=2.5
export PORT=27000
export SERVER=10.10.4.101
export URLORAS=oras://ghcr.io/siesta-eu

# DOWNLOAD
#apptainer run ${URLORAS}/download-${USECASE}.sif:${VER} input

# SCRAMBLE
#apptainer run oras://ghcr.io/siesta-eu/scramble.sif:${VER} input scrambled stub
#apptainer run oras://ghcr.io/siesta-eu/scramble.sif:${VER} input scrambled nii
#apptainer run oras://ghcr.io/siesta-eu/scramble.sif:${VER} input scrambled tsv
#apptainer run oras://ghcr.io/siesta-eu/scramble.sif:${VER} input scrambled json
#apptainer run oras://ghcr.io/siesta-eu/scramble.sif:${VER} input scrambled json -p '(?!AcquisitionTime).*'
#apptainer run oras://ghcr.io/siesta-eu/scramble.sif:${VER} input scrambled tsv permute -p '(?!AcquisitionTime).*'
#apptainer run oras://ghcr.io/siesta-eu/scramble.sif:${VER} input scrambled nii permute y -i

# CREATE SINGLESUBJECT
#for SUBJ in $(seq 1 $NSUBJ); do
   #apptainer run oras://ghcr.io/siesta-eu/singlesubject.sif:${VER} input singlesubject-$SUBJ $SUBJ
   #apptainer run --env MLM_LICENSE_FILE=${PORT}@${SERVER} pipeline_matlab.sif singlesubject-$SUBJ singlesubject-$SUBJ/derivatives/output participant
#done

# MERGE
#apptainer run ${URLORAS}/mergesubjects.sif:${VER} subjects-merged $(for SUBJ in $(seq 1 $NSUBJ); do echo -n "singlesubject-$SUBJ "; done)

for SUBJ in 30 31 33; do
#for SUBJ in $(seq 1 $NSUBJ); do
    #apptainer run oras://ghcr.io/siesta-eu/leaveoneout.sif:${VER} subjects-merged/derivatives/output leaveoneout-$SUBJ $SUBJ
    apptainer run --env MLM_LICENSE_FILE=${PORT}@${SERVER} pipeline_matlab.sif leaveoneout-$SUBJ leaveoneout-$SUBJ/derivatives/output group    
    #apptainer run pipeline.sif singlesubject-$SUBJ-output leaveoneout-$SUBJ-output group
done
