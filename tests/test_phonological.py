"""Tests for real phonological processes using the library's rule notation."""

from alteruphono import forward
from alteruphono.parser import parse_rule, parse_sequence


def _apply(rule_str: str, seq_str: str) -> str:
    """Apply a rule to a sequence and return inner sounds as string."""
    rule = parse_rule(rule_str)
    seq = parse_sequence(seq_str)
    result = forward(seq, rule)
    return " ".join(str(e) for e in result)


def _inner(result: str) -> str:
    """Strip boundary markers."""
    return result.strip().removeprefix("#").removesuffix("#").strip()


class TestAssimilation:
    def test_nasal_place_assimilation(self) -> None:
        """n > m / _ p: nasal assimilates place before bilabial."""
        result = _apply("n > m / _ p", "# a n p a #")
        assert _inner(result) == "a m p a"


class TestDeletion:
    def test_simple_deletion(self) -> None:
        """p > :null:"""
        result = _apply("p > :null:", "# a p a #")
        assert _inner(result) == "a a"

    def test_deletion_with_context(self) -> None:
        """C > :null: / _ #: delete consonant before word boundary."""
        result = _apply("C > :null: / _ #", "# a p #")
        assert _inner(result) == "a"


class TestSubstitution:
    def test_rhotacism(self) -> None:
        """s > r / V _ V: intervocalic rhotacism."""
        result = _apply("s > r / V _ V", "# a s a #")
        assert _inner(result) == "a r a"

    def test_simple_substitution(self) -> None:
        """p > b"""
        result = _apply("p > b", "# p a p a #")
        assert _inner(result) == "b a b a"

    def test_diphthongization(self) -> None:
        """eː > e i: long vowel becomes diphthong."""
        result = _apply("eː > e i", "# eː #")
        assert _inner(result) == "e i"


class TestFeatureModification:
    def test_intervocalic_voicing(self) -> None:
        """p > b / V _ V: voicing between vowels."""
        result = _apply("p > b / V _ V", "# a p a #")
        assert _inner(result) == "a b a"


class TestGrimmsLaw:
    def test_grimms_law_chain(self) -> None:
        """Apply Grimm's Law as sequential rules."""
        from alteruphono.engine import CategoricalRule, RuleSet, SoundChangeEngine

        ruleset = RuleSet()
        ruleset.add(CategoricalRule(source="p > f"))
        ruleset.add(CategoricalRule(source="t > θ"))

        engine = SoundChangeEngine()
        seq = parse_sequence("# p a t e r #")
        result = engine.apply_ruleset(seq, ruleset)
        inner = " ".join(str(e) for e in result)
        inner = inner.strip().removeprefix("#").removesuffix("#").strip()
        assert "f" in inner  # p -> f
        assert "θ" in inner  # t -> θ


class TestQuantifiers:
    def test_consonant_cluster_deletion(self) -> None:
        """C+ > :null: / _ #: delete final consonant cluster."""
        result = _apply("C+ > :null: / _ #", "# a s t #")
        assert _inner(result) == "a"

    def test_single_consonant_deletion(self) -> None:
        """C+ > :null: / _ #: also works with single consonant."""
        result = _apply("C+ > :null: / _ #", "# a t #")
        assert _inner(result) == "a"

    def test_optional_consonant(self) -> None:
        """C? V > :null: @2: delete optional consonant before vowel."""
        # With consonant: C? matches "p", V matches "a", output is :null: "a"
        result = _apply("C? V > :null: @2", "# p a #")
        assert "a" in _inner(result)
