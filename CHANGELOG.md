# Changelog

All notable changes to AlteruPhono will be documented in this file.

## [Unreleased]

### 2.0 design (M0, for approval)
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
