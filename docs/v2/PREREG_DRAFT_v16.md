# DRAFT for Tiago's review: blindrec v16 pre-registration (variant R)

**Status: a draft.** It is not in blindrec's PREREG.md, not frozen, and nothing in it has been run. If approved, it goes into blindrec's PREREG.md (on a branch) as `## Learned relative rates in stage 5 (v16): plan (<date>)` before any v16 number exists. The follow-up recommended in [CALIBRATION_M4b.md](CALIBRATION_M4b.md) is variant R only: use the model's relative rates, never its P(change).

## Method

v16 = v8, with one change in stage 5.

**The change.** In `Substitution` (`recon.py`), the off-diagonal rates `Q[i, j] = exp(-cost(x, y, ctx))` become the change model's relative rates. In the model's notation, these are `exp(eta(y | x, L, R))` without the branch offset. They are renormalised per row so that each row keeps the **exit rate v8 would have given it**.

**What blindrec keeps.** The overall rate of change (`expm(Q·t·μ)`, with μ fitted per track) stays blindrec's own. The model decides only where a change goes, which is the part M4b found better than phonetic distance on three families.

**The model.**
- The pack is F2, refitted on all four fitting families (Uto-Aztecan, Uralic, Japonic, Turkic).
- Its catalogue feature uses the half-A catalogue of the simulator split below (D5) for the simulated test, and the full catalogue minus the track's own family section for the real tracks.
- It is frozen by fingerprint.

**Environment.** The cache key of `Substitution.P` gains the proto-environment (left and right proto-neighbours from `column_envs`). This is a small blindrec change; a test shows that v8 outputs are unchanged when the wrapped cost ignores the environment.

**Everything else is unchanged:** EM over observed changes, the v8 objective, its weights and its constants.

## The simulator and the catalogue (DESIGN D5, option a)

**The split.** Index Diachronica's family sections and alteruphono's catalogue rules are split into halves A and B with a recorded seed:
- by section for Index Diachronica;
- by rule id for alteruphono's catalogue, because it has no family labels.

**Who uses which half.**
- The change model's catalogue feature uses half A only.
- The **fresh test families** are generated with `changegen` restricted to half B. This needs a `source_filter` argument in `changegen.load_rules` / `sample_mixture`: a small change, tested for disjoint and stable halves.
- The development families stay as they are; they share the catalogue, and that is stated.

## Development, before freezing

- **Families:** the existing development families only. These are 700–709 full lists, plus the short variants of 140–163 (where v8 = v5).
- **Development gate:**
  - full lists: paired NED v16 − v8, 95% bootstrap upper bound below 0;
  - short lists: upper bound below +0.005.
- **If the development gate fails,** nothing is frozen, no held-out seeds are spent, and the failure is recorded.
- **Sizing:** the paired SD of v16 − v8 on 700–709 sets N = ⌈(2.8·SD/0.016)²⌉ per list length, capped at 100. The default is 60, as in DESIGN §10.

## Held-out test (scored once)

**Procedure:**
1. Freeze v16 at a commit.
2. Generate N fresh families per list length, from half B, with seeds from **7000** upwards. They are checked unused against `data/sealed`, `data/work*`, the archive and PREREG at freeze time.
3. Score once.

**Primary.** Paired NED v16 − v8, full and short lists: two co-primary comparisons, each passing if its 95% bootstrap upper bound is below 0.

**Secondary, developer-exposed.** The real tracks (Germanic, Romance strict and broad, Tukanoan, Tier B), reported as such. A `distance` variant is reported alongside: the same plug point, with relative rates from the M3 distance kernel. This separates "learned shape" from "any change at all to the rate prior".

## Expectations, stated before any result

The two earlier directional priors showed no effect: H4 at −0.001, and v12 failed its gate. v16 differs from both in three ways:
- it changes relative rates inside the likelihood, never post-editing columns;
- its gain over phonetic distance in shape is measured, at 0.17–0.27 nats per changed segment on three families;
- the catalogue's weight in it is learned.

A plausible effect on NED is small, −0.005 to −0.02. A null result is entirely possible and would be recorded.

## Cost and practicalities

- **Pipeline time:** about 11 minutes per full track and 4 per short track for v3 on this machine, plus stage 5 for v8 and v16. At N = 60, that is about 15 hours of computing.
- **Scorer speed:** the model's relative rates are currently computed by the Python fitter's design code. That is fast enough for development, but the C scorer (DESIGN §6.7) should exist before the held-out run.
- **Decisions for Tiago:**
  - approve, change or reject this plan;
  - the D5 split (as above);
  - whether the C scorer is a precondition.
