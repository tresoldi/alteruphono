# Changelog

All notable changes to AlteruPhono will be documented in this file.

## [Unreleased]

### 2.0: the change-model scorer in C
- `ap_model_load`, `ap_model_eta`, `ap_model_logprob` (src/model.c), a
  text pack format (alteruphono/model/pack.py exports it), Python access via
  `alteruphono.model.pack.ChangeModel`. Agrees with the Python fitter to
  3.6e-15 on 184,101 candidate scores; about 100x faster. Tested
  (tests/c/test_model.c), fuzzed (fuzz_model_load), ASan/UBSan clean.

### 2.0, M3 and M4: the change model
- M3 (docs/v2/CALIBRATION_M3.md): the catalogue alone gives no usable rate,
  and as the shape of change it loses to phonetic distance.
- M4 (docs/v2/CALIBRATION_M4.md): the fitted model (distance base, learned
  catalogue weight lambda = 0.265 +/- 0.012, directional displacement,
  assimilation, environment) beats every baseline on held-out log-loss, but
  **fails the pre-registered calibration gate** (ECE of P(change) 0.166 and
  0.095, threshold 0.05). M4 stops: no stage-5 test, no held-out seeds spent.
- TRAINING_SPLIT.md committed before any fit; four deviations logged.
- M4b (docs/v2/CALIBRATION_M4b.md, plan committed first): the model's shape
  of change beats phonetic distance on the fresh family (Turkic) and on both
  post hoc families; its rate passes on Turkic after per-branch adaptation
  but fails on both post hoc families. Use: relative rates only (blindrec
  variant R), not the model's P(change).
- The stage-5 test (blindrec PREREG, method v16: v8's rates shared by the
  model's relative rates; frozen at blindrec c4348cc9; C scorer ap_model_*)
  **fails on held-out families, scored once**: v16 - v8 mean NED +0.0041
  [-0.0020, +0.0108] on 25 full lists and +0.0037 [-0.0020, +0.0093] on 99
  short lists; a distance-only pack does no better. The development gain
  (-0.0019 full) did not carry over. The model's shape advantage over
  distance (M4b) stands, but it does not become a reconstruction gain in
  stage 5. Real tracks were not run (no data in this environment).

### 2.0, M2: Python bindings, and blindrec on 2.0
- `alteruphono._native` (abi3, Python >= 3.12) compiles the C core and
  merkmal (cc-by data profile only); the 1.x Python API runs on it unchanged.
- Removed (decision 2): 1.x's feature tables (`sounds.tsv` names,
  `features.tsv`), the `tresoldi` and `distinctive` systems, `load_sounds`,
  `load_features`. Kept: 1.x's label vocabulary, the grapheme inventory
  (`graphemes_1x.txt`), the class pack, the 1.x geometry distance (D3).
- Upstream tests: 211 of 233 unchanged and passing; 18 removed and 4 edited,
  each for a removed module (docs/v2/PARITY.md).
- blindrec with 2.0 in place of its vendored 1.x: byte-identical outputs on
  five simulated tracks (simulators v4 and v5) and through the v3 pipeline
  and v8 stage 5 on three of them; the v4 simulator runs about twice as fast.
- Python-API speed: forward about 25x faster than 1.x; backward about 12x and
  uncached parsing about 1x, short of the 20x target.
- My mistake: I first dropped the development class `XXX` from the class
  pack, a needless break caught by an upstream test; it is back.

### 2.0, M1: the C engine at parity
- C99 core (`include/alteruphono.h`, `src/`): parser, matcher, `forward`,
  `backward` and 1.x's syllabifier, on merkmal (`alteruphono-1` projection,
  DESIGN 4.1). Segments are interned per context; class tests are bitset
  operations. No global mutable state.
