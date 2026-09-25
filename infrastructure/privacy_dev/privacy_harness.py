"""
privacy_harness.py — mechanism- and dataset-agnostic privacy/utility/stability stress harness.

LAYERS
  BlockSource   : yields aligned subject blocks (N x p). Synthetic or real (OASIS). The engine
                  is agnostic to which — swap the source, nothing else changes.
  mechanism     : black box  mechanism(y, D, S, noise_power=..., **cfg) -> NoiseModel
  membership game (remove-one adjacency, conservative attacker): fixed known background of N-1,
                  a coin puts a target IN/OUT, attacker guesses from the released block.

METRICS
  Privacy : membership advantage = TPR - FPR of a held-out LINEAR LDA membership attacker (threshold
            fit on train, evaluated held-out) + bootstrap CI. 0 = no evidence of leakage, 1 = exposed.
            LOWER BOUND on true leakage (an attack proves leakage; only a proof proves safety).
  Utility : a PANEL, not one number —
              rel_mse            : pixelwise magnitude of distortion (0 = identical)
              neighbour_corr_gap : |spatial neighbour-corr(true) - mean neighbour-corr(released)|
                                   (THE imaging axis MSE is blind to; iid noise inflates it)
              spearman           : rank/ordering preservation (1 = order intact)
              bias_norm          : ||E[released] - true|| / ||true||  (rejection can bias)
  Oracle  : analytic Mahalanobis advantage, exact only for linear pipeline + Gaussian mechanism;
            validates the empirical attacker.

"noise_power" = total noise variance summed over voxels. It is a fair-comparison knob, NOT epsilon
and NOT a DP guarantee. Matching it across mechanisms isolates noise SHAPE from noise AMOUNT.
"""
import numpy as np
from scipy.stats import norm, rankdata

# ===========================================================================
# 1. Block sources
# ===========================================================================
# The ENGINE is dataset-agnostic: it only calls source.sample(n, rng) -> (n, p).
# The agnostic boundary is drawn here:
#   * ArrayBlockSource  — the ONE generic source. Runs on ANY already-aligned dataset,
#                         given a (subjects, X, Y, Z) volume array + brain mask. No per-
#                         dataset code lives here. This is the plug-and-play path.
#   * loaders (load_*)  — tiny, honestly dataset-specific functions whose ONLY job is to
#                         turn a particular dataset into (volumes, mask). Quarantined here
#                         so the messy, irreducibly per-dataset part (finding/aligning files)
#                         never touches the engine.
#   * SyntheticBlockSource — generates rather than loads, so it is legitimately its own class.
#
# CONTRACT: ASSUMES volumes are already ALIGNED to a common space (voxel v = same anatomical
# location across subjects). The harness CANNOT verify registration from arrays alone; it only
# checks STRUCTURAL preconditions (shape, mask compatibility, finiteness, usable variance) and
# refuses loudly on those. Unaligned-but-structurally-valid input yields meaningless numbers.

class BlockSource:
    """Interface the engine depends on: .block_shape, .p, .N, .sample(n, rng) -> (n, p)."""
    block_shape = None; p = None; N = None
    def sample(self, n, rng): raise NotImplementedError


class ArrayBlockSource(BlockSource):
    """Generic source over an already-aligned (subjects, X, Y, Z) array. Dataset-agnostic:
    the same code runs on OASIS, ADNI, a BIDS folder, or your platform's volumes — anything
    that has been reduced to aligned volumes + a mask. Picks one in-brain block and samples
    n subjects at it."""
    def __init__(self, volumes, mask=None, block_shape=(4, 4, 4), N=60, seed=0):
        volumes = np.asarray(volumes, dtype=np.float64)
        _check_aligned(volumes, mask, block_shape)
        if mask is None:
            mask = np.isfinite(volumes).all(0) & (volumes != 0).any(0)
        self.block_shape = tuple(block_shape); self.p = int(np.prod(block_shape))
        self._pool = _extract_block(volumes, mask, block_shape, seed)   # (M, p) real subjects
        self.M = self._pool.shape[0]
        self.N = min(N, self.M)

    def sample(self, n, rng):
        idx = rng.choice(self.M, size=n, replace=(n > self.M))
        return self._pool[idx].copy()


