"""Shared feature system methods — avoids duplication across implementations."""

from __future__ import annotations

from alteruphono.features.geometry import GEOMETRY


def add_features(
    base: frozenset[str],
    added: frozenset[str],
    categories: dict[str, str],
    resolve_fn: object,
) -> frozenset[str]:
    """Add features to a base set, replacing within same category."""
    result = set(base)
    for feat in added:
        resolved = resolve_fn(feat)  # type: ignore[operator]
        cat = categories.get(resolved)
        if cat:
            result = {f for f in result if categories.get(f) != cat}
        result.add(resolved)
    return frozenset(result)


def partial_match(pattern: frozenset[str], target: frozenset[str]) -> bool:
    """Check if pattern features are a subset of target features.

    Supports negative features: a pattern feature starting with '-'
    means the target must NOT contain that feature.
    """
    positive = frozenset(f for f in pattern if not f.startswith("-"))
    negative = frozenset(f[1:] for f in pattern if f.startswith("-"))
    return positive <= target and not (negative & target)


def feature_distance(feat_a: str, feat_b: str) -> float:
    """Tree edge distance between two feature values."""
    return float(GEOMETRY.feature_distance(feat_a, feat_b))


def sound_distance(feats_a: frozenset[str], feats_b: frozenset[str]) -> float:
    """Geometry-weighted distance between two feature sets."""
    return GEOMETRY.sound_distance(feats_a, feats_b)
