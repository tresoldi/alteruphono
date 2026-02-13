# AlteruPhono

[![PyPI](https://img.shields.io/pypi/v/alteruphono.svg)](https://pypi.org/project/alteruphono)

AlteruPhono is a Python library for modeling phonological sound changes in
historical linguistics. It lets you define rules in standard notation
(`p > b / V _ V`), apply them forward to simulate language evolution, and apply
them backward to reconstruct proto-forms.

Zero dependencies, strict typing, frozen dataclasses, and ~3,000 lines of
source covering the full pipeline from parsing to comparative reconstruction.

## Documentation

- **[Comprehensive Guide](docs/guide.md)** — Theory, tutorials, and a worked
  Proto-Romance case study for grad students and researchers
- **[API Reference](docs/api_reference.md)** — Signatures and brief descriptions
  for all public modules

## Installation

```bash
pip install alteruphono
```

Development install:

```bash
git clone https://github.com/tresoldi/alteruphono.git
cd alteruphono
pip install -e ".[dev]"
```

Requires Python 3.12+. No runtime dependencies.

## Quick Start

### Python API

```python
import alteruphono

# Parse a rule and a sequence
rule = alteruphono.parse_rule("p > b / V _ V")
seq  = alteruphono.parse_sequence("# a p a #")

# Apply forward (simulate evolution)
result = alteruphono.forward(seq, rule)
print(" ".join(str(e) for e in result))
# → # a b a #

# Apply backward (reconstruct proto-forms)
daughter = alteruphono.parse_sequence("# a b a #")
protos = alteruphono.backward(daughter, rule)
for proto in protos:
    print(" ".join(str(e) for e in proto))
# → # a b a #
# → # a p a #
```

### Command Line

```bash
# Forward application
alteruphono forward "p > b / V _ V" "# a p a #"
# → # a b a #

# Backward reconstruction
alteruphono backward "p > b" "# a b a #"
# → # a b a #
# → # a p a #

# Inspect features
alteruphono features p
# → Grapheme: p
# → Partial: False
# → Features: bilabial, consonant, stop, voiceless

# JSON output
alteruphono --json forward "p > b / V _ V" "# a p a #"
# → {"rule": "p > b / V _ V", "input": "# a p a #", "output": "# a b a #"}
```

## Rule Notation

Rules follow the standard linguistic notation `ante > post / context`:

| Syntax | Meaning | Example |
|--------|---------|---------|
| `p > b` | p becomes b | Unconditional voicing |
| `p > b / V _ V` | p becomes b between vowels | Intervocalic voicing |
| `C > :null: / _ #` | Delete consonant before word boundary | Final consonant deletion |
| `C+ > :null: / _ #` | Delete consonant cluster before boundary | Cluster deletion |
| `C? V > :null: @2` | Optional consonant before vowel | Quantified pattern |
| `p\|b > f` | p or b becomes f | Choice in ante |
| `{p\|b} > {f\|v}` | p↔f, b↔v correspondence | Set correspondence |
| `C N > @1 / _ #` | Drop nasal, keep consonant | Back-reference (`@1` = matched C) |
| `C > @1[+voiced]` | Voice the matched consonant | Feature modifier |

### Key elements

- `#` — word boundary
- `_` — focus position in context
- `:null:` — deletion
- `@1`, `@2`, ... — back-references to matched positions (1-indexed)
- `@1[+voiced]` — back-reference with feature modification
- `p|b` — choice (match either)
- `{p|b}` — correspondence set
- `C+` — one or more consonants (quantifier)
- `V?` — zero or one vowel (quantifier)
- `_.onset`, `_.nucleus`, `_.coda` — syllable position conditions
- `V`, `C`, `N`, `S`, `L`, `K` — sound classes (loaded from TSV data)
- `>` or `→` — rule operator (`->` also accepted)

## Core API

All types are frozen dataclasses. Sequences are tuples.

### Types

```python
from alteruphono import Sound, Boundary, Rule, MatchResult

# Phonological primitives
Sound(grapheme="p", features=frozenset({"consonant", "voiceless", ...}), partial=False)
Boundary(marker="#")

# A parsed rule
Rule(source="p > b", ante=(...), post=(...))

# Match result
MatchResult(matched=True, bindings=(...))
```

### Token types (rule pattern elements)

```python
from alteruphono import (
    SegmentToken,      # Concrete sound
    BoundaryToken,     # Word boundary (#)
    BackRefToken,      # Back-reference (@1, @2)
    EmptyToken,        # Deletion (:null:)
    ChoiceToken,       # Alternatives (p|b)
    SetToken,          # Correspondence set ({p|b})
    FocusToken,        # Focus position (_)
    QuantifiedToken,   # Quantifier (C+, V?)
    SyllableCondToken, # Syllable condition (_.onset)
)
```

### Functions

```python
import alteruphono

# Parsing
rule = alteruphono.parse_rule("p > b / V _ V")
seq  = alteruphono.parse_sequence("# a p a #")

# Matching
result = alteruphono.match_pattern(seq, rule.ante)
# → MatchResult(matched=True/False, bindings=(...))

# Forward application (simulation)
output = alteruphono.forward(seq, rule)

# Backward reconstruction
protos = alteruphono.backward(seq, rule)
# → list of possible proto-form tuples
```

## Feature Systems

AlteruPhono ships with three pluggable feature systems backed by a TSV
inventory of 7,357 sounds and a feature geometry tree based on
Clements & Hume (1995).

```python
from alteruphono.features import sound, get_system, list_systems, set_default

# List available systems
list_systems()   # → ['ipa', 'tresoldi', 'distinctive']

# Create a sound with feature lookup
s = sound("a")
print(s.features)  # → frozenset({'vowel', 'open', 'front', 'unrounded'})

# Sound classes return partial sounds
v = sound("V")
print(v.partial)   # → True
print(v.features)  # → frozenset({'vowel'})

# Switch default system
set_default("tresoldi")
```

### IPA Categorical (`ipa`)

Standard IPA features extracted from the NAME column of `sounds.tsv`. Features
are categorical strings like `consonant`, `voiced`, `bilabial`, `stop`.
Supports negative features in class matching (e.g., `-stop` excludes stops).
Sound distance uses the feature geometry tree for weighted comparison.

### Tresoldi (`tresoldi`)

Broader feature set preserving the full IPA description (all modifiers, secondary
articulations, tonal features). Same 7,357-sound inventory, richer feature
representation. Geometry-based sound distance.

### Distinctive (`distinctive`)

Maps categorical features to 32 scalar dimensions (-1.0 to +1.0) organized
by feature geometry nodes: Laryngeal (voice, spread glottis, constricted
glottis, breathy voice, creaky voice), Manner (sonorant, continuant, nasal,
lateral, strident, delayed release, tap, syllabic), Labial (labial, round),
Coronal (coronal, anterior, distributed, apical), Dorsal (dorsal, high, low,
back), TongueRoot (ATR), and Prosodic (long, nasalized, labialized,
palatalized, pharyngealized, ejective, stress, tone). Dimensions are weighted
by inverse tree depth for geometry-aware sound distance.

### Feature Geometry

The feature geometry tree (`alteruphono.features.geometry`) implements the
Clements & Hume (1995) hierarchical model of phonological features:

```
Root
├── Laryngeal (voice, spread glottis, constricted glottis, breathy, creaky)
├── Manner (sonorant, continuant, nasal, lateral, strident, ...)
├── Place
│   ├── Labial (round)
│   ├── Coronal (anterior, distributed)
│   ├── Dorsal (high, low, back)
│   ├── Pharyngeal
│   └── Glottal
├── TongueRoot (ATR)
└── Prosodic (long, nasalized, stress, ...)
```

The tree provides feature distance calculations, sibling-based mutual
exclusivity, and weighted sound distance used across all feature systems.

### Custom feature systems

Any object satisfying the `FeatureSystem` protocol can be registered:

```python
from alteruphono.features import register
from alteruphono.features.protocol import FeatureSystem

class MySystem:
    @property
    def name(self) -> str: return "custom"
    def grapheme_to_features(self, grapheme: str) -> frozenset[str] | None: ...
    def features_to_grapheme(self, features: frozenset[str]) -> str | None: ...
    def is_class(self, grapheme: str) -> bool: ...
    def class_features(self, grapheme: str) -> frozenset[str] | None: ...
    def add_features(self, base: frozenset[str], added: frozenset[str]) -> frozenset[str]: ...
    def partial_match(self, pattern: frozenset[str], target: frozenset[str]) -> bool: ...
    def feature_distance(self, feat_a: str, feat_b: str) -> float: ...
    def sound_distance(self, feats_a: frozenset[str], feats_b: frozenset[str]) -> float: ...

register("custom", MySystem())
```

## Sound Change Engine

For ordered rule application and change tracking:

```python
from alteruphono.engine import SoundChangeEngine, CategoricalRule, GradientRule, RuleSet
from alteruphono.parser import parse_sequence

# Build a rule set
rs = RuleSet(name="Grimm's Law")
rs.add(CategoricalRule(source="p > f", name="p→f"))
rs.add(CategoricalRule(source="t > θ", name="t→θ"))
rs.add(CategoricalRule(source="k > x", name="k→x"))

# Apply
engine = SoundChangeEngine()
seq = parse_sequence("# p a t e r #")
result = engine.apply_ruleset(seq, rs)
print(" ".join(str(e) for e in result))
# → # f a θ e r #

# Track each step
trajectory = engine.apply_with_trajectory(seq, rs)
for step in trajectory.steps:
    if step.changed:
        print(f"{step.rule_name}: {step.input_str} → {step.output_str}")
```

### Gradient rules

```python
from alteruphono.engine import GradientRule, apply_gradient

# Full-strength application
rule = GradientRule(source="p > b", strength=1.0, name="voicing")

# Or use the function directly
result = apply_gradient(seq, "p > b", strength=1.0)
```

## Comparative Analysis

Pure-Python comparative method tools — no numpy/pandas needed.

```python
from alteruphono.comparative import ComparativeAnalysis, reconstruct_proto

# Build cognate sets
ca = ComparativeAnalysis()
ca.add_cognate_set({
    "latin":   ["p", "a", "t", "e", "r"],
    "spanish": ["p", "a", "d", "r", "e"],
    "french":  ["p", "ɛ", "ʁ"],
})
ca.add_cognate_set({
    "latin":   ["m", "a", "t", "e", "r"],
    "spanish": ["m", "a", "d", "r", "e"],
    "french":  ["m", "ɛ", "ʁ"],
})

# Find correspondences (using Needleman-Wunsch alignment)
corr = ca.find_correspondences()
for c in corr[:3]:
    print(f"Position {c.position}: {c.sounds}")

# Distance matrix
langs, matrix = ca.calculate_distance_matrix()
for i, lang in enumerate(langs):
    print(f"{lang}: {[f'{d:.2f}' for d in matrix[i]]}")

# Phylogeny (agglomerative clustering)
edges = ca.build_phylogeny()
for a, b, dist in edges:
    print(f"{a} — {b}  (distance {dist:.3f})")

# Proto-form reconstruction
proto = reconstruct_proto(
    {"A": ["p", "a"], "B": ["p", "a"], "C": ["b", "a"]},
    method="majority",  # or "conservative", "parsimony", "sankoff"
)
print(proto)  # → ['p', 'a']
```

### Reconstruction methods

- **majority** — selects the most frequent sound at each aligned position.
- **conservative** — weights sounds by phylogenetic branch independence;
  prefers less marked (simpler) sounds as tiebreaker.
- **parsimony** — Fitch algorithm minimizing the total number of changes
  on a phylogenetic tree.
- **sankoff** — Weighted parsimony using feature-based cost matrix for
  non-uniform transition costs.

## Prosody

Syllabification and prosodic structure:

```python
from alteruphono.prosody import syllabify, Syllable, ProsodicWord
from alteruphono.features import sound

sounds = tuple(sound(g) for g in ["p", "a", "t", "a"])
word = syllabify(sounds)

print(f"Syllables: {len(word)}")  # → 2
for syl in word.syllables:
    print(f"  onset={syl.onset} nucleus={syl.nucleus} coda={syl.coda}")
```

## CLI Reference

```
alteruphono [--json] [--version] <command> [args]
```

| Command | Description | Example |
|---------|-------------|---------|
| `forward` | Apply rule forward | `alteruphono forward "p > b" "# a p a #"` |
| `backward` | Reconstruct proto-forms | `alteruphono backward "p > b" "# a b a #"` |
| `features` | Show features for a grapheme | `alteruphono features p [--system tresoldi]` |
| `systems` | List feature systems | `alteruphono systems` |
| `validate` | Validate a rule | `alteruphono validate "p > b / V _ V"` |
| `apply-file` | Apply rules from TSV file | `alteruphono apply-file rules.tsv "# a p a #"` |

All commands support `--json` for machine-readable output.

## TSV Resources

The library ships with TSV data files in `resources/`:

| File | Records | Columns |
|------|---------|---------|
| `sounds.tsv` | 7,357 | GRAPHEME, NAME |
| `features.tsv` | 126 | VALUE, FEATURE |
| `classes.tsv` | 21 | SOUND_CLASS, DESCRIPTION, FEATURES, GRAPHEMES |
| `sound_changes.tsv` | 802 | ID, RULE, WEIGHT, TEST_ANTE, TEST_POST |

Access programmatically:

```python
from alteruphono.resources import load_sounds, load_features, load_classes, load_sound_changes

sounds = load_sounds()          # {grapheme: name}
features = load_features()      # [(value, feature), ...]
classes = load_classes()         # {class: (desc, feats, [graphemes])}
rules = load_sound_changes()    # [{"ID": ..., "RULE": ..., ...}, ...]
```

## Architecture

```
alteruphono/                 # 26 files, ~3,000 LOC
├── types.py                 # Sound, Boundary, Token union, Rule, MatchResult
├── resources.py             # TSV loader with @cache
├── parser.py                # parse_rule(), parse_sequence()
├── match.py                 # match_pattern() with quantifier support
├── modifiers.py             # apply_modifiers(), invert_modifiers()
├── forward.py               # forward() with variable-length windows
├── backward.py              # backward()
├── features/                # FeatureSystem Protocol + 3 implementations
│   ├── protocol.py          # FeatureSystem protocol definition
│   ├── common.py            # Shared: add_features(), partial_match(), distance
│   ├── geometry.py          # Clements & Hume feature geometry tree
│   ├── ipa.py               # IPA categorical features
│   ├── tresoldi.py          # Tresoldi extended features
│   ├── distinctive.py       # 32 ScalarDimension scalar features
│   └── __init__.py          # Registry: get_system(), sound(), etc.
├── engine/                  # Ordered rule application
│   ├── engine.py            # SoundChangeEngine
│   ├── rules.py             # CategoricalRule, GradientRule, RuleSet
│   ├── ordering.py          # analyze_interactions(), recommend_ordering()
│   └── gradient.py          # Gradient utilities
├── comparative/             # Comparative method
│   ├── analysis.py          # ComparativeAnalysis, Needleman-Wunsch alignment
│   └── reconstruction.py    # reconstruct_proto() (majority/conservative/parsimony/sankoff)
├── prosody.py               # Syllable, ProsodicWord, syllabify()
├── cli.py                   # argparse CLI
└── __main__.py              # python -m alteruphono

tests/                       # 18 files, ~1,450 LOC, 216 tests
resources/                   # TSV data files
```

### Design decisions

- **All types are frozen dataclasses** — immutable, hashable, no methods for
  feature arithmetic (those live in FeatureSystem).
- **Token is a union type** — dispatch via `isinstance()`, not an ABC hierarchy.
- **Sequences are tuples** — immutable, hashable, no wrapper class.
- **Feature geometry tree** — Clements & Hume (1995) hierarchy for principled
  feature distance and mutual exclusivity.
- **Sound classes loaded from TSV** — all class definitions come from
  `classes.tsv`, supporting negative features (e.g., `-stop`).
- **All public functions are pure** — no global mutable state except the
  feature system registry.
- **Zero runtime dependencies** — only stdlib.

## Citation

```bibtex
@software{tresoldi2026alteruphono,
  author  = {Tresoldi, Tiago},
  title   = {AlteruPhono: Phonological Sound Change Modeling},
  year    = {2026},
  url     = {https://github.com/tresoldi/alteruphono}
}
```

## License

MIT. See [LICENSE](LICENSE).