class TabularSource(BlockSource):
    """Non-spatial data (e.g. bivariate weight/height): p columns, no spatial neighbours.
    Lets the harness ingest tabular datasets through the same seam. block_shape=(p,)."""
    def __init__(self, table, N=None):
        table = np.asarray(table, float)
        if table.ndim != 2:
            raise ValueError(f"table must be (subjects, p); got {table.shape}")
        self._pool = table; self.M = table.shape[0]; self.p = table.shape[1]
        self.block_shape = (self.p,); self.N = N or self.M
    def sample(self, n, rng):
        return self._pool[rng.choice(self.M, size=n, replace=(n > self.M))].copy()


class GeneratedPopulationSource(BlockSource):
    """CHARACTERIZATION source (not real data): draws FRESH subjects from a chosen population each
    call, so a sweep can vary the population's correlation / spread. Mirrors the old Monte-Carlo's
    'generate data across regimes' axis. Label results as synthetic characterization, not empirical."""
    def __init__(self, N=60, p=2, correlation=0.6, base_std=1.0):
        self.N = N; self.p = p; self.block_shape = (p,)
        C = np.full((p, p), correlation, float); np.fill_diagonal(C, 1.0)
        self._L = np.linalg.cholesky(C * base_std**2 + 1e-10 * np.eye(p))
    def sample(self, n, rng):
        return rng.standard_normal((n, self.p)) @ self._L.T


class SyntheticBlockSource(BlockSource):
    """Generates aligned blocks from a known spatial covariance (no files to load)."""
    def __init__(self, N=60, block_shape=(4, 4, 4), spatial_corr=0.6, base_std=1.0):
        self.N = N; self.block_shape = tuple(block_shape); self.p = int(np.prod(block_shape))
        self.Sigma_x = _spatial_cov(block_shape, spatial_corr, base_std)
        self._L = np.linalg.cholesky(self.Sigma_x + 1e-10 * np.eye(self.p))
    def sample(self, n, rng):
        return rng.standard_normal((n, self.p)) @ self._L.T


# ---- dataset-specific loaders: (dataset) -> (volumes, mask). Small and isolated. ----
def load_oasis(n=100, data_dir=None):
    """OASIS gray-matter maps -> (subjects, X, Y, Z) float array + brain mask."""
    from nilearn import datasets
    import nibabel as nib
    oasis = datasets.fetch_oasis_vbm(n_subjects=n, data_dir=data_dir)
    vols = np.stack([nib.load(p).get_fdata(dtype=np.float32) for p in oasis.gray_matter_maps])
    mask = np.isfinite(vols).all(0) & (vols != 0).any(0)
    return vols.astype(np.float64), mask

def load_nifti_dir(path, pattern="*.nii*"):
    """A folder of ALREADY-ALIGNED NIfTIs -> (subjects, X, Y, Z) + mask.
    Does NOT register; alignment is the caller's responsibility (contract of the harness)."""
    import glob, os, nibabel as nib
    files = sorted(glob.glob(os.path.join(path, pattern)))
    if not files:
        raise FileNotFoundError(f"no NIfTIs matching {pattern} in {path}")
    vols = np.stack([nib.load(f).get_fdata(dtype=np.float32) for f in files])
    mask = np.isfinite(vols).all(0) & (vols != 0).any(0)
    return vols.astype(np.float64), mask

# Convenience: OASIS straight to a source in one line (loader + generic source).
def oasis_source(n=100, block_shape=(4, 4, 4), N=60, seed=0, data_dir=None):
    vols, mask = load_oasis(n=n, data_dir=data_dir)
    return ArrayBlockSource(vols, mask, block_shape=block_shape, N=N, seed=seed)


