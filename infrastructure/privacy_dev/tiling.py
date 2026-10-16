"""
tiling.py — whole-brain tiling layer built ON TOP of the frozen privacy_harness per-patch
mechanism. NEW module. Does NOT modify privacy_harness.py / cov_diagnostics.py /
inference_eval.py (verified by hash in the notebook).

WHAT THIS ADDS
  The harness studies ONE patch: statistic + sensitivity-informed correlated noise on a small
  block. This module tiles that per-patch mechanism over a whole brain volume, assembles the
  per-patch noise draws into a single whole-brain noise field (handling overlap), and exposes
  the structural rank of each patch's noise covariance.

PIPELINE SHAPE
  release = global statistic map (e.g. voxelwise group mean)  +  assembled noise field.
  The statistic is global; only the NOISE is built patch by patch, because the mechanism's
  covariance is estimated locally per patch. Overlap => a voxel's noise is combined from every
  patch covering it.

KEY DESIGN POINTS
  * Tiling: explicit start grid with BOUNDARY ANCHORING so the far edge of the volume is always
    covered (plain strided windowing drops the last partial window). view_as_windows is the
    library equivalent but silently under-covers the boundary, so we anchor the last start.
  * Overlap aggregation — the clean trio (one pass computes all three from the SAME draws):
        'average'     flat weights, divide by coverage count   -> blotchy, seams, var/k shrink
        'pou'         tapered (Hann) weights, divide by Sum w   -> smooth, seamless, still shrinks
        'pou_energy'  tapered weights, divide by sqrt(Sum w^2)  -> smooth AND magnitude held
  * Patch rank: read from the RAW Cov(LOO) perturbations (<= min(p, N-1)), NOT the mechanism's
    nominal_cov. The mechanism floors its covariance to full rank (+1e-8 I) so it can Cholesky-
    sample; that regularized object is always rank p and would hide the N-1 ceiling. The honest
    structural rank is the rank of np.cov(D), matching cov_diagnostics.covariance_report.
"""
import numpy as np
from scipy import ndimage
from joblib import Parallel, delayed
import privacy_harness as ph

PIPELINES = {"mean": ph.pipeline_mean, "median": ph.pipeline_median, "variance": ph.pipeline_variance}


# ===========================================================================
# 1. Substrate: synthetic brain-shaped phantom (portable) + OASIS loader
# ===========================================================================
def _gaussian_field(shape, corr_len, rng):
    """Spatially-correlated unit-variance Gaussian field: smoothed white noise, renormalized."""
    w = rng.standard_normal(shape)
    f = ndimage.gaussian_filter(w, sigma=max(corr_len / 2.0, 1e-3), mode="reflect")
    s = f.std()
    return f / s if s > 0 else f


def make_phantom(shape=(24, 24, 20), M=80, N=40, corr_lens=(2.0, 4.0, 6.0),
                 zone_amp=(1.0, 0.7, 1.3), base_std=1.0, seed=0):
    """Brain-shaped synthetic substrate with KNOWN autocorrelation structure.

    - ellipsoidal mask (not a cube -> boundary tiling is exercised)
    - shared smooth mean template
    - 3 radial zones with DIFFERENT correlation length + amplitude, so per-patch rank and
      noise structure vary BY LOCATION (the rank distribution is then non-degenerate)
    - M pooled subjects (>= N) = template + zone-dependent spatially-correlated deviation

    Returns dict(volumes (M,X,Y,Z), mask (X,Y,Z) bool, zones (X,Y,Z) int, corr_lens, N).
    The known corr_lens make this a ground-truth testbed for autocorrelation-based sizing.
    """
    rng = np.random.default_rng(seed)
    X, Y, Z = shape
    gx, gy, gz = np.mgrid[0:X, 0:Y, 0:Z].astype(float)
    cx, cy, cz = (X - 1) / 2, (Y - 1) / 2, (Z - 1) / 2
    ax, ay, az = X * 0.46, Y * 0.46, Z * 0.46
    r2 = ((gx - cx) / ax) ** 2 + ((gy - cy) / ay) ** 2 + ((gz - cz) / az) ** 2
    mask = r2 <= 1.0

    # radial zones: inner / middle / outer shell -> different smoothness
    rnorm = np.sqrt(r2)
    zones = np.zeros(shape, int)
    zones[rnorm > 0.4] = 1
    zones[rnorm > 0.75] = 2

    template = 2.0 * _gaussian_field(shape, corr_len=5.0, rng=rng) + 4.0  # smooth positive mean

    vols = np.empty((M, X, Y, Z))
    for i in range(M):
        dev = np.zeros(shape)
        for z, (cl, amp) in enumerate(zip(corr_lens, zone_amp)):
            fz = _gaussian_field(shape, corr_len=cl, rng=rng)
            dev = np.where(zones == z, amp * fz, dev)
        vols[i] = template + base_std * dev
    vols *= mask  # zero outside the brain
    return {"volumes": vols, "mask": mask, "zones": zones, "corr_lens": corr_lens,
            "shape": shape, "N": N, "M": M}


