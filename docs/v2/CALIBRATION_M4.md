# Calibration gate of the fitted change model: M4 (2026-11-13). **Failed.**

The gate is the one DESIGN §10 fixed before any fit, on the held-out families of [TRAINING_SPLIT.md](../../TRAINING_SPLIT.md) (Austroasiatic/Vietic, Bora–Muinane):

1. the fitted model's log-loss beats every baseline, with the paired 95% interval against the best baseline below 0;
2. the ECE of P(change) is below 0.05;
3. reported, not pass/fail: the l/r asymmetry interval covers 0.

**Condition 1 passes on both families. Condition 2 fails on both** (ECE 0.166 and 0.095). Under the plan, M4 stops here:
- the stage-5 test in blindrec is not pre-registered or run;
- no held-out seeds are spent;
- the model is not tuned until it passes.

Code: `alteruphono/model/fit.py` (the model, fitting, uncertainty) and `alteruphono/model/gate.py` (this gate). The model is DESIGN §6 as revised after M3, with Tiago's approval: phonetic distance is the base shape, and the catalogue is a correction with a learned weight. The parameterisation is in `fit.py`'s docstring.

## The fit

- **Data:** 27,210 opportunities from 54 branches in four families (Uto-Aztecan, Uralic, Japonic, Turkic); 438 parameters.
- **Shrinkage:** σ = 0.03, chosen by leave-one-family-out log-loss over the fitting families. The grid values tried were σ=0.01: 1.6370, σ=0.03: 1.6358, σ=0.1: 1.6600, σ=0.3: 1.6927, σ=1.0: 1.7406, σ=3.0: 1.7916.
- **Distance base:** β = 5.48 ± 0.10.
- **Catalogue weight:** λ = 0.265 ± 0.012 (Laplace) on log(1 + catalogue count). It is clearly nonzero: once exposure and distance are modelled, the catalogue does add information about where change goes. With each family's own Index Diachronica section left out, this λ is not an echo of the family's own entries.

## Results on the held-out families

The baselines' scalars were refitted on all four fitting families. The fitted model predicts each held-out branch with its branch offset at 0, the population mean.

### Austroasiatic

| model | log-loss [95% CI] | rate part | shape part, given a change | mean P(change) (observed 0.534) | ECE of P(change) | ECE over all candidates |
|---|---|---|---|---|---|---|
| fitted | 1.970 [1.776, 2.157] | 0.610 | 2.547 | 0.423 | 0.166 | 0.0067 |
| distance | 2.178 [1.991, 2.359] | 0.723 | 2.724 | 0.409 | 0.126 | 0.0079 |
| uniform | 2.643 [2.464, 2.818] | 0.723 | 3.594 | 0.409 | 0.126 | 0.0067 |
| catalogue | 2.628 [2.355, 2.883] | 0.964 | 3.115 | 0.200 | 0.334 | 0.0190 |
| historia | 3.166 [2.877, 3.440] | 1.016 | 4.024 | 0.274 | 0.261 | 0.0185 |

Paired log-loss differences, fitted minus each baseline (bootstrap over cognate sets): uniform: -0.673 [-0.749, -0.597]; distance: -0.208 [-0.268, -0.153]; catalogue: -0.658 [-0.755, -0.561]; historia: -1.196 [-1.336, -1.061].

Reliability of the fitted P(change) (mean predicted → observed, n): 0.20→1.00 (6) · 0.26→0.35 (226) · 0.34→0.26 (354) · 0.45→0.52 (131) · 0.55→0.84 (191) · 0.64→0.99 (160) · 0.73→1.00 (12).

### Bora-Muinane

| model | log-loss [95% CI] | rate part | shape part, given a change | mean P(change) (observed 0.456) | ECE of P(change) | ECE over all candidates |
|---|---|---|---|---|---|---|
| fitted | 1.727 [1.622, 1.853] | 0.684 | 2.288 | 0.426 | 0.095 | 0.0048 |
| distance | 1.843 [1.743, 1.959] | 0.694 | 2.523 | 0.409 | 0.047 | 0.0074 |
| uniform | 2.269 [2.162, 2.385] | 0.694 | 3.457 | 0.409 | 0.047 | 0.0030 |
| catalogue | 2.204 [2.023, 2.430] | 0.855 | 2.960 | 0.200 | 0.256 | 0.0174 |
| historia | 2.474 [2.288, 2.715] | 0.784 | 3.710 | 0.294 | 0.161 | 0.0152 |

Paired log-loss differences, fitted minus each baseline (bootstrap over cognate sets): uniform: -0.543 [-0.577, -0.512]; distance: -0.117 [-0.137, -0.095]; catalogue: -0.477 [-0.575, -0.387]; historia: -0.748 [-0.868, -0.646].

Reliability of the fitted P(change) (mean predicted → observed, n): 0.20→0.45 (60) · 0.24→0.24 (396) · 0.36→0.42 (1362) · 0.43→0.55 (1530) · 0.56→0.44 (1261) · 0.60→0.95 (19).

### l/r asymmetry (sanity check)

Between vowels, η(l→r) − η(r→l) = +0.063, 95% interval [-0.052, +0.179]. It covers 0, as expected: the model finds no l/r direction, as Index Diachronica does not (14 against 15).

## Why it fails, and what this does not show

- **The model predicts the shape of change better than every baseline, with intervals that exclude 0, on both families.** Given that a segment changed, its shape part is lower than distance's on both (2.55 against 2.72 on Vietic, 2.29 against 2.52 on Bora–Muinane). Its *rate* log-loss is also the lowest of all models. It discriminates which segments change better than a constant rate does.
- **What fails is the calibration of that rate.** The predicted P(change) is too compressed. On Vietic, segments predicted at 0.55–0.64 change 84–99% of the time, and segments predicted at 0.34 change 26% of the time. Both held-out families also change more often overall than the model's population-mean branch (0.53 and 0.46 observed, against 0.42–0.43 predicted).
- **Two causes are plausible; neither has been tested:**
  - the strong shrinkage chosen by cross-validation (σ = 0.03) flattens the predicted rates;
  - a branch's overall rate (its time depth) cannot be known for an unseen branch. That is exactly what the branch offset absorbs in fitting and sets to 0 in prediction.
- **A comparison that cuts against the gate's reading:** on Bora–Muinane, the distance baseline's single constant rate happens to have an ECE of 0.047, below the threshold, although its rate log-loss is worse than the fitted model's. ECE rewards a constant predictor that happens to match the mean. The threshold was fixed beforehand, and it stands.

## Deviations

- **The grid was extended downward.** The σ grid was first (0.1, 0.3, 1, 3), and 0.1, its edge, won. It was extended down to 0.01 before the held-out families were scored. The choice uses only leave-one-family-out loss on the fitting families.
- **No insertion stream.** The insertion stream is not modelled or scored.

## What would come next (for Tiago; nothing has been done)

Rescoring this gate in another way is excluded. Any of the following is a new question, to be planned before its data are looked at:

- **Shape-only use in blindrec.** blindrec's stage 5 supplies its own rates (`expm(Q·t·μ)` with μ fitted per track), and DESIGN's variant R takes only the model's *relative* rates. A gate on the shape part alone fits that use. The fitted model passes the shape comparison here, but a gate set after seeing this result would not be pre-registered. It would need fresh held-out data, or would have to be stated as post hoc.
- **Rate modelling.** A rate that depends on branch depth (known in blindrec from the dated tree), and a test of whether weaker shrinkage of the source-feature terms fixes the compression.
