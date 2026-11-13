"""alteruphono's `ipa` feature system: 1.x's label names and categories,
merkmal's values (by the C engine)."""

from __future__ import annotations

from functools import cache

from alteruphono import _core, _native, resources
from alteruphono.features import common as _common

from alteruphono.features.vocabulary import (  # noqa: E402,F401  (re-exported)
    _TONE_VALUES,
    FEATURE_ALIASES,
    FEATURE_CATEGORIES,
    resolve_alias,
)


class IPAFeatureSystem:
    """alteruphono 1.x's `ipa` feature system, on merkmal.

    Labels are 1.x's names (and categories, above), values are merkmal's
    `descriptive` system through the engine's `alteruphono-1` projection
    (docs/v2/DESIGN.md 4.1). Lookups are exact over 1.x's grapheme universe,
    as in 1.x. The distances are 1.x's feature-geometry distance over those
    labels (DESIGN D3): not a metric, and not a probability of change.
    """

    @property
    def name(self) -> str:
        return "ipa"

    def grapheme_to_features(self, grapheme: str) -> frozenset[str] | None:
        labels = _native.grapheme_features(_core.context(), grapheme)
        return None if labels is None else frozenset(labels)

    def features_to_grapheme(self, features: frozenset[str]) -> str | None:
        return _native.features_grapheme(_core.context(), tuple(features))

    def is_class(self, grapheme: str) -> bool:
        return _native.class_features(_core.context(), grapheme) is not None

    def class_features(self, grapheme: str) -> frozenset[str] | None:
        labels = _native.class_features(_core.context(), grapheme)
        return None if labels is None else frozenset(labels)

    def add_features(self, base: frozenset[str], added: frozenset[str]) -> frozenset[str]:
        return _common.add_features(base, added, FEATURE_CATEGORIES, resolve_alias)

    def partial_match(self, pattern: frozenset[str], target: frozenset[str]) -> bool:
        return _common.partial_match(pattern, target)

    def feature_distance(self, feat_a: str, feat_b: str) -> float:
        return _common.feature_distance(feat_a, feat_b)

    def sound_distance(self, feats_a: frozenset[str], feats_b: frozenset[str]) -> float:
        return _common.sound_distance(feats_a, feats_b)


@cache
def build_class_table() -> dict[str, frozenset[str]]:
    """Sound class -> features, from the engine's class pack (classes.tsv)."""
    result: dict[str, frozenset[str]] = {}
    for name in resources.sound_class_features():
        feats = _native.class_features(_core.context(), name)
        if feats is not None:
            result[name] = frozenset(feats)
    return result
