"""Sound change engine for ordered rule application."""

from __future__ import annotations

from alteruphono.engine.engine import SoundChangeEngine
from alteruphono.engine.gradient import apply_gradient
from alteruphono.engine.ordering import (
    Interaction,
    RuleInteraction,
    analyze_interactions,
    recommend_ordering,
)
from alteruphono.engine.rules import CategoricalRule, GradientRule, RuleSet

__all__ = [
    "SoundChangeEngine",
    "CategoricalRule",
    "GradientRule",
    "RuleSet",
    "apply_gradient",
    "Interaction",
    "RuleInteraction",
    "analyze_interactions",
    "recommend_ordering",
]
