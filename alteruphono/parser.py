"""Parsing of sound change rules and sequences (by the C engine).

The notation is exactly 1.x's; docs/guide.md describes it. Errors are
ValueError, with 1.x's messages for the cases its tests check.
"""

from __future__ import annotations

from alteruphono import _core
from alteruphono.types import Boundary, Rule, Sound


def parse_rule(source: str) -> Rule:
    """Parse a sound change rule string into a Rule.

    Accepted formats:
        "p > b"
        "p > b / V _ V"
        "V s → @1 z @1 / # p|b r _ t|d"
    """
    return _core.parse_rule(source)


def parse_sequence(source: str) -> tuple[Sound | Boundary, ...]:
    """Parse a space-separated sequence string into a tuple of Elements.

    Example: "# a p a #" -> (Boundary(), Sound("a"), Sound("p"), Sound("a"), Boundary())
    """
    return _core.parse_sequence(source)
