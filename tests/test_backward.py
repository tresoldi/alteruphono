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


class TestBackwardAlternatives:
    def test_deleted_choice_restores_every_alternative(self) -> None:
        # Restoring only the first alternative silently dropped h.
        results = _seq_strs(
            backward(parse_sequence("# a k a #"), parse_rule("x|h > :null: / a _ k"))
        )
        assert "# a x k a #" in results
        assert "# a h k a #" in results
        assert "# a k a #" in results


class TestChoiceOutputRejected:
    def test_choice_in_output_is_an_error(self) -> None:
        # It used to parse and then delete every match in forward.
        import pytest

        with pytest.raises(ValueError, match="use sets"):
            parse_rule("p|t|k > b|d|g / V _ V")

    def test_set_correspondence_still_works(self) -> None:
        rule = parse_rule("{p|t|k} > {b|d|g} / V _ V")
        results = _seq_strs(backward(parse_sequence("# a d a #"), rule))
        assert "# a t a #" in results
