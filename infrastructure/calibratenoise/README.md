Differential Privacy and NeuroImaging

## Table of Contents
- [Overview](#overview)
- [Methods](#methods)
- [Simulation](#simulations)
- [Usage](#usage)
- [Dependencies](#dependencies)
- [Output](#output)
- [Note](#note)
- [ToDo](#todo)

# Overview
$$Exploratory Analysis → DP Methods → Results → Verification$$

This project explores the impact of global differential privacy (GDP) on neuroimaging and tabular data. At the end we validate correctness of DP noise injection for our method. The core principle of GDP is ensuring that no single data point can significantly influence the results, preventing individual identification from aggregate outputs. We highlight the need for careful calibration of privacy mechanisms to balance data utility and confidentiality in statistical analyses.

## Methods
 - Noisy Mean: Adds Gaussian/Laplace noise to the sample mean.
 - Noisy Mean + Std: Adds Gaussian/Laplace into both mean and standard deviation.

## Simulation
In the test folder, we have prepared a number of simulation. This simulation examines the impact of DP on neuroimaging and tabular data in hypothesis testing. We evaluate how adding noise to data as well as summary statistics (mean, standard deviation, or t-values) affects type I error rates and power in a one-sample t-test. 

- Null Hypothesis Testing:
    - Type I error rates simulation for original and DP-adjusted
    - Evaluates type I error rates under DP
    - Error rate estimates
- Test Efficiency:
    - Statistical Power[$1 - \beta $] to tests DP impact data
    - Tests power for effect sizes

## Usage

```bash
python run.py <input.tsv>
```
## Dependencies
- Python 3.x
- Libraries: numpy, scipy, pandas, matplotlib, seaborn, pytest

## Output
- Some output
 
## Note
 - Some notes
## ToDo
- Add noise to the mean, but keeping original std
- Add noise to both mean and std
- Add noise directly to t-values to perturb the t-statistic directly.
	- Ensure t-test implementations produce expected type I error rates under the null.
- Exploratory Data Analysis: Visualize the relationship between, effect size, and statistical power
	- Replicate Monte Carlo experiments for varying effect sizes
- DP Methods Comparison: Compares the DP noise-injection methods
- Results Interpretation: Analyze simulation outputs and summarize key trade-offs between privacy
