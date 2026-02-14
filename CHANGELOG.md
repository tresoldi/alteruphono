# Changelog

All notable changes to AlteruPhono will be documented in this file.

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
