"""Backward reconstruction — given daughter form + rule, produce proto-forms."""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

from alteruphono.features import get_system, normalize_output
from alteruphono.match import match_pattern
from alteruphono.modifiers import apply_modifiers, invert_modifiers
from alteruphono.types import (
    BackRefToken,
    Boundary,
    BoundaryToken,
    ChoiceToken,
    EmptyToken,
    SegmentToken,
    SetToken,
    Sound,
)

if TYPE_CHECKING:
    from alteruphono.types import Element, MatchResult, Rule, Sequence, Token


def _carry_backref_modifier(
    ante_token: Token,
    post_token: BackRefToken,
    system_name: str | None,
) -> Token:
    """Apply the modifier from a backref to its ante source (for matching)."""
    if not post_token.modifier:
        return ante_token

    if isinstance(ante_token, SegmentToken):
        sys = get_system(system_name)
        snd = ante_token.sound
        if snd.features:
            new_feats = apply_modifiers(snd.features, post_token.modifier, sys)
            new_grapheme = sys.features_to_grapheme(new_feats) or snd.grapheme
            new_grapheme = normalize_output(new_grapheme)
            return SegmentToken(
                sound=Sound(grapheme=new_grapheme, features=new_feats, partial=snd.partial)
            )
    return ante_token


def _backward_translate(
    sub_seq: Sequence,
    rule: Rule,
    result: MatchResult,
    system_name: str | None,
) -> list[Element]:
    """Produce a reconstructed (proto) subsequence from a matched daughter."""
    sys = get_system(system_name)

    # Start from ante as template for reconstruction
    recons: list[Element | ChoiceToken | SetToken] = []
    set_indices: list[int] = []
    for i, tok in enumerate(rule.ante):
        if isinstance(tok, BoundaryToken):
            recons.append(Boundary())
        elif isinstance(tok, SegmentToken):
            recons.append(tok.sound)
        elif isinstance(tok, ChoiceToken):
            recons.append(tok)
        elif isinstance(tok, SetToken):
            recons.append(tok)
            set_indices.append(i)
        else:
            recons.append(Boundary())

    # Map post-tokens to matched seq tokens, skipping EmptyTokens
    set_idx_iter = iter(set_indices)
    seq_idx = 0

    for post_tok in rule.post:
        if isinstance(post_tok, EmptyToken):
            continue
        if seq_idx >= len(sub_seq) or seq_idx >= len(result.bindings):
            break
        seq_elem = sub_seq[seq_idx]
        binding = result.bindings[seq_idx]
        seq_idx += 1
        if isinstance(post_tok, BackRefToken):
            recons[post_tok.index] = seq_elem
            if post_tok.modifier and isinstance(seq_elem, Sound) and seq_elem.features:
                inv_mod = invert_modifiers(post_tok.modifier)
                new_feats = apply_modifiers(seq_elem.features, inv_mod, sys)
                new_gr = sys.features_to_grapheme(new_feats) or seq_elem.grapheme
                new_gr = normalize_output(new_gr)
                recons[post_tok.index] = Sound(grapheme=new_gr, features=new_feats)

        elif isinstance(post_tok, SetToken) and isinstance(binding, int):
            idx = next(set_idx_iter, None)
            if idx is not None:
                set_tok = rule.ante[idx]
                if isinstance(set_tok, SetToken):
                    choice = set_tok.choices[binding]
                    if isinstance(choice, SegmentToken):
                        recons[idx] = choice.sound

    # Filter out any remaining non-Element entries (choices that weren't resolved)
    result_elems: list[Element] = []
    for item in recons:
        if isinstance(item, (Sound, Boundary)):
            result_elems.append(item)
        elif isinstance(item, ChoiceToken):
            # Take first choice as fallback
            if item.choices and isinstance(item.choices[0], SegmentToken):
                result_elems.append(item.choices[0].sound)
        elif (
            isinstance(item, SetToken)
            and item.choices
            and isinstance(item.choices[0], SegmentToken)
        ):
            result_elems.append(item.choices[0].sound)

    return result_elems


def backward(
    sequence: Sequence,
    rule: Rule,
    system_name: str | None = None,
) -> list[Sequence]:
    """Given a daughter sequence and a rule, reconstruct possible proto-forms."""
    # Build the post-AST for matching: skip EmptyTokens, apply backref modifiers
    non_empty: list[Token] = [t for t in rule.post if not isinstance(t, EmptyToken)]
    post_tokens: list[Token] = []
    for t in non_empty:
        if isinstance(t, BackRefToken):
            post_tokens.append(_carry_backref_modifier(rule.ante[t.index], t, system_name))
        else:
            post_tokens.append(t)
    post_ast = tuple(post_tokens)

    len_seq = len(sequence)
    len_post = len(post_ast)

    if len_post == 0 or len_seq == 0:
        return [sequence]

    # Sliding window to find matches
    idx = 0
    alternatives: list[list[list[Element]]] = []

    while idx < len_seq:
        end = min(len_seq, idx + len_post)
        sub_seq = sequence[idx:end]

        if len(sub_seq) == len_post:
            result = match_pattern(sub_seq, post_ast, system_name)
            if result.matched:
                # Two alternatives: the backward-translated and the original
                translated = _backward_translate(sub_seq, rule, result, system_name)
                alternatives.append([list(sub_seq), translated])
                idx += len_post
                continue

        alternatives.append([[sequence[idx]]])
        idx += 1

    # Generate all combinations
    candidates: list[Sequence] = []
    for combo in itertools.product(*alternatives):
        flat: list[Element] = []
        for segment_list in combo:
            flat.extend(segment_list)
        candidates.append(tuple(flat))

    # Filter out sequences with internal boundaries
    filtered: list[Sequence] = []
    for seq in candidates:
        if len(seq) < 3:
            filtered.append(seq)
            continue
        interior = seq[1:-1]
        if not any(isinstance(e, Boundary) for e in interior):
            filtered.append(seq)

    # Deduplicate and sort
    seen: set[tuple[str, ...]] = set()
    unique: list[Sequence] = []
    for seq in filtered:
        key = tuple(str(e) for e in seq)
        if key not in seen:
            seen.add(key)
            unique.append(seq)

    unique.sort(key=lambda s: " ".join(str(e) for e in s))
    return unique
