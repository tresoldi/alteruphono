"""The bridge between alteruphono's Python objects and its C engine.

One engine context per process, on merkmal's `descriptive` system with the
`alteruphono-1` projection (docs/v2/DESIGN.md 4.1). Segments are interned in
the context; each id maps to one Sound object, created once, so equal sounds
coming out of the engine are the same object. A Sound made by hand is interned
on first use, with exactly the features it carries, as 1.x would treat it.

Not thread-safe: the context is used under the GIL by one thread at a time.
"""

from __future__ import annotations

import functools
import json
from typing import TYPE_CHECKING

from alteruphono import _native
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
)

if TYPE_CHECKING:
    from alteruphono.types import Element, Token

MERKMAL_SYSTEM = "descriptive"

_context = None
# id -> object; index 0 is the Boundary, so the engine's id 0 maps through too
_BOUNDARY = Boundary()
_sounds: list[Element | None] = [_BOUNDARY]


def context():
    global _context  # noqa: PLW0603
    if _context is None:
        _context = _native.new_context(MERKMAL_SYSTEM)
    return _context


def element(seg_id: int) -> Element:
    """The Sound (or Boundary, id 0) for an engine id."""
    if seg_id == 0:
        return _BOUNDARY
    if seg_id < len(_sounds):
        s = _sounds[seg_id]
        if s is not None:
            return s
    else:
        _sounds.extend([None] * (seg_id + 1 - len(_sounds)))
    grapheme, labels, partial = _native.seg_info(context(), seg_id)
    s = Sound(grapheme=grapheme, features=frozenset(labels), partial=partial)
    object.__setattr__(s, "_ap_id", seg_id)
    _sounds[seg_id] = s
    return s


def seg_id(elem: Element) -> int:
    """The engine id of a Sound or Boundary, interning a hand-made Sound."""
    if isinstance(elem, Boundary):
        return 0
    i = elem.__dict__.get("_ap_id")
    if i is None:
        i = _native.intern(context(), elem.grapheme, tuple(elem.features), elem.partial)
        object.__setattr__(elem, "_ap_id", i)
    return i


def make_sound(grapheme: str) -> Sound:
    """1.x features.sound(): a class, else a grapheme's features, else none."""
    return element(_native.intern(context(), grapheme))


def _token(node: dict) -> Token:
    kind = node["kind"]
    if kind == "segment":
        return SegmentToken(sound=element(node["id"]))
    if kind == "boundary":
        return BoundaryToken()
    if kind == "backref":
        return BackRefToken(index=node["index"], modifier=node["modifier"])
    if kind == "empty":
        return EmptyToken()
    if kind == "choice":
        return ChoiceToken(choices=tuple(_token(c) for c in node["choices"]))
    if kind == "set":
        return SetToken(choices=tuple(_token(c) for c in node["choices"]))
    if kind == "focus":
        return FocusToken()
    if kind == "quantified":
        return QuantifiedToken(inner=_token(node["inner"]), quantifier=node["quantifier"])
    if kind == "syllable":
        return SyllableCondToken(position=node["position"])
    if kind == "negation":
        return NegationToken(inner=_token(node["inner"]))
    msg = f"unknown token kind from the engine: {kind!r}"
    raise RuntimeError(msg)


def parse_rule(source: str) -> Rule:
    """Parsing is pure and a Rule is immutable, so results are cached by the
    exact source text (bounded; see parse_rule_uncached)."""
    return _parse_rule_cached(source)


def parse_rule_uncached(source: str) -> Rule:
    handle, tree = _native.parse_rule(context(), source)
    data = json.loads(tree)
    rule = Rule(
        source=source,
        ante=tuple(_token(t) for t in data["ante"]),
        post=tuple(_token(t) for t in data["post"]),
        left_len=data["left_len"],
        right_len=data["right_len"],
    )
    object.__setattr__(rule, "_ap_rule", handle)
    return rule


_parse_rule_cached = functools.lru_cache(maxsize=65536)(parse_rule_uncached)


def rule_handle(rule: Rule):
    """The compiled rule. A Rule built by hand is compiled from its source."""
    handle = rule.__dict__.get("_ap_rule")
    if handle is None:
        handle, _ = _native.parse_rule(context(), rule.source)
        object.__setattr__(rule, "_ap_rule", handle)
    return handle


def parse_sequence(source: str) -> tuple[Element, ...]:
    return tuple(element(i) for i in _native.parse_sequence(context(), source))


def forward(sequence, rule: Rule) -> tuple[Element, ...]:
    ctx = context()
    handle = rule.__dict__.get("_ap_rule") or rule_handle(rule)
    res = _native.forward_objs(ctx, handle, sequence, _sounds, Boundary)
    if res is None:  # an element without an id: intern, then the slow path
        res = _native.forward(ctx, handle, [seg_id(e) for e in sequence])
    if isinstance(res, list):  # new output segments: create their objects
        return tuple(element(i) for i in res)
    return res


def backward(sequence, rule: Rule) -> list[tuple[Element, ...]]:
    ctx = context()
    handle = rule.__dict__.get("_ap_rule") or rule_handle(rule)
    res = _native.backward_objs(ctx, handle, sequence, _sounds, Boundary)
    if res is None:
        res = _native.backward(ctx, handle, [seg_id(e) for e in sequence])
    return [c if isinstance(c, tuple) else tuple(element(i) for i in c) for c in res]
