"""
inference_eval.py — OPTIONAL downstream / scientific-utility layer, built ON TOP of the harness.

The harness utility_panel answers "how close is the released output to the clean output?".
This module answers a different question: "does privatization preserve valid scientific INFERENCE?"
It is deliberately SEPARATE from privacy_harness.py — the engine stays generic; t-tests etc. are
NOT hard-wired. You supply three callbacks; the module never assumes a particular test.

Callbacks (functional, not a class hierarchy):
    data_generator(rng, n) -> (n, p) array      # a scenario (null or non-null); YOU set effect/corr
    statistic(data)        -> (q,) output vec    # the researcher pipeline (e.g. per-variable t-stats)
    decide(output, n)      -> (q,) bool          # significance decision from the (noised) output
    mechanism              -> harness mechanism (y, D, S, subjects=...) -> NoiseModel

Metrics (clean vs privatized, on the SAME simulated datasets):
    per-variable reject rate  (Type-I under a null generator; power under a non-null generator)
    joint: at-least-one / all significant
    reject-rate DIFFERENCE (private - clean) with a PAIRED bootstrap CI over MC runs
    decision agreement + a clean/private confusion matrix

Nothing here is a DP guarantee. It measures whether the mechanism distorts statistical decisions.
"""
import numpy as np

def loo_statistic_artifacts(data, statistic):
    """LOO of a tabular statistic: full output, D (n, q) perturbations, S (q,) sensitivity."""
    n = data.shape[0]
    full = np.atleast_1d(statistic(data))
    D = np.array([np.atleast_1d(statistic(np.delete(data, i, axis=0))) - full for i in range(n)])
    return full, D, np.abs(D).max(0)

def _paired_bootstrap_ci(clean_col, priv_col, rng, n_boot=2000):
    """CI for (private - clean) reject rate, resampling MC iterations PAIRED (same index for both)."""
    m = len(clean_col); d = []
    for _ in range(n_boot):
        idx = rng.integers(0, m, m)
        d.append(priv_col[idx].mean() - clean_col[idx].mean())
    return float(np.quantile(d, .025)), float(np.quantile(d, .975))

def inference_experiment(data_generator, statistic, decide, mechanism, n, mc=1000,
                         mech_cfg=None, seed=0, n_boot=2000):
    """Run one scenario. Returns clean vs private reject rates, the paired-CI difference,
    decision agreement, and fallback rate. Interpret reject rate as Type-I under a null
    generator, as power under a non-null one."""
    rng = np.random.default_rng(seed); mech_cfg = mech_cfg or {}
    clean, priv, fb = [], [], 0
    for _ in range(mc):
        data = data_generator(rng, n)
        y, D, S = loo_statistic_artifacts(data, statistic)
        model = mechanism(y, D, S, subjects=data, **mech_cfg)
        noised = y + model.sample(rng)
        clean.append(np.atleast_1d(decide(y, n)))
        priv.append(np.atleast_1d(decide(noised, n)))
        fb += model.n_fallback                      # 0/1 per fresh model
    clean = np.array(clean, bool); priv = np.array(priv, bool)      # (mc, q)
    q = clean.shape[1]
    res = {"n": n, "mc": mc, "n_vars": q, "fallback_rate": fb / mc}
    for j in range(q):
        lo, hi = _paired_bootstrap_ci(clean[:, j].astype(float), priv[:, j].astype(float), rng, n_boot)
        res[f"reject_clean_v{j}"] = float(clean[:, j].mean())
        res[f"reject_private_v{j}"] = float(priv[:, j].mean())
        res[f"reject_diff_v{j}"] = float(priv[:, j].mean() - clean[:, j].mean())
        res[f"reject_diff_v{j}_lo"] = lo; res[f"reject_diff_v{j}_hi"] = hi
    res["reject_clean_any"] = float(clean.any(1).mean()); res["reject_private_any"] = float(priv.any(1).mean())
    res["reject_clean_all"] = float(clean.all(1).mean()); res["reject_private_all"] = float(priv.all(1).mean())
    cs, ps = clean.ravel(), priv.ravel()
    res["decision_agreement"] = float((cs == ps).mean())
    res["clean_sig_priv_sig"] = float((cs & ps).mean())
    res["clean_sig_priv_ns"]  = float((cs & ~ps).mean())
    res["clean_ns_priv_sig"]  = float((~cs & ps).mean())
    res["clean_ns_priv_ns"]   = float((~cs & ~ps).mean())
    return res

