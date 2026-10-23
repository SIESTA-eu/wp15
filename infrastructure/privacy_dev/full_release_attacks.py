"""
full_release_attacks.py — NEW module (additive), the attack layer for the full-release privacy
investigation (NB8). Built ON TOP of the frozen harness; edits NOTHING frozen.

Replaces the deprecated blended-LDA membership game (which estimated a p x p covariance from ~n/4
samples in a 6k-dim neighbourhood -- a p>>n pathology) with the principled, cheap attacks the
threat model actually supports:

  * known-background PROJECTION membership score  (primary)
        The harness threat model already gives the attacker the N-1 background AND the candidate
        target, so it knows g_in and g_out EXACTLY. The optimal 1-D test projects the released map
        onto the known influence direction Delta = g_in - g_out and thresholds. Advantage/threshold/
        CI are computed by REUSING the frozen ph._threshold_youden / ph._adv_at / ph._adv_ci on the
        1-D scores -- identical advantage semantics (0 = private, 1 = exposed), no new metric code,
        no dimensionality pathology, runs whole-brain. Orientation is fixed (IN scores higher by
        ||Delta||^2 > 0), so nothing is learned.

  * analytic PROJECTION oracle  (validation, k_check=0 only)
        With no rejection the noise is exactly N(0, scale^2 Cov(LOO)), so the projected score is
        Gaussian and advantage = 2 Phi( ||Delta||^2 / (2 sqrt(Delta^T Sigma Delta)) ) - 1, computed
        from the FACTORED covariance (never forms p x p). Validates the empirical projection attack.

  * reconstruction OUTLIER-DETECTABILITY  (supervisor's attack, additive)
        The frozen ph.reconstruction_attack gives the identifiability verdict + recon-advantage.
        This adds his "is the target still flaggable as an outlier?" question: reconstruct the
        target from the (mean) release and test it against the cohort by IQR / z-score.

Delta-support region helper (delta_support_region) replaces the arbitrary peak-voxel neighbourhood:
the attack region is the voxels carrying the top-energy of |Delta| (default 99%).
"""
import numpy as np
from scipy.stats import norm
import privacy_harness as ph


# ---------------------------------------------------------------------------
# membership — known-background projection score  (PRIMARY)
# ---------------------------------------------------------------------------
def projection_membership(g_in, g_out, m_in, m_out, n_trials, rng, batch=True):
    """1-D membership attack: project the release onto the KNOWN influence direction and threshold.

    g_in, g_out : clean statistic over the attack voxels WITH / WITHOUT the target (the attacker
                  knows both exactly).
    m_in, m_out : noise models for the two worlds, each exposing .sample(rng) -> noise vector of the
                  same length as g_in (a frozen NoiseModel for a single patch, or a
                  tiling.BlendedReleaseNoise for the blended release).
    Returns {advantage, adv_ci, delta_norm, fallback_in, fallback_out}. Mirrors the structure of
    ph.empirical_advantage (same split / threshold / held-out evaluation) but with a FIXED 1-D
    projection instead of a learned LDA direction, so the frozen advantage helpers apply unchanged.
    """
    g_in = np.asarray(g_in, float).reshape(-1); g_out = np.asarray(g_out, float).reshape(-1)
    Delta = g_in - g_out
    half = n_trials // 2
    if batch and hasattr(m_out, "sample_batch") and hasattr(m_in, "sample_batch"):
        # DIRECT batched path: one big draw per world instead of a per-trial python loop.
        s_out = (g_out[None, :] + m_out.sample_batch(half, rng)) @ Delta
        s_in  = (g_in[None, :]  + m_in.sample_batch(half, rng))  @ Delta
    else:
        s_out = np.array([Delta @ (g_out + np.asarray(m_out.sample(rng)).reshape(-1)) for _ in range(half)])
        s_in  = np.array([Delta @ (g_in  + np.asarray(m_in.sample(rng)).reshape(-1))  for _ in range(half)])
    X = np.concatenate([s_out, s_in]); yb = np.r_[np.zeros(half), np.ones(half)]
    idx = rng.permutation(len(X)); X, yb = X[idx], yb[idx]; cut = len(X) // 2
    thr = ph._threshold_youden(X[:cut], yb[:cut])
    adv = ph._adv_at(X[cut:], yb[cut:], thr)
    ci = ph._adv_ci(X[cut:], yb[cut:], thr)
    return {"advantage": adv, "adv_ci": ci, "delta_norm": float(np.linalg.norm(Delta)),
            "fallback_in": float(getattr(m_in, "fallback_rate", 0.0)),
            "fallback_out": float(getattr(m_out, "fallback_rate", 0.0))}


