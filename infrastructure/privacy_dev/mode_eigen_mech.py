"""
mode_eigen_mech.py — the mode-space L2 noise mechanism (handoff §4), the mode-space sibling of
l2_sensitivity's voxel-space L2 bar. Developed here for fast iteration; this is the exact code that
will be INLINED into notebook 6.4 §2, and later lifted next to l2_sensitivity.py when NB7 imports it.

Does NOT edit the frozen harness. Conforms to the frozen mechanism contract:
    mechanism(y, D, S, noise_power=None, subjects=None, **cfg) -> ph.NoiseModel
and returns a NoiseModel whose .sample(rng) yields (z, fell_back). The passed-in per-voxel bar S is
DELIBERATELY UNUSED: this mechanism computes its own bar in mode space.

KEY PROPERTY (the "brick"): a NATURAL draw (no rejection, k_check=0) has covariance exactly
    Cov(z) = scale^2 * Cov(LOO) = scale^2 * V diag(lambda) V^T,
because z = sum_m a_m V_m with a_m = scale*sqrt(lambda_m)*xi_m, xi ~ N(0,1) iid, and
Cov(LOO) = np.cov(D, rowvar=False) = V diag(lambda) V^T exactly (rank r = min(p, N-1)).

OOM discipline (§8): the mechanism NEVER forms a p x p object for sampling. It works in mode space
(dimension r = min(p, N-1) ~ 39) and assembles exactly ONE p-vector, for the winning draw only.
"""
import numpy as np


# ---------------------------------------------------------------------------
# core decomposition
# ---------------------------------------------------------------------------
def patch_modes(D, center=True):
    """Economy SVD of (centered) LOO perturbations D (N, p).

    Returns V (p, r), lam (r,) with lam_m = S_m^2/(N-1) = eigenvalues of Cov(LOO), r = min(p, N-1).
    V's columns are the covariance eigenmodes (variance-ordered), Vt[m] = V[:, m] = mode m.
    """
    A = np.asarray(D, float).reshape(np.asarray(D).shape[0], -1)       # (N, p)
    N = A.shape[0]
    Ac = A - A.mean(0, keepdims=True) if center else A
    # economy SVD: Ac = U S Vt, Vt is (r, p) with r = min(N, p)
    U, s, Vt = np.linalg.svd(Ac, full_matrices=False)
    lam = (s ** 2) / (N - 1)                                           # eigenvalues of Cov(LOO)
    # keep the genuine (rank <= N-1) modes; drop numerical-zero tail
    r_ceiling = min(A.shape[1], N - 1)
    V = Vt[:r_ceiling].T                                               # (p, r)
    lam = lam[:r_ceiling]
    return V, lam


def l2_selected_row(D):
    """i* = argmax_i ||D_i||_2 over subjects; returns (D_{i*} (raw p-vector), i*).
    Matches l2_sensitivity.l2_selected_bar's selection (basis-independent by Parseval)."""
    A = np.asarray(D, float).reshape(np.asarray(D).shape[0], -1)
    istar = int(np.argmax(np.linalg.norm(A, axis=1)))
    return A[istar].copy(), istar


def mode_space_bar(D, V):
    """Mode-space L2 bar b_m = |D_{i*} . V_m| for m = 1..r. Returns (b (r,), istar)."""
    d_istar, istar = l2_selected_row(D)
    b = np.abs(V.T @ d_istar)                                          # (r,)
    return b, istar


# ---------------------------------------------------------------------------
# mode-space tail-normal fallback (mode-space analog of ph._tail_normal)
# ---------------------------------------------------------------------------
def _tail_normal_modes(a, sd, b, unmet, rng):
    """In-place-style tail resample of the UNMET modes so each clears its bar.
    For mode m in `unmet`: redraw |a_m| from the folded tail of N(0, sd_m^2) beyond b_m,
    random sign. Modes not in `unmet` keep their natural coefficient a_m."""
    from scipy.stats import norm
    a = a.copy()
    idx = np.where(unmet)[0]
    good = idx[sd[idx] > 0]
    if good.size:
        alpha = norm.cdf(b[good] / sd[good])                          # P(|X| within bar) one-sided
        q = np.clip(alpha + (1 - alpha) * rng.random(good.size), None, 1 - 1e-12)
        mag = norm.ppf(q) * sd[good]
        sign = np.where(rng.random(good.size) < 0.5, 1.0, -1.0)
        a[good] = mag * sign
    # modes with sd==0 but positive bar cannot be satisfied; leave as-is (degenerate, flagged by caller)
    return a


