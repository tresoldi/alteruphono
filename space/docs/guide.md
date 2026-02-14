# AlteruPhono: A Comprehensive Guide

*For graduate students and researchers in historical and comparative linguistics*

## 1. Introduction

AlteruPhono is a Python library for modeling phonological sound changes. It
provides a complete pipeline for historical linguistics research: rule parsing,
forward application (simulating language evolution), backward reconstruction,
feature systems grounded in phonological theory, the comparative method, and
prosodic analysis.

**What you can do with AlteruPhono:**

- Define sound change rules in standard SPE-style notation
- Apply rules forward to simulate attested phonological changes
- Apply rules backward to reconstruct proto-forms
- Compare cognate sets across languages using Needleman-Wunsch alignment
- Build phylogenetic trees from phonological distance matrices
- Reconstruct proto-forms using majority vote, weighted parsimony, or Sankoff
- Syllabify sequences using the Sonority Sequencing Principle
- Analyze rule ordering interactions (feeding, bleeding, counterfeeding, counterbleeding)

**Requirements:** Python 3.12+, no external dependencies.

```bash
pip install alteruphono
```

### 1.1 For Historical Linguists Using the Space

This section is written for historical linguists who are using the Hugging Face
Space and are not primarily interested in programming details. The central
point is that AlteruPhono is a formal tool for testing hypotheses about
**regular sound change**. It does not replace philological judgment; it makes
your assumptions explicit and checks what follows from them.

In practice, the Space gives you three research actions. The **Forward**
operation asks what outcomes follow if a proposed rule is applied to a set of
forms. The **Backward** operation asks which earlier forms are compatible with
an attested form under that same rule. The **Validate** operation checks rule
well-formedness so that failures are not confused with notation errors.

Because the same rule can be tested quickly across many lexical items (one form
per line), the Space is useful for exploratory comparative work, internal
reconstruction, and refinement of conditioning environments.

#### Why this is not plain string replacement or regex

| Approach | Typical behavior | Limitation for historical phonology | AlteruPhono advantage |
|---------|-------------------|-------------------------------------|------------------------|
| Plain string replacement | Replaces exact character strings | No classes, no environment, no phonological conditioning | Uses classes (`V`, `C`, `N`, etc.) and environments (`V _ V`, `# _`) |
| Regex | Matches symbol patterns | Tracks symbols, not phonological structure; not reconstruction-oriented | Supports correspondence sets, back-references, and backward candidate generation |
| AlteruPhono | Applies phonological rules to segmented forms | Requires explicit segmentation and rule assumptions | Encodes regularity and conditioning environments directly |

Regex remains excellent for textual pattern search and corpus preprocessing, but
historical analysis usually requires more than symbol substitution. Sound
change proposals are about conditioned phonological behavior, class membership,
and structural position. AlteruPhono is designed for that analytical level.

#### How to work with results in the Space

A productive workflow is to begin with one explicit rule and a small but
representative form set. Run the same rule across multiple lines, inspect where
it succeeds and fails, then adjust conditioning only when necessary. If a rule
is failing unexpectedly, validate it first and then inspect segmentation and
context assumptions.

Interpret outputs as consequences of assumptions, not as historical proof.
Forward output answers: "what should happen if this rule is correct?" Backward
output answers: "which earlier forms remain possible under this rule?" Multiple
backward candidates are expected; that ambiguity is intrinsic to reconstruction,
not a software defect.

#### How to read outputs responsibly

When outputs overgenerate, that usually indicates underspecified conditioning,
missing rule ordering, or mixed strata in the dataset. Under-generation often
indicates that conditioning is too strict, segmentation is inconsistent, or the
hypothesis is wrong for part of the lexicon. In both cases, external evidence
remains decisive: correspondence structure, chronology, morphology, and
philological constraints must adjudicate among candidates.

#### Scope and limits (important)

AlteruPhono formalizes regular change, but historical language change includes
processes that are not fully rule-regular. The Space does not independently
model analogy, paradigm leveling, borrowing, areal convergence, or full
sociolinguistic lexical diffusion. It also does not decide chronology or
historical plausibility for you. Those decisions remain analytical tasks for
the researcher.

#### Typical use cases in historical linguistics

