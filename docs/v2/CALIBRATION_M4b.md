# M4b results: shape-only gate and rate modelling (2026-11-13)

The plan is [PLAN_M4b.md](PLAN_M4b.md), committed before any of these numbers was computed, and its code (`alteruphono/model/m4b.py`) was committed before the results. Every model is refitted on Uto-Aztecan, Uralic and Japonic. Turkic is the fresh test family; Vietic and Bora–Muinane are **post hoc**, since M4 saw them. All scores are on the evaluation halves E.

## Verdicts

| question | Turkic (fresh, primary) | Vietic (post hoc) | Bora–Muinane (post hoc) |
|---|---|---|---|
| **Q1** shape part, F1 − distance | -0.272 [-0.471, -0.047] **pass** | -0.188 [-0.343, -0.051] **pass** | -0.172 [-0.225, -0.122] **pass** |
| **Q2** F2-adapted: ECE < 0.05, and log-loss − distance-adapted < 0 | ECE 0.038; log-loss -0.052 [-0.099, -0.014] **pass** | ECE 0.138; log-loss -0.227 [-0.294, -0.157] **fail** | ECE 0.088; log-loss -0.104 [-0.129, -0.081] **fail** |

**Both gates pass on the primary, fresh family.** Q1 also holds on both post hoc families. **Q2 fails on both post hoc families**, on the ECE condition.

## The fit

- **F1:** σ = 0.01. **F2:** σ_src = 0.03, σ_rest = 0.03. Both were chosen by leave-one-family-out over the three fitting families.
- **Catalogue weight:** λ = 0.262 (F1), 0.261 (F2), as in M4.
- **Shrinkage.** Cross-validation did not prefer weaker shrinkage of the source-feature terms: it chose the same scale for both blocks. M4 had suggested that strong shrinkage compressed the rates. This result does not support that cause. F2's gain over F1 is small everywhere.

## All models, evaluation halves

The per-branch adaptation estimates each test branch's overall rate from its A half and nothing else: its offset for the fitted models, π for distance.

### Turkic (primary (fresh); 864 opportunities in E)

| model | log-loss | rate part | shape part, given a change | mean P(change) (observed 0.157) | ECE of P(change) |
|---|---|---|---|---|---|
| F1 | 1.046 | 0.663 | 2.435 | 0.461 | 0.309 |
| F1-adapted | 0.800 | 0.417 | 2.435 | 0.192 | 0.038 |
| F2 | 1.035 | 0.656 | 2.406 | 0.453 | 0.301 |
| F2-adapted | 0.794 | 0.416 | 2.406 | 0.192 | 0.038 |
| distance | 1.026 | 0.600 | 2.706 | 0.424 | 0.267 |
| distance-adapted | 0.846 | 0.420 | 2.706 | 0.195 | 0.040 |
| uniform | 1.131 | 0.600 | 3.372 | 0.424 | 0.267 |

F2-adapted reliability of P(change) (mean predicted → observed, n): 0.08→0.06 (219) · 0.16→0.13 (285) · 0.23→0.20 (202) · 0.33→0.22 (112) · 0.43→0.32 (37) · 0.54→0.80 (5) · 0.66→0.50 (4).

### Austroasiatic (post hoc (seen in M4); 539 opportunities in E)

| model | log-loss | rate part | shape part, given a change | mean P(change) (observed 0.527) | ECE of P(change) |
|---|---|---|---|---|---|
| F1 | 1.924 | 0.620 | 2.475 | 0.459 | 0.205 |
| F1-adapted | 1.910 | 0.606 | 2.475 | 0.542 | 0.153 |
| F2 | 1.886 | 0.591 | 2.458 | 0.444 | 0.127 |
| F2-adapted | 1.866 | 0.570 | 2.458 | 0.537 | 0.138 |
| distance | 2.116 | 0.713 | 2.662 | 0.424 | 0.103 |
| distance-adapted | 2.092 | 0.689 | 2.662 | 0.541 | 0.015 |
| uniform | 2.606 | 0.713 | 3.592 | 0.424 | 0.103 |

F2-adapted reliability of P(change) (mean predicted → observed, n): 0.25→0.12 (17) · 0.36→0.18 (82) · 0.45→0.43 (154) · 0.54→0.32 (93) · 0.66→0.78 (96) · 0.75→0.99 (86) · 0.82→1.00 (11).

### Bora-Muinane (post hoc (seen in M4); 2354 opportunities in E)

| model | log-loss | rate part | shape part, given a change | mean P(change) (observed 0.477) | ECE of P(change) |
|---|---|---|---|---|---|
| F1 | 1.792 | 0.669 | 2.352 | 0.431 | 0.083 |
| F1-adapted | 1.703 | 0.580 | 2.352 | 0.458 | 0.108 |
| F2 | 1.785 | 0.686 | 2.301 | 0.444 | 0.084 |
| F2-adapted | 1.697 | 0.598 | 2.301 | 0.456 | 0.088 |
| distance | 1.903 | 0.698 | 2.524 | 0.424 | 0.053 |
| distance-adapted | 1.801 | 0.596 | 2.524 | 0.458 | 0.027 |
| uniform | 2.353 | 0.698 | 3.467 | 0.424 | 0.053 |

F2-adapted reliability of P(change) (mean predicted → observed, n): 0.15→0.16 (189) · 0.23→0.33 (628) · 0.37→0.18 (363) · 0.46→0.35 (68) · 0.56→0.74 (170) · 0.65→0.70 (613) · 0.75→0.75 (323).

## What this shows

1. **Shape: the model is better than phonetic distance on every family tested,** including one it was never evaluated on. This is the part blindrec's variant R would use: relative rates among the candidate reflexes, with blindrec supplying the overall rate. It justifies drafting that pre-registration.
2. **Rate: it cannot be relied on.** Adapting the branch offset fixes the *level* of P(change) everywhere. On Vietic and Bora–Muinane, however, the model's ordering of *which* segments change is miscalibrated:
   - on Vietic, predicted 0.54 → observed 0.32, and predicted 0.75 → observed 0.99;
   - the adapted distance baseline, which predicts one rate per branch, is calibrated on all three families (ECE 0.040, 0.015, 0.027).

   Turkic passes Q2, but it is a low-change family (0.16 observed, proto-to-proto Wiktionary data), where most predictions sit in the easy low bins. One fresh pass against two seen failures does not license using the model's P(change).
3. **Consequence for blindrec.** Use the model's relative rates only (variant R). Do not use its total probabilities in the v8 objective (variant O). The stay probability must come from blindrec's own rate, μ·t.

## Limits

- There is one fresh family, of proto-to-proto data, with 864 opportunities in E.
- The post hoc families were seen in M4.
- The ambiguity rule of the aligner and the circularity of reconstructed data (TRAINING_SPLIT.md §5) apply throughout.
- The insertion stream is not modelled.
