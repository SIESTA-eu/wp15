# SIESTA - work package 15 - use case 2.7

This is a specific use case that serves as a prototype for development and testing the SIESTA computational strategy for sensitive medical imaging data on representative BIDS datasets. The general outline is provided in the documentation. In short, it consists of these steps:

- the data rights holder making a scrambled version of the data available
- the data user implementing and testing the pipeline on the scrambled version
- the data rights holder executing the pipeline on the real data

Note that it skips the step where the platform operator executes the differentially private resampling and execution of the pipeline on the resampled data. The approach followed here is more similar to federated analysis.

## Summary of the data

This dataset pertains to an fMRI study investigating the brain mechanisms underlying visual and multisensory recognition in 12 healthy participants (8 females; mean age = 28.06 years). Participants performed a short-term memory task involving auditory, visual, and audio‑visual stimuli, recognizing and remembering objects in different multisensory contexts. The dataset is organized in BIDS format (2.17 GB) and includes, for each participant, anatomical images (T1w.nii.gz), functional data (task-memory_run-_bold.nii.gz), and event files (_events.tsv) detailing conditions, responses, and reaction times. This dataset is intended as a standardized resource for the scientific community. It has already been used to test an automated fMRI analysis pipeline capable of preprocessing, motion correction, spatial normalization, and preparation of data for univariate and multivariate analyses, allowing evaluation of method robustness and reproducibility.

### Data citation

Nikolaus, M., Mozafari, M., Berry, I., Asher, N., Reddy, L., & VanRullen, R. (2025). SemReps-8K. OpenNeuro. https://doi.org/10.18112/openneuro.ds007272.v1.0.0

Nikolaus, M., Mozafari, M., Berry, I., Asher, N., Reddy, L., & VanRullen, R. (2025). Modality-Agnostic Decoding of Vision and Language from fMRI. eLife. https://doi.org/10.7554/eLife.107933

### Legal aspects of the input data

This dataset has been published under the CC0 license.

## Preparing the data by the data rights holder (DRH)

### Technical requirements for the data rights holder

The workflow requires a Linux environment with Apptainer (formerly Singularity) for running containers

#### Installing Apptainer

On Debian/Ubuntu:

```bash
sudo apt update
sudo apt install -y apptainer
```

On other distributions, or for the latest version, follow the instructions at https://apptainer.org/docs/admin/main/installation.html.

Verify the installation:

```bash
apptainer --version
```

#### Validate Apptainer with a hello-world container

```bash
apptainer run docker://busybox:latest echo "Hello, Apptainer works!"
```

#### Downloading and running BIDS Validator

The analysis pileline requires both the original data and the scrambled version of the data to be BIDS compliant. This can be tested using the bids-validator.

```bash
apptainer run docker://bidsc/bids-validator:latest --version
```

Validate the original BIDS dataset:

```bash
apptainer run --bind /path/to/dataset:/data \
    docker://bidsc/bids-validator:latest /data
```

### Scrambling the data with BIDScramble

Pull the BIDScramble container:

```bash
apptainer pull docker://bidsc/bidscramble:latest
```

Scramble the dataset:

```bash
apptainer run --bind /path/to/original:/input \
    --bind /path/to/scrambled:/output \
    docker://bidsc/bidscramble:latest \
    --input /input --output /output
```

Validate the scrambled dataset:

```bash
apptainer run --bind /path/to/scrambled:/data \
    docker://bidsc/bids-validator:latest /data
```

### Transferring the scrambled data from DRH to the DU

The data rights holder transfers the scrambled dataset to the data user (DU) via secure file transfer (e.g. `scp`, `rsync`, or a shared secure staging area).

```bash
rsync -avz /path/to/scrambled/ user@remote:/path/to/scrambled/
```

## Preparing the analysis pipeline by the data user (DU)

### Implementing and testing the analysis on scrambled data

