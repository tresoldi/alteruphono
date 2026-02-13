"""Frozen dataclass types for alteruphono v2."""

from __future__ import annotations

from dataclasses import dataclass, field

# --- Phonological primitives ---


@dataclass(frozen=True)
class Sound:
    """A phonological sound with grapheme and feature set."""

    grapheme: str
    features: frozenset[str] = field(default_factory=frozenset)
    partial: bool = False

    def __str__(self) -> str:
        return self.grapheme


@dataclass(frozen=True)
class Boundary:
    """Word/morpheme boundary (#)."""

    marker: str = "#"

    def __str__(self) -> str:
        return self.marker


type Element = Sound | Boundary
type Sequence = tuple[Element, ...]


# --- Tokens (rule pattern elements) ---


@dataclass(frozen=True)
class SegmentToken:
    """A concrete sound in a rule pattern."""

    sound: Sound

    def __str__(self) -> str:
        return str(self.sound)


@dataclass(frozen=True)
class BoundaryToken:
    """Word/morpheme boundary in a rule pattern."""

    marker: str = "#"

    def __str__(self) -> str:
        return self.marker


@dataclass(frozen=True)
class BackRefToken:
    """Back-reference to a matched element (@1, @2, ...)."""

    index: int
    modifier: str | None = None

    def __str__(self) -> str:
        if self.modifier:
            return f"@{self.index + 1}[{self.modifier}]"
        return f"@{self.index + 1}"


@dataclass(frozen=True)
class EmptyToken:
    """Represents deletion (:null:)."""

    def __str__(self) -> str:
        return ":null:"


@dataclass(frozen=True)
class ChoiceToken:
    """Alternative match (p|b)."""

    choices: tuple[Token, ...]

    def __str__(self) -> str:
        return "|".join(str(c) for c in self.choices)


@dataclass(frozen=True)
class SetToken:
    """Correspondence set ({p|b})."""

    choices: tuple[Token, ...]

    def __str__(self) -> str:
        return "{" + "|".join(str(c) for c in self.choices) + "}"


@dataclass(frozen=True)
class FocusToken:
    """Focus position (_) in rule context."""

    def __str__(self) -> str:
        return "_"


@dataclass(frozen=True)
class QuantifiedToken:
    """Token with quantifier: C+ (one-or-more) or C? (optional)."""

    inner: Token
    quantifier: str  # "+" or "?"

    def __str__(self) -> str:
        return f"{self.inner}{self.quantifier}"


@dataclass(frozen=True)
class SyllableCondToken:
    """Syllable position condition: _.onset, _.nucleus, _.coda."""

    position: str  # "onset", "nucleus", "coda"

    def __str__(self) -> str:
        return f"_.{self.position}"


@dataclass(frozen=True)
class NegationToken:
    """Negated match (!V, !p|b)."""

    inner: Token

    def __str__(self) -> str:
        return f"!{self.inner}"


type Token = (
    SegmentToken
    | BoundaryToken
    | BackRefToken
    | EmptyToken
    | ChoiceToken
    | SetToken
    | FocusToken
    | QuantifiedToken
    | SyllableCondToken
    | NegationToken
)


# --- Rule ---


@dataclass(frozen=True)
class Rule:
    """A parsed sound change rule."""

    source: str
    ante: tuple[Token, ...]
    post: tuple[Token, ...]

    def __str__(self) -> str:
        return self.source


# --- Match result ---


@dataclass(frozen=True)
class MatchResult:
    """Result of matching a sequence against a pattern."""

    matched: bool
    bindings: tuple[Element | int | None, ...]
    span: int = 0  # Number of sequence elements consumed (for variable-length matches)
