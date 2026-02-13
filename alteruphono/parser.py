"""Regex-based parser for sound change rules and sequences."""

from __future__ import annotations

import re
import unicodedata

from alteruphono.features import sound as make_sound
from alteruphono.types import (
    BackRefToken,
    Boundary,
    BoundaryToken,
    ChoiceToken,
    EmptyToken,
    FocusToken,
    NegationToken,
    QuantifiedToken,
    Rule,
    SegmentToken,
    SetToken,
    Sound,
    SyllableCondToken,
    Token,
)

# Regex patterns for rule structure
_RE_RULE_CTX = re.compile(r"^(?P<ante>[^>→]+)[>→](?P<post>[^/]+)/(?P<context>.+)$")
_RE_RULE_NOCTX = re.compile(r"^(?P<ante>[^>→]+)[>→](?P<post>[^/]+)$")
_RE_BACKREF_MOD = re.compile(r"^@(?P<index>\d+)\[(?P<mod>[^\]]+)\]$")
_RE_BACKREF_NOMOD = re.compile(r"^@(?P<index>\d+)$")


def _preprocess(text: str) -> str:
    """Normalize Unicode (NFD) and collapse whitespace."""
    text = unicodedata.normalize("NFD", text)
    text = re.sub(r"\s+", " ", text.strip())
    # Normalize -> to > for backward compat with v1 TSV
    text = text.replace("->", ">")
    return text


def _parse_atom(atom_str: str) -> Token:
    """Parse a single atom string into a Token."""
    atom_str = atom_str.strip()

    # Negation: !V, !p|b etc. — must be checked before "|" split
    if atom_str.startswith("!"):
        inner = _parse_atom(atom_str[1:])
        return NegationToken(inner=inner)

    if atom_str.startswith("{") and atom_str.endswith("}"):
        choices = tuple(_parse_atom(c) for c in atom_str[1:-1].split("|"))
        return SetToken(choices=choices)
    if "|" in atom_str:
        choices = tuple(_parse_atom(c) for c in atom_str.split("|"))
        return ChoiceToken(choices=choices)
    if atom_str == "#":
        return BoundaryToken()
    if atom_str == "_":
        return FocusToken()
    if atom_str == ":null:":
        return EmptyToken()

    # Syllable condition tokens: _.onset, _.nucleus, _.coda
    if atom_str.startswith("_.") and atom_str[2:] in ("onset", "nucleus", "coda"):
        return SyllableCondToken(position=atom_str[2:])

    m = _RE_BACKREF_MOD.match(atom_str)
    if m is not None:
        return BackRefToken(index=int(m.group("index")) - 1, modifier=m.group("mod"))

    m = _RE_BACKREF_NOMOD.match(atom_str)
    if m is not None:
        return BackRefToken(index=int(m.group("index")) - 1)

    # Quantifier: C+, V?, N+ etc.
    if len(atom_str) > 1 and atom_str[-1] in ("+", "?"):
        quantifier = atom_str[-1]
        inner = _parse_atom(atom_str[:-1])
        return QuantifiedToken(inner=inner, quantifier=quantifier)

    # Treat as a sound grapheme
    snd = make_sound(atom_str)
    return SegmentToken(sound=snd)


def _shift_backref(token: Token, offset: int) -> Token:
    """Shift a BackRefToken index by offset, pass-through for other tokens."""
    if isinstance(token, BackRefToken):
        return BackRefToken(index=token.index + offset, modifier=token.modifier)
    return token


def parse_rule(source: str) -> Rule:
    """Parse a sound change rule string into a Rule.

    Accepted formats:
        "p > b"
        "p > b / V _ V"
        "V s → @1 z @1 / # p|b r _ t|d"
    """
    text = _preprocess(source)

    m = _RE_RULE_CTX.match(text)
    if m is not None:
        ante_str, post_str, context_str = (
            m.group("ante").strip(),
            m.group("post").strip(),
            m.group("context").strip(),
        )
    else:
        m = _RE_RULE_NOCTX.match(text)
        if m is None:
            msg = f"Cannot parse rule: {source!r}"
            raise ValueError(msg)
        ante_str = m.group("ante").strip()
        post_str = m.group("post").strip()
        context_str = None

    ante_seq = [_parse_atom(a) for a in ante_str.split()]
    post_seq = [_parse_atom(a) for a in post_str.split()]

    if context_str is not None:
        ctx_tokens = [_parse_atom(a) for a in context_str.split()]
        # Find focus position
        focus_idx = None
        for i, tok in enumerate(ctx_tokens):
            if isinstance(tok, FocusToken):
                focus_idx = i
                break
        if focus_idx is None:
            msg = f"Context missing focus (_) in rule: {source!r}"
            raise ValueError(msg)

        left_ctx = ctx_tokens[:focus_idx]
        right_ctx = ctx_tokens[focus_idx + 1 :]

        offset_left = len(left_ctx)
        offset_ante = len(ante_seq)

        # Shift backrefs in ante and post by left-context length
        if left_ctx:
            ante_seq = [_shift_backref(t, offset_left) for t in ante_seq]
            post_seq = [_shift_backref(t, offset_left) for t in post_seq]

        # Merge: ante = left_ctx + ante + right_ctx (with shifted backrefs)
        merged_ante: list[Token] = list(left_ctx) + ante_seq
        merged_ante += [_shift_backref(t, offset_left + offset_ante) for t in right_ctx]

        # Post: left_ctx becomes backrefs, then original post, then right_ctx backrefs
        merged_post: list[Token] = [BackRefToken(index=i) for i in range(offset_left)]
        merged_post += post_seq
        merged_post += [
            BackRefToken(index=i + offset_left + offset_ante) for i in range(len(right_ctx))
        ]

        return Rule(source=source, ante=tuple(merged_ante), post=tuple(merged_post))

    return Rule(source=source, ante=tuple(ante_seq), post=tuple(post_seq))


def parse_sequence(source: str) -> tuple[Sound | Boundary, ...]:
    """Parse a space-separated sequence string into a tuple of Elements.

    Example: "# a p a #" -> (Boundary(), Sound("a"), Sound("p"), Sound("a"), Boundary())
    """
    text = _preprocess(source)
    elements: list[Sound | Boundary] = []
    for atom in text.split():
        if atom == "#":
            elements.append(Boundary())
        else:
            snd = make_sound(atom)
            elements.append(snd)
    return tuple(elements)
