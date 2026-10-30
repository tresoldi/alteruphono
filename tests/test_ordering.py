"""Tests for rule ordering analysis."""

from alteruphono.engine.ordering import (
    Interaction,
    analyze_interactions,
    recommend_ordering,
)


class TestInteractionDetection:
    def test_feeding(self) -> None:
        """p > b feeds 'b > :null: / V _ V' (voicing creates env for deletion)."""
        results = analyze_interactions(
            ["p > b", "b > :null: / V _ V"],
            test_sequences=["# a p a #"],
        )
        assert len(results) == 1
        assert results[0].interaction == Interaction.FEEDING

    def test_bleeding(self) -> None:
        """Deletion bleeds voicing: 'p > :null: / V _ V' bleeds 'p > b / V _ V'."""
        results = analyze_interactions(
            ["p > :null: / V _ V", "p > b / V _ V"],
            test_sequences=["# a p a #"],
        )
        assert len(results) == 1
        assert results[0].interaction == Interaction.BLEEDING

    def test_independent(self) -> None:
        """Rules affecting different sounds are independent."""
        results = analyze_interactions(
            ["p > b", "s > z"],
            test_sequences=["# a p a s a #"],
        )
        assert len(results) == 1
        assert results[0].interaction == Interaction.INDEPENDENT

    def test_example_fields(self) -> None:
        """RuleInteraction should have example input/output."""
        results = analyze_interactions(
            ["p > b", "b > m / _ n"],
            test_sequences=["# p n a #"],
        )
        assert len(results) == 1
        assert results[0].example_input
        assert results[0].ab_output
        assert results[0].ba_output


class TestRecommendations:
    def test_feeding_recommendation(self) -> None:
        results = analyze_interactions(
            ["p > b", "b > :null: / V _ V"],
            test_sequences=["# a p a #"],
        )
        recs = recommend_ordering(results)
        assert any("FEEDING" in r for r in recs)

    def test_independent_no_recommendation(self) -> None:
        results = analyze_interactions(
            ["p > b", "s > z"],
            test_sequences=["# a p a s a #"],
        )
        recs = recommend_ordering(results)
        # Independent rules produce no ordering recommendations
        assert not any("FEEDING" in r or "BLEEDING" in r for r in recs)

    def test_suggested_order(self) -> None:
        """Should suggest topological order for feeding chains."""
        results = analyze_interactions(
            ["p > b", "b > :null: / V _ V"],
            test_sequences=["# a p a #"],
        )
        recs = recommend_ordering(results)
        assert any("Suggested order" in r for r in recs)


class TestRivalOrders:
    def _scores(self, a: str, b: str, pairs: list[tuple[str, str]]) -> dict[str, object]:
        from alteruphono.engine.ordering import rival_orders

        return {r.rival: r for r in rival_orders(a, b, pairs)}

    def test_counterbleeding_beats_reverse_but_ties_simultaneous(self) -> None:
        pairs = [("# a k i #", "# a tʃ #"), ("# k i t a #", "# tʃ i t a #")]
        s = self._scores("k > tʃ / _ i", "i > :null: / _ #", pairs)
        assert s["a_then_b"].derived == 2
        assert s["b_then_a"].derived == 1
        # An opaque order is often indistinguishable from simultaneous application.
        assert s["simultaneous"].derived == 2

    def test_fused_and_analogy_are_reported_not_hidden(self) -> None:
        s = self._scores("p > b / V _ V", "t > p / V _ V", [("# a t a #", "# a p a #")])
        assert s["fused"].derived == s["a_then_b"].derived
        assert "cannot separate" in s["fused"].note
        assert "paradigm" in s["analogy"].note

    def test_conflicting_simultaneous_rewrite_is_undefined(self) -> None:
        s = self._scores("a > e", "a > o", [("# a #", "# e #")])
        assert s["simultaneous"].derived == 0
        assert "undefined" in s["simultaneous"].note