# ---- shared internals ----
def _check_aligned(volumes, mask, block_shape):
    if volumes.ndim != 4:
        raise ValueError(f"volumes must be (subjects, X, Y, Z); got shape {volumes.shape}")
    if volumes.shape[0] < 3:
        raise ValueError("need at least 3 subjects")
    if not np.isfinite(volumes).all():
        # allowed (mask handles it) but warn-by-contract: NaNs outside mask are fine
        pass
    if mask is not None and tuple(mask.shape) != tuple(volumes.shape[1:]):
        raise ValueError(f"mask shape {mask.shape} != volume shape {volumes.shape[1:]}")
    if any(b > s for b, s in zip(block_shape, volumes.shape[1:])):
        raise ValueError(f"block_shape {block_shape} does not fit in volume {volumes.shape[1:]}")

def _spatial_cov(shape, corr, std):
    coords = np.array(list(np.ndindex(*shape)), float)
    d = np.linalg.norm(coords[:, None, :] - coords[None, :, :], axis=-1)
    return (corr ** d) * (std ** 2)

def _extract_block(vols, mask, block_shape, seed, tries=4000):
    rng = np.random.default_rng(seed)
    X, Y, Z = mask.shape; bx, by, bz = block_shape
    for _ in range(tries):
        x = rng.integers(0, X - bx + 1); y = rng.integers(0, Y - by + 1); z = rng.integers(0, Z - bz + 1)
        if mask[x:x+bx, y:y+by, z:z+bz].all():
            blk = vols[:, x:x+bx, y:y+by, z:z+bz].reshape(vols.shape[0], -1)
            if np.isfinite(blk).all() and (blk.std(0) > 0).all():
                return blk.astype(np.float64)
    raise RuntimeError("no fully-in-brain block with variance found; try a smaller block_shape")


# ===========================================================================
# 2. Targets / pipelines / LOO
# ===========================================================================
def target_ksigma(subjects, k):
    return subjects.mean(0) + k * subjects.std(0)

def pipeline_mean(stack):     return stack.mean(0)
def pipeline_median(stack):   return np.median(stack, 0)   # nonlinear; LOO can be locally degenerate
def pipeline_variance(stack): return stack.var(0)

def loo_artifacts(stack, pipeline):
    y = pipeline(stack); n = stack.shape[0]; D = np.empty_like(stack)
    for i in range(n):
        D[i] = pipeline(np.delete(stack, i, axis=0)) - y
    return y, D, np.abs(D).max(0)

# ===========================================================================
# 3. Mechanisms  (black-box seam)
# ===========================================================================
class NoiseModel:
    """Wraps a sampler. The sampler may return z, or (z, fell_back) to report a fallback event;
    the model accumulates the fallback rate over all draws (a mechanism-internal diagnostic the
    privacy/utility metrics don't otherwise see).
      cov         : the noise covariance IFF the noise is exactly Gaussian (enables the analytic
                    Mahalanobis check). None for rejection/fallback mechanisms (non-Gaussian).
      nominal_cov : the covariance the mechanism CONSTRUCTED, for inspection/stability diagnostics,
                    regardless of whether sampling is Gaussian. Not used by the attacker."""
    def __init__(self, sampler, cov=None, nominal_cov=None):
        self._s = sampler; self.cov = cov
        self.nominal_cov = nominal_cov if nominal_cov is not None else cov
        self.n_samples = 0; self.n_fallback = 0
    def sample(self, rng):
        out = self._s(rng)
        z, fb = out if isinstance(out, tuple) else (out, False)
        self.n_samples += 1; self.n_fallback += int(fb)
        return z
    @property
    def fallback_rate(self):
        return self.n_fallback / self.n_samples if self.n_samples else 0.0

def mech_iid(y, D, S, noise_power=None, **cfg):
    p = y.size
    var = (noise_power / p) if noise_power is not None else float((S.reshape(-1) ** 2).mean())
    return NoiseModel(lambda rng: rng.standard_normal(p) * np.sqrt(var), cov=var * np.eye(p))

