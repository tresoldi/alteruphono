"""Pattern matching for sequences against rule patterns."""

from __future__ import annotations

from typing import TYPE_CHECKING

from alteruphono.features import get_system
from alteruphono.types import (
    Boundary,
    BoundaryToken,
    ChoiceToken,
    MatchResult,
    NegationToken,
    QuantifiedToken,
    SegmentToken,
    SetToken,
    Sound,
    SyllableCondToken,
)

if TYPE_CHECKING:
    from alteruphono.types import Element, Sequence, Token


def _has_quantifiers(pattern: tuple[Token, ...]) -> bool:
    """Check if a pattern contains any QuantifiedToken."""
    return any(isinstance(t, QuantifiedToken) for t in pattern)


def match_pattern(
    sequence: Sequence,
    pattern: tuple[Token, ...],
    system_name: str | None = None,
    syllable_map: dict[int, str] | None = None,
    offset: int = 0,
) -> MatchResult:
    """Match a sequence of Elements against a tuple of Tokens.

    Returns a MatchResult with:
      - matched: True if every position matches
      - bindings: for each position, the matched Element (or set index for SetTokens,
        or None for non-matches)
      - span: number of sequence elements consumed
    """
    sys = get_system(system_name)

    if _has_quantifiers(pattern):
        return _match_variable(sequence, pattern, sys, syllable_map, offset)

    return _match_fixed(sequence, pattern, sys, syllable_map, offset)


def _match_fixed(
    sequence: Sequence,
    pattern: tuple[Token, ...],
    sys: object,
    syllable_map: dict[int, str] | None = None,
    offset: int = 0,
) -> MatchResult:
    """Fixed-length matching (no quantifiers)."""
    if len(sequence) != len(pattern):
        return MatchResult(
            matched=False,
            bindings=tuple(None for _ in range(len(sequence))),
            span=0,
        )

    bindings: list[Element | int | None] = []

    for i, (elem, tok) in enumerate(zip(sequence, pattern, strict=True)):
        result = _match_one(elem, tok, sys, syllable_map, offset + i)
        bindings.append(result)

    all_matched = all(b is not None for b in bindings)
    return MatchResult(
        matched=all_matched,
        bindings=tuple(bindings),
        span=len(sequence) if all_matched else 0,
    )


def _match_variable(
    sequence: Sequence,
    pattern: tuple[Token, ...],
    sys: object,
    syllable_map: dict[int, str] | None = None,
    offset: int = 0,
) -> MatchResult:
    """Variable-length matching for patterns with QuantifiedTokens.

    Uses recursive backtracking: greedy for +, try-skip-first for ?.
    """
    max_len = len(sequence)
    result = _backtrack(sequence, 0, pattern, 0, [], sys, syllable_map, offset, max_len)
    if result is not None:
        bindings, span = result
        return MatchResult(matched=True, bindings=tuple(bindings), span=span)
    return MatchResult(matched=False, bindings=(), span=0)


def _backtrack(
    sequence: Sequence,
    seq_idx: int,
    pattern: tuple[Token, ...],
    pat_idx: int,
    bindings: list[Element | int | None],
    sys: object,
    syllable_map: dict[int, str] | None,
    offset: int,
    max_len: int,
) -> tuple[list[Element | int | None], int] | None:
    """Recursive backtracking matcher."""
    # Pattern exhausted: success if we matched something
    if pat_idx >= len(pattern):
        return (list(bindings), seq_idx)

    tok = pattern[pat_idx]

    if isinstance(tok, QuantifiedToken):
        if tok.quantifier == "+":
            # One-or-more: must match at least 1, then greedily try more
            return _backtrack_plus(
                sequence,
                seq_idx,
                pattern,
                pat_idx,
                bindings,
                sys,
                syllable_map,
                offset,
                max_len,
            )
        if tok.quantifier == "?":
            # Optional: try with 0 matches first, then 1
            # Try skip (0 matches)
            result = _backtrack(
                sequence,
                seq_idx,
                pattern,
                pat_idx + 1,
                bindings,
                sys,
                syllable_map,
                offset,
                max_len,
            )
            if result is not None:
                return result
            # Try 1 match
            if seq_idx < max_len:
                m = _match_one(
                    sequence[seq_idx],
                    tok.inner,
                    sys,
                    syllable_map,
                    offset + seq_idx,
                )
                if m is not None:
                    return _backtrack(
                        sequence,
                        seq_idx + 1,
                        pattern,
                        pat_idx + 1,
                        [*bindings, m],
                        sys,
                        syllable_map,
                        offset,
                        max_len,
                    )
            return None

    # Regular token: must match exactly 1
    if seq_idx >= max_len:
        return None

    m = _match_one(sequence[seq_idx], tok, sys, syllable_map, offset + seq_idx)
    if m is None:
        return None

    return _backtrack(
        sequence,
        seq_idx + 1,
        pattern,
        pat_idx + 1,
        [*bindings, m],
        sys,
        syllable_map,
        offset,
        max_len,
    )


