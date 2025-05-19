# mergegroup

The results of the group analysis pipeline executed on the [leave-one-out](https://en.wikipedia.org/wiki/Jackknife_resampling) samples are stored in a series of directories, one for each individual subject that was left out. Each directory can have one or multiple files with the results of the group analysis. The results can furthermode be represented over different file formats, such as `.txt`, `.tsv`, `.csv`, `.mat`, `.nii`, `.nii.gz`, as well as represent different sizes or dimensions within each file.

The `mergegroup` step is responsible to collect the results of all these leave-one-out samples, to represent each leave-one-out sample as a row vector, concatenated over all files that comprise the result, and to concatenate those vertically over all leave-one-out samples and store the resulting matrix in a tabular formatted file `results.tsv` that allows to calibrate the noise.

The `mergegroup.sif` container is built by `infrastructure/mergegroup.def` which runs `infrastructure/mergegroup/mergegroup.py`.

## Usage

```console
mergegroup.py <input dir 1> <input dir 2> ... <output dir> <whitelist.txt>
```

## Directory with tests

There are a number of tests that are organized like this:

```console
test0/
├── group-1
│   └── results.txt
├── group-2
│   └── results.txt
├── group-3
│   └── results.txt
└── whitelist.txt

test1/
├── group-1
│   └── results.tsv
├── group-2
│   └── results.tsv
├── group-3
│   └── results.tsv
├── whitelistA.txt
├── whitelistB.txt
├── whitelistC.txt
├── whitelistD.txt
├── whitelistE.txt
└── whitelistF.txt

...

test10/
├── group-1
│   ├── results.mat
│   ├── results.nii
│   └── results.tsv
├── group-2
│   ├── results.mat
│   ├── results.nii
│   └── results.tsv
├── group-3
│   ├── results.mat
│   ├── results.nii
│   └── results.tsv
└── whitelist.txt
```

### Practical usecase

The Python script can be executed on one of the test datasets as follows:

```console
cd tests/test0
mergegroup.py group-1 group-2 group-3 group-merged whitelist.txt
```

### Output

The output is stored in `group-merged/results.tsv`, which each row or line is a collection of all possible attribute, in all possible different files of each leave-one-out result.

Since each of the tests has group-[1:3], the `results.tsv` file will have 3 lines. This can be tested by

```bash
for file in whitelist*.txt ; do python mergegroup.py group-1 group-2 group-3 group-merged $file ; wc -l group-merged/group-merged.tsv ; done
```

where the output will be similar for each `whitelist.txt`

For `test0` this will be

```bash
Merging: group-1/results.txt -> group-merge/group-merged.tsv
Merging: group-2/results.txt -> group-merge/group-merged.tsv
Merging: group-3/results.txt -> group-merge/group-merged.tsv
3 group-merged/results.tsv
```
