"""
release_noise.py — NB8 v2 whole-brain release engine (Tier-3, frozen core untouched).

Two release kinds, both per-eigenmode-max bar, both direct (rejection-free):
  * ReleaseSingle   — the whole in-mask brain as ONE mode-eigen field (no tiling).
  * ReleasePatched  — tiled + blended patches (average / pou / pou_energy).

Design for the sweep:
  * Modes (V, lam, per-mode-max bar) are built ONCE in __init__. scale and k_check are applied at
    SAMPLE time, so the scale and k_check sweeps are cheap (no rebuild).
  * The membership attack is computed in MODE space: the projected noise onto a direction d is
    A @ (V^T·(weighted d)), so we never materialise the 283k-voxel field for the attack. Utility
    (which needs the field) materialises only n_rel small draws.

Calls frozen building blocks (mode_eigen_mech.patch_modes, privacy_harness.loo_artifacts); edits none.
"""
import numpy as np
from scipy.stats import norm
import privacy_harness as ph
import mode_eigen_mech as me
import tiling as T


# ---------------------------------------------------------------------------
# mode-space primitives
# ---------------------------------------------------------------------------
def mode_bundle(D, bar_kind="permax"):
    """From LOO perturbations D (N,p): economy-SVD modes V (p,r), lam (r,), and the bar (r,).
    bar_kind: 'permax' = max_i|D_i·V_m| (covers every subject per mode); 'l2' = |D_{i*}·V_m|."""
    A = np.asarray(D, float).reshape(np.asarray(D).shape[0], -1)
    V, lam = me.patch_modes(A)                         # frozen; V (p,r), lam (r,)
    proj = A @ V                                       # (N, r)
    if bar_kind == "permax":
        bar = np.abs(proj).max(0)
    elif bar_kind == "l2":
        bar = np.abs(proj[int(np.argmax(np.linalg.norm(A, axis=1)))])
    else:
        raise ValueError(bar_kind)
    return V, lam, bar, proj


def draw_coeffs(lam, bar, scale, k_check, n, rng, mode="hardbar"):
    """n direct coefficient vectors A (n, r) from the mechanism's OUTPUT law at this scale/k_check.

    mode='hardbar' (default): policed modes (m<k_check) are the folded tail of N(0, sd_m^2) beyond
        bar_m; the rest natural. sd = scale*sqrt(lam). This is the settled hard-bar mechanism.
    mode='optB' (variance-inflation): every mode is plain Gaussian; policed modes get an inflated SD
        sd'_m = sqrt(max(scale^2 * lam_m, bar_m^2)) so E[a_m^2] >= bar_m^2 (covers the bar IN
        EXPECTATION, not per draw); the rest natural. No truncation -> Gaussian, inference-friendlier."""
    r = lam.size
    kc = r if k_check is None else int(min(k_check, r))
    sd = scale * np.sqrt(np.clip(lam, 0.0, None))
    if mode == "optB":
        sdm = sd.copy()
        if kc > 0:
            sdm[:kc] = np.sqrt(np.maximum((scale ** 2) * np.clip(lam[:kc], 0.0, None), bar[:kc] ** 2))
        return rng.standard_normal((n, r)) * sdm[None, :]
    A = np.empty((n, r))
    if r > kc:
        A[:, kc:] = rng.standard_normal((n, r - kc)) * sd[kc:]
    if kc > 0:
        s = sd[:kc]; b = bar[:kc]; safe = s > 0
        alpha = np.where(safe, norm.cdf(np.where(safe, b / np.where(safe, s, 1.0), 0.0)), 0.0)
        u = np.clip(alpha[None, :] + (1 - alpha[None, :]) * rng.random((n, kc)), None, 1 - 1e-12)
        A[:, :kc] = np.where(safe[None, :], norm.ppf(u) * s[None, :] *
                             np.where(rng.random((n, kc)) < 0.5, -1.0, 1.0), 0.0)
    return A


def fallback_prob(lam, bar, scale, k_check, max_draws=3000):
    """Analytic rejection-fallback rate diagnostic (the direct sampler never falls back)."""
    kc = lam.size if k_check is None else int(min(k_check, lam.size))
    if kc <= 0:
        return 0.0
    sd = scale * np.sqrt(np.clip(lam[:kc], 0, None)); b = bar[:kc]
    pm = np.where(sd > 0, 2 * norm.cdf(-np.where(sd > 0, b / np.where(sd > 0, sd, 1), 0)),
                  np.where(b > 0, 0.0, 1.0))
    return float((1 - float(np.prod(pm))) ** max_draws)


