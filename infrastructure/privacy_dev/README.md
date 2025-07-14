Differential Privacy and NeuroImaging

## Table of Contents
- [Overview](#overview)
- [Simulation](#simulations)
- [Usage](#usage)
- [Dependencies](#dependencies)
- [Output](#output)
- [Note](#note)
- [ToDo](#todo)

# Overview
$$Exploratory Analysis → DP Methods → Results → Verification$$

This project explores the impact of global differential privacy (GDP) on neuroimaging and tabular data. At the end we validate correctness of DP noise injection for our method. The core principle of GDP is ensuring that no single data point can significantly influence the results, preventing individual identification from aggregate outputs. We highlight the need for careful calibration of privacy mechanisms to balance data utility and confidentiality in statistical analyses.

## Simulation
In the test folder, we have prepared a number of simulation. This simulation examines the impact of DP on neuroimaging and tabular data in hypothesis testing. We evaluate how adding noise to user output (1) ensures privacy and (2) affects statistical properties of the requested outputs.

*Notebook 1: This illustrates how an attacker can gain information about a subject from group results and how golbal privacy works*  
- simple exemple with an outlier, and how asking for the mean of the group can be used to gain information
- explain the loo approach to derive parameters for a Gaussian or Laplace distribution and the L1-norm as lower limnit to add noise
- perform the operation and show that results are private
- run a monte carlo 1000 times to show this is always globally private

*Notebook 2*: Assuming a user wants to perform a one-sample t-test on data, we test the type I error rates and power of the noisy outputs, either directly from a t-test or from noisy means and standard deviations (recomputing t-test).

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
- Exploratory Data Analysis: Visualize the relationship between different dimensions, effect size, and statistical power
	- Replicate Monte Carlo experiments
- Results Interpretation: Maybe analyze simulation outputs and summarize key trade-offs between privacy and utility.
