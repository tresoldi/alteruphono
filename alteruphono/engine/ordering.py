"""Rule ordering analysis — feeding, bleeding, and interaction detection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from alteruphono.forward import forward
from alteruphono.parser import parse_rule, parse_sequence

if TYPE_CHECKING:
    from alteruphono.types import Rule, Sequence


class Interaction(Enum):
    """Types of rule interaction in ordered phonology."""

    FEEDING = "feeding"
    BLEEDING = "bleeding"
    COUNTERFEEDING = "counterfeeding"
    COUNTERBLEEDING = "counterbleeding"
    INDEPENDENT = "independent"


@dataclass(frozen=True)
class RuleInteraction:
    """Result of analyzing the interaction between two rules."""

    rule_a: str
    rule_b: str
    interaction: Interaction
    example_input: str
    ab_output: str
    ba_output: str


def _apply(rule: Rule, seq: Sequence, system_name: str | None = None) -> Sequence:
    """Apply a rule to a sequence."""
    return forward(seq, rule, system_name)


def _seq_str(seq: Sequence) -> str:
    """Convert sequence to space-separated string."""
    return " ".join(str(e) for e in seq)


def _generate_probes(
    rule_a: Rule,
    rule_b: Rule,
    system_name: str | None = None,
) -> list[Sequence]:
    """Generate probe sequences from rule ante patterns.

    Creates test inputs by extracting sounds from rule patterns.
    """
    from alteruphono.types import SegmentToken, Sound

    probes: list[Sequence] = []

    # Extract sounds from ante patterns
    for rule in (rule_a, rule_b):
        sounds: list[Sound] = []
        for tok in rule.ante:
            if isinstance(tok, SegmentToken) and not tok.sound.partial:
                sounds.append(tok.sound)
        if sounds:
            from alteruphono.types import Boundary

            probe: Sequence = (Boundary(), *sounds, Boundary())
            probes.append(probe)

            # Also try with sounds from both rules
            other = rule_b if rule is rule_a else rule_a
            other_sounds: list[Sound] = []
            for tok in other.ante:
                if isinstance(tok, SegmentToken) and not tok.sound.partial:
                    other_sounds.append(tok.sound)
            if other_sounds:
                combined: Sequence = (
                    Boundary(),
                    *sounds,
                    *other_sounds,
                    Boundary(),
                )
                probes.append(combined)

    return probes


def _classify_interaction(
    rule_a: Rule,
    rule_b: Rule,
    probe: Sequence,
    system_name: str | None = None,
) -> Interaction:
    """Classify the interaction between two rules on a given probe."""
    # Apply A alone
    after_a = _apply(rule_a, probe, system_name)
    # Apply B alone
    after_b = _apply(rule_b, probe, system_name)
    # Apply A then B
    after_ab = _apply(rule_b, after_a, system_name)
    # Apply B then A
    after_ba = _apply(rule_a, after_b, system_name)

    a_changed = after_a != probe
    b_changed = after_b != probe
    b_after_a_changed = after_ab != after_a
    a_after_b_changed = after_ba != after_b

    # Feeding: A creates environment for B (B doesn't apply alone, but applies after A)
    if not b_changed and b_after_a_changed:
        return Interaction.FEEDING

    # Bleeding: A removes environment for B (B applies alone, but not after A)
    if b_changed and not b_after_a_changed:
        return Interaction.BLEEDING

    # Check if order matters
    if after_ab != after_ba:
        # Counterfeeding: B→A gives different result, B would feed A but doesn't get to
        if not a_changed and a_after_b_changed:
            return Interaction.COUNTERFEEDING
        # Counterbleeding: A→B gives different result, A would bleed B but doesn't
        if a_changed and not a_after_b_changed:
            return Interaction.COUNTERBLEEDING
        # Generic order-dependent — classify by which direction has feeding/bleeding
        if b_after_a_changed and not b_changed:
            return Interaction.FEEDING
        if b_changed and not b_after_a_changed:
            return Interaction.BLEEDING
        return Interaction.FEEDING  # Default for order-dependent

    return Interaction.INDEPENDENT


def analyze_interactions(
    ruleset: object,
    test_sequences: list[str] | None = None,
    system_name: str | None = None,
) -> list[RuleInteraction]:
    """Analyze pairwise rule interactions in a ruleset.

    Args:
        ruleset: A RuleSet or list of rule source strings.
        test_sequences: Optional probe sequences (space-separated).
            If not provided, probes are generated from rule patterns.
        system_name: Feature system to use.

    Returns:
        List of RuleInteraction results for each pair.
    """
    from alteruphono.engine.rules import CategoricalRule, GradientRule, RuleSet

    # Normalize input to list of (source, Rule)
    rules: list[tuple[str, Rule]] = []
    if isinstance(ruleset, RuleSet):
        for r in ruleset:
            rules.append((r.source, r.rule))
    elif isinstance(ruleset, list):
        for item in ruleset:
            if isinstance(item, str):
                rules.append((item, parse_rule(item)))
            elif isinstance(item, (CategoricalRule, GradientRule)):
                rules.append((item.source, item.rule))
    else:
        msg = f"Expected RuleSet or list, got {type(ruleset)}"
        raise TypeError(msg)

    # Parse test sequences
    probes: list[Sequence] = []
    if test_sequences:
        for seq_str in test_sequences:
            probes.append(parse_sequence(seq_str))

    interactions: list[RuleInteraction] = []

    for i in range(len(rules)):
        for j in range(i + 1, len(rules)):
            src_a, rule_a = rules[i]
            src_b, rule_b = rules[j]

            # Generate probes if none provided
            effective_probes = probes or _generate_probes(rule_a, rule_b, system_name)
            if not effective_probes:
                interactions.append(
                    RuleInteraction(
                        rule_a=src_a,
                        rule_b=src_b,
                        interaction=Interaction.INDEPENDENT,
                        example_input="",
                        ab_output="",
                        ba_output="",
                    )
                )
                continue

            # Test all probes, use first non-independent result
            best_interaction = Interaction.INDEPENDENT
            best_probe: Sequence = effective_probes[0]

            for probe in effective_probes:
                interaction = _classify_interaction(rule_a, rule_b, probe, system_name)
                if interaction != Interaction.INDEPENDENT:
                    best_interaction = interaction
                    best_probe = probe
                    break

            # Compute outputs for the example
            after_a = _apply(rule_a, best_probe, system_name)
            after_ab = _apply(rule_b, after_a, system_name)
            after_b = _apply(rule_b, best_probe, system_name)
            after_ba = _apply(rule_a, after_b, system_name)

            interactions.append(
                RuleInteraction(
                    rule_a=src_a,
                    rule_b=src_b,
                    interaction=best_interaction,
                    example_input=_seq_str(best_probe),
                    ab_output=_seq_str(after_ab),
                    ba_output=_seq_str(after_ba),
                )
            )

    return interactions


def recommend_ordering(
    interactions: list[RuleInteraction],
) -> list[str]:
    """Generate human-readable ordering recommendations.

    Also attempts topological sort when possible.
    """
    recommendations: list[str] = []
    # Collect ordering constraints: (should_come_first, should_come_second)
    order_before: dict[str, set[str]] = {}

    for ri in interactions:
        if ri.interaction == Interaction.INDEPENDENT:
            continue

        if ri.interaction == Interaction.FEEDING:
            recommendations.append(
                f"FEEDING: '{ri.rule_a}' feeds '{ri.rule_b}' — "
                f"apply '{ri.rule_a}' before '{ri.rule_b}'"
            )
            order_before.setdefault(ri.rule_a, set()).add(ri.rule_b)

        elif ri.interaction == Interaction.BLEEDING:
            recommendations.append(
                f"BLEEDING: '{ri.rule_a}' bleeds '{ri.rule_b}' — "
                f"apply '{ri.rule_a}' before '{ri.rule_b}' to get bleeding effect, "
                f"or reverse for counterbleeding"
            )
            order_before.setdefault(ri.rule_a, set()).add(ri.rule_b)

        elif ri.interaction == Interaction.COUNTERFEEDING:
            recommendations.append(
                f"COUNTERFEEDING: '{ri.rule_b}' could feed '{ri.rule_a}' but doesn't in A→B order"
            )

        elif ri.interaction == Interaction.COUNTERBLEEDING:
            recommendations.append(
                f"COUNTERBLEEDING: '{ri.rule_a}' could bleed '{ri.rule_b}' "
                f"but doesn't in A→B order"
            )

    # Attempt topological sort
    if order_before:
        all_rules: set[str] = set()
        for k, vs in order_before.items():
            all_rules.add(k)
            all_rules.update(vs)

        # Kahn's algorithm
        in_degree: dict[str, int] = {r: 0 for r in all_rules}
        for _, successors in order_before.items():
            for s in successors:
                in_degree[s] = in_degree.get(s, 0) + 1

        queue = sorted(r for r in all_rules if in_degree[r] == 0)
        topo_order: list[str] = []
        while queue:
            node = queue.pop(0)
            topo_order.append(node)
            for s in sorted(order_before.get(node, set())):
                in_degree[s] -= 1
                if in_degree[s] == 0:
                    queue.append(s)

        if len(topo_order) == len(all_rules):
            order_str = " → ".join(f"'{r}'" for r in topo_order)
            recommendations.append(f"Suggested order: {order_str}")

    return recommendations