Typical strong uses include stress-testing proposed correspondences across
cognate sets, checking whether a rule inventory can derive observed daughter
forms, comparing competing analyses with different conditioning environments,
and exploring feeding/bleeding effects before committing to a relative
chronology. A practical discipline is to keep explicit labels in your notes for
`attested changes`, `reconstructed changes`, and `proposed changes`, so that
formal outputs are not conflated with evidential status.

If you keep that distinction clear, the Space functions as it should: a
transparent comparative instrument for evaluating hypotheses, not a black-box
reconstruction oracle.

---

## 2. Sound Change Rules: Theory and Notation

### 2.1 Background

The Neogrammarian hypothesis holds that sound changes are regular — they apply
without exception in a given phonological environment. AlteruPhono encodes this
principle directly: a rule either matches or it doesn't, and when it matches it
always applies (unless using gradient/probabilistic mode).

Rules follow the SPE (Sound Pattern of English) notation:

```
A > B / C _ D
```

Read as: "A becomes B in the environment after C and before D", where `_` marks
the position of the sound undergoing change.

### 2.2 Rule Syntax

AlteruPhono accepts rules in several equivalent formats:

| Syntax | Meaning |
|--------|---------|
| `p > b` | Unconditional: p becomes b everywhere |
| `p → b` | Same (Unicode arrow) |
| `p -> b` | Same (ASCII arrow) |
| `p > b / V _ V` | Conditional: p becomes b between vowels |
| `p > b / # _` | p becomes b after word boundary (word-initially) |

### 2.3 Notation Elements

| Element | Meaning | Example |
|---------|---------|---------|
| `#` | Word/morpheme boundary | `# _ V` (word-initial before vowel) |
| `_` | Focus position in context | `V _ V` (between vowels) |
| `:null:` | Deletion (zero) | `C > :null:` (delete consonant) |
| `@1`, `@2` | Back-reference (1-indexed) | `@1` refers to first matched element |
| `@1[+voiced]` | Back-ref with feature modifier | Voice the matched consonant |
| `p\|b` | Choice (match either p or b) | `p\|b > f` |
| `{p\|b}` | Correspondence set | `{p\|b} > {f\|v}` (p↔f, b↔v) |
| `C+` | One or more consonants | `C+ > :null:` (delete cluster) |
| `V?` | Zero or one vowel | Optional matching |
| `_.onset` | Syllable onset position | `C > @1[+voiced] / _.onset` |
| `_.nucleus` | Syllable nucleus position | |
| `_.coda` | Syllable coda position | |
| `!V` | Negation (anything but a vowel) | `!V` matches consonants |
| `!p\|b` | Negation of choice | Matches anything except p or b |

### 2.4 Sound Classes

Sound classes are uppercase letters that match sets of sounds by feature:

| Class | Description | Typical Features |
|-------|-------------|------------------|
| `V` | Vowels | `{vowel}` |
| `C` | Consonants | `{consonant}` |
| `N` | Nasals | `{nasal}` |
| `S` | Sibilants | `{sibilant}` |
| `L` | Liquids | `{approximant}` or `{lateral}` |
| `K` | Plosives/Stops | `{stop}` |

Sound classes are defined in `classes.tsv` and support negative features
(e.g., `-stop` to exclude stops from a class).

---

## 3. Getting Started: Forward and Backward

### 3.1 Parsing Rules and Sequences

```python
from alteruphono import parse_rule, parse_sequence

# Parse a sound change rule
rule = parse_rule("p > b / V _ V")

# Parse a phonological sequence
seq = parse_sequence("# a p a #")
# Returns: (Boundary(), Sound("a"), Sound("p"), Sound("a"), Boundary())
```

The parser normalizes Unicode (NFD), collapses whitespace, and accepts `>`,
`→`, and `->` as the rule operator. Each element in the parsed sequence is
either a `Sound` (with grapheme and features) or a `Boundary`.

### 3.2 Forward Application

Forward application simulates language evolution — given a proto-form and a
rule, produce the daughter form:

```python
from alteruphono import parse_rule, parse_sequence, forward

# Intervocalic voicing: p > b between vowels
rule = parse_rule("p > b / V _ V")
seq = parse_sequence("# a p a #")
result = forward(seq, rule)
print(" ".join(str(e) for e in result))
# → # a b a #
```

More examples:

