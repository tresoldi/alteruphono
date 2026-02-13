"""Tests for alteruphono.resources — TSV data loading."""

from alteruphono import resources


class TestLoadSounds:
    def test_returns_dict(self) -> None:
        sounds = resources.load_sounds()
        assert isinstance(sounds, dict)

    def test_has_common_graphemes(self) -> None:
        sounds = resources.load_sounds()
        assert "a" in sounds
        assert "p" in sounds
        assert "i" in sounds

    def test_names_are_strings(self) -> None:
        sounds = resources.load_sounds()
        for g, name in list(sounds.items())[:10]:
            assert isinstance(g, str)
            assert isinstance(name, str)
            assert len(name) > 0

    def test_large_inventory(self) -> None:
        sounds = resources.load_sounds()
        # Should have thousands of sounds
        assert len(sounds) > 5000


class TestLoadFeatures:
    def test_returns_list(self) -> None:
        features = resources.load_features()
        assert isinstance(features, list)

    def test_has_entries(self) -> None:
        features = resources.load_features()
        assert len(features) > 100

    def test_tuple_structure(self) -> None:
        features = resources.load_features()
        for value, feature in features[:10]:
            assert isinstance(value, str)
            assert isinstance(feature, str)


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
