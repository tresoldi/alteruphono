# AlteruPhono

AlteruPhono applies sound-change rules written in standard notation
(`p > b / V _ V`) forwards, to simulate change, and backwards, to propose
proto-forms.

**2.0 (in development, branch `claude/optimistic-ptolemy-otlkig`)** rewrites the
engine in C99 on the [merkmal](https://github.com/tresoldi/merkmal) feature
library and keeps the 1.x Python API. The design is
[docs/v2/DESIGN.md](docs/v2/DESIGN.md); what has been checked, and how, is in
[docs/v2/PARITY.md](docs/v2/PARITY.md). The last Python-only release is tagged
`v1.0.0rc1-simultaneous`; use it to reproduce results made with 1.x.

## What the results mean

- **Rule application is deterministic and says nothing about probability.**
  `forward` applies a rule everywhere its pattern matches, all at once (SPE
  style: contexts are read from the input and never consumed). It does not
  model how likely a change is. A learned, directional model of change is
  planned as a separate object (DESIGN §6); nothing in the engine uses it.
- **`backward` proposes; it does not reconstruct.** It returns every form the
  rule could have come from, under the rule alone, including the unchanged
  form. It knows nothing of other rules, of the tree or of the lexicon. With
  more than 100,000 candidates it raises `OverflowError` instead of building
  them. Its inversion of feature modifiers is weak (1.x's, reproduced): it
  undoes `@1[+voiced]` by removing `voiced` without adding `voiceless`.
- **Features are merkmal's**, restricted to 1.x's label names (the
  `alteruphono-1` projection). For 7,342 of the 7,353 graphemes of 1.x's
  inventory that merkmal resolves, the labels equal 1.x's; the other 11 are
  listed in PARITY.md (one of them, `ʈʂː`, was a 1.x error).
- **`sound_distance` is 1.x's feature-geometry distance**, kept so that
  results that depended on it can be reproduced. It is not a metric, not a
  probability of change, and not evidence of direction. The same holds for
  merkmal's dissimilarities.
- **The speed figures are for this machine and this stream** (catalogue rules
  on catalogue words, mean 8.9 segments): forward is about 130–190× faster
  than 1.x in C and about 25× through the Python API; Python-level rule
  parsing is no faster than 1.x unless the parse is cached. PARITY.md has the
  numbers, including the targets that were missed.

## Documentation

- **[Comprehensive Guide](docs/guide.md)** — Theory, tutorials, and a worked
  Proto-Romance case study for grad students and researchers (written for 1.x;
  the notation and Python API are unchanged)
- **[API Reference](docs/api_reference.md)** — Signatures and brief descriptions
  for all public modules (1.x)
- **[2.0 design](docs/v2/DESIGN.md)**, **[parity record](docs/v2/PARITY.md)**,
  and design notes for [merkmal](docs/v2/notes/merkmal.md),
  [regulae](docs/v2/notes/regulae.md), [yvyra](docs/v2/notes/yvyra.md),
  [blindrec](docs/v2/notes/blindrec.md) and [historia](docs/v2/notes/historia.md)

## Installation

2.0 is built from source, next to a merkmal checkout on branch
`claude/alteruphono-support` (which adds the two merkmal calls 2.0 needs):

```bash
git clone -b claude/alteruphono-support https://github.com/tresoldi/merkmal.git
```

```bash
git clone -b claude/optimistic-ptolemy-otlkig https://github.com/tresoldi/alteruphono.git
```

```bash
cd alteruphono && pip install -e ".[dev]"
```

`AP_MERKMAL_SOURCE_DIR` points the build at another merkmal tree. The
extension embeds merkmal's CC-BY-4.0 data only (its `cc-by` profile); P-base
and PHOIBLE are left out. Requires Python 3.12+ and a C99 compiler; no runtime
dependencies.

The C library and its checks:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build && (cd build && ctest)
```

```bash
scripts/check.sh --full
```

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

2.0 has one built-in system, `ipa`: 1.x's label names and categories (`voiced`,
`bilabial`, `stop`, …; `features/vocabulary.py`), with values from merkmal's
`descriptive` system. 1.x's own `tresoldi` and `distinctive` tables are gone:
every feature value now comes from merkmal.

```python
from alteruphono.features import sound, get_system, list_systems

list_systems()   # → ['ipa']

s = sound("a")
print(s.features)  # → frozenset({'vowel', 'open', 'front', 'unrounded'})

v = sound("V")     # sound classes give partial sounds
print(v.partial, v.features)  # → True frozenset({'vowel'})
```

Lookups are exact over 1.x's grapheme inventory (`resources/graphemes_1x.txt`),
as in 1.x: a grapheme outside it has no features. Sound classes are the pack in
`resources/classes.tsv` (a class is a conjunction of features; `-stop` excludes
stops).

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

The tree provides 1.x's feature distance and weighted sound distance, kept in
2.0 for reproducibility (DESIGN D3). It is not a metric.

### Custom feature systems

An object satisfying the `FeatureSystem` protocol can still be registered with
`alteruphono.features.register`; it serves the Python-level code
(`match_pattern`, prosody, comparative analysis). `forward` and `backward` run
in the C engine on `ipa` only.

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

## Resources

| File | Records | Contents |
|------|---------|----------|
| `sound_changes.tsv` | 801 | ID, RULE, WEIGHT, TEST_ANTE, TEST_POST (test pairs apply inside `# … #`) |
| `classes.tsv` | 20 | SOUND_CLASS, DESCRIPTION, FEATURES |
| `graphemes_1x.txt` | 7,356 | 1.x's grapheme inventory, one per line, in 1.x order |

```python
from alteruphono.resources import load_sound_changes, load_classes, load_graphemes
```

1.x's `sounds.tsv` (grapheme → feature description) and `features.tsv` were
its feature tables and are gone, with `load_sounds` and `load_features`.

## Architecture

```
include/alteruphono.h        # the C API (ap_*): contexts, segments, rules, forward, backward
src/                         # the C99 engine: parser, matcher, forward, backward, syllabifier
src/generated/compat1x.c     # 1.x vocabulary, class pack, grapheme inventory (scripts/gen_compat1x.py)
python/_native.c             # CPython extension alteruphono._native (abi3, Python >= 3.12)
alteruphono/                 # the 1.x Python API, on the engine (_core.py is the bridge)
tests/c/, fuzz/              # C tests and libFuzzer targets (scripts/check.sh)
tests/parity/                # differential harness against 1.x
bench/                       # speed benchmarks (C and Python API)
docs/v2/                     # design, parity record, design notes for the other libraries
```

C conventions follow regulae: one public header, `ap_status` returns,
caller-owned diagnoses, no global mutable state, one thread per context
(`ap_context_clone` for another thread), `-Werror` and sanitizer builds in
`scripts/check.sh`.

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
