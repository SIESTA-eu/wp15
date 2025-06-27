# Mergegroup

This is a Python script that merges the results of the group analysis applied to the different [leave-one-out](https://en.wikipedia.org/wiki/Jackknife_resampling) samples.

The results of the group analysis pipeline executed on the LOO samples are stored in a series of directories, one for each individual subject that was left out. Each directory can have one or multiple files with the results of the group analysis. The results can furthermode be represented over different file formats, such as `.txt`, `.tsv`, `.csv`, `.mat`, `.nii`, `.nii.gz`, as well as represent different sizes or dimensions within each file.

The `mergegroup` step is responsible to collect the results of all these leave-one-out samples, to represent each leave-one-out sample as a row vector, concatenated over all files that comprise the result, and to concatenate those vertically over all leave-one-out samples and store the resulting matrix in a tabular formatted file `results.tsv` that allows to calibrate the noise.

## Requirements

Python 3.x

## Usage

```bash
mergegroup.py <inputdir 1> <inputdir 2> ... <outputdir> <whitelist.txt>
```

The output is stored in `group-merged/results.tsv`, which each row or line is a collection of all possible attribute, in all possible different files of each leave-one-out result.
