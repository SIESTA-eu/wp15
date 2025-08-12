# Notebook 2.1
## 1. Problem Statement ✅
## 2. Structure & Flow
Planned or current sections in the notebook:
- [x] Data loading
- [x] Solution explained
- [x] Simulations
- [ ] Interpretation
## 3. Status - To do 
- It is hard to understand why sensitivity increases with sample size, given that these are subsamples. The issue is that the sample size vs sensitivity is confounded by the outlier (large sample size tends to have more extreme values, which itself becomes even larger once -100 is added)
- [X] make 'two' simulations one without outliers and one with outliers (but ideally in a single double loop)
- [x] do the sample size vs sensitivity plots from the simulated data without adding the outlier in position 0 (no need to plot with outliers)
- [x] do the MAE vs sensitivity plots from the simulated data without outlier in position 0 (no need to plot with outliers)
- [X] compute the outlier in position 0 for the biggest sample size (ie 'data' in the code) and reuse that value in subsamples (ie get lower outside the loop) = the same outlier values is used for each subsamples in a given replicate
- [ ] plot together (on the same figure) the outlier detection rate for the fixed outlier (index 0) vs others (average of other indices)
- [x] **errors found in code to fix: n_replicates indexation is missing**
```
error_[size].append(recons_error)
sensitivities_[size].append(sens_outputs)
reconstructed[size].append(recons)
counts[size] += 1
id_dr[size][idx] += 1
````

🔴 bloker
Local differential privacy is wrong, since detection rates are too high
- [ ] start by testing for the observed data, to explain how it works (and figure out the right solution)
- [ ] try local privacy such as noise is signed (if a value is lower than user_output then the noise is added, if a value is higher than user_output, noise is substracted -- meaning that noise is an abs value (abs(laplace))
- [ ] then move to simulations

# Notebook 2.2
## 1. Problem Statement [ ]
## 2. Structure & Flow
Planned or current sections in the notebook:
- [x] Data loading
- [x] Solution explained
- [⚠️ ] Simulations
- [ ] Interpretation
## 3. To do 🔴