def load_oasis_volumes(n=100, data_dir=None):
    """OASIS gray-matter maps -> (volumes, mask). Needs nilearn (user environment)."""
    vols, mask = ph.load_oasis(n=n, data_dir=data_dir)
    return {"volumes": vols, "mask": mask, "zones": None, "corr_lens": None,
            "shape": tuple(mask.shape), "N": min(n, vols.shape[0]), "M": vols.shape[0]}


def sample_cohort(sub, N, seed=0):
    """Pick N subjects from the pooled volumes (reproducible)."""
    rng = np.random.default_rng(seed)
    M = sub["volumes"].shape[0]
    idx = rng.choice(M, size=min(N, M), replace=(N > M))
    return sub["volumes"][idx].copy()


# ===========================================================================
# 2. Autocorrelation (for the substrate check & the user's sizing work)
# ===========================================================================
def radial_acf(volumes, mask, max_lag=12, n_subj=20, seed=0):
    """Average radial autocorrelation of the subject deviation field vs voxel lag (axis-mean).
    Returns (lags, acf). Correlation length ~ lag where acf crosses 1/e."""
    rng = np.random.default_rng(seed)
    V = volumes[rng.choice(volumes.shape[0], size=min(n_subj, volumes.shape[0]), replace=False)]
    dev = V - V.mean(0, keepdims=True)
    lags = np.arange(max_lag + 1)
    acc = np.zeros(max_lag + 1)
    cnt = np.zeros(max_lag + 1)
    m = mask.astype(bool)
    for v in dev:
        v = v - v[m].mean()
        var = v[m].var() + 1e-12
        for ax in range(3):
            for L in lags:
                a = np.moveaxis(v, ax, 0)
                mm = np.moveaxis(m, ax, 0)
                if L == 0:
                    sel = mm
                    prod = (a[sel] * a[sel]).mean()
                else:
                    sel = mm[:-L] & mm[L:]
                    if sel.sum() < 10:
                        continue
                    prod = (a[:-L][sel] * a[L:][sel]).mean()
                acc[L] += prod / var
                cnt[L] += 1
    acf = np.where(cnt > 0, acc / np.maximum(cnt, 1), np.nan)
    return lags, acf


# ===========================================================================
# 3. Tiling geometry
# ===========================================================================
def stride_from_overlap(patch_size, overlap):
    """stride per axis = round(patch*(1-overlap)), floored at 1."""
    return tuple(max(1, int(round(p * (1.0 - overlap)))) for p in patch_size)


def _axis_starts(dim, patch, stride):
    if patch >= dim:
        return [0]
    s = list(range(0, dim - patch + 1, max(1, stride)))
    if s[-1] != dim - patch:
        s.append(dim - patch)       # boundary anchor -> full coverage
    return s


