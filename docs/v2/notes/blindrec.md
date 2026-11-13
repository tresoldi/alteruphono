# Design note: blindrec and alteruphono 2.0

Read against `tresoldi/prototypes` branch `claude/tender-mccarthy-mve03r` (`ee986949`). Nothing in blindrec has been changed. Nothing in `data/sealed/` or `gold/` was read, and the guard was not touched.

## 1. Swapping the package in (M2)

blindrec vendors alteruphono at `607b9f5` plus `vendor/alteruphono-simultaneous.patch` (= upstream `b466d90`, now tagged locally as `v1.0.0rc1-simultaneous`). It puts the copy first on `sys.path` in `blindrec/__init__.py:6`.

The surface it uses:
- `parse_rule`, `parse_sequence`, `forward` (always on `# … #` sequences; it `str()`s elements and drops `""` and `#`);
- `features.get_system()` with `grapheme_to_features`, `features_to_grapheme`, `add_features` and `sound_distance`;
- `features.ipa.FEATURE_CATEGORIES`;
- `resources.load_sound_changes()` (`RULE` and `WEIGHT`).

alteruphono 2.0 keeps all of these (DESIGN §3.4).

**The swap** replaces the vendored directory with an installed 2.0 wheel, or a vendored 2.0 source tree with the built extension. There are no code changes in blindrec. `vendor/README.md` would record the new commit and drop the patch, which is upstream.

**The one change that could alter results** is `sound_distance`, which feeds stage-5 costs (`recon.py` `Costs`: `0.5 + 1.5·d`). DESIGN §4.4 (D3) keeps the 1.x geometry distance as a compatibility function, so that outputs can be byte-identical. Moving to merkmal's dissimilarity would be a blindrec analysis change and would need its own PREREG entry.

**Byte-identity check (DESIGN §8.4).**
- Tracks: simulated development seeds 140 and 141 (full and short), one family from 700–709, and the Romance and Tukanoan stage 1–5 runs, all via the existing scripts (`scripts/run_v8.sh`).
- Every file under `data/work*/<track>/` is compared. Every difference is traced to a listed engine or feature case.

## 2. The parity check that already exists

`scripts/check_soundengine.py 2000 800` compares blindrec's own engine (`soundengine.py`) with alteruphono, on 2,000 rules from `changegen.sample_mixture` × 25 words from `Simulator4(Params4(seed=800))`. The result was 50,000 of 50,000 in agreement, 6,217 of them changing the word.

Two points:
- That check covers simulator v5. Simulators v6, v7 and v9 reuse its engine, so they are covered by inheritance, not by their own check.
- The same stream is reused unchanged as alteruphono 2.0's differential test (DESIGN §8.2, suite 4a). That requires the locally fetched Index Diachronica, which is never committed.

## 3. The stage-5 test (M4): plan to be written into PREREG.md before any test family exists

This section is the outline of the PREREG section, `## Learned change model in stage 5 (v16): plan (<date>)`. It is not the section itself; that is written, committed and frozen in M4, after the calibration gate.

- **What changes.** v16 = v8 plus a change-model pack, the `full` variant, frozen by fingerprint. Two plug points, both already used by earlier experiments:
  - **R (rates).** `Substitution` (`recon.py:503`) takes `ap_model_rates(x, ·, env)` in place of `exp(−Costs)`, with EM kept. `DirectionalCosts` (`recon.py:1049`) is the template for the wrapper. The cache key of `Substitution.P` gains the environment, because today it is keyed by the column `ctx` only.
  - **O (objective).** At the v8 move score (`recon.py:1582`, `d = d_lik + V5_LAMBDA · d_irr`), add `λ₂ · Σ_d w_d · (−log P(y_d | x, env))`. `w_d` are the existing `independence_weights`, and env comes from `column_envs`. λ₂ = 1 is set a priori.
- **Development** happens only on development families: 700–709 full lists, plus the short variants of 140–163. Every number goes into PREREG before freezing, including the rejected variants (R, O, R+O).
- **Development gate.**
  - Full lists: paired v16 − v8, 95% bootstrap upper bound below 0.
  - Short lists: not worse (upper bound below +0.005).
  - If the gate fails, nothing is frozen and no held-out seeds are spent.
- **Held-out families.**
  - Freeze at a commit.
  - Generate N fresh families per list length, at 15 per template × 4 templates by default, so N = 60. Size N from the paired SD measured on development families (DESIGN §10).
  - Score once.
- **Seeds.** Proposed 7000–7059 and their short variants. They are checked against `data/sealed`, `data/work*`, the archive and the log at freeze time; any seed already in use is replaced with the next unused one.
- **Primary.** Paired NED v16 − v8, full and short lists, two co-primary comparisons, each with a 95% bootstrap upper bound below 0. On short lists v8 equals v5 by construction, because it switches only at 200 or more concepts, and this is stated.
- **Secondary, developer-exposed.** The real tracks (Germanic, Romance strict and broad, Tukanoan, the Tier B families), with the `data-only` and `catalogue-only` packs alongside to show what the catalogue contributes.
- **Circularity (DESIGN D5).** The simulator draws changes from Index Diachronica and from alteruphono's catalogue, and the `full` pack's prior uses them too. Recommended option (a):
  - split both catalogues into halves by source language family, with a recorded seed;
  - fit the pack's prior on half A;
  - generate the fresh test families from half B.

  This needs a filter in `changegen.sample_mixture`: a small, test-covered change on a branch. The `data-only` comparison is reported alongside.

## 4. Proposed small changes to blindrec (branch only, test-covered; none made yet)

1. **`changegen`: catalogue-half filter** for option (a) above. A `source_filter` argument to `load_rules` and `sample_mixture`, with a seeded split by section, plus a test that the halves are disjoint and stable.
2. **`Substitution.P` cache key with environment.** This prepares plug point R. It changes no default behaviour: when the wrapped cost ignores env, the cache key is equivalent. A test checks that v8 outputs are unchanged on one development track.
3. **`vendor/README.md` / `requirements.txt`** for alteruphono 2.0 (at M2).

## 5. What I expect, stated before any result

The two failed directional priors argue against expecting a large gain:
- The model's gain should show up where a correct segment is attested in a minority of daughters (60% of wrong segments) and the alternative is an implausible direction in that environment, such as *tʃ → k before a front vowel.
- On genuinely symmetric pairs (l/r), the model should do nothing.
- A plausible effect size is around −0.01 to −0.02 NED against v8, if there is any effect. At N = 60 that is near the minimum detectable effect, which is why N is sized from the development SD and not fixed at 20.
- A null result would be a finding about how much directional typology can add once the tree and regularity are in the objective. It would be recorded as such.
