# AlteruPhono API Reference

Signatures and brief descriptions for all public modules. See
[guide.md](guide.md) for tutorials and worked examples.

---

## `alteruphono` — Top-Level Exports

```python
from alteruphono import (
    Sound, Boundary,
    SegmentToken, BoundaryToken, BackRefToken, EmptyToken,
    ChoiceToken, SetToken, FocusToken, QuantifiedToken,
    SyllableCondToken, NegationToken,
    Rule, MatchResult,
    parse_rule, parse_sequence, match_pattern,
    forward, backward,
)
```

---

## `alteruphono.types`

### Phonological Primitives

| Class | Fields | Description |
|-------|--------|-------------|
| `Sound` | `grapheme: str`, `features: frozenset[str]`, `partial: bool` | A phonological sound. `partial=True` for sound classes (V, C, N, ...). |
| `Boundary` | `marker: str = "#"` | Word/morpheme boundary. |

**Type aliases:**

- `Element = Sound | Boundary`
- `Sequence = tuple[Element, ...]`

### Token Types (Rule Pattern Elements)

| Class | Key Fields | Description |
|-------|------------|-------------|
| `SegmentToken` | `sound: Sound` | Concrete sound in a pattern. |
| `BoundaryToken` | `marker: str = "#"` | Boundary in a pattern. |
| `BackRefToken` | `index: int`, `modifier: str \| None` | Back-reference (`@1`, `@1[+voiced]`). 0-indexed internally. |
| `EmptyToken` | — | Deletion target (`:null:`). |
| `ChoiceToken` | `choices: tuple[Token, ...]` | Alternatives (`p\|b`). |
| `SetToken` | `choices: tuple[Token, ...]` | Correspondence set (`{p\|b}`). |
| `FocusToken` | — | Focus position (`_`) in context. |
| `QuantifiedToken` | `inner: Token`, `quantifier: str` | `C+` (one-or-more) or `V?` (optional). |
| `SyllableCondToken` | `position: str` | `_.onset`, `_.nucleus`, `_.coda`. |
| `NegationToken` | `inner: Token` | Negated match (`!V`, `!p\|b`). |

**Type alias:** `Token = SegmentToken | BoundaryToken | BackRefToken | EmptyToken | ChoiceToken | SetToken | FocusToken | QuantifiedToken | SyllableCondToken | NegationToken`

### Rule and MatchResult

| Class | Fields | Description |
|-------|--------|-------------|
| `Rule` | `source: str`, `ante: tuple[Token, ...]`, `post: tuple[Token, ...]` | A parsed sound change rule. |
| `MatchResult` | `matched: bool`, `bindings: tuple[Element \| int \| None, ...]`, `span: int` | Result of matching a sequence against a pattern. |

---

## `alteruphono.parser`

```python
def parse_rule(source: str) -> Rule
```
Parse a sound change rule string (e.g., `"p > b / V _ V"`) into a `Rule`. Accepts `>`, `→`, `->`.

```python
def parse_sequence(source: str) -> tuple[Sound | Boundary, ...]
```
Parse a space-separated sequence (e.g., `"# a p a #"`) into a tuple of elements.

---

## `alteruphono.match`

```python
def match_pattern(
    sequence: Sequence,
    pattern: tuple[Token, ...],
    system_name: str | None = None,
    syllable_map: dict[int, str] | None = None,
    offset: int = 0,
) -> MatchResult
```
Match a sequence against a token pattern. Returns `MatchResult` with match status, bindings, and span.

```python
def build_syllable_map(
    sequence: Sequence,
    system_name: str | None = None,
) -> dict[int, str]
```
Build a position → syllable role (`"onset"`, `"nucleus"`, `"coda"`) map for a sequence.

---

## `alteruphono.forward`

```python
def forward(
    sequence: Sequence,
    rule: Rule,
    system_name: str | None = None,
) -> Sequence
```
Apply a sound change rule forward to a sequence. Returns the transformed sequence.

---

## `alteruphono.backward`

```python
def backward(
    sequence: Sequence,
    rule: Rule,
    system_name: str | None = None,
) -> list[Sequence]
```
Reconstruct possible proto-forms from a daughter sequence and a rule. Returns a list of candidate sequences.

---

## `alteruphono.modifiers`

```python
def apply_modifiers(
    features: frozenset[str],
    modifier_str: str,
    system: FeatureSystem,
) -> frozenset[str]
```
Apply `+feature`/`-feature` modifiers to a feature set. E.g., `"+voiced,-voiceless"`.

