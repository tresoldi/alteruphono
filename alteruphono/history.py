"""Backward through an ordered history: proto-forms with provenance.

`backward` undoes one rule and returns every proto-form it allows, without
checking any of them. `backward_history` undoes an ordered list of rules from
the last to the first and keeps a candidate only when the rule, applied
forward, gives back the later form. Each kept proto-form therefore derives the
daughter exactly, and records which rule restored what, and where.

Two things a single-rule inverse cannot do are handled here:

* A **context-free deletion** (`H > :null:`) has infinitely many preimages.
  The lost segment is inserted only where an *earlier* rule needs it: where
  inserting it lets that rule's output pattern match, so that undoing the rule
  can use it, as `e > a / H _` needs an H before the *a* it coloured. An
  inserted segment that no earlier rule ends up using is dropped with its
  candidate. No trace, no insertion.
* An **opaque order** (a trigger later lost, a change later undone in form) is
  recovered by the order itself: undoing the later rule first restores the
  trigger the earlier one needs.

A restored sound class (`C`, `V`, ...) is an abstract segment, not a grapheme.
In the results it is reported as a merkmal `AbstractSegment` covering the
class's members.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from functools import cache
from typing import TYPE_CHECKING

from alteruphono.backward import _backward_translate, _carry_backref_modifier
from alteruphono.features import get_system
from alteruphono.forward import forward
from alteruphono.match import match_pattern
from alteruphono.parser import parse_rule
from alteruphono.types import (
    BackRefToken,
    Boundary,
    ChoiceToken,
    EmptyToken,
    SegmentToken,
    SetToken,
    Sound,
)

if TYPE_CHECKING:
    from alteruphono.types import Element, Rule, Sequence, Token


@dataclass(frozen=True)
class Restoration:
    """One step of a reconstruction, in the order the steps were undone."""

    rule_index: int
    rule: str
    kind: str  # "undo": a change reversed; "insert": a deleted segment restored
    position: int
    before: str
    after: str


@dataclass(frozen=True)
class Reconstruction:
    """A proto-form that derives the daughter through the whole history."""

    proto: Sequence
    steps: tuple[Restoration, ...]
    latents: tuple[tuple[int, object], ...] = ()  # (position, merkmal.AbstractSegment)

    def __str__(self) -> str:
        return " ".join(str(e) for e in self.proto)

    def __repr__(self) -> str:
        return (
            f"Reconstruction({str(self)!r}, steps={len(self.steps)}, latents={len(self.latents)})"
        )


@dataclass(frozen=True)
class BackwardResult:
    daughter: Sequence
    candidates: tuple[Reconstruction, ...]
    truncated: bool
    explored: int


@dataclass(frozen=True)
class _State:
    seq: tuple[Element, ...]
    tags: tuple[int, ...]  # 0, or the id of an insertion still waiting for a licence
    steps: tuple[Restoration, ...] = field(default=())

    @property
    def pending(self) -> int:
        return sum(1 for t in self.tags if t)

    def key(self) -> tuple[tuple[str, ...], tuple[bool, ...]]:
        return tuple(str(e) for e in self.seq), tuple(bool(t) for t in self.tags)


def _text(seq: Sequence) -> str:
    return " ".join(str(e) for e in seq)


def _focus(rule: Rule) -> tuple[tuple[Token, ...], tuple[Token, ...]]:
    ante = rule.ante[rule.left_len : len(rule.ante) - rule.right_len]
    post = rule.post[rule.left_len : len(rule.post) - rule.right_len]
    return ante, post


def _is_free_deletion(rule: Rule) -> bool:
    ante, post = _focus(rule)
    return (
        rule.left_len == 0
        and rule.right_len == 0
        and len(ante) > 0
        and all(isinstance(t, EmptyToken) for t in post)
    )


def _post_ast(rule: Rule, system_name: str | None) -> tuple[Token, ...]:
    """What the rule's output looks like, as a pattern (as `backward` builds it)."""
    tokens: list[Token] = []
    for t in rule.post:
        if isinstance(t, EmptyToken):
            continue
        if isinstance(t, BackRefToken):
            tokens.append(_carry_backref_modifier(rule.ante[t.index], t, system_name))
        else:
            tokens.append(t)
    return tuple(tokens)


