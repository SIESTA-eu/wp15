"""
bar_study.py — NEW Tier-3 module. Systematic comparison of the mechanism's rejection BAR:
  'l2'     : b_m = |D_{i*}·V_m|,  i* = argmax_i ||D_i||_2    (current single-subject L2 bar)
  'permax' : b_m = max_i |D_i·V_m|                           (per-mode max over subjects)

It does NOT edit the frozen mechanism (mode_eigen_mech.py). It CALLS the frozen building blocks
(patch_modes, loo_artifacts) and the validated direct sampler (tiling._direct_coeffs), assembling a
modes dict with whichever bar we want. The per-mode-max bar would be ~100% fallback under rejection
(infeasible); the direct sampler makes it free, because it samples the bar's conditional directly.

Privacy = known-background projection advantage (full_release_attacks.projection_membership).
Utility  = frozen utility_panel (rel-MSE, neighbour-corr gap, Spearman, bias).
Coverage = fraction of (subject, mode) influences the bar dominates.
Fallback = analytic diagnostic only (the direct sampler never actually falls back).
"""
import numpy as np
import privacy_harness as ph
import mode_eigen_mech as me
import tiling as T
import full_release_attacks as fra

PIPES = {"mean": ph.pipeline_mean, "median": ph.pipeline_median, "variance": ph.pipeline_variance}


# ---------------------------------------------------------------------------
# bar construction + coverage
# ---------------------------------------------------------------------------
def build_modes(D, scale, k_check=None, bar_kind="l2", k_noise=None):
    """Assemble a modes dict (compatible with tiling._direct_coeffs) for a chosen bar. Uses the frozen
    patch_modes for V, lam (centred SVD) and the raw (uncentred) subject projections for the bar —
    matching the frozen mechanism's own bar computation for bar_kind='l2'."""
    A = np.asarray(D, float).reshape(np.asarray(D).shape[0], -1)       # (N, p) raw LOO perturbations
    V, lam = me.patch_modes(A)                                         # V (p, r), lam (r,)  [frozen]
    r = lam.size
    k_noise = r if k_noise is None else int(min(k_noise, r))
    k_check = r if k_check is None else int(min(k_check, r))
    sd = scale * np.sqrt(np.clip(lam[:k_noise], 0.0, None))            # (k_noise,)
    proj = A @ V[:, :k_noise]                                          # (N, k_noise) subject·mode
    if bar_kind == "l2":
        istar = int(np.argmax(np.linalg.norm(A, axis=1)))
        bar = np.abs(proj[istar])
    elif bar_kind == "permax":
        bar = np.abs(proj).max(0)
        istar = int(np.argmax(np.linalg.norm(A, axis=1)))
    else:
        raise ValueError(f"bar_kind must be 'l2' or 'permax', got {bar_kind!r}")
    return {"V": V, "lam": lam, "sd": sd, "bar": bar, "k_noise": k_noise, "k_check": k_check,
            "r": r, "bar_kind": bar_kind, "istar": istar, "proj": proj}


def bar_coverage(modes):
    """Fraction of (subject, policed-mode) influences the bar dominates (|D_j·V_m| <= b_m). Overall,
    per-subject, and the worst/median subject. 1.0 => every subject covered in every policed mode."""
    proj = np.abs(modes["proj"]); bar = modes["bar"]; kc = int(modes["k_check"])
    covered = proj[:, :kc] <= bar[None, :kc]
    per_subject = covered.mean(1)
    return {"overall": float(covered.mean()), "min_subject": float(per_subject.min()),
            "median_subject": float(np.median(per_subject)), "per_subject": per_subject}


# ---------------------------------------------------------------------------
# a per-patch noise model the frozen attack/utility can consume
# ---------------------------------------------------------------------------
class DirectPatchNoise:
    """Rejection-free per-patch noise with a chosen bar. .sample / .sample_batch draw directly from the
    mechanism's output law (validated distribution-exact in tiling). fallback_rate is the ANALYTIC rate
    a rejection sampler WOULD see at max_draws (diagnostic only; nothing here ever falls back)."""
    def __init__(self, D, scale, k_check=None, bar_kind="l2", max_draws=3000):
        self.modes = build_modes(D, scale, k_check, bar_kind)
        self._q = T._patch_fallback_prob(self.modes, max_draws)
        self.cov = None; self.nominal_cov = None
    def sample_batch(self, n, rng):
        return T._direct_coeffs(self.modes, n, rng)          # (n, p)
    def sample(self, rng):
        return T._direct_coeffs(self.modes, 1, rng)[0]       # (p,)
    @property
    def fallback_rate(self):
        return float(self._q)


