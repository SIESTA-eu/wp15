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
- [x] make 'two' simulations one without outliers and one with outliers (but ideally in a single double loop)
- [x] do the sample size vs sensitivity plots from the simulated data without adding the outlier in position 0 (no need to plot with outliers)
- [x] do the MAE vs sensitivity plots from the simulated data without outlier in position 0 (no need to plot with outliers)
- [x] compute the outlier in position 0 for the biggest sample size (ie 'data' in the code) and reuse that value in subsamples (ie get lower outside the loop) = the same outlier values is used for each subsamples in a given replicate
- [x] plot together (on the same figure) the outlier detection rate for the fixed outlier (index 0) vs others (average of other indices)
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
- [x] start by testing for the observed data, to explain how it works (and figure out the right solution)
- [x] try local privacy such as noise is signed (if a value is lower than user_output then the noise is added, if a value is higher than user_output, noise is substracted -- meaning that noise is an abs value (abs(laplace))
- [x] then move to simulations

## 3. To do 🔴
- [ ] still results make no sense - check with team WP15-WP10

# Notebook 2.2
## 1. Problem Statement [ ]
## 2. Structure & Flow
Planned or current sections in the notebook:
- [x] Data loading
- [x] Solution explained
- [x] Simulations
- [x] Interpretation

# Notebook 3
- [ ] user_output ; return mean, std, t-test value
- [ ] dp as before
- [ ] set alpha 0.05
- [ ] for size, do as notebook 2 (subsamples)
- [ ] user_output(data) and then dp(mean), dp(std), dp(t-test)
- [ ] then test if dp(t-test), p-value and signitifcance
- [ ] same compute t-test from dp(mean) and dp(std), and get p-value and signitifcance

# Notebook 6
- [ ] use an MRI and an EEG dataset for dimenionality
- [ ] for MRI consider places where we have 0
- [ ] use the optimized code from notebook 5 (vectorized loo)
- [ ] use the cholensky favctorization to create multivariate Gaussian (see notebook 5)
- [ ] ensure regulatized covariance (see notebook 5)
- [ ] describe how outliers are made for MRI and for EEG (like a sub-region)
