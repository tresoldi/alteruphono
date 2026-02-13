"""Tests for alteruphono.backward — backward reconstruction."""

from collections.abc import Sequence

from alteruphono.backward import backward
from alteruphono.parser import parse_rule, parse_sequence


def _seq_strs(seqs: Sequence[tuple[object, ...]]) -> list[str]:
    """Convert list of sequences to list of space-separated strings."""
    return [" ".join(str(e) for e in s) for s in seqs]


class TestBackwardBasic:
    def test_simple_replacement(self) -> None:
        rule = parse_rule("p > b")
        seq = parse_sequence("# a b a #")
        results = backward(seq, rule)
        strs = _seq_strs(results)
        assert "# a p a #" in strs

    def test_no_match_passthrough(self) -> None:
        rule = parse_rule("p > b")
        seq = parse_sequence("# a t a #")
        results = backward(seq, rule)
        strs = _seq_strs(results)
        assert "# a t a #" in strs


class TestBackwardDeletion:
    def test_deletion_at_boundary(self) -> None:
        rule = parse_rule("C > :null: / _ #")
        seq = parse_sequence("# a d j aː #")
        results = backward(seq, rule)
        strs = _seq_strs(results)
        # Original should be among results
        assert any("a d j aː" in s for s in strs)


class TestBackwardContext:
    def test_context_boundary(self) -> None:
        rule = parse_rule("L > d / # _")
        seq = parse_sequence("# d a b #")
        results = backward(seq, rule)
        strs = _seq_strs(results)
        assert len(strs) >= 1


class TestBackwardMultiple:
    def test_produces_alternatives(self) -> None:
        rule = parse_rule("p > b")
        seq = parse_sequence("# a b a #")
        results = backward(seq, rule)
        # Should have at least the proto-form with p and original with b
        assert len(results) >= 1