def tile_boxes(vol_shape, patch_size, overlap, mask=None, min_frac=0.5, cover=True):
    """All patch origins (x0,y0,z0) covering the volume at the given overlap.

    Two-pass coverage: first keep every grid patch whose in-mask fraction >= min_frac (the
    well-estimated patches); then, if `cover`, greedily add boundary patches with 0 < fraction <
    min_frac until EVERY in-mask voxel is covered by at least one patch. Without this pass, in-mask
    voxels near the brain edge fall only under mostly-out-of-mask patches that min_frac drops, and
    would be RELEASED WITH NO NOISE (a privacy hole). Returns (boxes, fracs, stride); `fracs[i]` is
    the in-mask fraction of boxes[i], so callers can tell coverage-fill patches (frac < min_frac)
    from well-estimated ones."""
    stride = stride_from_overlap(patch_size, overlap)
    xs = _axis_starts(vol_shape[0], patch_size[0], stride[0])
    ys = _axis_starts(vol_shape[1], patch_size[1], stride[1])
    zs = _axis_starts(vol_shape[2], patch_size[2], stride[2])
    px, py, pz = patch_size
    all_boxes, all_fr = [], []
    for x0 in xs:
        for y0 in ys:
            for z0 in zs:
                frac = 1.0 if mask is None else float(mask[x0:x0+px, y0:y0+py, z0:z0+pz].mean())
                all_boxes.append((x0, y0, z0)); all_fr.append(frac)
    all_fr = np.array(all_fr)
    keep = [b for b, f in zip(all_boxes, all_fr) if f >= min_frac]
    fr = [f for f in all_fr if f >= min_frac]
    if cover and mask is not None:
        m = mask.astype(bool)
        covered = np.zeros(vol_shape, bool)
        for (x0, y0, z0) in keep:
            covered[x0:x0+px, y0:y0+py, z0:z0+pz] |= m[x0:x0+px, y0:y0+py, z0:z0+pz]
        if (m & ~covered).any():
            for idx in np.argsort(-all_fr):          # add highest-fraction boundary patches first
                f = all_fr[idx]
                if f <= 0 or f >= min_frac:
                    continue
                if not (m & ~covered).any():
                    break
                x0, y0, z0 = all_boxes[idx]
                sub = m[x0:x0+px, y0:y0+py, z0:z0+pz]
                if (sub & ~covered[x0:x0+px, y0:y0+py, z0:z0+pz]).any():
                    keep.append((x0, y0, z0)); fr.append(f)
                    covered[x0:x0+px, y0:y0+py, z0:z0+pz] |= sub
    return keep, np.array(fr), stride


def _hann_window(shape):
    """Separable Hann taper, strictly positive (floored), used for the POU blends."""
    w = np.ones(shape, float)
    for ax, L in enumerate(shape):
        h = np.hanning(L + 2)[1:-1] if L >= 1 else np.array([1.0])
        shp = [1] * len(shape); shp[ax] = L
        w = w * h.reshape(shp)
    return np.clip(w, 1e-3, None)


