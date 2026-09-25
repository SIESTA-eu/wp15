"""
cov_diagnostics.py — STRUCTURAL diagnostics of the LOO noise covariance, upstream of the harness.

The privacy harness measures OUTCOMES (attacker advantage, utility). This module inspects the noise
covariance OBJECT itself — before any noise is drawn — for any pipeline/statistic. It surfaces things
the harness structurally cannot see:

  * the mean-pipeline identity  Cov(LOO) == Cov(data)/(N-1)^2   (a covariance-level correctness oracle)
  * DEGENERACY: zero / rank-deficient covariance, zero sensitivity  (the median blind-spot detector)
  * data-vs-LOO correlation divergence, incl. sign flips           (the variance result)
  * eigenvalue spectrum / anisotropy / condition number           (low-rank motivation)

Works for any p (not just bivariate). No DP claim — this is structural characterization.
"""
import numpy as np

def loo_perturbations(data, pipeline):
    data = np.asarray(data, float); N = data.shape[0]
    full = np.atleast_1d(pipeline(data))
    loo = np.empty((N, full.size))
    for i in range(N):
        loo[i] = np.atleast_1d(pipeline(np.delete(data, i, axis=0)))
    return full, loo, loo - full            # output, loo outputs, perturbations d_i

def _corr_matrix(C):
    d = np.sqrt(np.clip(np.diag(C), 0, None))
    with np.errstate(invalid="ignore", divide="ignore"):
        R = C / np.outer(d, d)
    return R

def covariance_report(data, pipeline, name="pipeline", data_cov=None, zero_tol=1e-12):
    """Full structural report on the LOO noise covariance for one statistic."""
    data = np.asarray(data, float); N = data.shape[0]
    if data_cov is None:
        data_cov = np.cov(data.T)
    data_cov = np.atleast_2d(data_cov)
    full, loo, perturb = loo_perturbations(data, pipeline)
    loo_cov = np.atleast_2d(np.cov(perturb.T))
    p = loo_cov.shape[0]
    sensitivity = np.max(np.abs(perturb), axis=0)
    eig = np.linalg.eigvalsh(loo_cov)

    # --- degeneracy checks (the median blind-spot detector) ---
    total_var = float(np.trace(loo_cov))
    rank = int((eig > zero_tol * max(1.0, eig.max())).sum())
    zero_sens = np.where(sensitivity <= zero_tol)[0].tolist()
    degenerate = (total_var <= zero_tol) or (rank < p) or (len(zero_sens) > 0)
    flags = []
    if total_var <= zero_tol:      flags.append("ZERO_COVARIANCE (mechanism would add NO noise)")
    if rank < p:                   flags.append(f"RANK_DEFICIENT ({rank}/{p})")
    if zero_sens:                  flags.append(f"ZERO_SENSITIVITY at dims {zero_sens}")

    # --- data vs LOO correlation (only defined for p>=2 and non-degenerate) ---
    def off_corr(C):
        if C.shape[0] != 2: return None
        d = np.sqrt(C[0,0]*C[1,1])
        return float(C[0,1]/d) if d > 0 else None
    dcorr, lcorr = off_corr(data_cov), off_corr(loo_cov)
    sign_flip = (dcorr is not None and lcorr is not None and np.sign(dcorr) != np.sign(lcorr)
                 and abs(dcorr) > 1e-6 and abs(lcorr) > 1e-6)

    # --- mean-pipeline identity oracle: Cov(LOO) == Cov(data)/(N-1)^2 ---
    identity_err = float(np.max(np.abs(loo_cov - data_cov / (N-1)**2))) if loo_cov.shape==data_cov.shape else None

    return {"name": name, "output": full, "loo_cov": loo_cov, "sensitivity": sensitivity,
            "eigenvalues": eig, "total_variance": total_var, "rank": rank, "p": p,
            "degenerate": degenerate, "flags": flags,
            "data_corr": dcorr, "loo_corr": lcorr, "sign_flip": sign_flip,
            "condition_number": float(eig.max()/eig[eig>0].min()) if (eig>0).any() else np.inf,
            "mean_identity_err": identity_err}

def print_report(rep):
    print(f"\n{rep['name'].upper()}  (output={np.round(rep['output'],3)})")
    print(f"  sensitivity      : {np.round(rep['sensitivity'],4)}")
    print(f"  eigenvalues      : {np.round(rep['eigenvalues'],4)}   rank {rep['rank']}/{rep['p']}"
          f"   cond {rep['condition_number']:.1f}")
    if rep['data_corr'] is not None:
        print(f"  corr  data={rep['data_corr']:+.3f}   LOO={rep['loo_corr'] if rep['loo_corr'] is None else round(rep['loo_corr'],3)}"
              + ("   <-- SIGN FLIP" if rep['sign_flip'] else ""))
    if rep['mean_identity_err'] is not None:
        print(f"  mean-identity err: {rep['mean_identity_err']:.2e}")
    if rep['flags']:
        print("  ⚠ DEGENERATE:", "; ".join(rep['flags']))

def compare_pipelines(data, pipelines, data_cov=None):
    """Run covariance_report for a dict of {name: pipeline}; print and return the reports."""
    reps = {}
    for name, pipe in pipelines.items():
        rep = covariance_report(data, pipe, name=name, data_cov=data_cov)
        reps[name] = rep; print_report(rep)
    return reps

# --- the median-granularity investigation: is a zero-covariance an artifact of discreteness? ---
def jitter_probe(data, pipeline, scales=(0.0, 1e-3, 1e-2, 1e-1, 1.0), reps=20, seed=0):
    """Add small continuous jitter to the data and watch whether a degenerate LOO covariance
    'wakes up'. If total_variance grows from ~0 as jitter increases, the zero was a granularity
    artifact of the statistic on discrete data, NOT genuine zero sensitivity."""
    rng = np.random.default_rng(seed); data = np.asarray(data, float)
    col_sd = data.std(0)
    out = []
    for s in scales:
        tvs = []
        for _ in range(reps):
            noisy = data + rng.normal(0, 1, data.shape) * col_sd * s
            _, _, pert = loo_perturbations(noisy, pipeline)
            tvs.append(float(np.trace(np.atleast_2d(np.cov(pert.T)))))
        out.append({"jitter_frac_of_sd": s, "mean_total_variance": float(np.mean(tvs))})
    return out