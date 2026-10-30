"""Tests for alteruphono.history — backward through an ordered history."""

import pytest

from alteruphono.forward import forward
from alteruphono.history import backward_history
from alteruphono.parser import parse_rule, parse_sequence


def _protos(rules: list[str], daughter: str, **kw: object) -> list[str]:
    result = backward_history(parse_sequence(daughter), rules, **kw)
    return [str(c) for c in result.candidates]


def _derives(rules: list[str], proto: str, daughter: str) -> bool:
    seq = parse_sequence(proto)
    for r in rules:
        seq = forward(seq, parse_rule(r))
    return " ".join(str(e) for e in seq) == daughter


class TestVerified:
    @pytest.mark.parametrize(
        ("rules", "daughter"),
        [
            (["k > tʃ / _ i", "i > :null: / _ #"], "# a tʃ #"),
            (["p > b / V _ V", "t > p / V _ V"], "# a p a #"),
            (["e > a / h _", "h > :null:"], "# a k #"),
            (
                ["e > a / h _", "e > o / ʕ _", "V > @1[+long] / _ h|ʕ C", "h|ʕ > :null:"],
                "# aː t o k #",
            ),
        ],
    )
    def test_every_candidate_derives_the_daughter(self, rules: list[str], daughter: str) -> None:
        protos = _protos(rules, daughter)
        assert protos
        assert all(_derives(rules, p, daughter) for p in protos)

    def test_impossible_daughter_has_no_proto(self) -> None:
        # Unconditioned a > e leaves no a behind.
        assert _protos(["a > e"], "# e a #") == []


class TestOpacity:
    def test_counterbleeding_restores_the_lost_trigger(self) -> None:
        # Palatalisation before i, then final i lost: the trigger is gone.
        assert "# a k i #" in _protos(["k > tʃ / _ i", "i > :null: / _ #"], "# a tʃ #")

    def test_counterfeeding_keeps_the_new_stop_voiceless(self) -> None:
        # Voicing, then a new intervocalic p from t: the p was never voiced.
        assert _protos(["p > b / V _ V", "t > p / V _ V"], "# a p a #") == ["# a t a #"]


class TestLicensedInsertion:
    def test_lost_segment_restored_where_an_earlier_rule_needs_it(self) -> None:
        protos = _protos(["e > a / h _", "h > :null:"], "# a k #")
        assert "# h e k #" in protos

    def test_no_trace_no_insertion(self) -> None:
        # Nothing earlier uses h, so its loss restores nothing.
        assert _protos(["h > :null:"], "# a k #") == ["# a k #"]
        # And an h that would not undo the colouring is not invented either.
        protos = _protos(["e > a / h _", "h > :null:"], "# a k #")
        assert "# a h k #" not in protos and "# h a k #" not in protos

    def test_steps_record_provenance(self) -> None:
        result = backward_history(parse_sequence("# a k #"), ["e > a / h _", "h > :null:"])
        (cand,) = [c for c in result.candidates if str(c) == "# h e k #"]
        kinds = [(s.kind, s.rule) for s in cand.steps]
        assert kinds == [("insert", "h > :null:"), ("undo", "e > a / h _")]


class TestAbstractSegments:
    def test_restored_class_is_a_merkmal_bundle(self) -> None:
        merkmal = pytest.importorskip("merkmal")
        result = backward_history(parse_sequence("# a k #"), ["e > a / H _", "H > :null:"])
        (cand,) = [c for c in result.candidates if c.latents]
        position, segment = cand.latents[0]
        assert str(cand.proto[position]) == "H"
        assert isinstance(segment, merkmal.AbstractSegment)
        assert segment.compatible("h") and not segment.compatible("a")


class TestBounds:
    def test_truncation_is_reported(self) -> None:
        rules = ["p > b / V _ V"]
        result = backward_history(parse_sequence("# a b a b a b a #"), rules, max_candidates=2)
        assert result.truncated
        assert len(result.candidates) <= 2

    def test_words_do_not_grow_past_their_edges(self) -> None:
        protos = _protos(["k > tʃ / _ i", "i > :null: / _ #"], "# a tʃ #")
        assert all(p.startswith("# ") and p.endswith(" #") for p in protos)
