"""Tresoldi feature system (1,081 sounds, 43 features) from TSV resources."""

from __future__ import annotations

from functools import cache

from alteruphono import resources
from alteruphono.features import common as _common
from alteruphono.features.ipa import (
    FEATURE_CATEGORIES,
    build_class_table,
    resolve_alias,
)


@cache
def _build_tresoldi_table() -> dict[str, frozenset[str]]:
    """Build grapheme -> features from sounds.tsv NAME field.

    The Tresoldi system uses the same data as IPA but parses the full
    description into a richer feature set, preserving all modifiers.
    """
    sounds = resources.load_sounds()
    table: dict[str, frozenset[str]] = {}
    for grapheme, name in sounds.items():
        words = name.split()
        features: set[str] = set()
        for word in words:
            w = word.lower().strip()
            if w:
                # Keep underscored tone values as-is, replace _ with - for others
                if not w.startswith("with_"):
                    w = w.replace("_", "-")
                features.add(w)
        if features:
            table[grapheme] = frozenset(features)
    return table


@cache
def _build_tresoldi_reverse() -> dict[frozenset[str], str]:
    """Build features -> grapheme for Tresoldi."""
    table = _build_tresoldi_table()
    result: dict[frozenset[str], str] = {}
    for grapheme, features in table.items():
        if features not in result:
            result[features] = grapheme
    return result


class TresoldiFeatureSystem:
    """Tresoldi distinctive feature system with broad coverage."""

    @property
    def name(self) -> str:
        return "tresoldi"

    def grapheme_to_features(self, grapheme: str) -> frozenset[str] | None:
        return _build_tresoldi_table().get(grapheme)

    def features_to_grapheme(self, features: frozenset[str]) -> str | None:
        return _build_tresoldi_reverse().get(features)

    def is_class(self, grapheme: str) -> bool:
        return grapheme in build_class_table()

    def class_features(self, grapheme: str) -> frozenset[str] | None:
        return build_class_table().get(grapheme)

    def add_features(self, base: frozenset[str], added: frozenset[str]) -> frozenset[str]:
        return _common.add_features(base, added, FEATURE_CATEGORIES, resolve_alias)

    def partial_match(self, pattern: frozenset[str], target: frozenset[str]) -> bool:
        return _common.partial_match(pattern, target)

    def feature_distance(self, feat_a: str, feat_b: str) -> float:
        return _common.feature_distance(feat_a, feat_b)

    def sound_distance(self, feats_a: frozenset[str], feats_b: frozenset[str]) -> float:
        return _common.sound_distance(feats_a, feats_b)