# ---------------------------------------------------------------------------
# single whole-brain release
# ---------------------------------------------------------------------------
class ReleaseSingle:
    kind = "single"
    def __init__(self, volumes, mask, pipeline_name, bar_kind="permax"):
        self.mask = np.asarray(mask).astype(bool); self.shape = self.mask.shape
        pipe = T.PIPELINES[pipeline_name]
        y, D, _ = ph.loo_artifacts(np.asarray(volumes), pipe)   # y (X,Y,Z), D (N,X,Y,Z)
        mflat = self.mask.reshape(-1)
        Dm = D.reshape(D.shape[0], -1)[:, mflat]                 # (N, p_mask)
        self.V, self.lam, self.bar, self._proj = mode_bundle(Dm, bar_kind)
        self.clean = np.asarray(y).reshape(-1)[mflat]            # (p_mask,)
        self.p = int(mflat.sum()); self.n_patches = 1

    def prep_dcache(self, direction):
        """Precompute V^T·direction (r,) so a scale/k_check sweep reuses it."""
        return self.V.T @ np.asarray(direction, float).reshape(-1)

    def project_scores(self, direction, n, rng, scale, k_check, _dcache=None):
        """n values of direction·noise, in mode space (no field materialised)."""
        dproj = self.prep_dcache(direction) if _dcache is None else _dcache   # (r,)
        return draw_coeffs(self.lam, self.bar, scale, k_check, n, rng) @ dproj

    def sample_field(self, n, rng, scale, k_check, mode="hardbar"):
        """n noise fields over in-mask voxels (n, p_mask) — for utility (small n)."""
        A = draw_coeffs(self.lam, self.bar, scale, k_check, n, rng, mode=mode)
        return A @ self.V.T

    def coverage(self, k_check=None):
        kc = self.lam.size if k_check is None else int(min(k_check, self.lam.size))
        cov = np.abs(self._proj[:, :kc]) <= self.bar[None, :kc]
        return {"overall": float(cov.mean()), "min_subject": float(cov.mean(1).min())}

    def delta_coverage(self, direction):
        """Fraction of the attack direction's energy that lies in the noise span (span of V).
        1.0 = the noise can fully mask Δ; <1 = a component gets ZERO noise at any scale."""
        d = np.asarray(direction, float).reshape(-1); dp = self.V.T @ d
        n = float(d @ d); return float((dp @ dp) / n) if n > 0 else float("nan")

    def fallback_rate(self, scale, k_check):
        return fallback_prob(self.lam, self.bar, scale, k_check)


