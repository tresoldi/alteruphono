"""Property-based tests using hypothesis."""

import hypothesis.strategies as st
from hypothesis import given, settings

from alteruphono.comparative.analysis import needleman_wunsch
from alteruphono.features import get_system
from alteruphono.features.geometry import GEOMETRY


class TestDistanceProperties:
    def test_triangle_inequality_basic(self) -> None:
        """Feature distance satisfies triangle inequality for known features."""
        sys = get_system("ipa")
        sounds = ["p", "b", "t", "d", "k", "m", "n", "s", "a", "i", "u"]
        for a in sounds:
            for b in sounds:
                for c in sounds:
                    fa = sys.grapheme_to_features(a)
                    fb = sys.grapheme_to_features(b)
                    fc = sys.grapheme_to_features(c)
                    if fa and fb and fc:
                        d_ab = sys.sound_distance(fa, fb)
                        d_bc = sys.sound_distance(fb, fc)
                        d_ac = sys.sound_distance(fa, fc)
                        assert d_ac <= d_ab + d_bc + 1e-9, (
                            f"Triangle inequality violated: "
                            f"d({a},{c})={d_ac} > d({a},{b})={d_ab} + d({b},{c})={d_bc}"
                        )

    def test_distance_symmetry(self) -> None:
        """d(a,b) == d(b,a) for all sound pairs."""
        sys = get_system("ipa")
        sounds = ["p", "b", "t", "d", "k", "m", "n", "s", "a", "i", "u"]
        for a in sounds:
            for b in sounds:
                fa = sys.grapheme_to_features(a)
                fb = sys.grapheme_to_features(b)
                if fa and fb:
                    d_ab = sys.sound_distance(fa, fb)
                    d_ba = sys.sound_distance(fb, fa)
                    assert abs(d_ab - d_ba) < 1e-9, (
                        f"Asymmetry: d({a},{b})={d_ab} != "
                        f"d({b},{a})={d_ba}"
                    )


class TestNWAlignmentProperties:
    def test_identical_sequences(self) -> None:
        """Alignment of identical sequences -> exact match."""
        seq = ["p", "a", "t", "e", "r"]
        a, b, _ = needleman_wunsch(seq, seq)
        assert a == b

    def test_equal_length_output(self) -> None:
        """NW alignment always produces equal-length outputs."""
        pairs = [
            (["p", "a"], ["b", "a"]),
            (["p", "a", "t"], ["b", "a"]),
            (["a"], ["a", "b", "c"]),
        ]
        for seq_a, seq_b in pairs:
            a_aligned, b_aligned, _ = needleman_wunsch(seq_a, seq_b)
            assert len(a_aligned) == len(b_aligned), (
                f"Unequal lengths: {len(a_aligned)} vs {len(b_aligned)} "
                f"for {seq_a} vs {seq_b}"
            )

    @given(
        a=st.lists(
            st.sampled_from(["p", "b", "t", "d", "k", "a", "i", "u"]),
            min_size=1,
            max_size=8,
        ),
        b=st.lists(
            st.sampled_from(["p", "b", "t", "d", "k", "a", "i", "u"]),
            min_size=1,
            max_size=8,
        ),
    )
    @settings(max_examples=50)
    def test_nw_output_length(self, a: list[str], b: list[str]) -> None:
        """NW alignment output lengths always match."""
        a_aligned, b_aligned, _ = needleman_wunsch(a, b)
        assert len(a_aligned) == len(b_aligned)


class TestScalarRoundtrip:
    def test_roundtrip_preserves_key_dimensions(self) -> None:
        """Scalar round-trip preserves the key features for basic sounds."""
        from alteruphono.features.distinctive import DistinctiveFeatureSystem

        sys = DistinctiveFeatureSystem()
        for grapheme in ["p", "b", "t", "d", "s", "a", "i", "u"]:
            scalars = sys.grapheme_to_scalars(grapheme)
            assert scalars is not None, f"No scalars for {grapheme}"
            back = sys.scalars_to_features(scalars)
            assert len(back) > 0, f"Empty roundtrip for {grapheme}"


_GEO_FEATURES = [
    "voiced", "voiceless", "nasal", "lateral", "rounded",
    "unrounded", "close", "open", "front", "back",
]


class TestGeometryProperties:
    @given(
        a=st.sampled_from(_GEO_FEATURES),
        b=st.sampled_from(_GEO_FEATURES),
    )
    @settings(max_examples=50)
    def test_feature_distance_non_negative(self, a: str, b: str) -> None:
        """Feature distance is always >= 0."""
        d = GEOMETRY.feature_distance(a, b)
        assert d >= 0

    @given(
        a=st.sampled_from(_GEO_FEATURES),
        b=st.sampled_from(_GEO_FEATURES),
    )
    @settings(max_examples=50)
    def test_feature_distance_symmetric(self, a: str, b: str) -> None:
        """Feature distance is symmetric."""
        assert GEOMETRY.feature_distance(a, b) == GEOMETRY.feature_distance(b, a)