def _token_variants(tok: Token) -> list[Sound]:
    """The segments a deleted target token may have been."""
    if isinstance(tok, SegmentToken):
        return [tok.sound]
    if isinstance(tok, (ChoiceToken, SetToken)):
        return [c.sound for c in tok.choices if isinstance(c, SegmentToken)]
    return []


_Piece = tuple[tuple["Element", ...], tuple[int, ...], "Restoration | None"]


def _undo_windows(state: _State, rule: Rule, index: int, system_name: str | None) -> list[_State]:
    """Every combination of keeping or undoing each match of the rule's output."""
    post_ast = _post_ast(rule, system_name)
    seq = state.seq
    n = len(post_ast)
    if n == 0:
        return [state]
    pieces: list[list[_Piece]] = []
    idx = 0
    while idx < len(seq):
        window = seq[idx : idx + n]
        if len(window) == n:
            result = match_pattern(window, post_ast, system_name)
            if result.matched:
                tags = state.tags[idx : idx + n]
                options: list[_Piece] = [(tuple(window), tags, None)]
                for translated in _backward_translate(window, rule, result, system_name):
                    restored = tuple(translated)
                    if _text(restored) == _text(window):
                        continue
                    step = Restoration(
                        index, rule.source, "undo", idx, _text(window), _text(restored)
                    )
                    # Undoing uses every element of the window: an insertion waiting
                    # for a licence gets one here. Elements the window grew by were
                    # restored from the rule's own context and need none.
                    options.append((restored, (0,) * len(restored), step))
                pieces.append(options)
                idx += n
                continue
        pieces.append([((seq[idx],), (state.tags[idx],), None)])
        idx += 1

    out: list[_State] = []
    for combo in itertools.product(*pieces):
        new_seq: list[Element] = []
        new_tags: list[int] = []
        steps: list[Restoration] = list(state.steps)
        for elems, tags, undone in combo:
            new_seq.extend(elems)
            new_tags.extend(tags)
            if undone is not None:
                steps.append(undone)
        out.append(_State(tuple(new_seq), tuple(new_tags), tuple(steps)))
    return out


def _licensed_slots(
    seq: tuple[Element, ...],
    insert: tuple[Element, ...],
    earlier: list[tuple[Token, ...]],
    system_name: str | None,
) -> list[int]:
    """Positions where inserting `insert` lets some earlier rule's output match
    a window that contains the inserted material."""
    slots: list[int] = []
    for p in range(1, len(seq)):
        trial = seq[:p] + insert + seq[p:]
        lo, hi = p, p + len(insert)
        found = False
        for pattern in earlier:
            n = len(pattern)
            if n == 0:
                continue
            for start in range(max(0, hi - n), min(lo, len(trial) - n) + 1):
                if match_pattern(trial[start : start + n], pattern, system_name).matched:
                    found = True
                    break
            if found:
                break
        if found:
            slots.append(p)
    return slots


def _insertions(
    state: _State,
    rule: Rule,
    index: int,
    earlier: list[tuple[Token, ...]],
    budget: int,
    next_tag: list[int],
    system_name: str | None,
) -> list[_State]:
    """The state itself, plus every licensed restoration of the deleted target
    (up to `budget` of them)."""
    ante, _ = _focus(rule)
    variants = [tuple(combo) for combo in itertools.product(*(_token_variants(t) for t in ante))]
    out = [state]
    frontier = [state]
    for _ in range(budget):
        grown: list[_State] = []
        for st in frontier:
            for insert in variants:
                for p in _licensed_slots(st.seq, insert, earlier, system_name):
                    next_tag[0] += 1
                    tag = next_tag[0]
                    step = Restoration(index, rule.source, "insert", p, "", _text(insert))
                    grown.append(
                        _State(
                            st.seq[:p] + insert + st.seq[p:],
                            st.tags[:p] + (tag,) * len(insert) + st.tags[p:],
                            (*st.steps, step),
                        )
                    )
        out.extend(grown)
        frontier = grown
    return out


