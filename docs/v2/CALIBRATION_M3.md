# Calibration of the change model: M3, catalogue only (2026-11-13)

The question here: before any model is fitted to data, how good is the catalogue alone as P(reflex | proto-segment, environment), against simple baselines, on the held-out families of [TRAINING_SPLIT.md](../../TRAINING_SPLIT.md) (Austroasiatic/Vietic and Bora–Muinane)? M3 has no pass/fail gate (DESIGN §10); this report is the baseline that M4's gate is defined against.

Code: `alteruphono/model/extract.py` (pairs and opportunities) and `alteruphono/model/calibrate.py` (models and scoring). Data: the files listed in TRAINING_SPLIT.md §6, and `scripts/model/parse_diachronica.py` for Index Diachronica's rules (5,646, of which about 3,740 remain after leave-out).

## Data

| family | role | aligned pairs | dropped as ambiguous | opportunities | changed |
|---|---|---|---|---|---|
| Austroasiatic (Vietic) | held out | 371 | 3 | 1,080 | 577 |
| Bora–Muinane | held out | 835 | 259 (24%) | 4,628 | 2109 |
| Uto-Aztecan (3 datasets) | fitting (two baseline scalars only) | 3,104 | 501 (14%) | 12,550 | |

- **The ambiguity rule** (TRAINING_SPLIT.md §3) drops every pair with two optimal alignments that pair segments differently. That is 24% of Bora–Muinane's pairs. If ties fall more often on changed forms, the held-out change rate is biased downward; that has not been measured.
- **Changes are frequent:** 53% of Vietic and 46% of Bora–Muinane proto-segments differ from their reflex as transcribed. Some of that is transcription convention between a reconstruction and its daughters (length, vowel quality) and alignment error, not change. Nothing here separates them.

## Models

| model | P(change) | given a change, where to |
|---|---|---|
| uniform | π fitted on Uto-Aztecan (0.659 stay) | uniform over the candidates |
| distance | the same π | ∝ exp(−d/T), merkmal `descriptive` dissimilarity; T = 0.2 fitted on Uto-Aztecan |
| **catalogue** (M3) | **0.2, stipulated** (DESIGN §6.4) | catalogue rules that turn s into y in this environment, applied by the 2.0 engine (summed weight), + κ·kernel (κ = 1, T = 0.15, stipulated) |
| historia | blindrec's incumbent (`historia/direction.py`): identity 0.6, Index Diachronica counts smoothed toward a feature kernel | the same; it uses every Index Diachronica rule, Austroasiatic included |

The candidates are the daughter's segment inventory in its dataset, plus the source segment and deletion; they are the same for every model. Leave-out for the catalogue model is TRAINING_SPLIT.md §4, plus the evaluated family's own section (Austroasiatic for Vietic; Index Diachronica has no Bora–Muinane section).

## Results

The log-loss is the mean −log P(observed reflex) per opportunity; lower is better. It splits exactly into a *rate* part (did the segment change?) and a *shape* part (given that it changed, was the right reflex predicted?), shown separately. The 95% intervals are bootstraps over cognate sets: with two held-out families, a family bootstrap would mean nothing.

### Austroasiatic

| model | log-loss [95% CI] | rate part | shape part, given a change | mean P(change) | ECE of P(change) | ECE over all candidates |
|---|---|---|---|---|---|---|
| uniform | 2.689 [2.496, 2.876] | 0.769 | 3.594 | 0.341 | 0.193 | 0.0103 |
| distance | 2.224 [2.025, 2.417] | 0.769 | 2.724 | 0.341 | 0.193 | 0.0112 |
| catalogue | 2.628 [2.355, 2.883] | 0.964 | 3.115 | 0.200 | 0.334 | 0.0190 |
| historia | 3.166 [2.877, 3.440] | 1.016 | 4.024 | 0.274 | 0.261 | 0.0185 |

Paired log-loss differences, catalogue minus each baseline (bootstrap over cognate sets): uniform: -0.061 [-0.182, +0.062]; distance: +0.404 [+0.298, +0.517]; historia: -0.538 [-0.622, -0.454].

Reliability over all candidate probabilities (mean predicted → observed frequency, by bin):

