"""Shared modifier handling for forward/backward sound change application."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from alteruphono.features.protocol import FeatureSystem


def apply_modifiers(
    features: frozenset[str],
    modifier_str: str,
    system: FeatureSystem,
) -> frozenset[str]:
    """Apply +feature/-feature modifiers to a feature set.

    Single-pass: collect additions, apply via system.add_features,
    then remove subtractions.
    """
    additions: set[str] = set()
    subtractions: set[str] = set()

    for mod in modifier_str.split(","):
        mod = mod.strip()
        if mod.startswith("+"):
            additions.add(mod[1:])
        elif mod.startswith("-"):
            subtractions.add(mod[1:])
        else:
            additions.add(mod)

    result = system.add_features(features, frozenset(additions))
    if subtractions:
        result = frozenset(f for f in result if f not in subtractions)
    return result


def invert_modifiers(modifier_str: str) -> str:
    """Flip +/- prefixes for backward reconstruction."""
    inverted: list[str] = []
    for mod in modifier_str.split(","):
        mod = mod.strip()
        if mod.startswith("+"):
            inverted.append("-" + mod[1:])
        elif mod.startswith("-"):
            inverted.append("+" + mod[1:])
        else:
            inverted.append("-" + mod)
    return ",".join(inverted)