# ---------------------------------------------------------------------------
# patched + blended release
# ---------------------------------------------------------------------------
class ReleasePatched:
    kind = "patched"
    def __init__(self, volumes, mask, pipeline_name, patch_size, overlap, blend="pou_energy",
                 bar_kind="permax", min_frac=0.5, cover=True, boxes=None, n_build_jobs=1):
        """`boxes`: explicit list of patch origins (x0,y0,z0) of size `patch_size`; if None, tile the
        whole mask. `n_build_jobs`>1 parallelises the per-patch loo+SVD across THREADS (BLAS is capped
        to 1 thread, and LAPACK releases the GIL, so threads give real speed-up and share the volumes
        without pickling). Use it only when there is NO outer process parallelism, to avoid oversubscription."""
        if blend not in ("average", "pou", "pou_energy"):
            raise ValueError(blend)
        self.mask = np.asarray(mask).astype(bool); self.shape = self.mask.shape; self.blend = blend
        pipe = T.PIPELINES[pipeline_name]
        if boxes is None:
            boxes, fracs, stride = T.tile_boxes(self.shape, patch_size, overlap, self.mask, min_frac, cover=cover)
        else:
            boxes = list(boxes); stride = None
        if len(boxes) == 0:
            raise RuntimeError(f"no patches for {patch_size} overlap {overlap}")
        win = T._hann_window(patch_size); px, py, pz = patch_size
        m = self.mask.astype(float); vols = np.asarray(volumes)
        def _build_one(origin):
            x0, y0, z0 = origin
            sl = (slice(x0, x0+px), slice(y0, y0+py), slice(z0, z0+pz))
            sub = vols[:, x0:x0+px, y0:y0+py, z0:z0+pz]
            _, D, _ = ph.loo_artifacts(sub, pipe)
            V, lam, bar, proj = mode_bundle(D.reshape(D.shape[0], -1), bar_kind)
            mloc = m[sl]; wloc = win * mloc
            return {"sl": sl, "V": V, "lam": lam, "bar": bar, "proj": proj,
                    "mloc": mloc.reshape(-1), "wloc": wloc.reshape(-1), "ps": tuple(patch_size),
                    "_mloc3": mloc, "_wloc3": wloc}
        if n_build_jobs and n_build_jobs > 1 and len(boxes) > 1:
            from joblib import Parallel as _P, delayed as _d
            self.patches = _P(n_jobs=n_build_jobs, prefer="threads")(_d(_build_one)(b) for b in boxes)
        else:
            self.patches = [_build_one(b) for b in boxes]
        self.cnt = np.zeros(self.shape); self.den_w = np.zeros(self.shape); self.den_w2 = np.zeros(self.shape)
        for P in self.patches:                                   # serial accumulation (avoids a data race)
            sl = P["sl"]; mloc = P.pop("_mloc3"); wloc = P.pop("_wloc3")
            self.cnt[sl] += mloc; self.den_w[sl] += wloc; self.den_w2[sl] += wloc ** 2
        self.n_patches = len(self.patches); self.stride = stride
        self.clean = pipe(vols).reshape(-1)[self.mask.reshape(-1)]
        self.p = int(self.mask.sum())
        # numerator weight + denominator per blend (for projection and assembly)
        if blend == "average":
            self._den = self.cnt; self._wkey = "mloc"
        elif blend == "pou":
            self._den = self.den_w; self._wkey = "wloc"
        else:
            self._den = self.den_w2; self._wkey = "wloc"   # pou_energy: divide by sqrt(den_w2)
        self._energy = (blend == "pou_energy")

    def _patch_d(self, direction_vol):
        """Precompute per-patch d_p = V_p^T c_p where c_p = (dir * w_num / denom) over the box, so that
        direction·field = Σ_p A_p @ d_p. Depends on direction only (not scale/k_check)."""
        dv = np.asarray(direction_vol, float)
        out = []
        for P in self.patches:
            sl = P["sl"]; box = dv[sl].reshape(-1)
            den = self._den[sl].reshape(-1)
            wnum = P[self._wkey]
            denom = np.sqrt(den) if self._energy else den
            c = np.where(denom > 1e-9, box * wnum / np.where(denom > 1e-9, denom, 1.0), 0.0)
            out.append(P["V"].T @ c)          # (r_p,)
        return out

    def prep_dcache(self, direction):
        """Precompute the per-patch d_p list so a scale/k_check sweep reuses it."""
        return self._patch_d(self._as_vol(direction))

    def project_scores(self, direction, n, rng, scale, k_check, _dcache=None):
        """n values of direction·field via Σ_p A_p @ d_p (mode space; no field materialised).
        `direction` is a full-volume array (X,Y,Z) OR a (p_mask,) vector (expanded here)."""
        dps = self._patch_d(self._as_vol(direction)) if _dcache is None else _dcache
        scores = np.zeros(n)
        for P, dp in zip(self.patches, dps):
            A = draw_coeffs(P["lam"], P["bar"], scale, k_check, n, rng)
            scores += A @ dp
        return scores

    def sample_field(self, n, rng, scale, k_check, mode="hardbar"):
        """n blended noise fields over in-mask voxels (n, p_mask) — for utility (small n)."""
        num_avg = np.zeros((n,) + self.shape); num_w = np.zeros((n,) + self.shape)
        for P in self.patches:
            sl = P["sl"]; ps = P["ps"]
            z = (draw_coeffs(P["lam"], P["bar"], scale, k_check, n, rng, mode=mode) @ P["V"].T).reshape((n,) + ps)
            mloc = P["mloc"].reshape(ps); wloc = P["wloc"].reshape(ps)
            zz = z * mloc[None]
            num_avg[(slice(None),) + sl] += zz
            num_w[(slice(None),) + sl] += wloc[None] * zz
        if self.blend == "average":
            fld = np.where(self.cnt[None] > 0, num_avg / np.where(self.cnt[None] > 0, self.cnt[None], 1.0), 0.0)
        elif self.blend == "pou":
            fld = np.where(self.den_w[None] > 1e-9, num_w / np.where(self.den_w[None] > 1e-9, self.den_w[None], 1.0), 0.0)
        else:
            fld = np.where(self.den_w2[None] > 1e-9, num_w / np.sqrt(np.where(self.den_w2[None] > 1e-9, self.den_w2[None], 1.0)), 0.0)
        return fld[:, self.mask]

    def _as_vol(self, direction):
        d = np.asarray(direction, float)
        if d.shape == self.shape:
            return d
        v = np.zeros(self.shape); v[self.mask] = d.reshape(-1); return v

    def coverage(self, k_check=None):
        covs = []
        for P in self.patches:
            r = P["lam"].size; kc = r if k_check is None else int(min(k_check, r))
            covs.append((np.abs(P["proj"][:, :kc]) <= P["bar"][None, :kc]).mean())
        return {"overall": float(np.mean(covs)), "min_subject": float(np.min(covs))}

    def delta_coverage(self, direction):
        """Fraction of the (blend-weighted) attack direction's energy the noise span covers, summed
        over patches: Σ‖V_pᵀc_p‖² / Σ‖c_p‖². <1 ⇒ a part of Δ sees zero noise at any scale."""
        dv = self._as_vol(direction); covered = 0.0; total = 0.0
        for P in self.patches:
            sl = P["sl"]; box = dv[sl].reshape(-1); den = self._den[sl].reshape(-1); wnum = P[self._wkey]
            denom = np.sqrt(den) if self._energy else den
            c = np.where(denom > 1e-9, box * wnum / np.where(denom > 1e-9, denom, 1.0), 0.0)
            d = P["V"].T @ c; covered += float(d @ d); total += float(c @ c)
        return covered / total if total > 0 else float("nan")

    def fallback_rate(self, scale, k_check):
        return float(np.mean([fallback_prob(P["lam"], P["bar"], scale, k_check) for P in self.patches]))