```python
def invert_modifiers(modifier_str: str) -> str
```
Flip `+`/`-` prefixes for backward reconstruction.

---

## `alteruphono.features`

```python
def sound(grapheme: str, system_name: str | None = None) -> Sound
```
Create a `Sound` from a grapheme. Sound classes (V, C, N, ...) return `partial=True`.

```python
def get_system(name: str | None = None) -> FeatureSystem
```
Get a feature system by name. Default: `"ipa"`.

```python
def set_default(name: str) -> None
```
Set the default feature system.

```python
def list_systems() -> list[str]
```
List registered system names (default: `['ipa', 'tresoldi', 'distinctive']`).

```python
def register(name: str, system: FeatureSystem) -> None
```
Register a custom feature system.

```python
def normalize_output(grapheme: str) -> str
```
Map canonical ASCII forms back to IPA codepoints (e.g., ASCII `g` → IPA `ɡ`).

---

## `alteruphono.features.protocol`

```python
class FeatureSystem(Protocol):
    @property
    def name(self) -> str: ...
    def grapheme_to_features(self, grapheme: str) -> frozenset[str] | None: ...
    def features_to_grapheme(self, features: frozenset[str]) -> str | None: ...
    def is_class(self, grapheme: str) -> bool: ...
    def class_features(self, grapheme: str) -> frozenset[str] | None: ...
    def add_features(self, base: frozenset[str], added: frozenset[str]) -> frozenset[str]: ...
    def partial_match(self, pattern: frozenset[str], target: frozenset[str]) -> bool: ...
    def feature_distance(self, feat_a: str, feat_b: str) -> float: ...
    def sound_distance(self, feats_a: frozenset[str], feats_b: frozenset[str]) -> float: ...
```

---

## `alteruphono.features.geometry`

```python
@dataclass(frozen=True)
class FeatureNode:
    name: str         # e.g., "voice"
    positive: str     # e.g., "voiced"
    negative: str     # e.g., "voiceless"
```

```python
@dataclass(frozen=True)
class GeometryNode:
    name: str
    children: tuple[GeometryNode | FeatureNode, ...]

    def all_features(self) -> frozenset[str]: ...
    def find_feature(self, value: str) -> FeatureNode | None: ...
    def find_parent(self, value: str) -> GeometryNode | None: ...
    def siblings_of(self, value: str) -> frozenset[str]: ...
    def feature_distance(self, a: str, b: str) -> int: ...
    def sound_distance(self, feats_a: frozenset[str], feats_b: frozenset[str]) -> float: ...
```

```python
GEOMETRY: GeometryNode  # The Clements & Hume (1995) feature geometry tree.
FEATURE_TO_GEOMETRY_NODE: dict[str, str]  # Maps IPA features to geometry node names.
```

---

## `alteruphono.engine`

### Rules

```python
@dataclass(frozen=True)
class CategoricalRule:
    source: str               # Rule source string
    rule: Rule                # Auto-parsed (init=False)
    name: str = ""
    description: str = ""
```

```python
@dataclass(frozen=True)
class GradientRule:
    source: str
    rule: Rule                # Auto-parsed (init=False)
    strength: float = 1.0     # 0.0–1.0; per-site probability
    name: str = ""
    description: str = ""
    seed: int | None = None   # RNG seed for reproducibility
```

```python
@dataclass
class RuleSet:
    name: str = ""
    rules: list[CategoricalRule | GradientRule]

    def add(self, rule: CategoricalRule | GradientRule) -> None: ...
```

### Engine

```python
class SoundChangeEngine:
    def __init__(self, system_name: str | None = None) -> None: ...
    def apply_rule(self, sequence: Sequence, rule: CategoricalRule | GradientRule) -> Sequence: ...
    def apply_ruleset(self, sequence: Sequence, ruleset: RuleSet) -> Sequence: ...
    def apply_with_trajectory(self, sequence: Sequence, ruleset: RuleSet) -> Trajectory: ...
```

```python
@dataclass(frozen=True)
class StepResult:
    rule_name: str
    input_str: str
    output_str: str
    changed: bool

@dataclass
class Trajectory:
    input_seq: Sequence
    steps: list[StepResult]
    output_seq: Sequence
    @property
    def changed(self) -> bool: ...
```

### Gradient

```python
def apply_gradient(
    sequence: Sequence,
    rule_source: str,
    strength: float = 1.0,
    system_name: str | None = None,
    seed: int | None = None,
) -> Sequence
```
Apply a rule at given strength. `strength >= 1.0` = full apply; `<= 0.0` = no-op; between = per-site coin flip.

### Ordering Analysis

