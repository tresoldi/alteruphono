# alteruphono 2.0: closing report (2026-11-14)

This is a short record of what 2.0 set out to do, and what came of each part. The figures come from the documents linked below; this file adds nothing new.

## The goal

The goal had two parts:
- rewrite alteruphono as a C99 library, with a stable C ABI and Python bindings that keep the 1.x API, on merkmal features only;
- add a probabilistic, directional model of change, P(reflex | source features, environment), learned from catalogues and from real correspondences, to improve blindrec's reconstruction (stage 5).

## Success criteria

| criterion | result | record |
|---|---|---|
| Behavioural parity with 1.x | **Met.** 0 engine disagreements in 251,607 cases. With merkmal features, 11 of 7,353 graphemes differ, all listed. | `PARITY.md` (M1) |
| 1.x Python API kept; blindrec unchanged | **Met.** 211 of 233 upstream tests pass unchanged; 18 tests were removed and 4 edited, by decision 2. blindrec's outputs are byte-identical on simulators v4 and v5, the v3 pipeline, v8 stage 5 and gate G1. | `PARITY.md` (M2) |
| Speed | **Partly met.** forward: C about 130–190× faster, Python API about 25× (met). backward: C about 25–35× (met), Python API about 12–14× (missed). Rule parsing: missed (C about 10×; an uncached Python parse is no faster than 1.x). Model scorer: about 100× faster, but 0.3–0.4 µs per candidate against a 0.2 µs target (missed). | `PARITY.md` |
| Calibration of the change model | **Shape met, rate failed.** The fitted model (M4) failed its pre-registered calibration gate on P(change) (ECE 0.166 and 0.095, threshold 0.05). The diagnosis (M4b) is that the rate is compressed, not shrunk. Its *shape*, i.e. where a changing segment goes, beats phonetic distance on every held-out family (Turkic −0.27 nats per changed segment, [−0.47, −0.05]). The rate passes only on Turkic. | `CALIBRATION_M3.md`, `CALIBRATION_M4.md`, `CALIBRATION_M4b.md` |
| A pre-registered held-out gain in blindrec's stage 5 | **Not met.** Method v16 passed its development gate on seen families, then failed both co-primaries, scored once on fresh half-B families: full lists +0.0041 [−0.0020, +0.0108] (25), short lists +0.0037 [−0.0020, +0.0093] (99). A distance-only control did no better. | blindrec `PREREG.md`, the three v16 sections |

## What 2.0 delivers

- **The engine.** A C99 core (`include/alteruphono.h`, `src/`) with SPE simultaneous application, quantifier bugs Q1 and Q2 fixed, and a bounded `backward`. It is checked by gcc and clang `-Werror` builds, ASan and UBSan, and four libFuzzer targets (`scripts/check.sh`).
- **Python.** `alteruphono._native` (abi3, Python ≥ 3.12) runs 1.x's Python API on the C core. merkmal is compiled with its `cc-by` data profile only.
- **The change model.** A multinomial logit over candidate reflexes, made of:
  - a distance base and directed displacement;
  - assimilation, source-feature and environment terms;
  - a catalogue weight;
  - branch offsets.

  It is fitted with L-BFGS, with σ chosen by leaving one family out, and comes with a Laplace covariance. It loads as a text pack, which the C scorer `ap_model_*` reads; that scorer matches the Python fitter to 3.6e-15.
- **The training split** was committed before any fit (`TRAINING_SPLIT.md`), and its four deviations are logged there.

## What the negative results mean

- **The model is good at shape and poor at rate.** Use its relative rates, not its P(change).
- **Its shape advantage does not help blindrec's stage 5** on simulated families. Replacing v8's own shares, by learned or by distance-based ones, gives no gain. The model should not be wired into blindrec on the strength of this work.
- **The development families misled.** Their paired spread was a fifth of the held-out spread, under a deliberate shift in distribution (half B of Index Diachronica). Any successor should size from a pilot run on the test distribution.

## Not done

- **Real tracks** (v16 with `v16_real.pack` on Romance, Germanic and Tukanoan): not run, because their data are not in this environment.
- **Release.** 2.0 is merged into alteruphono `master` after merkmal's branch (2026-11-14), but not tagged. The tags `v1.0.0rc1` and `v1.0.0rc1-simultaneous` exist locally only (the push was refused).
- **merkmal.** Its inventory and normalisation API is merged into merkmal `master` (`1a8a90c`); 2.0 builds against it.