```python
# Final devoicing: voiced stops become voiceless word-finally
rule = parse_rule("b > p / _ #")
seq = parse_sequence("# a b #")
result = forward(seq, rule)
# → # a p #

# Consonant deletion: delete consonant between vowels
rule = parse_rule("C > :null: / V _ V")
seq = parse_sequence("# a t a #")
result = forward(seq, rule)
# → # a a #

# Cluster simplification with quantifier
rule = parse_rule("C+ > :null: / _ #")
seq = parse_sequence("# a s t #")
result = forward(seq, rule)
# → # a #

# Feature modification with back-reference
rule = parse_rule("C > @1[+voiced] / V _ V")
seq = parse_sequence("# a t a #")
result = forward(seq, rule)
# → # a d a #
```

### 3.3 Backward Reconstruction

Backward application reverses a rule: given a daughter form and the rule that
produced it, reconstruct possible proto-forms:

```python
from alteruphono import parse_rule, parse_sequence, backward

rule = parse_rule("p > b / V _ V")
daughter = parse_sequence("# a b a #")
protos = backward(daughter, rule)
for proto in protos:
    print(" ".join(str(e) for e in proto))
# → # a b a #    (no change — daughter form is also valid proto)
# → # a p a #    (proto-form before the rule applied)
```

`backward()` returns a list of possible proto-form tuples, since a daughter
form may be the result of the rule applying or may be unchanged.

### 3.4 Correspondence Sets

Correspondence sets let you model systematic sound correspondences:

```python
rule = parse_rule("{p|b} > {f|v}")
# p maps to f, b maps to v (by index)

seq = parse_sequence("# p a b a #")
result = forward(seq, rule)
# → # f a v a #
```

---

## 4. Feature Systems

### 4.1 Theory

Phonological features are the atomic properties of sounds. A voiceless
bilabial stop [p] has features like `consonant`, `voiceless`, `bilabial`,
`stop`. Feature systems define how graphemes map to feature bundles and how
feature bundles map back to graphemes.

AlteruPhono ships with three systems that share a 7,356-sound inventory
from `sounds.tsv`.

### 4.2 Using Feature Systems

```python
from alteruphono.features import sound, get_system, list_systems, set_default

# List available systems
print(list_systems())  # → ['ipa', 'tresoldi', 'distinctive']

# Create a Sound with feature lookup (uses default system)
s = sound("p")
print(s.features)
# → frozenset({'consonant', 'voiceless', 'bilabial', 'stop'})

# Sound classes return partial sounds
v = sound("V")
print(v.partial)   # → True
print(v.features)  # → frozenset({'vowel'})

# Get a specific system
sys = get_system("ipa")

# Look up features for a grapheme
feats = sys.grapheme_to_features("t")
# → frozenset({'consonant', 'voiceless', 'alveolar', 'stop'})

# Reverse lookup: features to grapheme
grapheme = sys.features_to_grapheme(frozenset({"consonant", "voiced", "bilabial", "stop"}))
# → 'b'

# Compute phonological distance between two sounds
dist = sys.sound_distance(
    sys.grapheme_to_features("p"),
    sys.grapheme_to_features("b"),
)
# → small float (differ only in voicing)

# Switch the default system
set_default("tresoldi")
```

### 4.3 The Three Systems

**IPA Categorical (`ipa`)** — The default system. Features are categorical
strings extracted from the NAME column of `sounds.tsv` (e.g., `consonant`,
`voiced`, `bilabial`, `stop`). Supports negative features in class matching
(e.g., `-stop` excludes stops). Sound distance uses the feature geometry tree.

**Tresoldi (`tresoldi`)** — A broader feature set preserving the full IPA
description including all modifiers, secondary articulations, and tonal
features. Same 7,356-sound inventory, richer feature representation.
Geometry-based sound distance.

**Distinctive (`distinctive`)** — Maps categorical features to 32 scalar
dimensions (`ScalarDimension` objects), each ranging from -1.0 to +1.0.
Dimensions are organized by geometry node: Laryngeal (voice, spread glottis,
constricted glottis, breathy voice, creaky voice), Manner (sonorant,
continuant, nasal, lateral, strident, delayed release, tap, syllabic), Labial
(labial, round), Coronal (coronal, anterior, distributed, apical), Dorsal
(dorsal, high, low, back), TongueRoot (ATR), and Prosodic (long, nasalized,
labialized, palatalized, pharyngealized, ejective, stress, tone). Dimension
weights are computed from inverse tree depth for geometry-aware distance.