def _cov_from_loo(D, noise_power, p):
    C = np.cov(D.reshape(D.shape[0], -1), rowvar=False) + 1e-10 * np.eye(p)
    if noise_power is not None:
        C = C * (noise_power / np.trace(C))
    return C

def mech_cov_gaussian(y, D, S, noise_power=None, **cfg):
    p = y.size; C = _cov_from_loo(D, noise_power, p)
    L = np.linalg.cholesky(C + 1e-12 * np.eye(p))
    return NoiseModel(lambda rng: L @ rng.standard_normal(p), cov=C)

def mech_cov_rejection(y, D, S, noise_power=None, max_draws=2000, **cfg):
    p = y.size; C = _cov_from_loo(D, noise_power, p)
    L = np.linalg.cholesky(C + 1e-12 * np.eye(p)); s = S.reshape(-1); sd = np.sqrt(np.diag(C))
    def sampler(rng):
        Z = rng.standard_normal((max_draws, p)) @ L.T
        ok = np.all(np.abs(Z) >= s[None, :], axis=1)
        if ok.any():
            return Z[np.argmax(ok)], False
        return _tail_normal(sd, s, rng), True        # fell back -> now flagged (was silently unreported)
    return NoiseModel(sampler, cov=None, nominal_cov=C)

def _cov2corr(C):
    d = np.sqrt(np.clip(np.diag(C), 1e-300, None))
    return C / np.outer(d, d)

def make_covsource_mechanism(cov_source="loo", scale_rule="supervisor", epsilon=1.0,
                             ddof=1, max_draws=2000):
    """The reference mechanism as a harness mechanism, with covariance SOURCE and noise SCALE as
    two ORTHOGONAL axes (do not conflate them):

      cov_source : where the CORRELATION structure comes from
                   'data' -> Cov(subject data)      'loo' -> Cov(LOO perturbations)
      scale_rule : how much noise, and how the marginals are set
                   'supervisor' -> rescale the chosen correlation to marginal SD = 2*loo_scale,
                                   loo_scale_j = SD(D[:,j], ddof)/epsilon. Marginals are then
                                   IDENTICAL across sources, so 'data' vs 'loo' differ ONLY in
                                   correlation (exact magnitude match; fixes the old ddof mismatch).
                   'raw'        -> use the chosen covariance DIRECTLY (no factor 2, no epsilon,
                                   no rescale). For cov_source='loo' this is Cov(LOO) itself.

    The three variants discussed:
        supervisor_data_corr = (cov_source='data', scale_rule='supervisor')
        supervisor_loo_corr  = (cov_source='loo',  scale_rule='supervisor')
        direct_loo_cov       = (cov_source='loo',  scale_rule='raw')

    noise_power: None -> intrinsic scale (as defined above). A float -> POWER-MATCHED: the final
    covariance is rescaled to trace == noise_power (a fair-comparison knob; NOT epsilon, NOT a DP
    guarantee). Honored here too, so no mechanism silently ignores it.

    ddof is explicit and consistent (default 1, matching np.cov). This deviates from the literal
    reference, which mixed np.std (ddof=0) with np.cov (ddof=1); documented, not silently 'fixed'
    in Baseline A (which is untouched)."""
    if scale_rule not in ("supervisor", "raw"):
        raise ValueError("scale_rule must be 'supervisor' or 'raw'")
    if cov_source not in ("data", "loo"):
        raise ValueError("cov_source must be 'data' or 'loo'")

    def mechanism(y, D, S, noise_power=None, subjects=None, **cfg):
        p = y.size
        A = D.reshape(D.shape[0], -1)                       # LOO perturbations (N, p)
        s = S.reshape(-1)
        # correlation source
        if cov_source == "loo":
            C_src = np.atleast_2d(np.cov(A, rowvar=False))
        else:
            if subjects is None:
                raise ValueError("cov_source='data' requires the raw subjects")
            C_src = np.atleast_2d(np.cov(subjects, rowvar=False))
        # scale rule
        if scale_rule == "supervisor":
            loo_scale = A.std(0, ddof=ddof) / epsilon
            target_sd = 2.0 * loo_scale
            C = np.diag(target_sd) @ _cov2corr(C_src) @ np.diag(target_sd)
        else:                                               # 'raw': use the covariance as-is
            C = C_src.copy()
        # optional power-matching (overrides intrinsic scale, keeps the shape)
        if noise_power is not None:
            tr = np.trace(C)
            if tr > 0:
                C = C * (noise_power / tr)
        # regularization (numerical, NOT privacy calibration)
        if np.min(np.linalg.eigvalsh(C)) <= 1e-10:
            C = C + np.eye(p) * 1e-8
        L = np.linalg.cholesky(C + 1e-12 * np.eye(p)); sd = np.sqrt(np.diag(C))
        def sampler(rng):
            Z = rng.standard_normal((max_draws, p)) @ L.T
            ok = np.all(np.abs(Z) >= s[None, :], axis=1)
            if ok.any():
                return Z[np.argmax(ok)], False
            return _tail_normal(sd, s, rng), True           # fell back -> flagged
        return NoiseModel(sampler, cov=None, nominal_cov=C)
    return mechanism

