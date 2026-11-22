"""Tests for alteruphono.features — feature system registry and implementations."""

import pytest

from alteruphono.features import get_system, list_systems, set_default, sound
from alteruphono.features.ipa import IPAFeatureSystem
from alteruphono.types import Sound


class TestRegistry:
    def test_list_systems(self) -> None:
        systems = list_systems()
        assert systems == ["ipa"]  # 2.0: 1.x's tresoldi and distinctive tables are gone

    def test_get_ipa(self) -> None:
        sys = get_system("ipa")
        assert sys.name == "ipa"

    def test_get_default(self) -> None:
        sys = get_system()
        assert sys.name == "ipa"

    def test_unknown_raises(self) -> None:
        with pytest.raises(KeyError):
            get_system("nonexistent")

    def test_set_default(self) -> None:
        set_default("ipa")
        assert get_system().name == "ipa"

    def test_set_default_unknown(self) -> None:
        with pytest.raises(KeyError):
            set_default("nonexistent")


class TestSoundFactory:
    def test_regular_grapheme(self) -> None:
        s = sound("a")
        assert isinstance(s, Sound)
        assert s.grapheme == "a"
        assert s.partial is False
        assert "vowel" in s.features

    def test_consonant(self) -> None:
        s = sound("p")
        assert s.grapheme == "p"
        assert "consonant" in s.features or len(s.features) > 0

    def test_sound_class_vowel(self) -> None:
        s = sound("V")
        assert s.partial is True
        assert "vowel" in s.features

    def test_sound_class_consonant(self) -> None:
        s = sound("C")
        assert s.partial is True
        assert "consonant" in s.features

    def test_unknown_grapheme(self) -> None:
        s = sound("☺")
        assert s.grapheme == "☺"
        assert s.features == frozenset()


class TestIPAFeatureSystem:
    def setup_method(self) -> None:
        self.sys = IPAFeatureSystem()

    def test_name(self) -> None:
        assert self.sys.name == "ipa"

    def test_grapheme_a(self) -> None:
        feats = self.sys.grapheme_to_features("a")
        assert feats is not None
        assert "vowel" in feats

    def test_grapheme_p(self) -> None:
        feats = self.sys.grapheme_to_features("p")
        assert feats is not None
        assert "consonant" in feats

    def test_unknown_grapheme(self) -> None:
        feats = self.sys.grapheme_to_features("☺")
        assert feats is None

    def test_is_class(self) -> None:
        assert self.sys.is_class("V") is True
        assert self.sys.is_class("C") is True
        assert self.sys.is_class("N") is True
        assert self.sys.is_class("a") is False

    def test_class_features(self) -> None:
        feats = self.sys.class_features("V")
        assert feats is not None
        assert "vowel" in feats

    def test_partial_match(self) -> None:
        vowel_feats = frozenset({"vowel"})
        a_feats = self.sys.grapheme_to_features("a")
        assert a_feats is not None
        assert self.sys.partial_match(vowel_feats, a_feats)

    def test_partial_match_negative(self) -> None:
        consonant_feats = frozenset({"consonant"})
        a_feats = self.sys.grapheme_to_features("a")
        assert a_feats is not None
        assert not self.sys.partial_match(consonant_feats, a_feats)

    def test_add_features(self) -> None:
        base = frozenset({"consonant", "voiceless", "bilabial", "stop"})
        added = frozenset({"voiced"})
        result = self.sys.add_features(base, added)
        assert "voiced" in result
        assert "voiceless" not in result  # Replaced in same category


# TestTresoldiFeatureSystem and TestDistinctiveFeatureSystem tested 1.x's own
# feature tables, removed in 2.0 (docs/v2/DESIGN.md 3.4).


def test_lookup_normalises_alternate_codepoints():
    """IPA g (U+0261) and dark l (U+026B) resolve as g and l + velarized, in grapheme_to_features
    as in sound(); graphemes that resolve as written are unchanged."""
    from alteruphono.features import get_system

    f = get_system()
    assert f.grapheme_to_features("ɡ") == f.grapheme_to_features("g")
    assert f.grapheme_to_features("ɡʱ") == f.grapheme_to_features("gʱ")
    assert f.grapheme_to_features("ɡʲ") == f.grapheme_to_features("gʲ")
    assert f.grapheme_to_features("ɫ") == f.grapheme_to_features("lˠ")
    assert f.grapheme_to_features("g") == frozenset({"velar", "stop", "voiced", "consonant"})