- Requires merkmal master at 1a8a90c or later (`mk_system_inventory`,
  `mk_unicode_normalize`; merged from merkmal's `claude/alteruphono-support`).
- Parity (docs/v2/PARITY.md): 0 disagreements with the Python reference on
  251,607 cases, including blindrec's 50,000-application gate stream and all
  801 catalogue test pairs. Feature changes from merkmal are confined to 11
  listed graphemes.
- Fixed relative to 1.x (D2): quantified rules apply simultaneously (Q1, Q2);
  `backward` keeps every alternative and a choice in the output is refused
  (from `3fdb52b`); `backward` refuses products over 100,000 candidates
  instead of building them.
- Tests (`tests/c/`), libFuzzer targets (`fuzz/`), `scripts/check.sh`
  (gcc/clang -Werror, ASan, UBSan, fuzzing), parity harness (`tests/parity/`),
  benchmarks (`bench/`).
- My mistake, caught by the parity harness: the first projection dropped
  `labial` everywhere, removing the place of bilabial clicks (`ʘ`).

### 2.0 design (M0, approved 2026-11-13 with the defaults of section 11)
- `docs/v2/DESIGN.md`: design of alteruphono 2.0 (C99 core on merkmal, Python
  bindings keeping the 1.x API, and a learned directional change model), with
  design notes for merkmal, regulae, yvyra, blindrec and historia in
  `docs/v2/notes/`. Nothing is implemented yet.
- Found while reading 1.x (not yet fixed; see DESIGN §2): quantified rules
  ignore or duplicate material (`p > b / V _ V?` changes nothing;
  `C? p > @1 b / V _` duplicates segments); the `ipa` system marks `ʈʂː` as
  voiced.

### Fixed
- Rule contexts are no longer consumed during matching: `forward()` and the
  probabilistic path of `apply_gradient()` now apply rules simultaneously
  (SPE-style), matching both contexts against the input. Previously
  `p > b / V _ V` turned `a p a p a` into `a b a p a`, and `t > :null: / t _`
  turned `a t t t a` into `a t t a`. `Rule` gains `left_len`/`right_len`
  (defaults 0, so hand-built rules are unaffected).

## [1.0.0rc1] - 2025-02-13

### Changed
- Rewrote all documentation: comprehensive guide (`docs/guide.md`) and slim
  API reference (`docs/api_reference.md`)
- Removed 3 broken docs files (`feature_systems.md`, `historical_linguistics.md`,
  `sound_change_tutorial.md`)
- Updated `README.md`: fixed stats, added sankoff method, added doc links,
  removed references to deleted `lenition_rule`/`fortition_rule`
- Rewrote `CHANGELOG.md` to cover pre-1.0 and 1.0 release-candidate releases

## [1.0.0rc0] - 2025-02-12

### Changed
- KISS/DRY/YAGNI cleanup: deduplicated feature system code into
  `features/common.py` (shared `add_features()`, `partial_match()`,
  `feature_distance()`, `sound_distance()`)
- Extracted shared modifier handling into `modifiers.py`
  (`apply_modifiers()`, `invert_modifiers()`)
- Made prosody `DEFAULT_SONORITY` configurable via
  `SyllableConstraints.sonority_scale`
- Simplified comparative module (`_find_root()` helper, removed dead code)

### Removed
- ~200 LOC of dead code and duplicated methods across feature systems
- Unused `grapheme_names` alias from `resources.py`
- Removed `lenition_rule` and `fortition_rule` helpers from engine

## [1.0.0b2] - 2025-02-11

### Added
- Complete feature geometry tree (Clements & Hume 1995) with Pharyngeal,
  Glottal, and TongueRoot nodes; breathy/creaky under Laryngeal
- Parser extensions: negation tokens (`!V`, `!p|b`), syllable conditions
  (`_.onset`, `_.nucleus`, `_.coda`), quantifiers (`C+`, `V?`)
- Rule ordering analysis: `analyze_interactions()`, `recommend_ordering()`,
  `Interaction` enum (feeding, bleeding, counterfeeding, counterbleeding)

### Fixed
- Feature alias resolution (`plosive` → `stop`) made public as
  `resolve_alias()` in `ipa.py`
- NegationToken parsed before `|` split in `_parse_atom()`
- Numerous phonological rule application bugs

## [1.0.0b1] - 2025-02-10

### Added
- Complete rewrite of AlteruPhono as a zero-dependency Python 3.12+ library
- All types as frozen dataclasses; sequences as tuples
- Union types (`type Token = ...`) with `isinstance()` dispatch
- Three pluggable feature systems: IPA categorical, Tresoldi, Distinctive
- `FeatureSystem` protocol for custom system registration
- 7,356-sound inventory from `sounds.tsv`
- Comparative module: `ComparativeAnalysis`, Needleman-Wunsch alignment
  (affine gaps, V-C penalty), `multi_align()`, NJ + UPGMA phylogeny,
  `reconstruct_proto()` (majority, conservative, parsimony, sankoff)
- Prosody module: `syllabify()` with Sonority Sequencing Principle
- Sound change engine: `SoundChangeEngine`, `CategoricalRule`, `GradientRule`,
  `RuleSet`, `apply_with_trajectory()`
- CLI with 6 subcommands (`forward`, `backward`, `features`, `systems`,
  `validate`, `apply-file`) and `--json` output
- 100% pass rate on 801 TSV sound change rules
- 227 tests across 17 test files

## [0.8.0] and earlier

Legacy versions with external `maniphono` dependency and `setup.py`-based
packaging. The 1.0.0b1 rewrite replaced the entire codebase.