### 4.4 Feature Geometry

The feature geometry tree (`alteruphono.features.geometry.GEOMETRY`) implements
the Clements & Hume (1995) hierarchical model. The tree organizes features
into a hierarchy that captures phonological naturalness:

```
Root
├── Laryngeal
│   ├── voice (voiced / voiceless)
│   ├── spread_glottis (aspirated)
│   ├── constricted_glottis (glottalized)
│   ├── breathy_voice (breathy)
│   └── creaky_voice (creaky)
├── Manner
│   ├── sonorant (sonorant / obstruent)
│   ├── continuant
│   ├── nasal
│   ├── lateral
│   ├── strident (sibilant)
│   ├── delayed_release (affricate)
│   ├── tap_feature (tap)
│   └── syllabic (syllabic / non-syllabic)
├── Place
│   ├── Labial
│   │   └── round (rounded / unrounded)
│   ├── Coronal
│   │   ├── anterior
│   │   └── distributed
│   ├── Dorsal
│   │   ├── high (close / open)
│   │   ├── low (near-open / near-close)
│   │   └── back (back / front)
│   ├── Pharyngeal
│   │   ├── pharyngeal
│   │   └── epiglottal
│   └── Glottal
│       └── glottal
├── TongueRoot
│   └── ATR (advanced-tongue-root / retracted-tongue-root)
└── Prosodic
    ├── long
    ├── nasalized
    ├── labialized
    ├── palatalized
    ├── pharyngealized
    ├── ejective
    └── primary-stress
```

The tree provides:
- **Feature distance**: Tree-edge distance between two feature values
- **Mutual exclusivity**: Sibling features under the same parent are mutually exclusive
- **Weighted sound distance**: Features deeper in the tree contribute less to overall distance

### 4.5 Custom Feature Systems

Any object satisfying the `FeatureSystem` protocol can be registered:

```python
from alteruphono.features import register
from alteruphono.features.protocol import FeatureSystem

class MySystem:
    @property
    def name(self) -> str:
        return "custom"

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

---

## 5. Pattern Matching

### 5.1 The Match Engine

`match_pattern()` is the core matching function. It checks whether a sequence
of elements matches a pattern of tokens:

```python
from alteruphono import parse_rule, parse_sequence, match_pattern

rule = parse_rule("V C V > @1 @2[+voiced] @3")
seq = parse_sequence("# a t a #")

# Match the ante pattern against a subsequence
result = match_pattern(seq[1:4], rule.ante)
print(result.matched)   # → True
print(result.bindings)  # → (Sound("a"), Sound("t"), Sound("a"))
print(result.span)      # → 3
```

### 5.2 Sound Classes and Partial Matching

Sound classes like `V`, `C`, `N` create partial sounds — their features must
be a subset of the target sound's features:

```python
from alteruphono.features import sound

# V matches any sound with 'vowel' in its features
v = sound("V")  # Sound(grapheme="V", features=frozenset({"vowel"}), partial=True)

# So V matches "a" because {"vowel"} ⊆ {"vowel", "open", "front", "unrounded"}
```

### 5.3 Negation

Negation tokens match anything that does NOT match the inner pattern:

```python
rule = parse_rule("!V > :null: / _ #")
# Matches any non-vowel before word boundary and deletes it
```

### 5.4 Quantifiers

Quantified patterns support variable-length matching:

```python
# C+ matches one or more consonants (greedy)
rule = parse_rule("C+ > :null: / _ #")
seq = parse_sequence("# a n t #")
result = forward(seq, rule)
# → # a #  (both n and t are deleted)

# V? matches zero or one vowel
rule = parse_rule("V? C > :null: @1")
# Optionally matches a vowel before a consonant
```

The matching engine uses recursive backtracking: `+` is greedy (tries most
matches first), `?` tries skip-first (0 matches, then 1).

### 5.5 Syllable Conditions

Rules can be conditioned on syllable position:

```python
# Voice consonants only in onset position
rule = parse_rule("C > @1[+voiced] / _.onset")
```

This requires building a syllable map from the sequence, which is done
automatically when syllable conditions are present in a rule.

---

## 6. The Sound Change Engine

### 6.1 Rule Types

The engine provides structured rule types with metadata:

```python
from alteruphono.engine import CategoricalRule, GradientRule, RuleSet