The analysis consists of a first (participant) level SPM GLM analysis, using standard preprocessing steps, followed by a GLM. The resulting contrast files are then subjected to a second (group) level analysis, to produce contrast files and T-maps.

The data user implements and tests the full analysis pipeline (participant-level and group-level SPM GLM) on the scrambled dataset. Any issues with the pipeline logic can be debugged without exposing real subject information.

### Output data

The output data that is to be shared consists of folders and files that represent group-level aggregated data. Many more individual-subject files are generated, but these should not be shared with the researcher. The `whitelist.txt` file contains a complete list of the output data that is to be shared.

The whitelisted files are:

- derivatives/group/con_0001.nii
- derivatives/group/spmT_0001.nii
- derivatives/group/con_0002.nii
- derivatives/group/spmT_0002.nii

Once implementation and testing by the DU is complete, the DU gathers the whitelisted subset of results, which can be shared with the data rights holder to be compared with the results from their local execution.

```bash
mkdir -p scrambled_whitelisted_results
cp derivatives/group/con_0001.nii scrambled_whitelisted_results/
cp derivatives/group/spmT_0001.nii scrambled_whitelisted_results/
cp derivatives/group/con_0002.nii scrambled_whitelisted_results/
cp derivatives/group/spmT_0002.nii scrambled_whitelisted_results/
zip -r scrambled_whitelisted_results.zip scrambled_whitelisted_results/
```

### Transferring the analysis container from DU to the DRH

The DU packages the analysis container (the SPM + MATLAB Runtime container with the pipeline implementation) and transfers it to the data rights holder:

```bash
apptainer build analysis.sif analysis.def
rsync -avz analysis.sif user@remote:/path/to/analysis.sif
```

Alternatively, if the container is on a registry, share the URI instead.

## Executing the analysis by the data rights holder (DRH)

### Downloading the analysis pipeline

```bash
rsync -avz analysis.sif user@remote:/path/to/analysis.sif
```

Alternatively, if the container is on a registry, the URI can be used instead of downloading the image.

### Testing the analysis on scrambled data

The data rights holder runs the transferred container on the scrambled dataset to verify it produces identical results:

```bash
apptainer run --bind /path/to/scrambled:/data \
    --bind /path/to/output:/output \
    analysis.sif \
    --input /data --output /output
```

If the data user shared the whitelisted results from the pipeline execution on the scrambled data, the data rights holder can compare their results to the shared ones.

#### If errors occur

If the data rights holder encounters errors, they share a full file listing of the scrambled dataset with the DU for diagnostics:

```bash
ls -lR /path/to/scrambled/ > file_listing.txt
# or
tree /path/to/scrambled/ > file_listing.txt
```

Alternatively, the data rights holder may transfer the entire scrambled dataset and logs back to the DU so they can perform more thorough debugging:

```bash
rsync -avz /path/to/scrambled/ user@du-server:/path/to/debug/
rsync -avz /path/to/output/ user@du-server:/path/to/debug/
```

#### If no errors occur

The data rights holder runs the analysis on the original (real) data:

### Executing the analysis on the original data

```bash
# Participant-level analysis
apptainer run --bind /path/to/original:/data \
    --bind /path/to/output:/output \
    analysis.sif \
    --input /data --output /output --level participant

# Group-level analysis
apptainer run --bind /path/to/original:/data \
    --bind /path/to/output:/output \
    analysis.sif \
    --input /data --output /output --level group
```

### Gathering whitelisted results

After successful execution on the original data, gather only the whitelisted files:

```bash
mkdir -p original_whitelisted_results
cp derivatives/group/con_0001.nii original_whitelisted_results/
cp derivatives/group/spmT_0001.nii original_whitelisted_results/
cp derivatives/group/con_0002.nii original_whitelisted_results/
cp derivatives/group/spmT_0002.nii original_whitelisted_results/
zip -r original_whitelisted_results.zip original_whitelisted_results/
```

Review the output for correctness, then transfer the results to the data user.