def analytic_projection_advantage(g_in, g_out, modes):
    """Oracle for the natural-draw case (k_check=0): the projection-attack advantage under the exact
    Gaussian noise N(0, scale^2 Cov(LOO)). `modes` is the dict from
    me.mech_mode_eigen(..., keep_modes=True).modes for the IN world. Uses the FACTORED covariance
    Sigma = Vk diag(sd^2) Vk^T, so Delta^T Sigma Delta = sum_m sd_m^2 (Delta . Vk_m)^2 -- never forms
    p x p. advantage = 2 Phi( ||Delta||^2 / (2 sqrt(Delta^T Sigma Delta)) ) - 1."""
    Delta = np.asarray(g_in, float).reshape(-1) - np.asarray(g_out, float).reshape(-1)
    V = np.asarray(modes["V"]); sd = np.asarray(modes["sd"]).reshape(-1); k = int(modes["k_noise"])
    Vk = V[:, :k]
    proj = Vk.T @ Delta                       # (k,)
    var_s = float(np.sum((sd ** 2) * (proj ** 2)))   # Delta^T Sigma Delta
    sep = float(Delta @ Delta)                       # ||Delta||^2
    if var_s <= 0:
        return 1.0 if sep > 0 else 0.0
    return float(2 * norm.cdf(sep / (2 * np.sqrt(var_s))) - 1)


# ---------------------------------------------------------------------------
# reconstruction — outlier-detectability  (supervisor's attack, additive)
# ---------------------------------------------------------------------------
def _outlier_flags(feat, values, z_thresh=3.0):
    """Return (iqr_flag, z_flag) for `values` against the reference feature distribution `feat`
    (both are 1-D arrays of a per-subject scalar). Upper-fence IQR test + two-sided z."""
    q1, q3 = np.percentile(feat, 25), np.percentile(feat, 75)
    iqr = q3 - q1; upper = q3 + 1.5 * iqr; lower = q1 - 1.5 * iqr
    mu, sd = feat.mean(), feat.std() + 1e-12
    v = np.atleast_1d(values)
    iqr_flag = (v > upper) | (v < lower)
    z_flag = np.abs((v - mu) / sd) > z_thresh
    return iqr_flag, z_flag


