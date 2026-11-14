# M4b plan: shape-only gate, and rate modelling (written and committed before any M4b number)

Tiago, 2026-11-13: "do both", after M4 failed its calibration gate ([CALIBRATION_M4.md](CALIBRATION_M4.md)). These are two new questions, not a rescoring of M4. M4's verdict stands.

## What has been seen, and what is fresh

**Vietic and Bora–Muinane, M4's held-out families.** Their results are known. Everything on them here is **post hoc** and is reported as such.

**Turkic**, the **fresh test family**. It was drawn by `random.Random(20261117).choice(sorted(["Japonic", "Turkic", "Uralic", "Uto-Aztecan"]))`. Its history in M4:
- **Used for fitting:** it was part of M4's fitting data.
- **Cross-validation:** it was one of the four folds of M4's σ selection. Only the total over the folds was looked at; Turkic's own fold loss was never printed or inspected.
- **Never evaluated as a test family.**

In M4b every model is refitted **without Turkic**, on Uto-Aztecan, Uralic and Japonic. A residual leak is admitted: M4's choice of grids and design saw a total that included Turkic.

## The split of each test branch

For each branch of a test family, the cognate sets (sorted ids) are shuffled with `random.Random(20261118)`. The first half is the **adaptation half A**, the rest the **evaluation half E**; an odd count gives E the extra set. Every score below is computed on E only, for every model, so that every comparison is made on the same opportunities.

## Models

All are fitted on Uto-Aztecan, Uralic and Japonic. The catalogue leave-out is as in M4: excluded sections, plus the opportunity's own family section, so Turkic's section "Altaic" is left out when Turkic is scored.

| model | what it is |
|---|---|
| F1 | M4's model. A single σ, chosen by leave-one-family-out over the three fitting families on M4's grid. |
| F2 | The same parameterisation with two shrinkage scales: σ_src for the source-feature and environment terms (g_sub, g_del, v_sub, v_del), and σ_rest for the rest (w, z, alpha). Grid σ_src ∈ {0.03, 0.1, 0.3, 1, 3} × σ_rest ∈ {0.01, 0.03, 0.1}, chosen by leave-one-family-out over the three fitting families. |
| F2-adapted | F2, with each test branch's offset α_b estimated by maximum a posteriori on the branch's A half (prior N(0, 1); every other parameter fixed). This is what blindrec does with a track: it fits the rate from the family's own data. |
| distance | As in M3/M4: π and T fitted on the three fitting families. |
| distance-adapted | distance with π_b = (stays + 1)/(n + 2), from the branch's A half. |
| uniform | as before |

## Q1: does the model predict the shape of change better than phonetic distance?

- **Metric.** The shape part of the log-loss, −log(P(y)/(1 − P(stay))), over the changed opportunities in E.
- **Gate Q1 (primary, on Turkic).** The paired difference F1 − distance, bootstrapped over cognate sets (1,000 replicates, seed 20261119), has a 95% interval below 0.
- **Also reported:** F2 − distance on Turkic; the same comparisons on Vietic and Bora–Muinane, labelled post hoc.

Q1 is the comparison that matters for blindrec's variant R. There blindrec supplies the rate and takes only the model's relative rates.

## Q2: can the rate be calibrated?

**Gate Q2 (primary, on Turkic E), both conditions required:**
1. The ECE of P(change) of F2-adapted is below 0.05. There are 10 equal-width bins, as in M4.
2. F2-adapted's total log-loss is lower than distance-adapted's, with the paired 95% interval below 0 (bootstrap seed 20261120).

**Also reported:**
- F1 and F2 unadapted, and F1 adapted, to separate the shrinkage effect from the adaptation effect.
- All of the above on Vietic and Bora–Muinane, labelled post hoc.

## What a pass would and would not mean

- **A pass on Q1** would say the model's shape is better than distance on one fresh family (proto-to-proto Wiktionary data) and two seen families. It would justify pre-registering blindrec's variant R. It would not justify variant O, which uses total probabilities.
- **A pass on Q2** would say that the rate is calibratable *once a branch's overall rate is estimated from its own data*. It would not say that rates transfer to an unseen branch: M4 says they do not.
- **A fail of either** is recorded as a fail. Nothing in this plan changes after its numbers are seen.