# Categorical: always applies at full strength
rule = CategoricalRule(source="p > b / V _ V", name="intervocalic voicing")

# Gradient: applies with a probability (0.0 to 1.0)
rule = GradientRule(
    source="p > b / V _ V",
    strength=0.7,    # 70% probability at each match site
    name="lenition",
    seed=42,          # for reproducibility
)
```

### 6.2 Rule Sets and the Engine

```python
from alteruphono.engine import SoundChangeEngine, CategoricalRule, RuleSet
from alteruphono import parse_sequence

# Build a rule set (rules apply in order)
rs = RuleSet(name="Grimm's Law")
rs.add(CategoricalRule(source="p > f", name="p→f"))
rs.add(CategoricalRule(source="t > θ", name="t→θ"))
rs.add(CategoricalRule(source="k > x", name="k→x"))

# Apply the entire rule set
engine = SoundChangeEngine()
seq = parse_sequence("# p a t e r #")
result = engine.apply_ruleset(seq, rs)
print(" ".join(str(e) for e in result))
# → # f a θ e r #
```

### 6.3 Trajectories

Track each rule's effect step by step:

```python
trajectory = engine.apply_with_trajectory(seq, rs)
for step in trajectory.steps:
    if step.changed:
        print(f"{step.rule_name}: {step.input_str} → {step.output_str}")
# → p→f: # p a t e r # → # f a t e r #
# → t→θ: # f a t e r # → # f a θ e r #
# → k→x: (no change)
```

### 6.4 Gradient Application

Gradient rules apply probabilistically, useful for modeling sound changes
in progress or variable application:

```python
from alteruphono.engine import apply_gradient

# Apply with 50% probability at each match site
result = apply_gradient(seq, "p > b", strength=0.5, seed=42)
```

At `strength >= 1.0`, every match site is changed. At `strength <= 0.0`,
no changes occur. Between 0 and 1, each match site gets an independent
coin flip.

### 6.5 Rule Ordering Analysis

Rule ordering is a central concern in phonological theory. AlteruPhono
can analyze pairwise rule interactions:

```python
from alteruphono.engine import analyze_interactions, recommend_ordering, RuleSet, CategoricalRule

rs = RuleSet()
rs.add(CategoricalRule(source="t > s / _ i", name="palatalization"))
rs.add(CategoricalRule(source="s > h / _ #", name="debuccalization"))

interactions = analyze_interactions(rs)
for ri in interactions:
    print(f"{ri.rule_a} / {ri.rule_b}: {ri.interaction.value}")
    # → FEEDING, BLEEDING, COUNTERFEEDING, COUNTERBLEEDING, or INDEPENDENT

recommendations = recommend_ordering(interactions)
for r in recommendations:
    print(r)
# → "FEEDING: 't > s / _ i' feeds 's > h / _ #' — apply ... before ..."
# → "Suggested order: 't > s / _ i' → 's > h / _ #'"
```

**Interaction types:**

- **Feeding**: Rule A creates the environment for Rule B to apply
- **Bleeding**: Rule A removes the environment for Rule B
- **Counterfeeding**: Rule B could feed Rule A, but doesn't in A→B order
- **Counterbleeding**: Rule A could bleed Rule B, but doesn't in A→B order
- **Independent**: Rules don't interact

The `recommend_ordering()` function also attempts a topological sort to
suggest a consistent rule ordering.

---

## 7. Comparative Method

### 7.1 Theory

The comparative method reconstructs proto-languages by systematically
comparing cognate words across related languages. The key steps are:

1. Assemble cognate sets (words with shared ancestry)
2. Align the sounds in each cognate set
3. Identify systematic sound correspondences
4. Reconstruct proto-sounds at each correspondence position

AlteruPhono implements all of these steps.

### 7.2 Setting Up a Comparative Analysis

```python
from alteruphono.comparative import ComparativeAnalysis, reconstruct_proto

ca = ComparativeAnalysis()

