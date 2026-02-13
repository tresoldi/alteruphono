"""AlteruPhono — Historical linguistics sound change library."""

from __future__ import annotations

__version__ = "1.0.0rc1"

from alteruphono.backward import backward
from alteruphono.forward import forward
from alteruphono.match import match_pattern
from alteruphono.parser import parse_rule, parse_sequence
from alteruphono.types import (
    BackRefToken,
    Boundary,
    BoundaryToken,
    ChoiceToken,
    EmptyToken,
    FocusToken,
    MatchResult,
    NegationToken,
    QuantifiedToken,
    Rule,
    SegmentToken,
    SetToken,
    Sound,
    SyllableCondToken,
)

__all__ = [
    "__version__",
    # Primitives
    "Sound",
    "Boundary",
    # Tokens
    "SegmentToken",
    "BoundaryToken",
    "BackRefToken",
    "EmptyToken",
    "ChoiceToken",
    "SetToken",
    "FocusToken",
    "QuantifiedToken",
    "SyllableCondToken",
    "NegationToken",
    # Rule & result
    "Rule",
    "MatchResult",
    # Functions
    "parse_rule",
    "parse_sequence",
    "match_pattern",
    "forward",
    "backward",
]