- distance: 0.001→0.000 (n=277) · 0.002→0.000 (n=11781) · 0.006→0.007 (n=16231) · 0.017→0.026 (n=8468) · 0.042→0.094 (n=2653) · 0.659→0.466 (n=1080)
- catalogue: 0.000→0.002 (n=27269) · 0.002→0.020 (n=3851) · 0.006→0.033 (n=3568) · 0.018→0.079 (n=2574) · 0.055→0.062 (n=1888) · 0.128→0.038 (n=260) · 0.800→0.466 (n=1080)
- historia: 0.000→0.006 (n=26763) · 0.002→0.020 (n=4920) · 0.005→0.034 (n=2321) · 0.017→0.039 (n=2617) · 0.056→0.043 (n=2130) · 0.139→0.042 (n=577) · 0.292→0.195 (n=82) · 0.689→0.577 (n=870) · 0.879→0.005 (n=210)

### Bora-Muinane

| model | log-loss [95% CI] | rate part | shape part, given a change | mean P(change) | ECE of P(change) | ECE over all candidates |
|---|---|---|---|---|---|---|
| uniform | 2.293 [2.177, 2.418] | 0.717 | 3.457 | 0.341 | 0.114 | 0.0074 |
| distance | 1.867 [1.759, 1.991] | 0.717 | 2.523 | 0.341 | 0.114 | 0.0101 |
| catalogue | 2.204 [2.023, 2.430] | 0.855 | 2.960 | 0.200 | 0.256 | 0.0174 |
| historia | 2.474 [2.288, 2.715] | 0.784 | 3.710 | 0.294 | 0.161 | 0.0152 |

Paired log-loss differences, catalogue minus each baseline (bootstrap over cognate sets): uniform: -0.089 [-0.181, +0.018]; distance: +0.337 [+0.245, +0.443]; historia: -0.271 [-0.313, -0.229].

Reliability over all candidate probabilities (mean predicted → observed frequency, by bin):

- distance: 0.001→0.000 (n=234) · 0.002→0.001 (n=36520) · 0.005→0.007 (n=62867) · 0.017→0.012 (n=24792) · 0.050→0.094 (n=14570) · 0.659→0.544 (n=4628)
- catalogue: 0.000→0.003 (n=101877) · 0.002→0.018 (n=14803) · 0.006→0.066 (n=6957) · 0.019→0.049 (n=5460) · 0.061→0.082 (n=7995) · 0.130→0.094 (n=1891) · 0.800→0.544 (n=4628)
- historia: 0.000→0.006 (n=107980) · 0.003→0.023 (n=2972) · 0.006→0.044 (n=7050) · 0.017→0.036 (n=8307) · 0.060→0.050 (n=8866) · 0.144→0.089 (n=3401) · 0.342→0.150 (n=407) · 0.694→0.586 (n=4247) · 0.830→0.076 (n=381)

## What this shows

1. **The catalogue gives no usable rate.** DESIGN §6.1 predicted this. With the stipulated P(change) = 0.2, the catalogue model is badly calibrated: the held-out families change at 0.53 and 0.46, giving an ECE of P(change) of 0.33 and 0.26. Every model here predicts one constant rate, so the P(change) reliability curve has a single bin for each. The candidate-level curves above are the informative ones.
2. **As the shape of change, the catalogue loses to plain phonetic distance.** Given that a segment changed, the distance kernel fitted on Uto-Aztecan predicts the reflex better than the catalogue counts with their stipulated smoothing:
   - Vietic: shape part 2.72 for distance against 3.11 for the catalogue;
   - Bora–Muinane: 2.52 against 2.96.

   The catalogue model beats uniform and blindrec's incumbent, and loses to distance overall (intervals above). This is a negative result for the catalogue as a prior *on its own*. Whether it adds anything on top of data, through the learned weight λ, is M4's question; λ ≈ 0 is an allowed answer.
3. **blindrec's incumbent is the worst calibrated.** `historia/direction.py` has the highest log-loss on both families. Its reliability curve has a bin in which it assigns about 0.85 on average to outcomes that occur 0.5% (Vietic) and 7.6% (Bora–Muinane) of the time. I have not traced the cause; its fixed identity share interacting with renormalisation over the candidate set is a guess, not a finding. It has also seen Austroasiatic's catalogue section, which can only have helped it.

## Limits

- There are two held-out families, one of them small (1,080 opportunities).
- Only one fitting family is used here (Uto-Aztecan, for two scalars); the Wiktionary families arrive in M4.
- The catalogue model's constants are stipulated, not estimated.
- The insertion stream is not scored in M3.
- The model is one-step (DESIGN §6.3).
- Every proto-form is a reconstruction, so the circularity of TRAINING_SPLIT.md §5 applies.