# Add cognate sets: each is a dict of {language: [sound, sound, ...]}
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
```

### 7.3 Sound Alignment

AlteruPhono uses Needleman-Wunsch global alignment with affine gap penalties
for pairwise alignment, then progressive multi-alignment for three or more
languages:

```python
from alteruphono.comparative import needleman_wunsch

# Pairwise alignment
aligned_a, aligned_b, score = needleman_wunsch(
    ["p", "a", "t", "e", "r"],
    ["p", "a", "d", "r", "e"],
    gap_open=-2.0,     # penalty for opening a gap
    gap_extend=-0.5,   # penalty for extending a gap
    system_name="ipa", # use feature-weighted costs (optional)
)
# aligned_a: ['p', 'a', 't', 'e', 'r']
# aligned_b: ['p', 'a', 'd', 'r', 'e']
# None in aligned sequences represents a gap
```

When `system_name` is provided, the cost function uses feature-based sound
distance instead of simple match/mismatch scoring. Vowel-consonant mismatches
receive an extra penalty.

For multi-sequence alignment:

```python
from alteruphono.comparative.analysis import multi_align

aligned = multi_align({
    "latin":   ["p", "a", "t", "e", "r"],
    "spanish": ["p", "a", "d", "r", "e"],
    "french":  ["p", "ɛ", "ʁ"],
}, system_name="ipa")
# Returns: {language: [sound_or_None, ...]}
```

### 7.4 Finding Correspondences

```python
correspondences = ca.find_correspondences()
for c in correspondences[:5]:
    print(f"Position {c.position}: {c.sounds}")
# → Position 0: {'latin': 'p', 'spanish': 'p', 'french': 'p'}
# → Position 1: {'latin': 'a', 'spanish': 'a', 'french': 'ɛ'}
# → ...
```

### 7.5 Distance Matrix and Phylogeny

```python
# Compute pairwise phonological distances
langs, matrix = ca.calculate_distance_matrix()
for i, lang in enumerate(langs):
    print(f"{lang}: {[f'{d:.3f}' for d in matrix[i]]}")

# Build a phylogenetic tree
edges = ca.build_phylogeny(method="nj")  # or "upgma"
for node_a, node_b, dist in edges:
    print(f"{node_a} — {node_b}  (distance {dist:.3f})")
```

**Neighbor-Joining (`nj`)** — Does not assume a molecular clock. Computes a
Q-matrix to find the optimal pair to join at each step. Preferred for
linguistic phylogenies where rates of change vary.

**UPGMA (`upgma`)** — Assumes a molecular clock (equal rates of change across
branches). Simpler but less realistic for language phylogenies.

### 7.6 Proto-Form Reconstruction

```python
proto = reconstruct_proto(
    {"latin": ["p", "a", "t"], "spanish": ["p", "a", "d"], "french": ["p", "a"]},
    method="majority",
)
print(proto)  # → ['p', 'a', 't'] or ['p', 'a', 'd'] depending on alignment
```

**Reconstruction methods:**

- **`majority`** — Selects the most frequent sound at each aligned position.
  Simple and effective when most languages preserve the proto-sound.

- **`conservative`** — Weights sounds by phylogenetic branch independence
  (deeper branches get higher weight). Uses feature markedness (fewer features
  = simpler = preferred) as a tiebreaker. Requires a `phylogeny` argument for
  best results.

- **`parsimony`** — Fitch algorithm: bottom-up intersect child sets (union on
  conflict), top-down select from set. Minimizes total changes on the tree.
  Requires `phylogeny`.

- **`sankoff`** — Weighted parsimony using feature-based cost matrix for
  non-uniform transition costs. More realistic than Fitch parsimony because
  p→b (voicing change) costs less than p→ʃ (place + manner change). Requires
  `phylogeny`.

```python
# With phylogeny for tree-based methods
edges = ca.build_phylogeny()
proto = reconstruct_proto(
    cognate_set,
    method="sankoff",
    phylogeny=edges,
    system_name="ipa",
)
```

---

## 8. Prosody and Syllabification

### 8.1 Sonority Sequencing Principle

AlteruPhono syllabifies sequences using the Sonority Sequencing Principle
(SSP): onsets rise in sonority toward the nucleus, and codas fall. The
default sonority scale is:

| Sonority Level | Sound Types |
|:-:|---|
| 5 | Vowels |
| 4 | Approximants, Laterals |
| 3 | Trills, Taps |
| 2 | Nasals |
| 1 | Fricatives |
| 0 | Stops, Affricates, Clicks, Implosives |

### 8.2 Basic Syllabification

```python
from alteruphono.prosody import syllabify, ProsodicWord, Syllable
from alteruphono.features import sound

