"""Rule types for the sound change engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from alteruphono.parser import parse_rule

if TYPE_CHECKING:
    from alteruphono.types import Rule


@dataclass(frozen=True)
class CategoricalRule:
    """A standard categorical sound change rule (A > B).

    Wraps a parsed Rule with metadata.
    """

    source: str
    rule: Rule = field(init=False)
    name: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "rule", parse_rule(self.source))


@dataclass(frozen=True)
class GradientRule:
    """A gradient sound change with strength parameter.

    Applies feature shifts at a given strength (0.0 to 1.0).
    At strength 0.0 no change occurs; at 1.0 full change applies.
    Between 0 and 1, each match site is independently applied with
    probability = strength using a seeded RNG.
    """

    source: str
    rule: Rule = field(init=False)
    strength: float = 1.0
    name: str = ""
    description: str = ""
    seed: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "rule", parse_rule(self.source))


@dataclass
class RuleSet:
    """An ordered collection of rules applied in sequence."""

    name: str = ""
    rules: list[CategoricalRule | GradientRule] = field(default_factory=list)

    def add(self, rule: CategoricalRule | GradientRule) -> None:
        """Add a rule to the set."""
        self.rules.append(rule)

    def __len__(self) -> int:
        return len(self.rules)

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self.rules)
