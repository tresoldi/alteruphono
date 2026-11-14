"""Tests for alteruphono.resources — TSV data loading."""

from alteruphono import resources


class TestLoadGraphemes:
    """2.0: 1.x's sounds.tsv and features.tsv (its feature tables) are gone;
    the grapheme universe remains (docs/v2/DESIGN.md 4.3)."""

    def test_large_inventory(self) -> None:
        graphemes = resources.load_graphemes()
        assert isinstance(graphemes, tuple)
        assert len(graphemes) > 5000

    def test_has_common_graphemes(self) -> None:
        graphemes = set(resources.load_graphemes())
        assert {"a", "p", "i"} <= graphemes

    def test_no_feature_tables(self) -> None:
        assert not hasattr(resources, "load_sounds")
        assert not hasattr(resources, "load_features")


class TestLoadClasses:
    def test_returns_dict(self) -> None:
        classes = resources.load_classes()
        assert isinstance(classes, dict)

    def test_has_common_classes(self) -> None:
        classes = resources.load_classes()
        # Sound classes from TSV
        assert "A" in classes  # affricate
        assert "B" in classes  # back vowel

    def test_structure(self) -> None:
        classes = resources.load_classes()
        for _cls, (desc, feats, graphemes) in list(classes.items())[:5]:
            assert isinstance(desc, str)
            assert isinstance(feats, str)
            assert isinstance(graphemes, list)


class TestLoadSoundChanges:
    def test_loads_rules(self) -> None:
        changes = resources.load_sound_changes()
        assert isinstance(changes, list)
        assert len(changes) > 0
        assert "RULE" in changes[0]

    def test_has_test_data(self) -> None:
        changes = resources.load_sound_changes()
        for row in changes[:5]:
            assert "TEST_ANTE" in row
            assert "TEST_POST" in row


class TestDerivedFunctions:
    def test_feature_values(self) -> None:
        fv = resources.feature_values()
        assert "manner" in fv
        assert "stop" in fv["manner"]

    def test_sound_class_graphemes(self) -> None:
        scg = resources.sound_class_graphemes()
        assert isinstance(scg, dict)
        for _cls, graphemes in scg.items():
            assert isinstance(graphemes, frozenset)

    def test_sound_class_features(self) -> None:
        scf = resources.sound_class_features()
        assert isinstance(scf, dict)