# ---------------------------------------------------------------------------
# builders + two-world attack
# ---------------------------------------------------------------------------
def build_release(volumes, mask, stat, patch, overlap=0.5, blend="pou_energy", bar_kind="permax",
                  boxes=None, n_build_jobs=1):
    """patch='single' -> whole-brain single field; a tuple (e.g. (5,5,5)) -> tiled+blended.
    `boxes` (explicit origins) and `n_build_jobs` (threaded patch build) forward to ReleasePatched."""
    if patch == "single" or patch is None:
        return ReleaseSingle(volumes, mask, stat, bar_kind)
    return ReleasePatched(volumes, mask, stat, tuple(patch), overlap, blend, bar_kind,
                          boxes=boxes, n_build_jobs=n_build_jobs)


def select_targets(cohort, mask, stat):
    """Return {'worst': idx, 'ksigma': vector}. worst = subject most under the per-mode-max... (here the
    L2 bar, i.e. the subject the single-i* bar least covers, the discriminating case). ksigma = synthetic
    mean + 2*sd outlier over the whole volume."""
    pipe = T.PIPELINES[stat]
    _, D, _ = ph.loo_artifacts(cohort, pipe)
    A = D.reshape(D.shape[0], -1); V, _ = me.patch_modes(A); proj = A @ V
    istar = int(np.argmax(np.linalg.norm(A, axis=1))); bar_l2 = np.abs(proj[istar])
    worst = int(np.argmax((np.abs(proj) - bar_l2[None, :]).max(1)))
    ksigma = cohort.mean(0) + 2.0 * cohort.std(0)
    return {"worst": worst, "istar": istar, "ksigma": ksigma}