class OptionBPatchNoise:
    """Variance-inflation variant (SPEC_option_B): each policed mode is GAUSSIAN with its variance
    raised to cover the bar — sigma_m^2 = max(scale^2 * lam_m, b_m^2) — instead of a hard magnitude
    floor. No truncation, no rejection -> the noise stays Gaussian (inference-friendly) and covers b_m
    in EXPECTATION (high-probability), not every draw. Uses the per-mode-max bar by default."""
    def __init__(self, D, scale, k_check=None, bar_kind="permax"):
        m = build_modes(D, scale, k_check, bar_kind)
        self.modes = m
        k = int(m["k_noise"]); kc = int(m["k_check"])
        sd = np.asarray(m["sd"], float).copy()                 # scale*sqrt(lam), (k_noise,)
        bar = np.asarray(m["bar"], float)[:k]
        sd[:kc] = np.maximum(sd[:kc], bar[:kc])                # variance floor on policed modes
        self.sd_B = sd
        self.Vk = m["V"][:, :k]
        self.cov = None; self.nominal_cov = None
    def sample_batch(self, n, rng):
        A = rng.standard_normal((n, self.sd_B.size)) * self.sd_B[None, :]
        return A @ self.Vk.T
    def sample(self, rng):
        return self.sample_batch(1, rng)[0]
    @property
    def fallback_rate(self):
        return 0.0                                             # no rejection / fallback


def make_noise(D, scale, k_check, bar_kind, mech_kind):
    """Build the per-patch noise model for a mechanism variant: 'hardbar' (folded-tail direct sampler)
    or 'optionB' (variance-inflation Gaussian). Both use `bar_kind` (default per-mode-max)."""
    if mech_kind == "hardbar":
        return DirectPatchNoise(D, scale, k_check, bar_kind)
    if mech_kind == "optionB":
        return OptionBPatchNoise(D, scale, k_check, bar_kind)
    raise ValueError(f"mech_kind must be 'hardbar' or 'optionB', got {mech_kind!r}")


def mech_factory(scale, mech_kind, bar_kind="permax", k_check=None):
    """Wrap a variant as a frozen-contract mechanism(y,D,S,subjects=...) -> ph.NoiseModel, so
    inference_eval.inference_experiment can test its statistical-inference validity."""
    def mech(y, D, S, noise_power=None, subjects=None, **cfg):
        mdl = make_noise(D, scale, k_check, bar_kind, mech_kind)
        return ph.NoiseModel(lambda rng: mdl.sample(rng), cov=None)
    return mech


# ---------------------------------------------------------------------------
# target selection + two-world construction (remove-one game on a fixed cohort)
# ---------------------------------------------------------------------------
def select_targets(pool_stack, pipe):
    """Pick the two attack targets (indices into the cohort): 'istar' (the L2-largest subject, which
    the L2 bar covers) and 'worst' (the subject that pokes furthest above the L2 bar — where the L2 bar
    under-covers and per-mode-max should help)."""
    N = pool_stack.shape[0]
    _, D, _ = ph.loo_artifacts(pool_stack, pipe)
    A = D.reshape(N, -1); V, _ = me.patch_modes(A)
    proj = A @ V
    istar = int(np.argmax(np.linalg.norm(A, axis=1)))
    bar_l2 = np.abs(proj[istar])
    exceed = (np.abs(proj) - bar_l2[None, :]).max(1)         # how far each subject pokes above L2 bar
    worst = int(np.argmax(exceed))
    return {"istar": istar, "worst": worst, "exceed_worst": float(exceed[worst])}


def patch_worlds(pool_stack, pipe, scale, bar_kind, target_idx, k_check=None, mech_kind="hardbar"):
    """Remove-one two worlds on a fixed cohort: in-world = all N (target present), out-world = the N-1
    others. Returns clean stats + noise models for each world (bar/variance from each world's D).
    mech_kind selects 'hardbar' (folded-tail) or 'optionB' (variance-inflation Gaussian)."""
    N = pool_stack.shape[0]; bs = pool_stack.shape[1:]
    mask = np.ones(N, bool); mask[target_idx] = False
    stack_in = pool_stack                                    # N subjects (target included)
    stack_out = pool_stack[mask]                             # N-1 subjects
    g_in = pipe(stack_in).reshape(-1); g_out = pipe(stack_out).reshape(-1)
    _, D_in, _ = ph.loo_artifacts(stack_in, pipe)
    _, D_out, _ = ph.loo_artifacts(stack_out, pipe)
    m_in = make_noise(D_in, scale, k_check, bar_kind, mech_kind)
    m_out = make_noise(D_out, scale, k_check, bar_kind, mech_kind)
    return {"g_in": g_in, "g_out": g_out, "m_in": m_in, "m_out": m_out, "bs": bs}