# ===========================================================================
# 4. Per-patch worker + whole-brain assembly
# ===========================================================================
def _process_chunk(volumes, boxes_idx, patch_size, pipeline_name, epsilon, base_seed,
                   max_draws=2000, mech_kind="mode-eigen", mech_scale=None, mech_kcheck=None):
    """Run the per-patch mechanism on a chunk of patches. Self-contained & picklable.
    Returns per-patch (idx, origin, noise_draw, numerical_rank, eff95_rank, loo_total_var, fell_back).

    mech_kind selects the mechanism:
      'mode-eigen' -> mode_eigen_mech.mech_mode_eigen: correlated noise as one coefficient per
                      covariance eigenmode, mode-space L2 bar. Never forms p x p, so it scales to the
                      large (OASIS-size) patches the voxel mechanisms OOM on. Uses the operating point
                      (mech_scale, mech_kcheck, max_draws); scale defaults to 2/epsilon.
      'supervisor' -> mech_supervisor_loo_corr (per-voxel bar S_j = max_i|D_ij|)  [legacy voxel]
      'l2'         -> l2_sensitivity.l2_bar on the supervisor (L2-selected voxel bar)  [legacy voxel]

    max_draws controls the rejection-sampler budget. fell_back is tracked."""
    import numpy as np
    import privacy_harness as ph
    pipe = {"mean": ph.pipeline_mean, "median": ph.pipeline_median,
            "variance": ph.pipeline_variance}[pipeline_name]
    if mech_kind == "mode-eigen":
        import mode_eigen_mech as me
        _scale = mech_scale if mech_scale is not None else 2.0 / epsilon

        def mech(y, D, S, **kw):
            return me.mech_mode_eigen(y, D, S, scale=_scale, k_check=mech_kcheck,
                                      max_draws=max_draws, **kw)
    else:
        base = ph.mech_supervisor_loo_corr(epsilon=epsilon, max_draws=max_draws)
        if mech_kind == "l2":
            import l2_sensitivity as l2s
            mech = l2s.l2_bar(base)
        else:
            mech = base
    px, py, pz = patch_size
    out = []
    for idx, (x0, y0, z0) in boxes_idx:
        sub = volumes[:, x0:x0+px, y0:y0+py, z0:z0+pz]
        N = sub.shape[0]
        y, D, S = ph.loo_artifacts(sub, pipe)
        m = mech(y, D, S, subjects=sub.reshape(N, -1))
        rng = np.random.default_rng(np.random.SeedSequence([int(base_seed), int(idx)]))
        z = np.asarray(m.sample(rng)).reshape(patch_size)
        fell_back = int(m.n_fallback)
        # structural rank from the RAW Cov(LOO) eigenvalues, via the ECONOMY SVD of the centred
        # perturbations (N x p) -- NEVER forms the p x p covariance, so this is OOM-safe at large p.
        # The p x p covariance has only r = min(p, N-1) nonzero eigenvalues anyway, so the economy
        # eigenvalues (s^2/(N-1)) reproduce the rank and 95% effective rank exactly.
        A = D.reshape(N, -1)
        Ac = A - A.mean(0, keepdims=True)
        sv = np.linalg.svd(Ac, compute_uv=False)
        ev = (sv ** 2) / (N - 1)
        ev = ev[:min(A.shape[1], N - 1)]
        tot = float(ev.sum())
        mx = ev.max() if ev.size else 0.0
        rank = int((ev > 1e-9 * max(mx, 1e-30)).sum())
        if tot > 0:
            eff95 = int(np.searchsorted(np.cumsum(ev) / tot, 0.95) + 1)
        else:
            eff95 = 0
        out.append((idx, (x0, y0, z0), z, rank, eff95, tot, fell_back))
    return out


def assemble_field(volumes, mask, pipeline_name, patch_size, overlap, epsilon=1.0,
                   base_seed=0, min_frac=0.5, n_jobs=2, chunks_per_job=6, max_draws=2000,
                   mech_kind="mode-eigen", mech_scale=None, mech_kcheck=None, cover=True):
    """Build the whole-brain noise field by tiling the per-patch mechanism and overlap-adding.
    Returns dict with the blended fields, clean statistic, coverage multiplicity, per-patch rank
    records, per-patch fallback flags, and the mean fallback rate. mech_kind/mech_scale/mech_kcheck
    select the per-patch mechanism and its operating point (see _process_chunk). `cover` toggles the
    boundary coverage pass in tile_boxes (True = no privacy holes; False = threshold patches only)."""
    vol_shape = mask.shape
    boxes, fracs, stride = tile_boxes(vol_shape, patch_size, overlap, mask, min_frac, cover=cover)
    boxes_idx = list(enumerate(boxes))
    if len(boxes_idx) == 0:
        raise RuntimeError(f"no patches for size {patch_size} overlap {overlap}")
    n_chunks = max(1, min(len(boxes_idx), n_jobs * chunks_per_job))
    splits = np.array_split(np.arange(len(boxes_idx)), n_chunks)
    chunks = [[boxes_idx[i] for i in sp] for sp in splits if len(sp)]
    results = Parallel(n_jobs=n_jobs, prefer="processes")(
        delayed(_process_chunk)(volumes, ch, patch_size, pipeline_name, epsilon, base_seed,
                                max_draws, mech_kind, mech_scale, mech_kcheck)
        for ch in chunks)
    flat = [r for sub in results for r in sub]

    px, py, pz = patch_size
    m = mask.astype(float)
    num_avg = np.zeros(vol_shape); cnt = np.zeros(vol_shape)
    num_w = np.zeros(vol_shape); den_w = np.zeros(vol_shape); den_w2 = np.zeros(vol_shape)
    win = _hann_window(patch_size)
    ranks, eff, centers, fvals, fbacks, nfb = [], [], [], [], [], 0
    for idx, (x0, y0, z0), z, rank, eff95, tot, fell_back in flat:
        nfb += fell_back
        sl = (slice(x0, x0+px), slice(y0, y0+py), slice(z0, z0+pz))
        mloc = m[sl]
        wloc = win * mloc
        zz = z * mloc
        num_avg[sl] += zz; cnt[sl] += mloc
        num_w[sl] += wloc * zz; den_w[sl] += wloc; den_w2[sl] += wloc ** 2
        ranks.append(rank); eff.append(eff95)
        centers.append((x0 + px / 2.0, y0 + py / 2.0, z0 + pz / 2.0))
        fvals.append(fracs[idx]); fbacks.append(bool(fell_back))

    fields = {
        "sum":        num_avg * m,                                     # raw Σ of contributions, no averaging
        "average":    np.where(cnt > 0, num_avg / np.where(cnt > 0, cnt, 1.0), 0.0),
        "pou":        np.where(den_w > 1e-9, num_w / np.where(den_w > 1e-9, den_w, 1.0), 0.0),
        "pou_energy": np.where(den_w2 > 1e-9, num_w / np.sqrt(np.where(den_w2 > 1e-9, den_w2, 1.0)), 0.0),
    }
    clean = PIPELINES[pipeline_name](volumes)
    return {"fields": fields, "clean": clean * mask, "mult": cnt, "stride": stride,
            "ranks": np.array(ranks), "eff": np.array(eff), "centers": np.array(centers),
            "patch_frac": np.array(fvals), "fallbacks": np.array(fbacks, bool), "n_patches": len(flat),
            "fallback_rate": nfb / max(1, len(flat)),
            "patch_size": patch_size, "overlap": overlap, "pipeline": pipeline_name}