def two_worlds(cohort, mask, stat, patch, overlap, blend, target, bar_kind="permax", rel_full=None,
               n_build_jobs=1):
    """Remove-one worlds. `target` is a subject index (real target) OR an array (synthetic, e.g. ksigma).
    Returns g_in, g_out (clean stats over in-mask), release_in, release_out, direction (=g_in-g_out).

    `rel_full`: a release already built on the FULL `cohort` with the SAME (patch, overlap, blend, stat,
    bar_kind). For a REAL target the in-world is exactly the full cohort (remove-one then add-back = the
    same subject set; the statistic is order-invariant), so rel_full is reused as rel_in and its clean as
    g_in — saving one whole-brain build per real target. Ignored for a synthetic target (different set)."""
    pipe = T.PIPELINES[stat]; N = cohort.shape[0]; mflat = mask.reshape(-1)
    real = np.isscalar(target) or np.ndim(target) == 0
    if real:
        keep = np.ones(N, bool); keep[int(target)] = False
        background = cohort[keep]; tvol = cohort[int(target)]
    else:
        background = cohort[1:]; tvol = np.asarray(target)         # synthetic: drop one, add target
    vols_in = np.vstack([background, tvol[None]])                  # N subjects
    vols_out = background                                          # N-1
    g_out = pipe(vols_out).reshape(-1)[mflat]
    rel_out = build_release(vols_out, mask, stat, patch, overlap, blend, bar_kind, n_build_jobs=n_build_jobs)
    if real and rel_full is not None:
        rel_in = rel_full; g_in = rel_full.clean                  # vols_in == full cohort set
    else:
        rel_in = build_release(vols_in, mask, stat, patch, overlap, blend, bar_kind, n_build_jobs=n_build_jobs)
        g_in = pipe(vols_in).reshape(-1)[mflat]
    return g_in, g_out, rel_in, rel_out, (g_in - g_out)


