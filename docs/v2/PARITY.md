# Parity of alteruphono 2.0 with 1.x

This file records what the parity checks found, as they were run. Method: [`tests/parity/README.md`](../../tests/parity/README.md). Design: [DESIGN.md §8](DESIGN.md).

## M1: the C engine (2026-11-13)

**Reference.** Python 1.x at tag `v1.0.0rc1-simultaneous` (`b466d90`), with `3fdb52b` applied (D2). merkmal is branch `claude/alteruphono-support` (`af81477`), system `descriptive`. The harness seed is 20261113, and 7 for the sanity rerun.

### Engine: the C port of the engine against the Python reference

The Python reference here runs with merkmal's features and the fixed quantifier semantics: `--features merkmal --quantifiers fixed`.

| stream | cases | forward | backward | disagreements |
|---|---|---|---|---|
| catalogue: every `sound_changes.tsv` rule, TEST_ANTE forward and TEST_POST backward | 1,602 | 801 | 801 | **0** |
| regression: simultaneous application (tresoldi/alteruphono#1, blindrec's test) | 5 | 5 | 0 | **0** |
| blindrec: gate G1's rule stream (2,000 rules × 25 words, seed 800) | 50,000 | 50,000 | 0 | **0** |
| random: grammar over the whole notation, on catalogue words | 200,000 | 160,000 | 40,000 | **0** |

In the random stream, 3,057 cases are errors on both sides: unparseable rules, set mismatches, out-of-range back-references, and the backward cap. They count as agreements. They are not hidden: the C side's error count is in the report.

The C catalogue test (`tests/c/test_catalogue.c`) also checks all 801 test pairs directly: **801 of 801**.

### Features: what moving to merkmal changes (D1)

These are the differences between 1.x's own feature table and merkmal's labels, projected onto 1.x's vocabulary with the rules of DESIGN §4.1.

**By grapheme.** Over the 7,356 graphemes of 1.x's `sounds.tsv`:
- merkmal resolves 7,353 of them;
- for **7,342**, the projected labels equal 1.x's;
- the other 11 differ:

| grapheme(s) | 1.x | merkmal (projected) | reason |
|---|---|---|---|
| `ê̞ː ê̞ˑ ô̞ ô̞ː ô̞ˑ ø̞̂ ø̞̂ˑ ɤ̞̟̃` (8) | `mid` | `close-mid`, `lowered` | different description of lowered close-mid vowels |
| `ʈʂː` | `voiced` | `voiceless` | a 1.x data error |
| `ǃǃ` | `click consonant retroflex voiceless` | `consonant` only | merkmal reads the doubled grapheme as a two-click cluster; its per-click labels (`n1-…`, `n2-…`) are outside 1.x's vocabulary |
| `ⁿgǃ` | `nasal-click` | `click` | different click description |
| `k` + U+F268, `k` + U+F268 + `ʼ`, `oz̻` | (1.x labels) | not resolved | a private-use code point; a cluster; 1.x's behaviour for an unknown grapheme applies (no features) |

**By case.**
- catalogue: **0** differences;
- blindrec stream: **0** differences;
- random stream: 789 of 200,000.
  - 785 change only the features carried by some output element.
  - 4 change graphemes, because `ʈʂː` no longer matches the class `CV` (voiced consonant).

  Every one of the 789 involves `ʈʂː` or `ǃǃ`, which the random grammar draws on purpose.

**A mistake of mine, caught by this comparison.** The first projection rule dropped merkmal's `labial` everywhere. That also removed the only place label of the 42 bilabial clicks (`ʘ`, `gʘ`, `ŋʘ`, …), for which 1.x uses `labial` as the place. It showed up as feature-only differences on `ʘ`. The rule now drops `labial` only when a finer place label is present (DESIGN §4.1).

### Quantifiers: what fixing Q1/Q2 changes (D2)

There are 3,066 differences in the random stream, every one on a rule with a top-level `+` or `?`. None of the 801 catalogue rules, and none in blindrec's stream, has a quantifier. The fixed semantics are implemented twice, independently (C, and `oracle.py`), and the two agree on every case.

### Not covered in M1

The upstream Python tests and blindrec's outputs need the bindings; both are in M2 below.

### A weakness of 1.x, reproduced rather than fixed

`backward` undoes `@1[+voiced]` by applying `-voiced`, which removes voicing without adding voicelessness. The "undone" `d` keeps its grapheme and is deduplicated away. So `S > @1[+voiced] / V _ V` does not reconstruct `*t` from `d`; with `@1[-voiced,+voiceless]` written out, it does. 2.0 reproduces this, because a fix would change results (`tests/c/test_backward.c`). Should it be fixed? That is a question for Tiago.

## Speed, C level (M1)

Machine: this session's container. Both engines run on the same stream: 801 catalogue rules, and 200,000 C / 20,000 Python seeded pairs of (rule, catalogue word), mean 8.9 segments. Caches are warm on both sides. Scripts: `bench/bench_engine.c` and `bench/bench_python.py`. Three C runs and two Python runs:

| operation | Python 1.x (µs) | C (µs) | ratio | target (DESIGN §9) |
|---|---|---|---|---|
| forward | 25.0–27.0 | 0.14–0.19 | about 130–190× | ≥ 100×: **met** |
| backward | 31–37 | 0.98–1.3 | about 25–35× | ≥ 20×: met |
| parse a sequence | 12–19 | 0.9–1.3 | about 10–20× | (none) |
| parse a rule | 12–18 | 1.3–1.8 | about 8–13× | ≥ 20×: **not met** |

DESIGN §9's parse target was set against a cold-cache figure (68.9 µs) that I measured carelessly. Against the cold figure, the C parser is about 40× faster; against warm 1.x, which is the fair comparison, it is about 10×. Rule parsing is not on any hot path in blindrec. The Python-API numbers come in M2.

## M2: the Python bindings, and blindrec (2026-11-13)

### Upstream tests

The 233 tests of 1.x (`b466d90`) were run on 2.0 unchanged (`--continue-on-collection-errors`): **191 passed**, and 42 failed or could not be collected. Every one of the 42 tested something 2.0 removes or changes on purpose. After the edits listed below, the suite has 218 tests, all passing.

| tests | count | what happened | why |
|---|---|---|---|
| `test_features.py`: `TestTresoldiFeatureSystem` (4), `TestDistinctiveFeatureSystem` (4), `TestRegistry::test_get_tresoldi`, `::test_get_distinctive` | 10 | removed | 1.x's own feature systems are gone (decision 2) |
| `test_properties.py::TestScalarRoundtrip` | 1 | removed | the same (`distinctive`) |
| `test_resources.py`: `TestLoadSounds` (4), `TestLoadFeatures` (3) | 7 | removed; replaced by `TestLoadGraphemes` (3) | 1.x's feature tables are gone; the grapheme inventory remains |
| `test_features.py::TestRegistry::test_list_systems`, `::test_set_default` | 2 | edited: `['ipa']` only | the same |
| `test_regression.py::TestToneParsing::test_toned_sounds_have_tone_features` | 1 | edited: counts toned graphemes through merkmal's labels instead of 1.x's `sounds.tsv` names (still > 50) | the same |
| `test_integration.py::TestEndToEnd::test_import_api` | 1 | edited: version `2.0.0.dev0` | version |
| the 30 tests of `test_features.py` | (30) | the file could not be imported (it imported the removed modules); its other 18 tests pass unchanged once the imports are gone | the same |

`test_regression.py::TestAllTSVClasses::test_all_classes_loaded` failed at first, because I had dropped 1.x's development class `XXX` from the class pack. That was a gratuitous break, and `XXX` is back.

The other 211 upstream tests pass unchanged. They include the simultaneous-application tests, the parser's error messages, `backward`, the engine and ordering tests, the comparative module and the CLI.

### Feature values through the Python API

`get_system().grapheme_to_features` differs from 1.x for exactly **14 of the 7,356 graphemes** in 1.x's inventory. These are the 11 of the M1 table, plus the 3 that merkmal does not resolve (`k`+U+F268, `k`+U+F268+`ʼ`, `oz̻`), which 1.x described and 2.0 treats as unknown. blindrec's `phon.distance` (stage-5 costs) can change only for pairs that involve one of these 14.

### blindrec

**Method.** Two scratch copies of blindrec's code (`prototypes` branch `claude/tender-mccarthy-mve03r`, `ee986949`) were run side by side:
- **A** with its vendored 1.x;
- **B** with this branch's package in `vendor/alteruphono`.

blindrec's code was not changed. The sealing guard was on throughout, and nothing under `data/sealed/` was read or compared.

**Checks run, and results:**

| check | A (1.x) | B (2.0) | identical |
|---|---|---|---|
| blindrec's test suite | 25 passed, 1 skipped | 25 passed, 1 skipped | same result |
| gate G1, `scripts/check_soundengine.py 2000 800` | 50,000/50,000 agree, 6,217 changed | 50,000/50,000 agree, 6,217 changed | same result |
| simulator v4: `synth4 140 140s 141s` (uses alteruphono's `forward`) | | | **byte-identical** `data/work` |
| simulator v5: `synth5 800 800s` (uses alteruphono's features in `changegen`) | | | **byte-identical** `data/work` |
| v3 pipeline on `synth-140s`, `synth-800s`, `synth-140`: relatedness, cognates, phylo, yvyra, network, recon, morph, loans | | | **byte-identical** `data/work_v3`, except yvyra's run files (below) |
| v8 stage 5 (recon, loans) on the same three tracks, as `scripts/run_v8.sh` | | | **byte-identical** `data/work_v8` |

**yvyra's run files.** In all 57 of them, the only differences are a run ID header (`[ID: …]`). In the logs there are also three more lines: an unused clock-derived start-value seed (the analysis seed is set to 1), the MCMC stamp, and CPU time. None of these comes from alteruphono. The posterior samples, trees and consensus trees are otherwise identical.

**Not run.**
- The LexStat/SCA baselines stage needs lingpy, which is not installed here. It does not use alteruphono, and v8 does not read its outputs.
- The real tracks (Romance, Germanic, Tukanoan, Tier B) need data that are not in this environment. On them, results can differ only through the 14 graphemes listed above, and only if a track's inventory contains one of them.

**Speed in blindrec** (wall clock, one machine, sequential):

| stage | A (1.x) | B (2.0) |
|---|---|---|
| simulator v4, `synth4 140s` | 21.7 s | 11.1 s |
| simulator v4, `synth4 140 141s` | 217.8 s | 113.2 s |
| simulator v5, `synth5 800s 800` | 101.4 s | 109.2 s |
| v3 pipeline (sum of 3 tracks) | 1,073 s | 1,058 s |
| v8 stage 5 (sum of 3 tracks) | 44 s | 40 s |

As DESIGN §9 predicted, faster rule application roughly halves the v4 simulator's time. It leaves the v5 simulator (its own engine) and stage 5 (`expm` and EM) essentially unchanged; the 1–10% differences in those rows are within run-to-run noise. Any speed-up of stage 5 would have to come from the change model, not from this port.

## Speed through the Python API (M2)

`bench/bench_python.py` runs the same stream as M1, with 20,000 pairs, warm. Two runs of each:

| operation | 1.x (µs) | 2.0 (µs) | ratio | target |
|---|---|---|---|---|
| `forward` | 25.0–27.0 | 0.97–1.0 | about 25× | ≥ 20×: **met** |
| `backward` | 31–37 | 2.6–2.7 | about 12–14× | ≥ 20×: **not met** |
| `parse_rule`, uncached | 12–18 | 16–22 | about 1× (no faster) | ≥ 20×: **not met** |
| `parse_rule`, repeated text (cached by source) | 12–18 | 0.14–0.18 | (a cache hit) | |
| `parse_sequence` | 12–19 | 2.1–3.8 | about 5× | (none) |

The uncached Python parse is no faster than 1.x. The C parse takes 1.5 µs; the rest goes on decoding the token tree from JSON and building 1.x's dataclasses. Repeated rule texts are served from a bounded cache keyed on the exact source string, which is safe because a `Rule` is immutable.

## The change-model scorer (C) against the Python fitter (2026-11-13)

**What was compared.** `tests/parity/model_parity.py` exports M4's fitted parameters with each held-out family's catalogue. It then scores every opportunity in C (`ap_model_logprob`) and with the Python reference (`fit.py`'s design matrix).

**Agreement.** The largest difference of log-probabilities is **3.6 × 10⁻¹⁵**, over 184,101 candidate scores on 5,708 opportunities.

**Speed**, through the Python API on this machine, with about 37 candidates per opportunity:

| scorer | per opportunity | ratio |
|---|---|---|
| Python reference | 1.2–1.6 ms | |
| C, warm caches | 11–14 µs | about 100× |
| C, cold caches | 100–200 µs | every catalogue rule runs once per new environment |

DESIGN §9's targets were ≥ 20× (met) and ≤ 0.2 µs per opportunity in C. The second is **not met**: it comes to about 0.3–0.4 µs per *candidate*, including the Python crossing.
