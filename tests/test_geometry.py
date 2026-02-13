"""Tests for alteruphono.features.geometry — feature geometry tree."""

from alteruphono.features.geometry import GEOMETRY, FeatureNode, GeometryNode


class TestGeometryStructure:
    def test_root_is_geometry_node(self) -> None:
        assert isinstance(GEOMETRY, GeometryNode)
        assert GEOMETRY.name == "Root"

    def test_frozen(self) -> None:
        """Tree nodes are immutable."""
        try:
            GEOMETRY.name = "Modified"  # type: ignore[misc]
            msg = "Should be frozen"
            raise AssertionError(msg)
        except AttributeError:
            pass

    def test_top_level_groups(self) -> None:
        names = [c.name for c in GEOMETRY.children]
        assert "Laryngeal" in names
        assert "Manner" in names
        assert "Place" in names
        assert "Prosodic" in names

    def test_all_features_covers_basics(self) -> None:
        all_feats = GEOMETRY.all_features()
        assert "voiced" in all_feats
        assert "voiceless" in all_feats
        assert "nasal" in all_feats
        assert "lateral" in all_feats
        assert "rounded" in all_feats
        assert "unrounded" in all_feats
        assert "close" in all_feats
        assert "open" in all_feats
        assert "front" in all_feats
        assert "back" in all_feats
        assert "long" in all_feats


class TestFeatureLookup:
    def test_find_feature_voiced(self) -> None:
        node = GEOMETRY.find_feature("voiced")
        assert node is not None
        assert isinstance(node, FeatureNode)
        assert node.name == "voice"
        assert node.positive == "voiced"
        assert node.negative == "voiceless"

    def test_find_feature_unknown(self) -> None:
        assert GEOMETRY.find_feature("xyz_nonexistent") is None

    def test_find_parent_voiced(self) -> None:
        parent = GEOMETRY.find_parent("voiced")
        assert parent is not None
        assert parent.name == "Laryngeal"

    def test_find_parent_rounded(self) -> None:
        parent = GEOMETRY.find_parent("rounded")
        assert parent is not None
        assert parent.name == "Labial"

    def test_find_parent_close(self) -> None:
        parent = GEOMETRY.find_parent("close")
        assert parent is not None
        assert parent.name == "Dorsal"


class TestSiblings:
    def test_siblings_of_voiced(self) -> None:
        sibs = GEOMETRY.siblings_of("voiced")
        assert "voiceless" in sibs

    def test_siblings_of_rounded(self) -> None:
        sibs = GEOMETRY.siblings_of("rounded")
        assert "unrounded" in sibs

    def test_siblings_of_unknown(self) -> None:
        sibs = GEOMETRY.siblings_of("xyz_nonexistent")
        assert sibs == frozenset()


class TestFeatureDistance:
    def test_same_feature(self) -> None:
        assert GEOMETRY.feature_distance("voiced", "voiced") == 0

    def test_voicing_pair(self) -> None:
        # voiced and voiceless share FeatureNode "voice" under Laryngeal
        d = GEOMETRY.feature_distance("voiced", "voiceless")
        assert d == 2  # up to FeatureNode "voice", down to the other pole

    def test_different_subtrees(self) -> None:
        # voiced (Laryngeal) vs rounded (Place > Labial) — cross-subtree
        d = GEOMETRY.feature_distance("voiced", "rounded")
        assert d > 2

    def test_unknown_feature(self) -> None:
        d = GEOMETRY.feature_distance("voiced", "xyz_nonexistent")
        assert d == 999


class TestSoundDistance:
    def test_identical(self) -> None:
        feats = frozenset({"voiced", "nasal"})
        assert GEOMETRY.sound_distance(feats, feats) == 0.0

    def test_voicing_pair_closer_than_vowel(self) -> None:
        """Use realistic feature sets: p and b differ only in voicing,
        while p and a are fundamentally different sounds."""
        from alteruphono.features import get_system

        sys = get_system("ipa")
        p_feats = sys.grapheme_to_features("p")
        b_feats = sys.grapheme_to_features("b")
        a_feats = sys.grapheme_to_features("a")
        assert p_feats is not None
        assert b_feats is not None
        assert a_feats is not None
        d_pb = GEOMETRY.sound_distance(p_feats, b_feats)
        d_pa = GEOMETRY.sound_distance(p_feats, a_feats)
        assert d_pb < d_pa

    def test_empty_features(self) -> None:
        empty: frozenset[str] = frozenset()
        assert GEOMETRY.sound_distance(empty, empty) == 0.0

    def test_symmetry(self) -> None:
        a = frozenset({"voiced", "nasal"})
        b = frozenset({"voiceless", "lateral"})
        assert GEOMETRY.sound_distance(a, b) == GEOMETRY.sound_distance(b, a)