```python
class Interaction(Enum):
    FEEDING = "feeding"
    BLEEDING = "bleeding"
    COUNTERFEEDING = "counterfeeding"
    COUNTERBLEEDING = "counterbleeding"
    INDEPENDENT = "independent"

@dataclass(frozen=True)
class RuleInteraction:
    rule_a: str
    rule_b: str
    interaction: Interaction
    example_input: str
    ab_output: str
    ba_output: str
```

```python
def analyze_interactions(
    ruleset: RuleSet | list[str],
    test_sequences: list[str] | None = None,
    system_name: str | None = None,
) -> list[RuleInteraction]
```
Analyze pairwise rule interactions. Auto-generates probes if `test_sequences` is `None`.

```python
def recommend_ordering(interactions: list[RuleInteraction]) -> list[str]
```
Generate human-readable ordering recommendations with topological sort.

---

## `alteruphono.comparative`

```python
@dataclass
class CorrespondenceSet:
    position: int
    sounds: dict[str, str]    # language → sound
    @property
    def languages(self) -> list[str]: ...
```

```python
def needleman_wunsch(
    seq_a: list[str],
    seq_b: list[str],
    gap_open: float = -2.0,
    gap_extend: float = -0.5,
    system_name: str | None = None,
) -> tuple[list[str | None], list[str | None], float]
```
Affine-gap Needleman-Wunsch alignment. Returns `(aligned_a, aligned_b, score)`. `None` = gap.

```python
def multi_align(
    forms: dict[str, list[str]],
    system_name: str | None = None,
) -> dict[str, list[str | None]]
```
Progressive multi-alignment using pairwise NW.

```python
@dataclass
class ComparativeAnalysis:
    cognates: list[dict[str, list[str]]]
    system_name: str | None = None

    def add_cognate_set(self, forms: dict[str, list[str]]) -> None: ...
    def find_correspondences(self) -> list[CorrespondenceSet]: ...
    def calculate_distance_matrix(self) -> tuple[list[str], list[list[float]]]: ...
    def build_phylogeny(self, method: str = "nj") -> list[tuple[str, str, float]]: ...
```
`method`: `"nj"` (neighbor-joining) or `"upgma"`.

```python
def reconstruct_proto(
    forms: dict[str, list[str]],
    method: str = "majority",
    phylogeny: list[tuple[str, str, float]] | None = None,
    system_name: str | None = None,
) -> list[str]
```
`method`: `"majority"`, `"conservative"`, `"parsimony"`, or `"sankoff"`.

---

## `alteruphono.prosody`

```python
DEFAULT_SONORITY: dict[str, int]  # {"vowel": 5, "approximant": 4, ...}
```

```python
@dataclass(frozen=True)
class Syllable:
    onset: tuple[Sound, ...] = ()
    nucleus: tuple[Sound, ...] = ()
    coda: tuple[Sound, ...] = ()
    @property
    def sounds(self) -> tuple[Sound, ...]: ...

@dataclass
class ProsodicWord:
    syllables: list[Syllable]
    @property
    def sounds(self) -> tuple[Sound, ...]: ...

@dataclass(frozen=True)
class SyllableConstraints:
    allow_s_cluster: bool = False
    max_onset: int = 3
    max_coda: int = 3
    sonority_scale: tuple[tuple[str, int], ...] = tuple(DEFAULT_SONORITY.items())
```

```python
def syllabify(
    sounds: tuple[Sound, ...],
    system_name: str | None = None,
    constraints: SyllableConstraints | None = None,
) -> ProsodicWord
```
Syllabify using the Sonority Sequencing Principle.

---

## `alteruphono.resources`

```python
def load_sounds() -> dict[str, str]                          # GRAPHEME → NAME
def load_features() -> list[tuple[str, str]]                 # [(VALUE, FEATURE), ...]
def load_classes() -> dict[str, tuple[str, str, list[str]]]  # CLASS → (DESC, FEATS, [GRAPHEMES])
def load_sound_changes() -> list[dict[str, str]]                  # TSV rows as dicts
def feature_values() -> dict[str, set[str]]                  # FEATURE → {VALUES}
def sound_class_graphemes() -> dict[str, frozenset[str]]     # CLASS → frozenset of graphemes
def sound_class_features() -> dict[str, str]                 # CLASS → FEATURES string
```

All loaders are `@cache`-decorated (loaded once per process).

---

## `alteruphono.cli`

```python
def main(argv: list[str] | None = None) -> int
```

Subcommands: `forward`, `backward`, `features`, `systems`, `validate`, `apply-file`. All support `--json`.