def inference_sweep(effect_sizes, correlations, n_list, statistic, decide, mechanisms,
                    p=2, mc=1000, seed=0, n_boot=1500, mech_cfgs=None):
    """Full grid: effect_size x correlation x N x mechanism (reproduces the older Monte-Carlo's axes).
    effect_sizes: list of per-variable effects (scalar -> all vars; tuple -> per-variable). An all-zero
    effect is labelled scenario='type1', otherwise 'power'. Returns tidy long-form with per-variable
    clean/private reject rates, paired-CI differences, decision agreement and fallback rate."""
    import pandas as pd
    mech_cfgs = mech_cfgs or {}; rows = []
    for eff in effect_sizes:
        eff_arr = np.full(p, eff, float) if np.isscalar(eff) else np.asarray(eff, float)
        scen = "type1" if np.allclose(eff_arr, 0) else "power"
        for corr in correlations:
            gen = gaussian_generator(effect=eff_arr, corr=corr, p=p)
            for n in n_list:
                for mname, mech in mechanisms.items():
                    r = inference_experiment(gen, statistic, decide, mech, n, mc=mc,
                                             mech_cfg=mech_cfgs.get(mname, {}), seed=seed, n_boot=n_boot)
                    for j in range(r["n_vars"]):
                        rows.append({"scenario": scen, "effect1": float(eff_arr[0]),
                                     "effect2": float(eff_arr[1]) if p > 1 else np.nan,
                                     "correlation": corr, "n": n, "mechanism": mname, "variable": j,
                                     "reject_clean": r[f"reject_clean_v{j}"],
                                     "reject_private": r[f"reject_private_v{j}"],
                                     "diff": r[f"reject_diff_v{j}"],
                                     "diff_lo": r[f"reject_diff_v{j}_lo"], "diff_hi": r[f"reject_diff_v{j}_hi"],
                                     "decision_agreement": r["decision_agreement"],
                                     "fallback_rate": r["fallback_rate"]})
    return pd.DataFrame(rows)


def type1_power_sweep(null_generator, alt_generator, statistic, decide, mechanisms,
                      n_list, mc=1000, seed=0, n_boot=1500, mech_cfgs=None):
    """Tidy long-form comparison of mechanisms on Type-I error (null scenario) and power (non-null),
    with paired-bootstrap CIs on the private-minus-clean difference. Returns a DataFrame."""
    import pandas as pd
    mech_cfgs = mech_cfgs or {}; rows = []
    for scen, gen in (("type1", null_generator), ("power", alt_generator)):
        for n in n_list:
            for mname, mech in mechanisms.items():
                r = inference_experiment(gen, statistic, decide, mech, n, mc=mc,
                                         mech_cfg=mech_cfgs.get(mname, {}), seed=seed, n_boot=n_boot)
                q = r["n_vars"]
                for j in range(q):
                    rows.append({"scenario": scen, "mechanism": mname, "n": n, "variable": j,
                                 "reject_clean": r[f"reject_clean_v{j}"],
                                 "reject_private": r[f"reject_private_v{j}"],
                                 "diff": r[f"reject_diff_v{j}"],
                                 "diff_lo": r[f"reject_diff_v{j}_lo"], "diff_hi": r[f"reject_diff_v{j}_hi"],
                                 "decision_agreement": r["decision_agreement"],
                                 "fallback_rate": r["fallback_rate"]})
    return pd.DataFrame(rows)

# ----- optional ready-made callbacks (kept here, NOT in the engine) -----
def make_onesample_ttest(alpha=0.05):
    """(statistic, decide) for a per-variable one-sample t-test vs 0. statistic -> t-stats; decide -> |t|>crit."""
    from scipy.stats import t as tdist
    def statistic(data):
        m = data.mean(0); sd = data.std(0, ddof=1); n = data.shape[0]
        return m / (sd / np.sqrt(n))
    def decide(tstats, n):
        return np.abs(np.atleast_1d(tstats)) > tdist.ppf(1 - alpha/2, df=n-1)
    return statistic, decide

def gaussian_generator(effect=0.0, corr=0.0, p=2):
    """rng, n -> (n, p) MVN with given per-variable effect (mean) and equicorrelation."""
    C = np.full((p, p), corr, float); np.fill_diagonal(C, 1.0)
    L = np.linalg.cholesky(C)
    mean = np.full(p, effect, float) if np.isscalar(effect) else np.asarray(effect, float)
    def gen(rng, n): return mean + rng.standard_normal((n, p)) @ L.T
    return gen