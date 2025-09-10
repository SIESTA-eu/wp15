import numpy as np
import warnings
from joblib import Parallel, delayed
from numba import jit

def user_pipeline(data):
    return np.mean(data, axis=1, keepdims=True)

@jit(nopython=True)
def loo_(data):
    n_features, n_samples = data.shape
    loo_means = np.zeros((n_features, n_samples))
    loo_stds = np.zeros((n_features, n_samples))

    for i in range(n_features):
        v = data[i]
        s, s2 = np.sum(v), np.sum(v**2)
        means = (s - v) / (n_samples - 1)
        vars_ = ((s2 - v**2) - (n_samples - 1) * means**2) / (n_samples - 2)
        loo_means[i], loo_stds[i] = means, np.sqrt(vars_)

    return loo_means, loo_stds

@jit(nopython=True)
def gen_noise(chol_factor, sensitivity, max_attempts=10000):
    dim = sensitivity.shape[0]
    for _ in range(max_attempts):
        z = np.random.standard_normal(dim)
        noise = chol_factor @ z
        if np.all(noise >= sensitivity):
            return noise, True
    return noise, False

def dp(data, original_output, epsilon=1.0):
    loo_means, loo_stds = loo_(data)
    sensitivity = np.max(np.abs(loo_means - original_output), axis=1)

    loo_scales = np.std(loo_stds, axis=1) / epsilon
    cov = np.cov(data)
    scale_factors = 2 * loo_scales / np.sqrt(np.diag(cov))
    scale_matrix = np.diag(scale_factors)

    noise_cov = scale_matrix @ cov @ scale_matrix
    if np.min(np.linalg.eigvals(noise_cov)) <= 1e-10:
        noise_cov += np.eye(data.shape[0]) * 1e-8

    try:
        chol = np.linalg.cholesky(noise_cov)
        noise, success = gen_noise(chol, sensitivity)
        if not success:
            raise ValueError("Correlated noise generation failed")
    except (np.linalg.LinAlgError, ValueError):
        warnings.warn("Failed to generate correlated noise, using independent noise")
        noise = np.array([np.random.normal(0, 2 * s) for s in loo_scales])
        for i in range(len(noise)):
            while abs(noise[i]) < sensitivity[i]:
                noise[i] = np.random.normal(0, 2 * loo_scales[i])

    noisy_outputs = original_output.flatten() + noise
    return noisy_outputs, sensitivity