# ---------------------------------------------------------------------------
# the comparison
# ---------------------------------------------------------------------------
def run_comparison(pool_stack, stat, scales, bars=("l2", "permax"), targets=("istar", "worst"),
                   n_trials=4000, n_rel=200, seed=0):
    """One cohort, one statistic: sweep bar x target x scale. Returns tidy rows with projection
    advantage, bar coverage, utility (rel-MSE, neighbour-corr gap, Spearman, bias), and the analytic
    fallback diagnostic."""
    import pandas as pd
    pipe = PIPES[stat]
    tsel = select_targets(pool_stack, pipe)
    rows = []
    for bar_kind in bars:
        for tname in targets:
            tidx = tsel[tname]
            for scale in scales:
                w = patch_worlds(pool_stack, pipe, scale, bar_kind, tidx)
                adv = fra.projection_membership(w["g_in"], w["g_out"], w["m_in"], w["m_out"],
                                                n_trials, np.random.default_rng(seed + 7), batch=True)
                cov = bar_coverage(w["m_in"].modes)
                util = ph.utility_panel(w["g_in"], w["m_in"], w["bs"], np.random.default_rng(seed),
                                        n_rel=n_rel)
                rows.append({"stat": stat, "bar": bar_kind, "target": tname, "scale": scale,
                             "adv": adv["advantage"], "adv_lo": adv["adv_ci"][0],
                             "adv_hi": adv["adv_ci"][1], "coverage": cov["overall"],
                             "cov_min_subj": cov["min_subject"], "fallback_diag": w["m_in"].fallback_rate,
                             "rel_mse": util["rel_mse"], "nc_gap": util["neighbour_corr_gap"],
                             "spearman": util["spearman"], "bias_norm": util["bias_norm"]})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# option-B comparison runners  (hardbar vs variance-inflation)
# ---------------------------------------------------------------------------
def run_mech_comparison(pool_stack, stat, scales, mechs=("hardbar", "optionB"),
                        targets=("istar", "worst"), bar_kind="permax", n_trials=4000, n_rel=200, seed=0):
    """Privacy + utility for the two MECHANISM variants (hardbar vs optionB) at the settled per-mode-max
    bar. Sweep mech x target x scale. Returns tidy rows (advantage, utility panel)."""
    import pandas as pd
    pipe = PIPES[stat]; tsel = select_targets(pool_stack, pipe); rows = []
    for mech_kind in mechs:
        for tname in targets:
            tidx = tsel[tname]
            for scale in scales:
                w = patch_worlds(pool_stack, pipe, scale, bar_kind, tidx, mech_kind=mech_kind)
                adv = fra.projection_membership(w["g_in"], w["g_out"], w["m_in"], w["m_out"],
                                                n_trials, np.random.default_rng(seed + 7), batch=True)
                util = ph.utility_panel(w["g_in"], w["m_in"], w["bs"], np.random.default_rng(seed),
                                        n_rel=n_rel)
                rows.append({"stat": stat, "mech": mech_kind, "target": tname, "scale": scale,
                             "adv": adv["advantage"], "adv_lo": adv["adv_ci"][0],
                             "adv_hi": adv["adv_ci"][1], "rel_mse": util["rel_mse"],
                             "nc_gap": util["neighbour_corr_gap"], "spearman": util["spearman"],
                             "bias_norm": util["bias_norm"]})
    return pd.DataFrame(rows)


def run_inference(scales, mechs=("hardbar", "optionB"), bar_kind="permax", n=40, mc=1000, seed=0,
                  effect_null=0.0, effect_alt=0.5, corr=0.3, p=2, n_boot=500):
    """Statistical-inference validity of each mechanism variant via inference_eval: Type-1 (null) and
    power (non-null) of a one-sample t-test, clean vs privatized. The DECIDING axis for option B —
    expectation: optionB (Gaussian) keeps Type-1 near alpha; the hard bar (non-Gaussian) inflates it."""
    import pandas as pd, inference_eval as ie
    stat, dec = ie.make_onesample_ttest(0.05)
    ng = ie.gaussian_generator(effect_null, corr, p); ag = ie.gaussian_generator(effect_alt, corr, p)
    rows = []
    for mech_kind in mechs:
        for scale in scales:
            mech = mech_factory(scale, mech_kind, bar_kind)
            r1 = ie.inference_experiment(ng, stat, dec, mech, n, mc=mc, seed=seed, n_boot=n_boot)
            r2 = ie.inference_experiment(ag, stat, dec, mech, n, mc=mc, seed=seed, n_boot=n_boot)
            q1, q2 = r1["n_vars"], r2["n_vars"]
            rows.append({"mech": mech_kind, "scale": scale,
                         "type1_clean": float(np.mean([r1[f"reject_clean_v{j}"] for j in range(q1)])),
                         "type1": float(np.mean([r1[f"reject_private_v{j}"] for j in range(q1)])),
                         "power_clean": float(np.mean([r2[f"reject_clean_v{j}"] for j in range(q2)])),
                         "power": float(np.mean([r2[f"reject_private_v{j}"] for j in range(q2)]))})
    return pd.DataFrame(rows)