sounds = tuple(sound(g) for g in ["p", "a", "t", "a"])
word = syllabify(sounds)

print(f"Syllables: {len(word)}")  # → 2
for syl in word.syllables:
    onset  = "".join(str(s) for s in syl.onset)
    nuc    = "".join(str(s) for s in syl.nucleus)
    coda   = "".join(str(s) for s in syl.coda)
    print(f"  σ: onset={onset or '∅'} nucleus={nuc} coda={coda or '∅'}")
# → σ: onset=p nucleus=a coda=∅
# → σ: onset=t nucleus=a coda=∅
```

### 8.3 Syllable Constraints

```python
from alteruphono.prosody import SyllableConstraints

constraints = SyllableConstraints(
    allow_s_cluster=True,   # Allow sC onsets (e.g., English /st/)
    max_onset=3,
    max_coda=3,
    sonority_scale=tuple({   # Custom sonority scale
        "vowel": 5,
        "approximant": 4,
        "lateral": 4,
        "trill": 3,
        "tap": 3,
        "nasal": 2,
        "fricative": 1,
        "stop": 0,
    }.items()),
)

word = syllabify(sounds, constraints=constraints)
```

### 8.4 Syllable-Conditioned Rules

Syllable structure feeds back into rule application. Use syllable condition
tokens in rules:

```python
from alteruphono import parse_rule, parse_sequence, forward

# Voice consonants only in onset position
rule = parse_rule("C > @1[+voiced] / _.onset")
seq = parse_sequence("# a p t a #")
result = forward(seq, rule)
```

When a rule contains syllable conditions (`_.onset`, `_.nucleus`, `_.coda`),
the engine automatically syllabifies the sequence and builds a position map
before matching.

---

## 9. Worked Case Study: Proto-Romance to Daughter Languages

This section demonstrates a complete workflow: defining sound changes,
applying them to Latin forms, comparing daughter languages, and
reconstructing proto-forms.

### 9.1 Define Sound Changes

```python
from alteruphono import parse_rule, parse_sequence, forward
from alteruphono.engine import SoundChangeEngine, CategoricalRule, RuleSet

# Some simplified Latin-to-Spanish sound changes
latin_to_spanish = RuleSet(name="Latin → Spanish")
latin_to_spanish.add(CategoricalRule(
    source="t > d / V _ V",
    name="intervocalic voicing (t)",
))
latin_to_spanish.add(CategoricalRule(
    source="p > b / V _ V",
    name="intervocalic voicing (p)",
))
latin_to_spanish.add(CategoricalRule(
    source="k > ɡ / V _ V",
    name="intervocalic voicing (k)",
))

engine = SoundChangeEngine()
```

### 9.2 Apply Rules to Latin Forms

```python
# Latin PATER → Spanish padre
pater = parse_sequence("# p a t e r #")
spanish_pater = engine.apply_ruleset(pater, latin_to_spanish)
print(" ".join(str(e) for e in spanish_pater))
# → # p a d e r #

# Track the trajectory
trajectory = engine.apply_with_trajectory(pater, latin_to_spanish)
for step in trajectory.steps:
    if step.changed:
        print(f"  {step.rule_name}: {step.input_str} → {step.output_str}")
```

### 9.3 Compare Daughter Languages

```python
from alteruphono.comparative import ComparativeAnalysis, reconstruct_proto

ca = ComparativeAnalysis(system_name="ipa")

# Cognate: PATER (father)
ca.add_cognate_set({
    "spanish": ["p", "a", "d", "r", "e"],
    "french":  ["p", "ɛ", "ʁ"],
    "italian": ["p", "a", "d", "r", "e"],
})

# Cognate: MATER (mother)
ca.add_cognate_set({
    "spanish": ["m", "a", "d", "r", "e"],
    "french":  ["m", "ɛ", "ʁ"],
    "italian": ["m", "a", "d", "r", "e"],
})

