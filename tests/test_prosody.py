"""Tests for alteruphono.prosody — syllabification and prosodic structure."""

from alteruphono.features import sound as make_sound
from alteruphono.prosody import ProsodicWord, Syllable, syllabify


class TestSyllable:
    def test_create_empty(self) -> None:
        s = Syllable()
        assert s.sounds == ()
        assert str(s) == ""

    def test_cv(self) -> None:
        p = make_sound("p")
        a = make_sound("a")
        s = Syllable(onset=(p,), nucleus=(a,))
        assert s.sounds == (p, a)
        assert str(s) == "pa"

    def test_cvc(self) -> None:
        p = make_sound("p")
        a = make_sound("a")
        t = make_sound("t")
        s = Syllable(onset=(p,), nucleus=(a,), coda=(t,))
        assert len(s.sounds) == 3


class TestProsodicWord:
    def test_empty(self) -> None:
        pw = ProsodicWord()
        assert len(pw) == 0

    def test_single_syllable(self) -> None:
        p = make_sound("p")
        a = make_sound("a")
        syl = Syllable(onset=(p,), nucleus=(a,))
        pw = ProsodicWord(syllables=[syl])
        assert len(pw) == 1
        assert str(pw) == "pa"


class TestSyllabify:
    def test_simple_cv(self) -> None:
        sounds = (make_sound("p"), make_sound("a"))
        pw = syllabify(sounds)
        assert len(pw) >= 1

    def test_cvcv(self) -> None:
        sounds = (make_sound("p"), make_sound("a"), make_sound("t"), make_sound("a"))
        pw = syllabify(sounds)
        # Should syllabify as pa.ta
        assert len(pw) == 2

    def test_single_vowel(self) -> None:
        sounds = (make_sound("a"),)
        pw = syllabify(sounds)
        assert len(pw) == 1
        assert pw.syllables[0].nucleus == sounds

    def test_consonant_cluster(self) -> None:
        sounds = (
            make_sound("s"),
            make_sound("t"),
            make_sound("a"),
        )
        pw = syllabify(sounds)
        assert len(pw) >= 1
