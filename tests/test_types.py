"""Tests for alteruphono.types — frozen dataclasses."""

import pytest

from alteruphono.types import (
    BackRefToken,
    Boundary,
    BoundaryToken,
    ChoiceToken,
    EmptyToken,
    FocusToken,
    MatchResult,
    Rule,
    SegmentToken,
    SetToken,
    Sound,
)


class TestSound:
    def test_create_basic(self) -> None:
        s = Sound(grapheme="p")
        assert s.grapheme == "p"
        assert s.features == frozenset()
        assert s.partial is False

    def test_create_with_features(self) -> None:
        s = Sound("p", frozenset({"consonant", "voiceless"}))
        assert s.features == frozenset({"consonant", "voiceless"})

    def test_create_partial(self) -> None:
        s = Sound("V", frozenset({"vowel"}), partial=True)
        assert s.partial is True

    def test_frozen(self) -> None:
        s = Sound("p")
        with pytest.raises(AttributeError):
            s.grapheme = "b"  # type: ignore[misc]

    def test_hashable(self) -> None:
        s1 = Sound("p", frozenset({"consonant"}))
        s2 = Sound("p", frozenset({"consonant"}))
        assert hash(s1) == hash(s2)
        assert s1 == s2
        assert {s1, s2} == {s1}

    def test_str(self) -> None:
        assert str(Sound("p")) == "p"
        assert str(Sound("aː")) == "aː"

    def test_inequality(self) -> None:
        assert Sound("p") != Sound("b")
        assert Sound("p", frozenset({"x"})) != Sound("p", frozenset({"y"}))


class TestBoundary:
    def test_default(self) -> None:
        b = Boundary()
        assert b.marker == "#"
        assert str(b) == "#"

    def test_custom(self) -> None:
        b = Boundary(marker="##")
        assert b.marker == "##"

    def test_hashable(self) -> None:
        assert hash(Boundary()) == hash(Boundary())


class TestTokens:
    def test_segment_token(self) -> None:
        s = Sound("p")
        t = SegmentToken(sound=s)
        assert str(t) == "p"
        assert t.sound == s

    def test_boundary_token(self) -> None:
        t = BoundaryToken()
        assert str(t) == "#"
        assert t.marker == "#"

    def test_backref_token(self) -> None:
        t = BackRefToken(index=0)
        assert str(t) == "@1"
        t2 = BackRefToken(index=2, modifier="+voiced")
        assert str(t2) == "@3[+voiced]"

    def test_empty_token(self) -> None:
        t = EmptyToken()
        assert str(t) == ":null:"

    def test_focus_token(self) -> None:
        t = FocusToken()
        assert str(t) == "_"

    def test_choice_token(self) -> None:
        c = ChoiceToken(
            choices=(SegmentToken(Sound("p")), SegmentToken(Sound("b")))
        )
        assert str(c) == "p|b"

    def test_set_token(self) -> None:
        s = SetToken(
            choices=(SegmentToken(Sound("p")), SegmentToken(Sound("b")))
        )
        assert str(s) == "{p|b}"


class TestRule:
    def test_create(self) -> None:
        r = Rule(
            source="p > b",
            ante=(SegmentToken(Sound("p")),),
            post=(SegmentToken(Sound("b")),),
        )
        assert str(r) == "p > b"
        assert len(r.ante) == 1
        assert len(r.post) == 1

    def test_frozen(self) -> None:
        r = Rule(source="p > b", ante=(), post=())
        with pytest.raises(AttributeError):
            r.source = "x"  # type: ignore[misc]


class TestMatchResult:
    def test_create(self) -> None:
        mr = MatchResult(matched=True, bindings=(Sound("p"), None))
        assert mr.matched is True
        assert len(mr.bindings) == 2