# ---------------------------------------------------------------------------
# the mechanism
# ---------------------------------------------------------------------------
def mech_mode_eigen(y, D, S, noise_power=None, subjects=None,
                    k_noise=None, k_check=None, scale=None, epsilon=1.0,
                    max_draws=2000, chunk=256, center=True, keep_modes=False, **_ignored):
    """Mode-space L2 mechanism. Config rides in **cfg / mech_cfg:

        k_noise   : # modes that receive noise (default r). Modes m > k_noise get ZERO
                    (only when deliberately truncating noise).
        k_check   : rejection depth, # modes whose bar must be cleared (default r). Require k_check<=k_noise.
                    k_check=0 => no rejection => pure natural correlated Gaussian (the covariance-identity case).
        scale     : noise scale on each mode's natural SD: a_m = scale*sqrt(lam_m)*xi_m. Default 2/epsilon
                    (=2 at epsilon=1), mirroring the frozen supervisor's marginal SD = 2*loo_scale.
        epsilon   : only used to set the default scale = 2/epsilon.
        max_draws : rejection-sampler budget (high is cheap: each draw is O(r)).
        center    : center D before SVD (True; the covariance-identity is exact only when centered).
        keep_modes: attach (V, lam, istar, bar, scale) to the returned model for §2/§5 diagnostics.

    noise_power (float) => POWER-MATCH: rescale so total natural power trace == noise_power, i.e.
    scale^2 = noise_power / sum(lam_used). Honored so the mechanism never silently ignores it.
    """
    A = np.asarray(D, float).reshape(np.asarray(D).shape[0], -1)       # (N, p)
    p = A.shape[1]
    V, lam = patch_modes(A, center=center)                            # V (p, r), lam (r,)
    r = lam.size
    if scale is None:
        scale = 2.0 / epsilon
    k_noise = r if k_noise is None else int(min(k_noise, r))
    k_check = r if k_check is None else int(k_check)
    if k_check > k_noise:
        raise ValueError(f"k_check ({k_check}) must be <= k_noise ({k_noise})")
    k_check = min(k_check, k_noise)

    # mode-space bar for the modes that will be noised
    bar_full, istar = mode_space_bar(A, V)                            # (r,)
    b = bar_full[:k_noise]                                            # bars we might check (only 1..k_check used)

    # per-mode natural SD on the noised modes
    sd = scale * np.sqrt(np.clip(lam[:k_noise], 0, None))             # (k_noise,)

    # power-match: rescale 'scale' so total natural power == noise_power
    if noise_power is not None:
        tot = float(np.sum(sd ** 2))
        if tot > 0:
            fac = np.sqrt(noise_power / tot)
            scale = scale * fac
            sd = sd * fac

    Vk = V[:, :k_noise]                                               # (p, k_noise) assembly basis

    # Power reporting is intentionally dropped (per user): nominal_cov stays None so we NEVER form
    # p x p. The constructed covariance scale^2*V diag(lam) V^T is available in FACTORED form via
    # keep_modes=True (V, lam, sd, scale) -- all §2/§5 need -- without ever materializing p x p.
    nominal_cov = None

    draws_to_accept = []                                             # for the §3b budget curve

    def sampler(rng):
        # a_m = scale*sqrt(lam_m)*xi_m  (sd absorbs scale). k_check=0 => no rejection => natural draw.
        if k_check == 0:
            draws_to_accept.append(1)
            return Vk @ (rng.standard_normal(k_noise) * sd), False
        # CHUNKED short-circuit rejection: draw candidates in blocks, stop at the first accept.
        # Drawing in chunks consumes the SAME rng stream as one (max_draws, k_noise) block, so the
        # candidate sequence -- hence the accepted draw, draws_to_accept and fallback decision -- are
        # identical to a full-batch draw; only wasted draws past the winner are avoided (the handoff
        # time(D)=Σ min(draws,D)·per_draw cost model).
        drawn = 0; last = None
        while drawn < max_draws:
            bsz = min(chunk, max_draws - drawn)
            Acoef = rng.standard_normal((bsz, k_noise)) * sd[None, :]
            ok = np.all(np.abs(Acoef[:, :k_check]) >= b[:k_check], axis=1)
            if ok.any():
                t = int(np.argmax(ok))
                draws_to_accept.append(drawn + t + 1)
                return Vk @ Acoef[t], False
            drawn += bsz; last = Acoef
        # fallback: take a natural draw, tail-resample the unmet checked modes so they clear the bar
        draws_to_accept.append(max_draws + 1)                        # sentinel: exceeded budget
        a = last[0].copy()
        unmet = np.zeros(k_noise, bool)
        unmet[:k_check] = np.abs(a[:k_check]) < b[:k_check]
        a = _tail_normal_modes(a, sd, b, unmet, rng)
        return Vk @ a, True

    model = ph_NoiseModel(sampler, cov=None, nominal_cov=nominal_cov)
    model.draws_to_accept = draws_to_accept                          # exposed for the budget curve
    if keep_modes:
        model.modes = {"V": V, "lam": lam, "istar": istar, "bar": bar_full,
                       "scale": scale, "sd": sd, "k_noise": k_noise, "k_check": k_check, "r": r}
    return model


# import the frozen NoiseModel without touching the frozen module
from privacy_harness import NoiseModel as ph_NoiseModel
