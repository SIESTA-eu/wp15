Differential Privacy and NeuroImaging

# Overview
$$Exploratory Analysis → DP Methods → Results → Verification$$

This project explores the impact of global differential privacy (GDP) on neuroimaging and tabular data. We validate correctness of DP noise injection for our method (ie does it provide private data) and evaluate the impact of DP on statistical properties of common analyses (eg t-tests).

## Notebooks
In the test folder, we have prepared a number of simulation. This simulation examines the impact of DP on neuroimaging and tabular data in hypothesis testing. We evaluate how adding noise to user output (1) ensures privacy and (2) affects statistical properties of the requested outputs.

*[Notebook 1](https://github.com/SIESTA-eu/wp15/blob/dev-code-under-loo-privacy/infrastructure/privacy_dev/notebook_1.ipynb): This illustrates how an attacker can gain information about a subject from group results and how golbal privacy works*  
- simple example with an outlier, and how asking for the mean of the group can be used to gain information

*[Notebook 2.1](https://github.com/SIESTA-eu/wp15/blob/dev-code-under-loo-privacy/infrastructure/privacy_dev/notebook_2.1.ipynb)*: Illustration of global privacy using mean value
- use the 1st column of use case 2.1 and compute the mean
- explain the loo approach to privacy to derive parameters for a Gaussian or Laplace distribution and the L1-norm as lower limnit to add noise
- run a monte carlo 1000 times to prove this is always globally private

*[Notebook 2.2](https://github.com/SIESTA-eu/wp15/blob/dev-code-under-loo-privacy/infrastructure/privacy_dev/notebook_2.2.ipynb)*: Same as 2.1 but we use a Gaussian distribution rather than a Laplace distribution for noise. If Gaussian works, that is the prefered method.

*[Notebook 3](https://github.com/SIESTA-eu/wp15/blob/dev-code-under-loo-privacy/infrastructure/privacy_dev/notebook_3.ipynb)*: Assuming a user wants to perform a one-sample t-test on data, we test the type I error rates and power of the noisy outputs, either directly from a t-test or from noisy means and standard deviations (recomputing t-test).

*[Notebook 4](https://github.com/SIESTA-eu/wp15/blob/dev-code-under-loo-privacy/infrastructure/privacy_dev/notebook_4.ipynb)*: Illustration of global privacy using bivariate mean values
- use data from use case 2.1 and compute the means
- exploit covariance to create multivariate noise with the same covariance
- run a monte carlo 1000 times to prove this is always globally private

*[Notebook 5](https://github.com/SIESTA-eu/wp15/blob/dev-code-under-loo-privacy/infrastructure/privacy_dev/notebook_5.ipynb)*: Assuming a user wants to perform one-sample t-tests on data, we test the type I error rates and power of the noisy outputs from bivariate data directly from a t-test.

*[Notebook 6](https://github.com/SIESTA-eu/wp15/blob/dev-code-under-loo-privacy/infrastructure/privacy_dev/notebook_6.ipynb)*: Illustration of global privacy using multivariate noise for real neuroimaging data
