"""Tests for alteruphono.parser — rule and sequence parsing."""

import pytest

from alteruphono.parser import parse_rule, parse_sequence
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


class TestParseRuleSimple:
    def test_simple_replacement(self) -> None:
        rule = parse_rule("p > b")
        assert len(rule.ante) == 1
        assert len(rule.post) == 1
        assert isinstance(rule.ante[0], SegmentToken)
        assert isinstance(rule.post[0], SegmentToken)
        assert rule.ante[0].sound.grapheme == "p"
        assert rule.post[0].sound.grapheme == "b"

    def test_arrow_alias(self) -> None:
        rule = parse_rule("p → b")
        assert isinstance(rule.ante[0], SegmentToken)
        assert rule.ante[0].sound.grapheme == "p"

    def test_dash_arrow(self) -> None:
        rule = parse_rule("p -> b")
        assert rule.ante[0].sound.grapheme == "p"  # type: ignore[union-attr]
        assert rule.post[0].sound.grapheme == "b"  # type: ignore[union-attr]

    def test_deletion(self) -> None:
        rule = parse_rule("C > :null:")
        assert isinstance(rule.post[0], EmptyToken)

    def test_backref(self) -> None:
        rule = parse_rule("C N > @1")
        assert isinstance(rule.post[0], BackRefToken)
        assert rule.post[0].index == 0

    def test_choice_in_ante(self) -> None:
        rule = parse_rule("p|b > f")
        assert isinstance(rule.ante[0], ChoiceToken)
        assert len(rule.ante[0].choices) == 2

    def test_set(self) -> None:
        rule = parse_rule("{p|b} > {f|v}")
        assert isinstance(rule.ante[0], SetToken)
        assert isinstance(rule.post[0], SetToken)


class TestParseRuleContext:
    def test_context_basic(self) -> None:
        rule = parse_rule("p > b / V _ V")
        # After merging context: ante = V p V, post = @1 b @3
        assert len(rule.ante) == 3
        assert len(rule.post) == 3

    def test_context_boundary(self) -> None:
        rule = parse_rule("C > :null: / _ #")
        # ante = C #, post = :null: @2
        assert len(rule.ante) == 2
        assert isinstance(rule.ante[1], BoundaryToken)

    def test_context_boundary_left(self) -> None:
        rule = parse_rule("L > d / # _")
        # ante = # L, post = @1 d
        assert len(rule.ante) == 2
        assert isinstance(rule.ante[0], BoundaryToken)

    def test_context_choice(self) -> None:
        rule = parse_rule("V s > @1 z @1 / # p|b r _ t|d")
        # Context left: # p|b r, context right: t|d
        # ante should be: # p|b r V s t|d (6 elements)
        assert len(rule.ante) == 6

    def test_missing_focus_raises(self) -> None:
        with pytest.raises(ValueError, match="focus"):
            parse_rule("p > b / V V")

    def test_multiple_focus_raises(self) -> None:
        with pytest.raises(ValueError, match="exactly one focus"):
            parse_rule("p > b / _ V _")


class TestParseRuleBadInput:
    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_rule("")

    def test_no_arrow_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_rule("p b")

    def test_backref_with_modifier(self) -> None:
        rule = parse_rule("C > @1[+voiced]")
        assert isinstance(rule.post[0], BackRefToken)
        assert rule.post[0].modifier == "+voiced"

    def test_set_arity_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="Set correspondence mismatch"):
            parse_rule("{p|b} > {f|v} {f|v}")


class TestParseSequence:
    def test_basic(self) -> None:
        seq = parse_sequence("# a p a #")
        assert len(seq) == 5
        assert isinstance(seq[0], Boundary)
        assert isinstance(seq[1], Sound)
        assert seq[1].grapheme == "a"
        assert isinstance(seq[4], Boundary)

    def test_no_boundaries(self) -> None:
        seq = parse_sequence("a p a")
        assert len(seq) == 3
        assert all(isinstance(e, Sound) for e in seq)

    def test_unicode(self) -> None:
        seq = parse_sequence("# ɡ e ɡ #")
        assert seq[1].grapheme == "ɡ"

    def test_long_sequence(self) -> None:
        seq = parse_sequence("# p r e s t o #")
        assert len(seq) == 8
