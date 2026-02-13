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
