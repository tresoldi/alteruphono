"""Tests for alteruphono.forward — forward rule application."""

from alteruphono.forward import forward
from alteruphono.parser import parse_rule, parse_sequence


class TestForwardBasic:
    def test_simple_replacement(self) -> None:
        rule = parse_rule("p > b")
        seq = parse_sequence("# a p a #")
        result = forward(seq, rule)
        result_str = " ".join(str(e) for e in result)
        assert result_str == "# a b a #"

    def test_no_match(self) -> None:
        rule = parse_rule("p > b")
        seq = parse_sequence("# a t a #")
        result = forward(seq, rule)
        result_str = " ".join(str(e) for e in result)
        assert result_str == "# a t a #"

    def test_deletion(self) -> None:
        rule = parse_rule("C > :null: / _ #")
        seq = parse_sequence("# a d j aː d #")
        result = forward(seq, rule)
        result_str = " ".join(str(e) for e in result)
        assert result_str == "# a d j aː #"

    def test_boundary_literal_in_post(self) -> None:
        rule = parse_rule("p > #")
        seq = parse_sequence("# a p a #")
        result = forward(seq, rule)
        result_str = " ".join(str(e) for e in result)
        assert result_str == "# a # a #"


class TestForwardWithContext:
    def test_context_simple(self) -> None:
        rule = parse_rule("L > d / # _")
        seq = parse_sequence("# l a b j o p l ɔ l #")
        result = forward(seq, rule)
        result_str = " ".join(str(e) for e in result)
        assert result_str == "# d a b j o p l ɔ l #"


class TestForwardBackref:
    def test_backref_copy(self) -> None:
        rule = parse_rule("C N > @1 / _ #")
        seq = parse_sequence("# a ɡ r o ɡ ŋ #")
        result = forward(seq, rule)
        result_str = " ".join(str(e) for e in result)
        assert result_str == "# a ɡ r o ɡ #"


class TestForwardComplex:
    def test_vs_rule_0(self) -> None:
        """V s > @1 z @1 / # p|b r _ t|d"""
        rule = parse_rule("V s > @1 z @1 / # p|b r _ t|d")
        seq = parse_sequence("# p r e s t o #")
        result = forward(seq, rule)
        result_str = " ".join(str(e) for e in result)
        assert result_str == "# p r e z e t o #"

    def test_deletion_r_context(self) -> None:
        """C > :null: / r _"""
        rule = parse_rule("C > :null: / r _")
        seq = parse_sequence("# i k ʔ e r j a #")
        result = forward(seq, rule)
        result_str = " ".join(str(e) for e in result)
        assert result_str == "# i k ʔ e r a #"

    def test_s_c_deletion(self) -> None:
        """s C > :null: / _ #"""
        rule = parse_rule("s C > :null: / _ #")
        seq = parse_sequence("# ɡ e ɡ s i s k #")
        result = forward(seq, rule)
        result_str = " ".join(str(e) for e in result)
        assert result_str == "# ɡ e ɡ s i #"

    def test_choice_keep(self) -> None:
        """s|k C > @1 / _ #"""
        rule = parse_rule("s|k C > @1 / _ #")
        seq = parse_sequence("# a k a n k m i k s #")
        result = forward(seq, rule)
        result_str = " ".join(str(e) for e in result)
        assert result_str == "# a k a n k m i k #"
