"""Sound change engine — applies rule sets to sequences."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from alteruphono.engine.gradient import apply_gradient
from alteruphono.forward import forward

if TYPE_CHECKING:
    from alteruphono.engine.rules import CategoricalRule, GradientRule, RuleSet
    from alteruphono.types import Sequence


@dataclass(frozen=True)
class StepResult:
    """Result of a single rule application step."""

    rule_name: str
    input_str: str
    output_str: str
    changed: bool


@dataclass
class Trajectory:
    """Full trajectory of a sequence through a rule set."""

    input_seq: Sequence
    steps: list[StepResult] = field(default_factory=list)
    output_seq: Sequence = ()

    @property
    def changed(self) -> bool:
        return any(s.changed for s in self.steps)


class SoundChangeEngine:
    """Engine for applying ordered rule sets to sequences."""

    def __init__(self, system_name: str | None = None) -> None:
        self._system_name = system_name

    def apply_rule(
        self,
        sequence: Sequence,
        rule: CategoricalRule | GradientRule,
    ) -> Sequence:
        """Apply a single rule to a sequence."""
        from alteruphono.engine.rules import GradientRule

        if isinstance(rule, GradientRule):
            return apply_gradient(
                sequence, rule.source, rule.strength, self._system_name, rule.seed
            )
        return forward(sequence, rule.rule, self._system_name)

    def apply_ruleset(
        self,
        sequence: Sequence,
        ruleset: RuleSet,
    ) -> Sequence:
        """Apply all rules in a ruleset sequentially."""
        current = sequence
        for rule in ruleset:
            current = self.apply_rule(current, rule)
        return current

    def apply_with_trajectory(
        self,
        sequence: Sequence,
        ruleset: RuleSet,
    ) -> Trajectory:
        """Apply rules and record the full trajectory."""
        trajectory = Trajectory(input_seq=sequence)
        current = sequence

        for rule in ruleset:
            input_str = " ".join(str(e) for e in current)
            result = self.apply_rule(current, rule)
            output_str = " ".join(str(e) for e in result)

            step = StepResult(
                rule_name=rule.name or rule.source,
                input_str=input_str,
                output_str=output_str,
                changed=input_str != output_str,
            )
            trajectory.steps.append(step)
            current = result

        trajectory.output_seq = current
        return trajectory
