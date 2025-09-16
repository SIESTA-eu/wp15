import numpy as np
import warnings
from joblib import Parallel, delayed
from numba import jit


@jit(nopython=True)
def user_pipeline(data):
    n_rows, n_cols = data.shape
    result = np.empty((n_rows, 1), dtype=np.float64)
    for i in range(n_rows):
        row_sum = 0.0
        for j in range(n_cols):
            row_sum += data[i, j]
        result[i, 0] = row_sum / n_cols
    return result

@jit(nopython=True)
def loo_(data):
    if not isinstance(data, np.ndarray):
        data = np.array(data)
    
    #if data.ndim != 2:
    #    raise ValueError("Input array must be 2-dimensional")
    
    n_rows, n_cols = data.shape
    
    for i in range(n_rows):
        for j in range(n_cols):
            if not np.isfinite(data[i, j]):
                raise ValueError("Array contains NaN or infinite values")
    
    loo_results = np.empty((n_rows, n_cols), dtype=np.float32)
    row_sums = np.empty(n_rows, dtype=np.float64)
    for i in range(n_rows):
        row_sums[i] = 0.0
        for j in range(n_cols):
            row_sums[i] += data[i, j]

    for j in range(n_cols):
        reduced_means = np.empty((n_rows, 1), dtype=np.float64)
        for i in range(n_rows):
            reduced_means[i, 0] = (row_sums[i] - data[i, j]) / (n_cols - 1)

        result = user_pipeline(reduced_means)
        
        for i in range(n_rows):
            loo_results[i, j] = result[i, 0]

    return loo_results

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
    loo_results = loo_(data)
    sensitivity = np.max(np.abs(loo_results - original_output), axis=1)

    loo_scales = np.std(loo_results, axis=1) / epsilon
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
