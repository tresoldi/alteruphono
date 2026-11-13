"""Backward reconstruction — given daughter form + rule, produce proto-forms.

Runs in the C engine. Semantics are 1.x's with tresoldi/alteruphono 3fdb52b:
a choice or set the output does not resolve stands for all its alternatives.
A product of more than 100,000 candidates raises OverflowError instead of
being built; a back-reference out of range raises IndexError, as in 1.x.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alteruphono import _core
from alteruphono.features import get_system

if TYPE_CHECKING:
    from alteruphono.types import Rule, Sequence


def backward(
    sequence: Sequence,
    rule: Rule,
    system_name: str | None = None,
) -> list[Sequence]:
    """Given a daughter sequence and a rule, reconstruct possible proto-forms."""
    if system_name is not None:
        get_system(system_name)  # an unknown system is an error, as in 1.x
    return _core.backward(sequence, rule)