# named convenience constructors for the three variants
def mech_supervisor_data_corr(epsilon=1.0, **kw): return make_covsource_mechanism("data", "supervisor", epsilon, **kw)
def mech_supervisor_loo_corr(epsilon=1.0, **kw):  return make_covsource_mechanism("loo",  "supervisor", epsilon, **kw)
def mech_direct_loo_cov(**kw):                     return make_covsource_mechanism("loo",  "raw", **kw)

def _tail_normal(sd, s, rng):
    p = len(s); z = np.zeros(p); good = (s > 0) & (sd > 0)
    if good.any():
        a = norm.cdf(s[good] / sd[good])
        q = np.clip(a + (1 - a) * rng.random(good.sum()), None, 1 - 1e-12)
        z[good] = norm.ppf(q) * sd[good] * np.where(rng.random(good.sum()) < .5, 1, -1)
    return z

# ===========================================================================
# 4. Membership game + attackers
# ===========================================================================
def _worlds(source, N, pipeline, background, target, noise_power, mechanism, mech_cfg):
    bs = source.block_shape
    stack_in  = np.vstack([background, target[None, :]]).reshape(N, *bs)
    stack_out = background.reshape(N - 1, *bs)
    g_in  = pipeline(stack_in).reshape(-1)
    g_out = pipeline(stack_out).reshape(-1)
    subj_in  = stack_in.reshape(N, -1)        # raw subjects (some mechanisms need Cov(data))
    subj_out = stack_out.reshape(N - 1, -1)
    m_in  = mechanism(*loo_artifacts(stack_in,  pipeline), noise_power=noise_power,
                      subjects=subj_in,  **mech_cfg)
    m_out = mechanism(*loo_artifacts(stack_out, pipeline), noise_power=noise_power,
                      subjects=subj_out, **mech_cfg)
    return g_in, g_out, m_in, m_out

def analytic_advantage(g_in, g_out, m_in, m_out, tol=1e-9):
    if m_in.cov is None or m_out.cov is None: return None
    if not np.allclose(m_in.cov, m_out.cov, atol=tol, rtol=1e-6): return None
    diff = g_in - g_out
    Delta = float(np.sqrt(diff @ np.linalg.solve(m_in.cov, diff)))
    return 2 * norm.cdf(Delta / 2) - 1

def empirical_advantage(g_in, g_out, m_in, m_out, n_trials, rng):
    half = n_trials // 2
    Xout = g_out[None, :] + np.array([m_out.sample(rng) for _ in range(half)])
    Xin  = g_in[None, :]  + np.array([m_in.sample(rng)  for _ in range(half)])
    X = np.vstack([Xout, Xin]); yb = np.r_[np.zeros(half), np.ones(half)]
    idx = rng.permutation(len(X)); X, yb = X[idx], yb[idx]; cut = len(X) // 2
    w = _lda_dir(X[:cut], yb[:cut])
    thr = _threshold_youden(X[:cut] @ w, yb[:cut])
    ste = X[cut:] @ w
    return {"advantage": _adv_at(ste, yb[cut:], thr), "adv_ci": _adv_ci(ste, yb[cut:], thr)}

