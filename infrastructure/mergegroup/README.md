The result of the [Jacknife resampling](https://en.wikipedia.org/wiki/Jackknife_resampling) is stored in usecase2.x/group-n/group/ where $x$ indicates different usecases, and $n$ is each individual.

**mergegroup.sif** container is built by $\text{infrastructure/mergegroup.def]}$ which runs $\text{infrastructure/mergegroup/mergegroup.py]}$, responsible to collect the mentioned result of each individual $n$ and store it in $\text{[usecase2.x/group-merge/group-merged.tsv]}$, for further analysis in the pipeline. 

The indiv results can be saved in different extensions such as $\text{[.txt, .tsv, .csv, .mat, .nii, .nii.gz, ...]}$ as well as different dimensions, $[i \cdot j]$ where $i$ indicates result, and $j$ is different attributes.

### mergegroup.py usecase:

```python
mergegroup.py <input dir 1> <input dir 2> ... <output dir> <whitelist.txt>
```

In this directory there exists number of tests, representing possible usecases with possible results.[extension] and different dimensionality. Usecase shows
$\text{<input dir 1> <input dir 2> ...}$, the directory for each individuals, $\text{<output dir>}$ for output directory, and $\text{whitelist.txt}$ which is a list of filenames of all results. 
Python script is practically run as below:

```python
python3 mergegroup.py group-1 group-2 group-3 group-merge whitelist.txt
```
### Directory
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
```
### Output
The output is stored in usecase2.x/group-merge/group-merged.tsv, which each line is a collection of all possible attribute, in all possible different file type of each individual, resulting in a tsv file of $[n \cdot m]$, where $n$ is individuals and $m$ is attributes. 
### Practical usecase
```bash
python3 mergegroup.py group-1 group-2 group-3 group-merge whitelist.txt
```
# Test
Since each test has group-[1:3], the output file will have 3 lines. This can be tested by 
```bash
for file in whitelist*.txt; do python3 mergegroup.py group-1 group-2 group-3 group-merge "$file"; wc -l group-merge/group-merged.tsv; done
```
where the result for test0 will be 
```bash
Merging: group-1/results.txt -> group-merge/group-merged.tsv
Merging: group-2/results.txt -> group-merge/group-merged.tsv
Merging: group-3/results.txt -> group-merge/group-merged.tsv
3 group-merge/group-merged.tsv
```