def _backtrack_plus(
    sequence: Sequence,
    seq_idx: int,
    pattern: tuple[Token, ...],
    pat_idx: int,
    bindings: list[Element | int | None],
    sys: object,
    syllable_map: dict[int, str] | None,
    offset: int,
    max_len: int,
) -> tuple[list[Element | int | None], int] | None:
    """Match a + quantifier: greedy, at least 1."""
    tok = pattern[pat_idx]
    assert isinstance(tok, QuantifiedToken)

    # Collect all consecutive matches
    matched_bindings: list[Element | int | None] = []
    idx = seq_idx
    while idx < max_len:
        m = _match_one(sequence[idx], tok.inner, sys, syllable_map, offset + idx)
        if m is None:
            break
        matched_bindings.append(m)
        idx += 1

    # Try from most to fewest matches (greedy)
    for n in range(len(matched_bindings), 0, -1):
        result = _backtrack(
            sequence,
            seq_idx + n,
            pattern,
            pat_idx + 1,
            [*bindings, *matched_bindings[:n]],
            sys,
            syllable_map,
            offset,
            max_len,
        )
        if result is not None:
            return result

    return None


def _match_one(
    elem: Element,
    tok: Token,
    sys: object,
    syllable_map: dict[int, str] | None = None,
    seq_pos: int = 0,
) -> Element | int | None:
    """Match a single element against a single token."""
    if isinstance(tok, BoundaryToken):
        if isinstance(elem, Boundary):
            return elem
        return None

    if isinstance(tok, SegmentToken):
        return _match_segment(elem, tok, sys)

    if isinstance(tok, ChoiceToken):
        return _match_choice(elem, tok, sys, syllable_map, seq_pos)

    if isinstance(tok, SetToken):
        return _match_set(elem, tok, sys, syllable_map, seq_pos)

    if isinstance(tok, SyllableCondToken):
        if (
            syllable_map is not None
            and seq_pos in syllable_map
            and syllable_map[seq_pos] == tok.position
        ):
            return elem
        return None

    if isinstance(tok, NegationToken):
        inner_result = _match_one(elem, tok.inner, sys, syllable_map, seq_pos)
        return elem if inner_result is None else None

    return None


def _match_segment(
    elem: Element,
    tok: SegmentToken,
    sys: object,
) -> Element | None:
    """Match an element against a SegmentToken."""
    if not isinstance(elem, Sound):
        return None

    pattern_sound = tok.sound

    # Exact match
    if not pattern_sound.partial:
        if elem.grapheme == pattern_sound.grapheme:
            return elem
        if elem == pattern_sound:
            return elem
        return None

    # Partial match: pattern features must be subset of element features
    if pattern_sound.features and elem.features:
        if hasattr(sys, "partial_match"):
            if sys.partial_match(pattern_sound.features, elem.features):
                return elem
        elif pattern_sound.features <= elem.features:
            return elem
        return None

    return None


def _match_choice(
    elem: Element,
    tok: ChoiceToken,
    sys: object,
    syllable_map: dict[int, str] | None = None,
    seq_pos: int = 0,
) -> Element | None:
    """Match an element against any of the choices."""
    for choice in tok.choices:
        result = _match_one(elem, choice, sys, syllable_map, seq_pos)
        if result is not None:
            return elem
    return None


def _match_set(
    elem: Element,
    tok: SetToken,
    sys: object,
    syllable_map: dict[int, str] | None = None,
    seq_pos: int = 0,
) -> int | None:
    """Match an element against a set and return the matched index."""
    for i, choice in enumerate(tok.choices):
        result = _match_one(elem, choice, sys, syllable_map, seq_pos)
        if result is not None:
            return i
    return None


def build_syllable_map(
    sequence: Sequence,
    system_name: str | None = None,
) -> dict[int, str]:
    """Build a position -> syllable role map for a sequence.

    Returns dict mapping sequence index to "onset", "nucleus", or "coda".
    Skips Boundary elements.
    """
    from alteruphono.prosody import syllabify

    # Extract just the sounds with their original indices
    sounds: list[tuple[int, Sound]] = []
    for i, elem in enumerate(sequence):
        if isinstance(elem, Sound):
            sounds.append((i, elem))

    if not sounds:
        return {}

    sound_tuple = tuple(s for _, s in sounds)
    word = syllabify(sound_tuple, system_name)

    result: dict[int, str] = {}
    sound_idx = 0
    for syl in word.syllables:
        for _ in syl.onset:
            if sound_idx < len(sounds):
                result[sounds[sound_idx][0]] = "onset"
                sound_idx += 1
        for _ in syl.nucleus:
            if sound_idx < len(sounds):
                result[sounds[sound_idx][0]] = "nucleus"
                sound_idx += 1
        for _ in syl.coda:
            if sound_idx < len(sounds):
                result[sounds[sound_idx][0]] = "coda"
                sound_idx += 1

    return result