def reconstruction_attack(source, N, pipeline, background, target, noise_power,
                          mechanism, mech_cfg, rng, n_rel=200):
    """Reconstruction (stronger than membership): recover the target's VALUES from the released output,
    given the known N-1 background. Honest only for statistics where the target is IDENTIFIABLE from
    the release (essentially linear pipelines, e.g. the mean). For non-identifiable statistics
    (variance, median: many subjects map to one output) it returns identifiable=False and a best-effort
    number that must NOT be read as precise. Reported as error vs a naive population-mean baseline;
    a LOWER BOUND on reconstruction risk (one attacker, not a proof)."""
    bs = source.block_shape
    stack_in = np.vstack([background, target[None, :]]).reshape(N, *bs)
    g_in = pipeline(stack_in).reshape(-1)
    m_in = mechanism(*loo_artifacts(stack_in, pipeline), noise_power=noise_power,
                     subjects=stack_in.reshape(N, -1), **mech_cfg)
    bg = background.reshape(N - 1, -1)

    # Identifiability: is the target a linear function of the (known) release? Test numerically —
    # does perturbing the target move the clean output linearly & invertibly?
    identifiable, invert = _linear_inverter(pipeline, bg, target, bs, N)

    errs, base_errs = [], []
    naive = bg.mean(0)                                   # baseline guess: population mean
    for _ in range(n_rel):
        released = g_in + m_in.sample(rng)
        x_hat = invert(released) if identifiable else naive
        errs.append(np.linalg.norm(x_hat - target))
        base_errs.append(np.linalg.norm(naive - target))
    err = float(np.mean(errs)); base = float(np.mean(base_errs))
    return {"recon_error": err, "recon_baseline_error": base,
            "recon_advantage": float(1 - err / base) if base > 0 else np.nan,
            "identifiable": bool(identifiable)}

def _linear_inverter(pipeline, bg, target, bs, N, tol=1e-6):
    """If stat(bg + x) is affine and invertible in x, return (True, inverse_map(released)->x_hat)."""
    p = target.size
    def clean(x):
        return pipeline(np.vstack([bg, x[None, :]]).reshape(N, *bs)).reshape(-1)
    y0 = clean(np.zeros(p)); J = np.zeros((p, p))
    for j in range(p):                                    # Jacobian by finite differences
        e = np.zeros(p); e[j] = 1.0
        J[:, j] = (clean(e) - y0)
    # linear check: prediction at target vs actual
    if np.linalg.norm(clean(target) - (y0 + J @ target)) > tol * (1 + np.linalg.norm(target)):
        return False, None
    sv = np.linalg.svd(J, compute_uv=False)               # invertible iff well-conditioned
    if sv.max() == 0 or sv.min() / sv.max() < tol:        # (det underflows in high dim; use cond)
        return False, None
    Jinv = np.linalg.inv(J)
    return True, (lambda released: Jinv @ (released - y0))

def _lda_dir(Xtr, ytr):
    m1, m0 = Xtr[ytr == 1].mean(0), Xtr[ytr == 0].mean(0)
    Sw = np.cov(Xtr.T) + 1e-6 * np.eye(Xtr.shape[1])
    return np.linalg.solve(Sw, m1 - m0)

def _threshold_youden(s, y):
    o = np.argsort(s)[::-1]; ys = y[o]; P, Nn = y.sum(), len(y) - y.sum()
    return s[o][np.argmax(np.cumsum(ys)/P - np.cumsum(1-ys)/Nn)]

def _adv_at(s, y, thr):
    pred = s >= thr; P, Nn = y.sum(), len(y) - y.sum()
    return float(((pred & (y == 1)).sum())/P - ((pred & (y == 0)).sum())/Nn)