def _well_formed(seq: tuple[Element, ...], daughter: tuple[Element, ...]) -> bool:
    """Boundaries stay where the daughter has them: a word does not grow
    material past its edges (undoing `i > :null: / _ #` at the left edge would
    otherwise restore an *i* before the initial #)."""
    edges = [i for i, e in enumerate(daughter) if isinstance(e, Boundary)]
    found = [i for i, e in enumerate(seq) if isinstance(e, Boundary)]
    if len(found) != len(edges):
        return False
    if edges and edges[0] == 0 and found[0] != 0:
        return False
    return not (edges and edges[-1] == len(daughter) - 1 and found[-1] != len(seq) - 1)


def _verify(
    candidate: _State, rule: Rule, later: tuple[Element, ...], system_name: str | None
) -> bool:
    return _text(forward(candidate.seq, rule, system_name)) == _text(later)


@cache
def _class_members(features: frozenset[str], system_name: str | None) -> tuple[str, ...]:
    from alteruphono.features.ipa import _build_grapheme_table

    sys = get_system(system_name)
    return tuple(
        sorted(g for g, f in _build_grapheme_table().items() if sys.partial_match(features, f))
    )


def _as_abstract_segment(sound: Sound, merkmal_system: str, system_name: str | None) -> object:
    try:
        import merkmal  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - environment without merkmal
        msg = "backward_history reports restored classes as merkmal AbstractSegments"
        raise ImportError(msg) from exc

    usable = []
    for g in _class_members(sound.features, system_name):
        try:
            merkmal.AbstractSegment.from_grapheme(g, system=merkmal_system)
        except (ValueError, NotImplementedError, KeyError, merkmal.NativeError):
            continue
        usable.append(g)
    if not usable:
        return merkmal.AbstractSegment(system=merkmal_system)
    return merkmal.AbstractSegment.covering(usable, system=merkmal_system)


def backward_history(
    daughter: Sequence,
    rules: list[Rule | str],
    *,
    system_name: str | None = None,
    max_candidates: int = 2000,
    max_insertions: int = 2,
    merkmal_system: str = "distinctive",
) -> BackwardResult:
    """Proto-forms that derive `daughter` through `rules`, applied in order.

    Rules are undone from the last to the first. After each, a candidate is kept
    only if the rule applied forward gives back the form it was undone from, so
    every result derives the daughter exactly. At most `max_candidates` states
    are kept per step, preferring fewer pending insertions and fewer steps;
    `truncated` says whether any were dropped. A context-free deletion restores
    at most `max_insertions` segments per step, and only where an earlier rule
    uses them.
    """
    parsed = [parse_rule(r) if isinstance(r, str) else r for r in rules]
    patterns = [_post_ast(r, system_name) for r in parsed]
    states = [_State(tuple(daughter), (0,) * len(daughter))]
    truncated = False
    explored = 0
    next_tag = [0]

    for index in range(len(parsed) - 1, -1, -1):
        rule = parsed[index]
        free = _is_free_deletion(rule)
        new_states: dict[tuple[tuple[str, ...], tuple[bool, ...]], _State] = {}
        for state in states:
            if free:
                expansions = _insertions(
                    state, rule, index, patterns[:index], max_insertions, next_tag, system_name
                )
            else:
                expansions = []
                for undone in _undo_windows(state, rule, index, system_name):
                    expansions.append(undone)
            for cand in expansions:
                explored += 1
                if not _well_formed(cand.seq, tuple(daughter)):
                    continue
                if not _verify(cand, rule, state.seq, system_name):
                    continue
                new_states.setdefault(cand.key(), cand)
        ranked = sorted(new_states.values(), key=lambda s: (s.pending, len(s.steps), s.key()))
        if len(ranked) > max_candidates:
            truncated = True
            ranked = ranked[:max_candidates]
        states = ranked

    finals = []
    seen: set[tuple[str, ...]] = set()
    for state in states:
        if state.pending:
            continue  # an insertion no earlier rule used: no trace, no segment
        key = tuple(str(e) for e in state.seq)
        if key in seen:
            continue
        seen.add(key)
        latents = tuple(
            (i, _as_abstract_segment(e, merkmal_system, system_name))
            for i, e in enumerate(state.seq)
            if isinstance(e, Sound) and e.partial
        )
        finals.append(Reconstruction(state.seq, state.steps, latents))
    finals.sort(key=lambda r: (len(r.steps), str(r)))
    return BackwardResult(tuple(daughter), tuple(finals), truncated, explored)


__all__ = ["BackwardResult", "Reconstruction", "Restoration", "backward_history", "Boundary"]