# Cognate: LUPUS (wolf)
ca.add_cognate_set({
    "spanish": ["l", "o", "b", "o"],
    "french":  ["l", "u"],
    "italian": ["l", "u", "p", "o"],
})
```

### 9.4 Build Phylogeny

```python
# Distance matrix
langs, matrix = ca.calculate_distance_matrix()
print("Languages:", langs)
for i, lang in enumerate(langs):
    print(f"  {lang}: {[f'{d:.3f}' for d in matrix[i]]}")

# Build tree
edges = ca.build_phylogeny(method="nj")
for a, b, dist in edges:
    print(f"  {a} — {b}  ({dist:.3f})")
```

### 9.5 Reconstruct Proto-Forms

```python
# Reconstruct the proto-form for 'father'
cognate = {
    "spanish": ["p", "a", "d", "r", "e"],
    "french":  ["p", "ɛ", "ʁ"],
    "italian": ["p", "a", "d", "r", "e"],
}

# Simple majority vote
proto_majority = reconstruct_proto(cognate, method="majority", system_name="ipa")
print(f"Majority: *{''.join(proto_majority)}")

# Weighted parsimony with phylogeny
proto_sankoff = reconstruct_proto(
    cognate,
    method="sankoff",
    phylogeny=edges,
    system_name="ipa",
)
print(f"Sankoff:  *{''.join(proto_sankoff)}")
```

---

## 10. Command-Line Interface

AlteruPhono provides a CLI with 6 subcommands. All support `--json` for
machine-readable output.

### 10.1 Forward Application

```bash
alteruphono forward "p > b / V _ V" "# a p a #"
# → # a b a #

alteruphono --json forward "p > b / V _ V" "# a p a #"
# → {"rule": "p > b / V _ V", "input": "# a p a #", "output": "# a b a #"}
```

### 10.2 Backward Reconstruction

```bash
alteruphono backward "p > b" "# a b a #"
# → # a b a #
# → # a p a #
```

### 10.3 Feature Lookup

```bash
alteruphono features p
# → Grapheme: p
# → Partial: False
# → Features: bilabial, consonant, stop, voiceless

alteruphono features p --system tresoldi
# → (Tresoldi feature set for p)
```

### 10.4 List Feature Systems

```bash
alteruphono systems
# → ipa
# → tresoldi
# → distinctive
```

### 10.5 Validate a Rule

```bash
alteruphono validate "p > b / V _ V"
# → Valid rule: p > b / V _ V
# → Ante tokens: 3
# → Post tokens: 3
```

### 10.6 Apply Rules from File

```bash
alteruphono apply-file rules.tsv "# a p a #"
```

The file can be plain text (one rule per line) or TSV format. Lines starting
with `#` are treated as comments. In TSV format, the RULE column (second
column) is used.

---

## 11. TSV Resources

AlteruPhono ships with TSV data files in the `resources/` directory:

| File | Records | Columns |
|------|---------|---------|
| `sounds.tsv` | 7,356 | GRAPHEME, NAME |
| `features.tsv` | 126 | VALUE, FEATURE |
| `classes.tsv` | 20 | SOUND_CLASS, DESCRIPTION, FEATURES, GRAPHEMES |
| `sound_changes.tsv` | 801 | ID, RULE, WEIGHT, TEST_ANTE, TEST_POST |

Access programmatically:

```python
from alteruphono.resources import (
    load_sounds,
    load_features,
    load_classes,
    load_sound_changes,
)

sounds = load_sounds()          # {grapheme: name}
features = load_features()      # [(value, feature), ...]
classes = load_classes()         # {class: (desc, feats, [graphemes])}
rules = load_sound_changes()    # [{"ID": ..., "RULE": ..., ...}, ...]
```

All loaders use `@cache` — data is loaded once and reused across the session.

Additional convenience functions:

```python
from alteruphono.resources import feature_values, sound_class_graphemes, sound_class_features

# FEATURE -> set of VALUES
fv = feature_values()  # {"manner": {"stop", "fricative", ...}, ...}

# SOUND_CLASS -> frozenset of graphemes
scg = sound_class_graphemes()  # {"V": frozenset({"a", "e", "i", ...}), ...}

# SOUND_CLASS -> FEATURES string
scf = sound_class_features()   # {"V": "vowel", "C": "consonant", ...}
```