def _adv_ci(s, y, thr, B=150, seed=0):
    rng = np.random.default_rng(seed); n = len(y)
    a = [_adv_at(s[i], y[i], thr) for i in (rng.integers(0, n, n) for _ in range(B))]
    return (float(np.quantile(a, .025)), float(np.quantile(a, .975)))

# ===========================================================================
# 5. Utility panel  (spatial structure is the headline, not just MSE)
# ===========================================================================
def _neighbour_corr(vec, shape):
    v = np.asarray(vec).reshape(shape); cs = []
    for ax in range(v.ndim):
        a = np.moveaxis(v, ax, 0); x = a[:-1].reshape(-1); y = a[1:].reshape(-1)
        if x.std() > 1e-12 and y.std() > 1e-12:
            cs.append(np.corrcoef(x, y)[0, 1])
    return float(np.mean(cs)) if cs else np.nan

def utility_panel(g_true, noise_model, shape, rng, n_rel=200):
    t = g_true
    rels = np.array([t + noise_model.sample(rng) for _ in range(n_rel)])
    rel_mse = float(np.mean((rels - t) ** 2) / (np.mean(t ** 2) + 1e-12))
    spatial = len(shape) >= 2 and all(d >= 2 for d in shape)   # neighbour-corr only meaningful spatially
    if spatial:
        nc_true = _neighbour_corr(t, shape)
        nc_rel  = float(np.nanmean([_neighbour_corr(r, shape) for r in rels]))
    else:
        nc_true = nc_rel = np.nan
    spear = float(np.nanmean([_spearman(t, r) for r in rels]))
    bias_norm = float(np.linalg.norm(rels.mean(0) - t) / (np.linalg.norm(t) + 1e-12))
    return {"rel_mse": rel_mse, "neighbour_corr_true": nc_true,
            "neighbour_corr_released": nc_rel, "neighbour_corr_gap": abs(nc_true - nc_rel),
            "spearman": spear, "bias_norm": bias_norm}

def _spearman(a, b):
    ra, rb = rankdata(a), rankdata(b)
    if ra.std() < 1e-12 or rb.std() < 1e-12: return np.nan
    return np.corrcoef(ra, rb)[0, 1]

# ===========================================================================
# 6. evaluate one configuration  &  sweep driver
# ===========================================================================
def evaluate(source, pipeline, mechanism, mech_cfg=None, N=None, k=2.0, noise_power=None,
             n_trials=4000, n_rel=200, seed=0, reconstruction=False, target_mode="k_sigma"):
    """target_mode: 'k_sigma' = synthetic mean + k*SD target (explicit adversarial STRESS test;
    elevated in every dimension at once, unrealistically extreme in high-p). 'actual' = a real
    held-out subject, guaranteed NOT present in the known N-1 background. Recorded in the output."""
    rng = np.random.default_rng(seed); mech_cfg = mech_cfg or {}
    N = N or source.N; bs = source.block_shape
    pool = source.sample(N, rng)
    background = source.sample(N - 1, rng)
    if target_mode == "k_sigma":
        target = target_ksigma(pool, k)
    elif target_mode == "actual":
        target = pool[0].copy()                 # a real subject; background is an independent draw
        # guarantee the target is not duplicated in its known background
        if np.any(np.all(np.isclose(background, target[None, :]), axis=1)):
            background = background + 0.0        # (independent draws; collision is measure-zero, but)
            mask = ~np.all(np.isclose(background, target[None, :]), axis=1)
            if not mask.all():
                extra = source.sample(int((~mask).sum()) + 5, rng)
                background = np.vstack([background[mask], extra])[:N - 1]
    else:
        raise ValueError("target_mode must be 'k_sigma' or 'actual'")
    # noise_power is passed THROUGH: None => each mechanism's intrinsic scale; float => power-matched
    # (trace == noise_power) for every mechanism. evaluate does NOT invent a scale.
    g_in, g_out, m_in, m_out = _worlds(source, N, pipeline, background, target,
                                       noise_power, mechanism, mech_cfg)
    emp = empirical_advantage(g_in, g_out, m_in, m_out, n_trials, rng)
    ana = analytic_advantage(g_in, g_out, m_in, m_out)
    util = utility_panel(g_in, m_in, bs, rng, n_rel=n_rel)
    realized_power = (noise_power if noise_power is not None
                      else (float(np.trace(np.atleast_2d(m_in.nominal_cov)))
                            if m_in.nominal_cov is not None else None))
    out = {"N": N, "k": k, "target_mode": target_mode, "noise_power": realized_power,
           "empirical_adv": emp["advantage"], "adv_ci_lo": emp["adv_ci"][0],
           "adv_ci_hi": emp["adv_ci"][1], "analytic_adv": ana,
           "fallback_rate": m_in.fallback_rate, **util}
    if reconstruction:
        rec = reconstruction_attack(source, N, pipeline, background, target, noise_power,
                                    mechanism, mech_cfg, rng, n_rel=n_rel)
        out.update({"recon_advantage": rec["recon_advantage"],
                    "recon_identifiable": rec["identifiable"], "recon_error": rec["recon_error"]})
    return out

