"""Regression tests — pin specific bug-fix behaviors."""

from alteruphono.features import get_system, sound
from alteruphono.features.ipa import IPAFeatureSystem


class TestToneParsing:
    """Phase 1a: Toned sounds must have tone features."""

    def test_falling_tone_vowel(self) -> None:
        s = sound("â")
        assert "with_falling_tone" in s.features

    def test_high_tone_vowel(self) -> None:
        s = sound("é")
        assert "with_high_tone" in s.features

    def test_mid_tone_vowel(self) -> None:
        s = sound("ā")
        assert "with_mid_tone" in s.features

    def test_toned_sounds_have_tone_features(self) -> None:
        """Check a sample of toned sounds from sounds.tsv."""
        from alteruphono.resources import load_sounds

        sounds = load_sounds()
        toned = {g: n for g, n in sounds.items() if "with_" in n}
        assert len(toned) > 50, "Expected many toned sounds in inventory"

        sys = get_system("ipa")
        missing_tone = 0
        for grapheme in list(toned)[:50]:
            feats = sys.grapheme_to_features(grapheme)
            if feats is not None:
                has_tone = any(f.startswith("with_") for f in feats)
                if not has_tone:
                    missing_tone += 1
        assert missing_tone == 0, f"{missing_tone} toned sounds missing tone features"


class TestSoundClassS:
    """Phase 1b: S class = stop (not fricative)."""

    def test_class_s_is_stop(self) -> None:
        sys = IPAFeatureSystem()
        feats = sys.class_features("S")
        assert feats is not None
        assert "stop" in feats
        assert "fricative" not in feats

    def test_class_s_matches_stop(self) -> None:
        sys = IPAFeatureSystem()
        s_feats = sys.class_features("S")
        p_feats = sys.grapheme_to_features("p")
        assert s_feats is not None
        assert p_feats is not None
        assert sys.partial_match(s_feats, p_feats)

    def test_class_s_no_fricative(self) -> None:
        sys = IPAFeatureSystem()
        s_feats = sys.class_features("S")
        s_sound_feats = sys.grapheme_to_features("s")
        assert s_feats is not None
        assert s_sound_feats is not None
        assert not sys.partial_match(s_feats, s_sound_feats)


class TestClassR:
    """Phase 1b: R class with negative features."""

    def test_class_r_matches_nasal(self) -> None:
        sys = IPAFeatureSystem()
        r_feats = sys.class_features("R")
        n_feats = sys.grapheme_to_features("n")
        assert r_feats is not None
        assert n_feats is not None
        assert sys.partial_match(r_feats, n_feats)

    def test_class_r_no_stop(self) -> None:
        sys = IPAFeatureSystem()
        r_feats = sys.class_features("R")
        p_feats = sys.grapheme_to_features("p")
        assert r_feats is not None
        assert p_feats is not None
        assert not sys.partial_match(r_feats, p_feats)


class TestLateral:
    """Phase 1d: Lateral is in manner category."""

    def test_lateral_replaces_manner(self) -> None:
        sys = IPAFeatureSystem()
        base = frozenset({"consonant", "stop", "alveolar"})
        result = sys.add_features(base, frozenset({"lateral"}))
        assert "lateral" in result
        assert "stop" not in result
        assert "consonant" in result
        assert "alveolar" in result


class TestBetaEquivalence:
    """Phase 1e: No-op beta mapping removed."""

    def test_no_noop_equivalence(self) -> None:
        from alteruphono.features import _IPA_EQUIVALENCES

        for k, v in _IPA_EQUIVALENCES.items():
            assert k != v, f"No-op equivalence: {k!r} -> {v!r}"


class TestAllTSVClasses:
    """Phase 1b: All TSV classes recognized."""

    def test_all_classes_loaded(self) -> None:
        from alteruphono.resources import sound_class_features

        classes = sound_class_features()
        sys = IPAFeatureSystem()
        for cls_name in classes:
            assert sys.is_class(cls_name), f"Class {cls_name} not recognized"
