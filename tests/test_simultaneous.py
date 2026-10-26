"""Contexts are matched against the input and never consumed (SPE-style)."""
import pytest

import alteruphono as a


def _f(seq, rule):
    return " ".join(str(x) for x in a.forward(a.parse_sequence(seq), a.parse_rule(rule)))


@pytest.mark.parametrize("seq,rule,expected", [
    ("# a p a p a #", "p > b / V _ V", "# a b a b a #"),
    ("# k i t a p e k #", "S > @1[+voiced] / V _ V", "# k i d a b e k #"),
    ("# a p a t a #", "{p|t} > {b|d} / V _ V", "# a b a d a #"),
    ("# a t t t a #", "t > :null: / t _", "# a t a #"),
    ("# p r e s t o #", "V s > @1 z @1 / # p|b r _ t|d", "# p r e z e t o #"),
])
def test_contexts_not_consumed(seq, rule, expected):
    assert _f(seq, rule) == expected


def test_probabilistic_contexts_not_consumed():
    from alteruphono.engine.gradient import _forward_probabilistic
    seq = a.parse_sequence("# a p a p a #")
    rule = a.parse_rule("p > b / V _ V")
    out = " ".join(str(x) for x in _forward_probabilistic(seq, rule, 0.999999, None, 0))
    assert out == "# a b a b a #"
    out = " ".join(str(x) for x in _forward_probabilistic(seq, rule, 1e-9, None, 0))
    assert out == "# a p a p a #"
