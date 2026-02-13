"""Tests for alteruphono.engine — sound change engine."""

from alteruphono.engine import (
    CategoricalRule,
    GradientRule,
    RuleSet,
    SoundChangeEngine,
    apply_gradient,
)
from alteruphono.parser import parse_sequence


def _seq_str(seq: tuple[object, ...]) -> str:
    return " ".join(str(e) for e in seq)


class TestCategoricalRule:
    def test_create(self) -> None:
        r = CategoricalRule(source="p > b")
        assert r.source == "p > b"
        assert len(r.rule.ante) > 0
        assert len(r.rule.post) > 0

    def test_with_metadata(self) -> None:
        r = CategoricalRule(source="p > b", name="Lenition")
        assert r.name == "Lenition"


class TestGradientRule:
    def test_create(self) -> None:
        r = GradientRule(source="p > b", strength=0.5)
        assert r.strength == 0.5

    def test_full_strength(self) -> None:
        r = GradientRule(source="p > b", strength=1.0)
        assert r.strength == 1.0


class TestRuleSet:
    def test_empty(self) -> None:
        rs = RuleSet(name="empty")
        assert len(rs) == 0

    def test_add_rules(self) -> None:
        rs = RuleSet(name="test")
        rs.add(CategoricalRule(source="p > b"))
        rs.add(CategoricalRule(source="t > d"))
        assert len(rs) == 2

    def test_iteration(self) -> None:
        rs = RuleSet(name="test")
        rs.add(CategoricalRule(source="p > b"))
        rs.add(CategoricalRule(source="t > d"))
        sources = [r.source for r in rs]
        assert sources == ["p > b", "t > d"]


class TestSoundChangeEngine:
    def test_apply_single_rule(self) -> None:
        engine = SoundChangeEngine()
        seq = parse_sequence("# a p a #")
        rule = CategoricalRule(source="p > b")
        result = engine.apply_rule(seq, rule)
        assert _seq_str(result) == "# a b a #"

    def test_apply_ruleset(self) -> None:
        engine = SoundChangeEngine()
        seq = parse_sequence("# a p a t a #")
        rs = RuleSet(name="voicing")
        rs.add(CategoricalRule(source="p > b"))
        rs.add(CategoricalRule(source="t > d"))
        result = engine.apply_ruleset(seq, rs)
        assert _seq_str(result) == "# a b a d a #"

    def test_trajectory(self) -> None:
        engine = SoundChangeEngine()
        seq = parse_sequence("# a p a t a #")
        rs = RuleSet(name="voicing")
        rs.add(CategoricalRule(source="p > b", name="p-voicing"))
        rs.add(CategoricalRule(source="t > d", name="t-voicing"))
        traj = engine.apply_with_trajectory(seq, rs)
        assert traj.changed is True
        assert len(traj.steps) == 2
        assert traj.steps[0].rule_name == "p-voicing"
        assert traj.steps[0].changed is True
        assert traj.steps[1].rule_name == "t-voicing"
        assert traj.steps[1].changed is True
        assert _seq_str(traj.output_seq) == "# a b a d a #"

    def test_no_change_trajectory(self) -> None:
        engine = SoundChangeEngine()
        seq = parse_sequence("# a b a #")
        rs = RuleSet()
        rs.add(CategoricalRule(source="p > t"))
        traj = engine.apply_with_trajectory(seq, rs)
        assert traj.changed is False

    def test_gradient_rule(self) -> None:
        engine = SoundChangeEngine()
        seq = parse_sequence("# a p a #")
        rule = GradientRule(source="p > b", strength=1.0)
        result = engine.apply_rule(seq, rule)
        assert _seq_str(result) == "# a b a #"

    def test_gradient_zero_strength(self) -> None:
        engine = SoundChangeEngine()
        seq = parse_sequence("# a p a #")
        rule = GradientRule(source="p > b", strength=0.0)
        result = engine.apply_rule(seq, rule)
        assert _seq_str(result) == "# a p a #"


class TestGradientUtilities:
    def test_apply_gradient_full(self) -> None:
        seq = parse_sequence("# a p a #")
        result = apply_gradient(seq, "p > b", strength=1.0)
        assert _seq_str(result) == "# a b a #"

    def test_apply_gradient_zero(self) -> None:
        seq = parse_sequence("# a p a #")
        result = apply_gradient(seq, "p > b", strength=0.0)
        assert _seq_str(result) == "# a p a #"