def sweep(source, pipeline, mechanisms, N_list=None, power_scales=None, k=2.0,
          n_trials=3000, n_rel=150, seeds=(1, 2, 3), mech_cfgs=None):
    """Grid over mechanism x N x power x SEED on one source. Returns the tidy per-seed dataframe
    (long form). Use aggregate_sweep() to collapse seeds into mean +/- CI.

    power_scales=None  -> run once per config with noise_power=None, i.e. each mechanism uses its
                          OWN intrinsic scale (correct for the covariance-source mechanisms, which
                          are not power-matched). Pass a tuple (e.g. (10,30)) to sweep noise power
                          relative to the iid budget instead (for iid-vs-Gaussian comparisons)."""
    import pandas as pd
    mech_cfgs = mech_cfgs or {}
    N_list = N_list or [source.N]
    rows = []
    for N in N_list:
        if power_scales is None:
            scales, base = [None], None
        else:
            base = evaluate(source, pipeline, mech_iid, N=N, k=k,
                            n_trials=500, n_rel=20, seed=0)["noise_power"]
            scales = list(power_scales)
        for name, mech in mechanisms.items():
            for sc in scales:
                for sd in seeds:
                    npow = None if sc is None else base * sc
                    r = evaluate(source, pipeline, mech, mech_cfg=mech_cfgs.get(name, {}),
                                 N=N, k=k, noise_power=npow, n_trials=n_trials,
                                 n_rel=n_rel, seed=sd)
                    rows.append({"mechanism": name, "power_x": sc, "seed": sd, **r})
    return pd.DataFrame(rows)


def aggregate_sweep(df, group_cols=("mechanism",),
                    metrics=("empirical_adv", "fallback_rate", "rel_mse")):
    """Collapse the per-seed sweep into mean +/- 95% CI across seeds (captures data-draw +
    attacker variability, not just the within-run bootstrap). CI = mean +/- 1.96*SEM."""
    import pandas as pd
    group_cols = list(group_cols)
    out = []
    for keys, sub in df.groupby(group_cols):
        keys = keys if isinstance(keys, tuple) else (keys,)
        row = dict(zip(group_cols, keys)); row["n_seeds"] = int(len(sub))
        for m in metrics:
            v = sub[m].dropna().to_numpy(float)
            if len(v) == 0:
                row[f"{m}_mean"] = np.nan; row[f"{m}_lo"] = row[f"{m}_hi"] = np.nan; continue
            mean = float(v.mean())
            sem = float(v.std(ddof=1) / np.sqrt(len(v))) if len(v) > 1 else 0.0
            row[f"{m}_mean"] = mean; row[f"{m}_sem"] = sem
            row[f"{m}_lo"] = mean - 1.96 * sem; row[f"{m}_hi"] = mean + 1.96 * sem
        out.append(row)
    return pd.DataFrame(out)