The result of the [Jacknife resampling](https://en.wikipedia.org/wiki/Jackknife_resampling) is stored in usecase2.x/group-n/group/ where $x$ indicates different usecases, and $n$ is each individual.

**mergegroup.sif** container is built by infrastructure/mergegroup.def which runs infrastructure/mergegroup/mergegroup.py, responsible to collect the mentioned result of each individual $n$ and store it for further analysis in the pipeline. The results can be saved in different extensions such as $[.txt, .tsv, .csv, .mat, .nii, .nii.gz, ...]$, as well as different dimensions, $[i x j]$ where $i$ indicates result, and $j$ is different attributs.

### mergegroup.py usecase:

```python
mergegroup.py <input dir 1> <input dir 2> ... <output dir> <whitelist.txt>
```

In this directory there exists number of tests, representing possible usecases with possible results.[extension] and different dimensionality.

```python
python3 mergegroup.py group-1 group-2 group-3 group-merge whitelist.txt
```
test0/
├── group-1 
│   ├── results.txt
├── group-2
│   ├── results.txt
├── group-3
│   ├── results.txt
└── whitelist.txt
test1/
├── group-1 
│   ├── results.tsv
├── group-2
│   ├── results.tsv
├── group-3
│   ├── results.tsv
├── whitelistA.txt
├── whitelistB.txt
├── whitelistC.txt
├── whitelistD.txt
├── whitelistE.txt
└── whitelistF.txt
---
---
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

### Practical usecase
```bash
python3 mergegroup.py group-1 group-2 group-3 group-merge whitelist.txt
```
# Test

```bash
for file in whitelist*.txt; do python3 mergegroup.py group-1 group-2 group-3 group-merge "$file"; wc -l group-merge/group-merged.tsv; done
```