# ===========================================================================
# 5. Whole-brain utility (reuses harness metric definitions)
# ===========================================================================
def whole_brain_utility(clean, field, mask):
    """rel-MSE, neighbour-corr gap, Spearman, SSIM of (clean+field) vs clean, within mask.
    rel-MSE and neighbour-corr reuse the harness' own definitions (ph._neighbour_corr/_spearman)."""
    mb = mask.astype(bool)
    noisy = clean + field
    t = clean[mb]; r = noisy[mb]
    rel_mse = float(np.mean((r - t) ** 2) / (np.mean(t ** 2) + 1e-12))
    nc_true = ph._neighbour_corr(clean * mask, mask.shape)
    nc_rel = ph._neighbour_corr(noisy * mask, mask.shape)
    nc_gap = float(abs(nc_true - nc_rel)) if np.isfinite(nc_true) and np.isfinite(nc_rel) else np.nan
    spear = ph._spearman(t, r)
    try:
        from skimage.metrics import structural_similarity as ssim
        rng_val = float(t.max() - t.min()) or 1.0
        sl = ndimage.find_objects(mb.astype(int))[0]
        a_im = clean[sl]; b_im = noisy[sl]
        # robust window: largest odd <= 7 that fits the smallest cropped dim; channel_axis=None
        # forces a true 3-D SSIM (older/newer skimage differ on the default), which was the silent
        # failure mode that left ssim all-NaN on some environments.
        dmin = min(a_im.shape)
        win = min(7, dmin if dmin % 2 == 1 else dmin - 1)
        if win >= 3:
            ss = float(ssim(a_im, b_im, data_range=rng_val, win_size=win, channel_axis=None))
        else:
            ss = np.nan
    except Exception as e:
        ss = np.nan
        if not getattr(whole_brain_utility, "_ssim_warned", False):
            import warnings
            warnings.warn(f"SSIM disabled ({type(e).__name__}: {e}); other metrics unaffected.")
            whole_brain_utility._ssim_warned = True
    return {"rel_mse": rel_mse, "neighbour_corr_gap": nc_gap, "spearman": float(spear),
            "ssim": ss, "neighbour_corr_true": float(nc_true), "neighbour_corr_released": float(nc_rel)}
