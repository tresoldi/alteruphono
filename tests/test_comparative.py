"""Tests for alteruphono.comparative — analysis and reconstruction."""

from alteruphono.comparative import (
    ComparativeAnalysis,
    CorrespondenceSet,
    reconstruct_proto,
)


class TestCorrespondenceSet:
    def test_create(self) -> None:
        cs = CorrespondenceSet(position=0, sounds={"latin": "p", "greek": "p"})
        assert cs.position == 0
        assert cs.languages == ["greek", "latin"]


class TestComparativeAnalysis:
    def test_empty(self) -> None:
        ca = ComparativeAnalysis()
        assert ca.find_correspondences() == []

    def test_add_cognate_set(self) -> None:
        ca = ComparativeAnalysis()
        ca.add_cognate_set({"latin": ["p", "a"], "greek": ["p", "a"]})
        assert len(ca.cognates) == 1

    def test_find_correspondences(self) -> None:
        ca = ComparativeAnalysis()
        ca.add_cognate_set({"latin": ["p", "a"], "greek": ["p", "a"]})
        corr = ca.find_correspondences()
        assert len(corr) == 2
        assert corr[0].sounds["latin"] == "p"

    def test_distance_matrix(self) -> None:
        ca = ComparativeAnalysis()
        ca.add_cognate_set({"A": ["p", "a"], "B": ["b", "a"], "C": ["p", "o"]})
        langs, matrix = ca.calculate_distance_matrix()
        assert len(langs) == 3
        assert len(matrix) == 3
        # Distance from A to itself should be 0
        idx_a = langs.index("A")
        assert matrix[idx_a][idx_a] == 0.0

    def test_phylogeny(self) -> None:
        ca = ComparativeAnalysis()
        ca.add_cognate_set({"A": ["p", "a"], "B": ["p", "a"], "C": ["b", "o"]})
        edges = ca.build_phylogeny()
        assert len(edges) >= 1
        # A and B should be closest (identical forms)
        first_edge = edges[0]
        assert {"A", "B"} == {first_edge[0], first_edge[1]}


class TestReconstruction:
    def test_majority(self) -> None:
        forms = {
            "A": ["p", "a"],
            "B": ["p", "a"],
            "C": ["b", "a"],
        }
        proto = reconstruct_proto(forms, method="majority")
        assert proto == ["p", "a"]

    def test_majority_tie(self) -> None:
        forms = {
            "A": ["p", "a"],
            "B": ["b", "a"],
        }
        proto = reconstruct_proto(forms, method="majority")
        assert len(proto) == 2
        assert proto[0] in ("p", "b")
        assert proto[1] == "a"

    def test_empty(self) -> None:
        assert reconstruct_proto({}) == []

    def test_conservative(self) -> None:
        forms = {"A": ["p"], "B": ["p"], "C": ["b"]}
        proto = reconstruct_proto(forms, method="conservative")
        assert proto == ["p"]

    def test_parsimony(self) -> None:
        forms = {"A": ["p"], "B": ["p"], "C": ["b"]}
        proto = reconstruct_proto(forms, method="parsimony")
        assert proto == ["p"]