def grid_origins(center, patch_size, stride, k, shape, mask=None, min_frac=0.3):
    """k patch origins on a `stride`-spaced grid aligned so one box is centred on `center`, taken in
    order of distance to `center`, keeping boxes with >= min_frac in-mask. stride = patch_size ->
    non-overlapping; stride = patch_size//2 -> 50% overlap."""
    import itertools
    ps = np.array(patch_size, int); st = np.array(stride, int); shp = np.array(shape, int); c = np.array(center, int)
    base = c - ps // 2; axpts = []
    for ax in range(3):
        n_neg = base[ax] // st[ax] + 1; start = base[ax] - n_neg * st[ax]
        pts = np.arange(start, shp[ax] - ps[ax] + 1, st[ax]); axpts.append(pts[pts >= 0])
    origins = sorted(itertools.product(*axpts), key=lambda o: float(np.sum((np.array(o) + ps // 2 - c) ** 2)))
    out = []
    for o in origins:
        o = tuple(int(x) for x in o); sl = tuple(slice(a, a + p) for a, p in zip(o, ps))
        if mask is not None and np.asarray(mask)[sl].mean() < min_frac:
            continue
        out.append(o)
        if len(out) >= k:
            break
    return out


def two_worlds_boxes(cohort, mask, stat, origins, patch_size, blend, target, bar_kind="permax", n_build_jobs=1):
    """Remove-one worlds for a release made of EXACTLY the given `origins` (k patches). The attack is
    restricted to the released region (union of the boxes ∩ mask), so advantage reflects that region
    only. Returns g_in, g_out, rel_in, rel_out, direction, n_region_voxels."""
    mask = np.asarray(mask).astype(bool); px, py, pz = patch_size
    submask = np.zeros(mask.shape, bool)
    for (x0, y0, z0) in origins:
        sl = (slice(x0, x0+px), slice(y0, y0+py), slice(z0, z0+pz)); submask[sl] = mask[sl]
    pipe = T.PIPELINES[stat]; N = cohort.shape[0]; sflat = submask.reshape(-1)
    real = np.isscalar(target) or np.ndim(target) == 0
    if real:
        keep = np.ones(N, bool); keep[int(target)] = False; background = cohort[keep]; tvol = cohort[int(target)]
    else:
        background = cohort[1:]; tvol = np.asarray(target)
    vols_in = np.vstack([background, tvol[None]]); vols_out = background
    g_in = pipe(vols_in).reshape(-1)[sflat]; g_out = pipe(vols_out).reshape(-1)[sflat]
    ri = build_release(vols_in, submask, stat, tuple(patch_size), 0.5, blend, bar_kind,
                       boxes=origins, n_build_jobs=n_build_jobs)
    ro = build_release(vols_out, submask, stat, tuple(patch_size), 0.5, blend, bar_kind,
                       boxes=origins, n_build_jobs=n_build_jobs)
    return g_in, g_out, ri, ro, (g_in - g_out), int(submask.sum())


def _center_box(shape, center, patch_size):
    ps = np.array(patch_size, int); c = np.array(center, int)
    lo = np.clip(c - ps // 2, 0, np.array(shape) - ps)
    return tuple(slice(int(l), int(l + p)) for l, p in zip(lo, ps))


def peak_influence_voxel(cohort, mask, stat, target):
    """Voxel of maximum |Delta|^2 for `target` (Delta = statistic with vs without), within mask."""
    pipe = T.PIPELINES[stat]; N = cohort.shape[0]; mask = np.asarray(mask).astype(bool)
    if np.isscalar(target) or np.ndim(target) == 0:
        keep = np.ones(N, bool); keep[int(target)] = False
        gi = pipe(cohort).reshape(mask.shape); go = pipe(cohort[keep]).reshape(mask.shape)
    else:
        bg = cohort[1:]
        gi = pipe(np.vstack([bg, np.asarray(target)[None]])).reshape(mask.shape); go = pipe(bg).reshape(mask.shape)
    e = ((gi - go) ** 2) * mask
    return np.unravel_index(int(np.argmax(e)), mask.shape)


def isolated_patch_worlds(cohort, mask, stat, patch_size, center, target, bar_kind="permax"):
    """Two-world attack on ONE isolated patch (sub-volume) — no tiling, no blending. The release is a
    single mode-eigen field over the patch box (intersected with the mask). Tests whether a lone patch
    release leaks before any assembly. Returns g_in, g_out, rel_in, rel_out, direction, n_in_patch."""
    mask = np.asarray(mask).astype(bool)
    box = _center_box(mask.shape, center, patch_size)
    sub = cohort[(slice(None),) + box]; submask = mask[box]
    if submask.sum() < 2:
        submask = np.ones(tuple(patch_size), bool)
    tgt = target[box] if (not np.isscalar(target) and np.ndim(target) != 0) else target
    gi, go, ri, ro, d = two_worlds(sub, submask, stat, "single", 0.5, "pou_energy", tgt, bar_kind)
    return gi, go, ri, ro, d, int(submask.sum())


def projection_advantage(g_in, g_out, rel_in, rel_out, direction, n_trials, rng, scale, k_check):
    """Known-background projection membership advantage, mode-space. Reuses the frozen advantage
    helpers on the 1-D scores s = direction·(g_world + noise)."""
    d = np.asarray(direction, float).reshape(-1)
    off_in = float(g_in @ d); off_out = float(g_out @ d)
    half = n_trials // 2
    # cache per-patch d_p so the sweep over (scale,k_check) reuses it (patched); single ignores cache
    s_out = off_out + _scores(rel_out, d, half, rng, scale, k_check)
    s_in = off_in + _scores(rel_in, d, half, rng, scale, k_check)
    X = np.concatenate([s_out, s_in]); yb = np.r_[np.zeros(half), np.ones(half)]
    idx = rng.permutation(len(X)); X, yb = X[idx], yb[idx]; cut = len(X) // 2
    thr = ph._threshold_youden(X[:cut], yb[:cut])
    return {"advantage": ph._adv_at(X[cut:], yb[cut:], thr),
            "adv_ci": ph._adv_ci(X[cut:], yb[cut:], thr),
            "fallback_in": rel_in.fallback_rate(scale, k_check)}


def _scores(rel, direction, n, rng, scale, k_check, dcache=None):
    return rel.project_scores(direction, n, rng, scale, k_check, _dcache=dcache)


def advantage_sweep(g_in, g_out, rel_in, rel_out, direction, scales, k_check, n_trials, rng):
    """Projection membership advantage across a list of `scales`, reusing one dcache per world (the
    expensive V^T·direction product is computed once, not per scale). k_check fixed. Returns a list of
    {scale, advantage, adv_ci}."""
    d = np.asarray(direction, float).reshape(-1)
    off_in = float(g_in @ d); off_out = float(g_out @ d)
    dc_in = rel_in.prep_dcache(direction); dc_out = rel_out.prep_dcache(direction)
    half = n_trials // 2; rows = []
    for sc in scales:
        s_out = off_out + _scores(rel_out, d, half, rng, sc, k_check, dc_out)
        s_in = off_in + _scores(rel_in, d, half, rng, sc, k_check, dc_in)
        X = np.concatenate([s_out, s_in]); yb = np.r_[np.zeros(half), np.ones(half)]
        idx = rng.permutation(len(X)); X, yb = X[idx], yb[idx]; cut = len(X) // 2
        thr = ph._threshold_youden(X[:cut], yb[:cut])
        rows.append(dict(scale=sc, advantage=ph._adv_at(X[cut:], yb[cut:], thr),
                         adv_ci=ph._adv_ci(X[cut:], yb[cut:], thr)))
    return rows


def kcheck_sweep(g_in, g_out, rel_in, rel_out, direction, scale, k_checks, n_trials, rng):
    """Projection advantage across a list of `k_check` values at fixed `scale` (reuses dcache)."""
    d = np.asarray(direction, float).reshape(-1)
    off_in = float(g_in @ d); off_out = float(g_out @ d)
    dc_in = rel_in.prep_dcache(direction); dc_out = rel_out.prep_dcache(direction)
    half = n_trials // 2; rows = []
    for kc in k_checks:
        s_out = off_out + _scores(rel_out, d, half, rng, scale, kc, dc_out)
        s_in = off_in + _scores(rel_in, d, half, rng, scale, kc, dc_in)
        X = np.concatenate([s_out, s_in]); yb = np.r_[np.zeros(half), np.ones(half)]
        idx = rng.permutation(len(X)); X, yb = X[idx], yb[idx]; cut = len(X) // 2
        thr = ph._threshold_youden(X[:cut], yb[:cut])
        rows.append(dict(k_check=kc, advantage=ph._adv_at(X[cut:], yb[cut:], thr),
                         adv_ci=ph._adv_ci(X[cut:], yb[cut:], thr)))
    return rows


# ---------------------------------------------------------------------------
# utility panel on the whole-brain release
# ---------------------------------------------------------------------------
class _FixedNoise:
    """Adapter: a release pinned at one (scale, k_check), exposing .sample(rng) -> (p_mask,) noise and
    a .fallback_rate attribute, so full_release_attacks.outlier_detectability (which expects the old
    NoiseModel interface) can run on the whole-brain release unchanged."""
    def __init__(self, release, scale, k_check, mode="hardbar"):
        self.r = release; self.scale = scale; self.kc = k_check; self.mode = mode
        self.fallback_rate = release.fallback_rate(scale, k_check)
    def sample(self, rng):
        return self.r.sample_field(1, rng, self.scale, self.kc, mode=self.mode)[0]


def fixed_noise(release, scale, k_check, mode="hardbar"):
    return _FixedNoise(release, scale, k_check, mode)


def release_utility(release, scale, k_check, rng, n_rel=50, mode="hardbar"):
    """Mean utility over n_rel released noise fields: rel-MSE, neighbour-corr gap, Spearman, SSIM —
    all on the whole in-mask brain (reconstructs each noisy field to full volume, reuses frozen helpers)."""
    shape = release.shape; mask = release.mask
    clean_vol = np.zeros(shape); clean_vol[mask] = release.clean
    fields = release.sample_field(n_rel, rng, scale, k_check, mode=mode)   # (n_rel, p_mask) — NOISE fields
    acc = {}
    for z in fields:
        field_vol = np.zeros(shape); field_vol[mask] = z           # noise only; util adds clean itself
        u = T.whole_brain_utility(clean_vol, field_vol, mask)
        for k, v in u.items():
            acc.setdefault(k, []).append(v)
    return {k: float(np.mean(v)) for k, v in acc.items()}


# ---------------------------------------------------------------------------
# §5 inference validity ON THE IMAGING RELEASE (mass-univariate one-sample t-test)
# ---------------------------------------------------------------------------
def _signal_region(sd_vox, frac, seed):
    """A fixed contiguous-by-index block of p*frac in-mask voxels to carry the injected effect."""
    p = sd_vox.size; k = max(1, int(round(frac * p)))
    start = int(np.random.default_rng(seed).integers(0, max(1, p - k)))
    reg = np.zeros(p, bool); reg[start:start + k] = True
    return reg


def imaging_inference(release, cohort, mask, scale, k_check, alpha=0.05, n_mc=200,
                      effect=0.8, region_frac=0.05, seed=0, mode="hardbar"):
    """Mass-univariate one-sample t-test on the imaging MEAN release, clean vs privatized.

    Null scenario : sign-flip (Rademacher) of the centered cohort deviations (true per-voxel mean = 0,
                    per-voxel variance preserved exactly) -> any corrected rejection is a false
                    positive -> FWER (Bonferroni) / FDR (BH). This is the exact one-sample permutation
                    null, so clean FWER ~ alpha (a bootstrap-with-replacement null would shrink the
                    variance estimate via ties and over-reject).
    Signal scenario: null + a fixed per-voxel effect (effect * sd_vox) on a fixed region -> power.
    The mechanism noise (release.sample_field, one draw per MC) is added to the released mean map;
    the per-voxel t is recomputed; Bonferroni (FWER) and Benjamini-Hochberg (FDR) are applied.

    `release` must be a mean-statistic release (built with stat='mean'); its noise is calibrated to
    the real cohort and is what the mechanism actually adds. Returns clean vs private FWER and power.
    """
    from scipy.stats import t as _t
    mflat = np.asarray(mask).reshape(-1).astype(bool)
    Xm = np.asarray(cohort).reshape(np.asarray(cohort).shape[0], -1)[:, mflat]   # (N, p)
    N, p = Xm.shape; df = N - 1
    dev = Xm - Xm.mean(0)                                 # true pop mean ~ 0
    sd_vox = dev.std(0, ddof=1) + 1e-12
    region = _signal_region(sd_vox, region_frac, seed)
    eff = np.zeros(p); eff[region] = effect * sd_vox[region]
    crit_bonf = float(_t.ppf(1 - alpha / (2 * p), df))    # scalar Bonferroni threshold on |t|
    rng = np.random.default_rng(seed + 12345)

    def _bh_reject(pvals):
        """BH step-up: boolean reject mask at level alpha."""
        order = np.argsort(pvals); ranked = pvals[order]
        thresh = alpha * (np.arange(1, p + 1) / p)
        below = ranked <= thresh
        kmax = np.nonzero(below)[0]
        rej = np.zeros(p, bool)
        if kmax.size:
            rej[order[:kmax.max() + 1]] = True
        return rej

    acc = {k: 0.0 for k in ("fwer_clean", "fwer_priv", "fdr_fp_clean", "fdr_fp_priv",
                            "pow_bonf_clean", "pow_bonf_priv", "pow_bh_clean", "pow_bh_priv")}
    for _ in range(n_mc):
        s = rng.choice(np.array([-1.0, 1.0]), size=(N, 1))   # sign-flip null (exact, variance-preserving)
        d = dev * s
        mean0 = d.mean(0); se = d.std(0, ddof=1) / np.sqrt(N) + 1e-12
        z = release.sample_field(1, rng, scale, k_check, mode=mode)[0]   # mechanism noise on the mean map
        # --- NULL (mean0 ~ 0): any rejection is a false positive ---
        for tag, mu in (("clean", mean0), ("priv", mean0 + z)):
            tt = np.abs(mu / se)
            acc[f"fwer_{tag}"] += float((tt > crit_bonf).any())
            pv = 2 * _t.sf(tt, df)
            acc[f"fdr_fp_{tag}"] += float(_bh_reject(pv).any())
        # --- SIGNAL (mean0 + eff): power = detected fraction over the true-effect region ---
        for tag, mu in (("clean", mean0 + eff), ("priv", mean0 + eff + z)):
            tt = np.abs(mu / se)
            acc[f"pow_bonf_{tag}"] += float((tt[region] > crit_bonf).mean())
            pv = 2 * _t.sf(tt, df)
            acc[f"pow_bh_{tag}"] += float(_bh_reject(pv)[region].mean())
    out = {k: v / n_mc for k, v in acc.items()}
    out.update(alpha=alpha, n_mc=n_mc, p=p, N=N, crit_bonf=crit_bonf,
               region_frac=region_frac, effect=effect)
    return out
