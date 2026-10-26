"""Gradient/probabilistic sound change utilities."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from alteruphono.forward import _needs_syllable_map, _pattern_length_range, forward
from alteruphono.match import _has_quantifiers, build_syllable_map, match_pattern
from alteruphono.parser import parse_rule

if TYPE_CHECKING:
    from alteruphono.types import Element, Rule, Sequence


def apply_gradient(
    sequence: Sequence,
    rule_source: str,
    strength: float = 1.0,
    system_name: str | None = None,
    seed: int | None = None,
) -> Sequence:
    """Apply a sound change rule at a given strength.

    - strength >= 1.0: full apply (every match site)
    - strength <= 0.0: no-op
    - 0 < strength < 1: per-site coin flip with probability = strength
    """
    if strength <= 0.0:
        return sequence
    if strength >= 1.0:
        rule = parse_rule(rule_source)
        return forward(sequence, rule, system_name)

    rule = parse_rule(rule_source)
    return _forward_probabilistic(sequence, rule, strength, system_name, seed)


def _forward_probabilistic(
    sequence: Sequence,
    rule: Rule,
    strength: float,
    system_name: str | None,
    seed: int | None,
) -> Sequence:
    """Apply rule with per-site probability."""
    # Import translate from forward — use it via forward() for matched sites
    from alteruphono.forward import _translate

    rng = random.Random(seed)
    len_seq = len(sequence)

    if len(rule.ante) == 0 or len_seq == 0:
        return sequence

    has_quant = _has_quantifiers(rule.ante)

    syllable_map: dict[int, str] | None = None
    if _needs_syllable_map(rule.ante):
        syllable_map = build_syllable_map(sequence, system_name)

    idx = 0
    output: list[Element] = []
    left, right = rule.left_len, rule.right_len

    if has_quant:
        min_len, max_len = _pattern_length_range(rule.ante)
        while idx < len_seq:
            matched = False
            window_max = min(max_len, len_seq - idx)
            for window in range(window_max, min_len - 1, -1):
                sub_seq = sequence[idx : idx + window]
                result = match_pattern(sub_seq, rule.ante, system_name, syllable_map, idx)
                if result.matched:
                    # Right context is only looked at, not consumed.
                    span = max(result.span - right, 1)
                    if rng.random() < strength:
                        translated = _translate(sub_seq, rule.ante, rule.post, result, system_name)
                        output.extend(translated[: len(translated) - right])
                    else:
                        output.extend(sub_seq[:span])
                    idx += span
                    matched = True
                    break
            if not matched:
                output.append(sequence[idx])
                idx += 1
    else:
        # Simultaneous application: contexts are matched against the input.
        len_rule = len(rule.ante)
        focus_len = len_rule - left - right
        while idx < len_seq:
            start = idx - left
            if start >= 0 and start + len_rule <= len_seq:
                sub_seq = sequence[start : start + len_rule]
                result = match_pattern(sub_seq, rule.ante, system_name, syllable_map, start)
                if result.matched:
                    if rng.random() < strength:
                        translated = _translate(sub_seq, rule.ante, rule.post, result, system_name)
                        output.extend(translated[left : len(translated) - right])
                        if focus_len == 0:
                            output.append(sequence[idx])
                    else:
                        output.extend(sequence[idx : idx + max(focus_len, 1)])
                    idx += max(focus_len, 1)
                    continue
            output.append(sequence[idx])
            idx += 1

    return tuple(output)
