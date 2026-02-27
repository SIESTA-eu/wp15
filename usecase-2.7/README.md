# SIESTA - work package 15 - use case 2.1

This is a specific use case that serves as a prototype for development and testing the SIESTA computational strategy for sensitive medical imaging data on representative BIDS datasets. The general outline is provided in the documentation. In short, it consists of these steps:

- the data rights holder making a scrambled version of the data available
- the data user implementing and testing the pipeline on the scrambled version
- the data rights holder executing the pipeline on the real data

# Data rights holder

## Summary of the input data

The dataset pertains to an fMRI study investigating the brain mechanisms underlying visual and multisensory recognition in 12 healthy participants (8 females; mean age = 28.06 years). Participants performed a short-term memory task involving auditory, visual, and audio‑visual stimuli, recognizing and remembering objects in different multisensory contexts. The dataset is organized in BIDS format (2.17 GB) and includes, for each participant, anatomical images (T1w.nii.gz), functional data (task-memory_run-_bold.nii.gz), and event files (_events.tsv) detailing conditions, responses, and reaction times.

The dataset is intended as a standardized resource for the scientific community. It has already been used to test an automated fMRI analysis pipeline capable of preprocessing, motion correction, spatial normalization, and preparation of data for univariate and multivariate analyses, allowing evaluation of method robustness and reproducibility.

## Data citation

_Please specify how the data should be cited, for example by pointing to a previous paper that uses the data._

## Legal aspects of the input data

_Please specify that the data cannot be shared for privacy reasons._

# Data user

## Pipeline results

The analysis results in ...

## Computational requirements for the participant level

The execution of the pipeline for each participant takes ...

## Computational requirements for the group level

The execution of the group-level pipeline takes ...

## Output data

The output data that is to be shared consists of folders and files that represent group-level aggregated data. Many more individual-subject files are generated but these should not be shared with the researcher.
