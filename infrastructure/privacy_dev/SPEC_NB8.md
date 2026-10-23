# SPEC — Notebook 8: full-release privacy investigation

Agreed spec (Lukas + assistant, 2026-10-21). Build target: a thorough empirical privacy
characterisation of the **tiled, blended whole-brain release** on OASIS, with a re-derived
per-statistic operating point, utility and fallback tracked throughout. Empirical privacy
only — no formal ε.

## Tier policy (what may change)
- **Tier 1 — invariant:** `mode_eigen_mech.py` (mechanism core: mode-space draw z = Σ aₘVₘ,
  covariance-identity, bar). Never edited.
- **Tier 2 — stable, extended ADDITIVELY only:** `privacy_harness.py`, `inference_eval.py`.
  Reused, never edited. New behaviour lives in a new module, never by patching these.
- **Tier 3 — freely editable:** `tiling.py`, the notebook, and the new attack module.

Upstream comparability with the *previous* NB8 privacy eval is explicitly NOT required; that
evaluation (LDA membership on the blended neighbourhood) is deprecated — see below.

## Attack layer (the core change)

### Membership — known-background projection score (PRIMARY; replaces the LDA)
Threat model (as already in the frozen harness `_worlds`): attacker knows the N−1 background
and the candidate target, hence knows `g_in` and `g_out` exactly. Optimal test is 1-D: project
the released map onto the known influence direction `Δ = g_in − g_out` and threshold.
- Per trial, world ∈ {in,out}: `R = g_world + noise`; score `s = Δ · R[attack_voxels]`.
- Advantage/threshold/CI computed by REUSING the frozen `ph._threshold_youden`, `ph._adv_at`,
  `ph._adv_ci` on the 1-D scores — identical advantage semantics (0 = private, 1 = exposed),
  no new metric code, no p≫n pathology (the old LDA estimated a p×p covariance from ~n/4 samples
  in a 6k-dim neighbourhood — deprecated).
- Orientation fixed: IN scores higher by ‖Δ‖² > 0, so no direction is learned.
- Analytic oracle for the natural-draw case (`k_check=0`, no rejection): the noise is then
  exactly N(0, scale²·Cov(LOO)), so the projected score is Gaussian and
  `advantage = 2Φ(SNR/2) − 1`, `SNR = ‖Δ‖² / sqrt(ΔᵀΣΔ)`, `ΔᵀΣΔ = scale²·Σ_m λ_m (Δ·V_m)²`.
  Used to validate the empirical projection attack (mode-space analog of `analytic_advantage`).
- A **white-box mode-space-whitened** projection is parked for later (not built now).

### Reconstruction — supervisor's attack, kept as the interpretable verdict
- Keep the frozen `reconstruction_attack` (inverts the known pipeline given N−1; honest for the
  mean, self-flags `identifiable=False` for median/variance). This is the differencing attack
  from NB1.1/NB2.1 generalised to the aggregate release.
- Add (additive) the **outlier-detectability** metric: reconstruct the target (mean release,
  identifiable), then test whether it is still flaggable as an outlier (IQR / z-score) relative
  to the cohort — the "did my neighbour participate?" question.

### Attack region for the blended membership game
The old peak-voxel "neighbourhood" box is retired. Because `s = Δ·R` gets ≈0 contribution from
voxels where `Δ≈0`, the region is defined as the **support of Δ**: the patches covering the top
**99%** of Δ's L2 energy. Justified by the attack's structure and bounded by compute, not by LDA
conditioning.

## Module structure
- New module **`full_release_attacks.py`**: projection scorer, analytic projection oracle,
  outlier-detectability. Leans on frozen helpers; edits nothing frozen.
- **`tiling.py`**: house the cached, resampleable **blended-release noise model**
  (`BlendedReleaseNoise`) as the single source of blend truth — it reuses `tile_boxes`,
  `_hann_window` and the exact `average`/`pou`/`pou_energy` math from `assemble_field`. This
  removes the duplicated `BlendedNeighborhoodNoise` + duplicated `_hann` that lived in the
  notebook (the drift source). **Fallback is aggregated per sample here** (the old blended class
  never updated `n_fallback` — bug fixed).

## Substrate & anchors
OASIS GM maps, GM mask as in NB8; N=40 (rank ceiling N−1=39). Statistics: mean, median,
variance. Starting operating point (to be re-derived by §5/§6): scale=3, k_check=39 (clamped to
each world's rank r=min(p,N−1)), max_draws=3000. Phantom fast-path for plumbing; OASIS for real.

## The three screens (restored, at 5³ / 50% overlap)
- **5a — fallback map (attack-free):** fallback vs (scale × max_draws) on representative 5³
  patches, per statistic → iso-0 curve (min max_draws per scale for ~0 fallback).
  Grids: scale {1,2,3,5,8,10}, max_draws {3k,10k,30k,100k}, "~0" = ≤0.5%.
- **5b — fallback → privacy/utility (the restored screen):** fix scale & k_check at the
  operating point, sweep max_draws so fallback runs high → ~0; at each level measure
  **projection membership advantage**, **inference validity** (Type-1/power via `inference_eval`,
  null + non-null one-sample t-test), AND **imaging utility** (rel-MSE). One figure per
  statistic. Decisive read: fallback→0 but advantage still high ⇒ magnitude (scale) is the
  binding lever, not tail-fill.
- **5c — k_check → privacy on the blended release:** scan k_check {8,16,26,39} at the scales that
  reach ~0 fallback (from 5a), measuring projection membership advantage. Scales where ~0
  fallback is unreachable are excluded.

## §6 — grid sweep & recommendation
scale × k_check × max_draws at 5³/50% first, then patch size × overlap, using the 5a/5b/5c
margins. Per config record: projection membership advantage + reconstruction verdict +
outlier-detectability + fallback + full utility panel (rel-MSE, neighbour-corr gap, Spearman,
SSIM) + inference validity. Output the privacy/utility **frontier** and a **per-statistic
operating-point recommendation** (mean/median/variance may differ).

## Cross-cutting
- Patch size is a real axis around 5³: **{3³, 5³, 7³}**. Overlap a free axis: **{0, 25, 50}%**
  (50% is the utility default, never privacy-validated — a free privacy variable).
- **Fallback metric:** tracked quantity is the **per-patch mean fallback fraction** (fraction of
  individual patch-draws that fell back); additionally log the **per-sample fallback count
  distribution**. The per-sample "any-fallback" rate is NOT used — it saturates to ~1 at
  whole-brain patch counts.
- **Parallelism:** config-level joblib across ~50 cores, BLAS pinned to 1 thread/worker (OMP/MKL/
  OPENBLAS/NUMEXPR via setdefault), serial path at `N_JOBS=1`, validated parallel==serial on the
  phantom. No parallelism inside frozen modules.
- Integrity hash on the two genuinely frozen files (`privacy_harness.py`, `inference_eval.py`)
  only — the dead `cov_diagnostics.py` entry is dropped.

## Mistakes to not repeat (carried from HANDOVER)
- Overlap and patch size are free privacy axes, not fixed/validated.
- Fallback is patch-SIZE driven; do not attribute it to the k_check change.
- The frontier spans all five free axes (scale, k_check, max_draws, patch size, overlap).
- Do not edit frozen modules to add parallelism — only own config loops.
