import numpy as np, sys
sys.path.insert(0, ".")
import privacy_harness as ph

print("ORACLE: empirical membership advantage must track analytic Mahalanobis (iid, matched power).\n")
src = ph.SyntheticBlockSource(N=60, block_shape=(4,4,4), spatial_corr=0.6)
base = ph.evaluate(src, ph.pipeline_mean, ph.mech_iid, k=2.0, n_trials=500, n_rel=10, seed=3)["noise_power"]
allok = True
for scale in [3, 10, 30, 100]:
    r = ph.evaluate(src, ph.pipeline_mean, ph.mech_iid, k=2.0, noise_power=base*scale,
                    n_trials=6000, n_rel=10, seed=3)
    ana, emp, lo, hi = r["analytic_adv"], r["empirical_adv"], r["adv_ci_lo"], r["adv_ci_hi"]
    ok = lo - 0.04 <= ana <= hi + 0.04; allok &= ok
    print(f"iid power x{scale:3d}: analytic={ana:.3f} empirical={emp:.3f} CI[{lo:.3f},{hi:.3f}] {'OK' if ok else 'MISMATCH'}")
print("\nORACLE", "PASSED" if allok else "FAILED")

print("\nUtility panel sanity (iid vs cov-gaussian, matched power) — spatial structure axis:")
for nm, mech in [("iid", ph.mech_iid), ("cov-gaussian", ph.mech_cov_gaussian)]:
    r = ph.evaluate(src, ph.pipeline_mean, mech, k=2.0, noise_power=base*30, n_trials=1000, n_rel=200, seed=3)
    print(f"  {nm:12s}: adv={r['empirical_adv']:.3f}  rel_mse={r['rel_mse']:.2f}  "
          f"nc_true={r['neighbour_corr_true']:.2f} nc_rel={r['neighbour_corr_released']:.2f} "
          f"gap={r['neighbour_corr_gap']:.2f}  spearman={r['spearman']:.2f}  bias={r['bias_norm']:.3f}")