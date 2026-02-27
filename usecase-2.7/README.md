# SIESTA - work package 15 - use case 2.1

The pipeline is expected to be executed on a Linux computer, although it might also work on macOS or Windows.

## Input data
The dataset ds001345 (Audio‑Visual Memory in the Context of Multisensory Integration) pertains to an fMRI study investigating the brain mechanisms underlying visual and multisensory recognition in 12 healthy participants (8 females; mean age = 28.06 years). Participants performed a short-term memory task involving auditory, visual, and audio‑visual stimuli, recognizing and remembering objects in different multisensory contexts. The dataset is organized in BIDS format (2.17 GB) and includes, for each participant, anatomical images (T1w.nii.gz), functional data (task-memory_run-_bold.nii.gz), and event files (_events.tsv) detailing conditions, responses, and reaction times.

No specific cognitive results are expected; the dataset is intended as a standardized resource for the scientific community. It has already been used to test an automated fMRI analysis pipeline capable of preprocessing, motion correction, spatial normalization, and preparation of data for univariate and multivariate analyses, allowing evaluation of method robustness and reproducibility.
