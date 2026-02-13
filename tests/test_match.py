"""Tests for alteruphono.match — pattern matching."""

from alteruphono.features import sound as make_sound
from alteruphono.match import match_pattern
from alteruphono.types import (
    Boundary,
    BoundaryToken,
    ChoiceToken,
    SegmentToken,
    SetToken,
)


class TestExactMatch:
    def test_single_sound(self) -> None:
        seq = (make_sound("p"),)
        pat = (SegmentToken(sound=make_sound("p")),)
        result = match_pattern(seq, pat)
        assert result.matched is True

    def test_single_sound_mismatch(self) -> None:
        seq = (make_sound("p"),)
        pat = (SegmentToken(sound=make_sound("b")),)
        result = match_pattern(seq, pat)
        assert result.matched is False

    def test_boundary(self) -> None:
        seq = (Boundary(),)
        pat = (BoundaryToken(),)
        result = match_pattern(seq, pat)
        assert result.matched is True

    def test_boundary_vs_sound(self) -> None:
        seq = (make_sound("p"),)
        pat = (BoundaryToken(),)
        result = match_pattern(seq, pat)
        assert result.matched is False

    def test_length_mismatch(self) -> None:
        seq = (make_sound("p"), make_sound("a"))
        pat = (SegmentToken(sound=make_sound("p")),)
        result = match_pattern(seq, pat)
        assert result.matched is False


class TestPartialMatch:
    def test_vowel_class(self) -> None:
        a = make_sound("a")
        v_class = make_sound("V")
        seq = (a,)
        pat = (SegmentToken(sound=v_class),)
        result = match_pattern(seq, pat)
        assert result.matched is True

    def test_consonant_class(self) -> None:
        p = make_sound("p")
        c_class = make_sound("C")
        seq = (p,)
        pat = (SegmentToken(sound=c_class),)
        result = match_pattern(seq, pat)
        assert result.matched is True

    def test_class_mismatch(self) -> None:
        a = make_sound("a")  # vowel
        c_class = make_sound("C")  # consonant class
        seq = (a,)
        pat = (SegmentToken(sound=c_class),)
        result = match_pattern(seq, pat)
        assert result.matched is False


class TestChoiceMatch:
    def test_first_choice(self) -> None:
        p = make_sound("p")
        choice = ChoiceToken(
            choices=(SegmentToken(sound=make_sound("p")), SegmentToken(sound=make_sound("b")))
        )
        result = match_pattern((p,), (choice,))
        assert result.matched is True

    def test_second_choice(self) -> None:
        b = make_sound("b")
        choice = ChoiceToken(
            choices=(SegmentToken(sound=make_sound("p")), SegmentToken(sound=make_sound("b")))
        )
        result = match_pattern((b,), (choice,))
        assert result.matched is True

    def test_no_choice_match(self) -> None:
        t = make_sound("t")
        choice = ChoiceToken(
            choices=(SegmentToken(sound=make_sound("p")), SegmentToken(sound=make_sound("b")))
        )
        result = match_pattern((t,), (choice,))
        assert result.matched is False


class TestSetMatch:
    def test_set_returns_index(self) -> None:
        p = make_sound("p")
        s = SetToken(
            choices=(SegmentToken(sound=make_sound("p")), SegmentToken(sound=make_sound("b")))
        )
        result = match_pattern((p,), (s,))
        assert result.matched is True
        assert result.bindings[0] == 0

    def test_set_second_index(self) -> None:
        b = make_sound("b")
        s = SetToken(
            choices=(SegmentToken(sound=make_sound("p")), SegmentToken(sound=make_sound("b")))
        )
        result = match_pattern((b,), (s,))
        assert result.matched is True
        assert result.bindings[0] == 1


class TestMultiElement:
    def test_boundary_sound_boundary(self) -> None:
        seq = (Boundary(), make_sound("a"), Boundary())
        pat = (BoundaryToken(), SegmentToken(sound=make_sound("V")), BoundaryToken())
        result = match_pattern(seq, pat)
        # V should partial-match 'a' which is a vowel
        assert result.matched is True

    def test_complex_pattern(self) -> None:
        seq = (make_sound("p"), make_sound("a"), make_sound("t"))
        pat = (
            SegmentToken(sound=make_sound("C")),
            SegmentToken(sound=make_sound("V")),
            SegmentToken(sound=make_sound("C")),
        )
        result = match_pattern(seq, pat)
        assert result.matched is True