def outlier_detectability(background_vox, target_vox, N, noise_model, rng, n_rel=200, z_thresh=3.0):
    """Supervisor-style: can the attacker still FLAG the target as an outlier after reconstruction?

    For the MEAN release (identifiable), the attacker who knows the N-1 background recovers the
    target voxelwise from a release R = global_mean + noise by  x_hat = N*R - sum(background), i.e.
    x_hat = target + N*noise. We measure, over releases, how often x_hat is flagged as an outlier
    relative to the cohort. Per-subject feature = L2 distance from the cohort median (over the attack
    voxels). Compare the CLEAN flag (noise-free target) to the PRIVATE flag RATE (noised releases):
    privacy is good when the noise pulls the private flag rate well below the clean flag.

    background_vox : (N-1, p) the known background over the attack voxels.
    target_vox     : (p,)     the target over the attack voxels.
    N              : cohort size (so the mean inversion scale is correct).
    noise_model    : exposes .sample(rng) -> noise vector of length p (single-patch NoiseModel or a
                     tiling.BlendedReleaseNoise cropped to the attack voxels).
    """
    background_vox = np.asarray(background_vox, float); target_vox = np.asarray(target_vox, float).reshape(-1)
    cohort = np.vstack([background_vox, target_vox[None, :]])        # (N, p)
    med = np.median(cohort, axis=0)
    feat = np.linalg.norm(cohort - med[None, :], axis=1)            # per-subject distance-from-median
    # clean (noise-free) flag for the true target
    clean_iqr, clean_z = _outlier_flags(feat, np.linalg.norm(target_vox - med), z_thresh)
    # private flags over noised reconstructions
    iqr_hits = z_hits = 0
    for _ in range(n_rel):
        z = np.asarray(noise_model.sample(rng)).reshape(-1)
        x_hat = target_vox + N * z
        f_hat = np.linalg.norm(x_hat - med)
        i_flag, z_flag = _outlier_flags(feat, f_hat, z_thresh)
        iqr_hits += int(bool(i_flag)); z_hits += int(bool(z_flag))
    return {"clean_iqr_flag": bool(clean_iqr), "clean_z_flag": bool(clean_z),
            "private_iqr_rate": iqr_hits / n_rel, "private_z_rate": z_hits / n_rel,
            "n_rel": n_rel, "fallback": float(getattr(noise_model, "fallback_rate", 0.0))}


# ---------------------------------------------------------------------------
# attack region — support of Delta  (replaces the arbitrary peak-voxel box)
# ---------------------------------------------------------------------------
def delta_support_region(g_in, g_out, mask, half=8, pad=0):
    """A bounded box around the PEAK-|Delta|^2 voxel (Delta = g_in - g_out), of half-width `half` per
    axis, intersected with `mask`. This is the compute-bounded attack region for the blended game.

    Why a bounded box, not the top-k voxels: for a DIFFUSE target (an arbitrary real subject) the top-|
    Delta|^2 voxels are SCATTERED across the whole brain, so their bounding box is the whole brain and
    the blended model tiles ~10^4 patches (the overnight-runtime trap). A fixed box around the peak of
    influence bounds the patch count DETERMINISTICALLY (~(2*half/stride)^3), independent of how diffuse
    Delta is. The projection score has no dimensionality penalty, so restricting to a local box is cheap
    and sound; it captures the strongest contiguous chunk of the target's influence. For a concentrated
    target (a localized perturbation) the box captures essentially all of it. Widen `half` for a more
    complete (slower) attack. Returns (slice_tuple, keep_mask), keep_mask = mask within the box."""
    mask = np.asarray(mask).astype(bool)
    e = ((np.asarray(g_in, float) - np.asarray(g_out, float)) ** 2) * mask
    if e.sum() <= 0:
        peak = np.array([s // 2 for s in mask.shape])
    else:
        peak = np.array(np.unravel_index(int(np.argmax(e)), mask.shape))
    lo = np.maximum(peak - half - pad, 0)
    hi = np.minimum(peak + half + 1 + pad, np.array(mask.shape))
    sl = tuple(slice(int(l), int(h)) for l, h in zip(lo, hi))
    keep = np.zeros_like(mask); keep[sl] = mask[sl]
    return sl, keep


def region_energy_coverage(g_in, g_out, mask, keep):
    """Fraction of ||Delta||^2 captured inside the attack region `keep`, relative to the whole in-mask
    brain. ~1.0 => the boxed attacker is ~ the full-brain attacker (trust the number); low => the box
    discards signal, so a low advantage may OVERSTATE privacy. Report this alongside every blended
    advantage so the approximation is measured, not hidden."""
    mask = np.asarray(mask).astype(bool); keep = np.asarray(keep).astype(bool)
    d2 = (np.asarray(g_in, float) - np.asarray(g_out, float)) ** 2
    tot = float(d2[mask].sum())
    return float(d2[keep].sum() / tot) if tot > 0 else 1.0
