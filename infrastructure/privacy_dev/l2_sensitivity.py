"""
l2_sensitivity.py — the L2-SELECTED sensitivity bar, as a thin wrapper on the frozen harness.

Baseline A's bar (in privacy_harness.loo_artifacts) is the per-voxel max  S_j = max_i |D_ij|.
This swaps in a group/L2-selected bar: pick the single subject with the largest whole-patch L2
influence, i* = argmax_i ||D_i||_2, and use that subject's per-voxel |influence| as the bar.

Only the sensitivity vector changes. The wrapped mechanism's covariance, rejection rule (per-voxel
|Z_j| >= S_j for all j) and fallback are the frozen ones, reused verbatim -- so a Baseline-A-vs-l2
comparison isolates the bar. Nothing here edits the toolkit or Baseline A. No DP guarantee.
"""
import numpy as np


def l2_selected_bar(D):
    """(|D_{i*}| flattened, i*) where i* = argmax_i ||D_i||_2 over subjects."""
    A = np.asarray(D).reshape(np.asarray(D).shape[0], -1)          # (N, p)
    istar = int(np.argmax(np.linalg.norm(A, axis=1)))
    return np.abs(A[istar]), istar


def l2_bar(base_mech):
    """Wrap a frozen harness mechanism so it uses the L2-selected bar instead of the passed-in S.
    base_mech is e.g. ph.mech_supervisor_loo_corr(); the wrapper has the same (y, D, S, **kw) signature,
    so evaluate/sweep/_worlds drive it as an ordinary candidate."""
    def mechanism(y, D, S, **kw):
        return base_mech(y, D, l2_selected_bar(D)[0].reshape(S.shape), **kw)
    return mechanism


def selected_subject_distribution(source, pipeline, n_patches=400, N=None, seed=0):
    """Tally i* = argmax_i ||D_i||_2 over many fresh patches (echoes A's 'single extreme subjects')."""
    import privacy_harness as ph
    rng = np.random.default_rng(seed); N = N or source.N
    counts = np.zeros(N, int); gaps = []
    for _ in range(n_patches):
        _, D, _ = ph.loo_artifacts(source.sample(N, rng), pipeline)
        _, istar = l2_selected_bar(D)
        counts[istar] += 1
        srt = np.sort(np.linalg.norm(D.reshape(N, -1), axis=1))[::-1]
        gaps.append(srt[0] / srt[1] - 1.0 if srt[1] > 0 else np.nan)
    pk = counts / counts.sum(); nz = pk[pk > 0]
    return {"counts": counts, "share_top": float(pk.max()),
            "entropy_bits": float(-(nz * np.log2(nz)).sum()), "max_entropy_bits": float(np.log2(N)),
            "norm_gap": float(np.nanmean(gaps))}
