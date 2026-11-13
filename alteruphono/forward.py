"""Forward application of sound change rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

from alteruphono import _core, _native
from alteruphono.features import get_system, normalize_output
from alteruphono.match import _has_quantifiers, build_syllable_map, match_pattern
from alteruphono.modifiers import apply_modifiers
from alteruphono.types import (
    BackRefToken,
    Boundary,
    BoundaryToken,
    EmptyToken,
    QuantifiedToken,
    SegmentToken,
    SetToken,
    Sound,
    SyllableCondToken,
)

if TYPE_CHECKING:
    from alteruphono.types import Element, MatchResult, Rule, Sequence, Token


def _pattern_length_range(pattern: tuple[Token, ...]) -> tuple[int, int]:
    """Compute min and max possible match lengths for a pattern."""
    min_len = 0
    max_len = 0
    for tok in pattern:
        if isinstance(tok, QuantifiedToken):
            if tok.quantifier == "+":
                min_len += 1
                max_len += 100  # Generous upper bound
            elif tok.quantifier == "?":
                max_len += 1
        else:
            min_len += 1
            max_len += 1
    return min_len, max_len


def _needs_syllable_map(pattern: tuple[Token, ...]) -> bool:
    """Check if a pattern uses syllable conditions."""
    return any(isinstance(tok, SyllableCondToken) for tok in pattern)


def _build_pattern_elem_map(
    ante: tuple[Token, ...],
    sub_seq: Sequence,
    result: MatchResult,
) -> dict[int, Element]:
    """Map ante pattern indices to their matched sequence elements.

    For quantified tokens that match multiple elements, maps to the last one.
    For fixed tokens, maps directly by position.
    """
    mapping: dict[int, Element] = {}
    binding_idx = 0

    for pat_idx, tok in enumerate(ante):
        if isinstance(tok, QuantifiedToken):
            # Quantified tokens consume variable number of bindings
            # We map the pattern index to the last element matched
            last_elem: Element | None = None
            while binding_idx < len(result.bindings):
                b = result.bindings[binding_idx]
                if b is None:
                    break
                if isinstance(b, (Sound, Boundary)):
                    last_elem = b
                binding_idx += 1
                # Check if the next binding belongs to the next pattern token
                if binding_idx < len(result.bindings) and pat_idx + 1 < len(ante):
                    # Peek: if remaining bindings can satisfy remaining pattern
                    remaining_bindings = len(result.bindings) - binding_idx
                    remaining_fixed = sum(
                        1 for t in ante[pat_idx + 1 :] if not isinstance(t, QuantifiedToken)
                    )
                    if remaining_bindings <= remaining_fixed:
                        break
            if last_elem is not None:
                mapping[pat_idx] = last_elem
        else:
            if binding_idx < len(sub_seq):
                mapping[pat_idx] = sub_seq[binding_idx]
                binding_idx += 1

    return mapping


def _translate(
    sub_seq: Sequence,
    ante: tuple[Token, ...],
    post: tuple[Token, ...],
    result: MatchResult,
    system_name: str | None,
) -> list[Element]:
    """Translate a matched subsequence using the rule's post pattern."""
    sys = get_system(system_name)
    output: list[Element] = []

    # Build pattern-index to element mapping for BackRefToken resolution
    has_quant = _has_quantifiers(ante)
    elem_map = _build_pattern_elem_map(ante, sub_seq, result) if has_quant else {}

    # Collect set-match indexes from bindings for SetToken resolution
    set_indexes: list[int] = [b for b in result.bindings if isinstance(b, int)]
    set_idx_iter = iter(set_indexes)

    for token in post:
        if isinstance(token, EmptyToken):
            continue

        if isinstance(token, SegmentToken):
            output.append(token.sound)

        elif isinstance(token, SetToken):
            idx = next(set_idx_iter, None)
            if idx is None:
                msg = "Set correspondence mismatch: post uses more set tokens than ante."
                raise ValueError(msg)
            if idx >= len(token.choices):
                msg = "Set correspondence mismatch: set index out of range in post token."
                raise ValueError(msg)
            choice = token.choices[idx]
            if isinstance(choice, SegmentToken):
                output.append(choice.sound)

        elif isinstance(token, BackRefToken):
            if has_quant:
                elem = elem_map.get(token.index)
            else:
                elem = sub_seq[token.index] if token.index < len(sub_seq) else None

            if elem is None:
                continue

            if token.modifier and isinstance(elem, Sound) and elem.features:
                new_feats = apply_modifiers(elem.features, token.modifier, sys)
                new_grapheme = sys.features_to_grapheme(new_feats)
                if new_grapheme:
                    new_grapheme = normalize_output(new_grapheme)
                output.append(
                    Sound(
                        grapheme=new_grapheme or elem.grapheme,
                        features=new_feats,
                    )
                )
            else:
                output.append(elem)

        elif isinstance(token, BoundaryToken):
            output.append(Boundary())

    return output


def forward(
    sequence: Sequence,
    rule: Rule,
    system_name: str | None = None,
) -> Sequence:
    """Apply a sound change rule forward to a sequence.

    Runs in the C engine. Rules apply simultaneously (SPE): contexts are
    matched against the input and never consumed, for fixed-length and
    quantified rules alike. The helpers above are 1.x's Python matcher, kept
    for engine.gradient's probabilistic application.
    """
    if system_name is not None:
        get_system(system_name)  # an unknown system is an error, as in 1.x
    if len(rule.ante) == 0 or len(sequence) == 0:
        return sequence
    return _core.forward(sequence, rule)
