"""Unified distinctive feature system with scalar values (-1.0 to +1.0).

Uses ~26 curated scalar dimensions derived from the feature geometry tree,
covering Laryngeal, Manner, Syllabic, Place, and Prosodic categories.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache

from alteruphono import resources
from alteruphono.features import common as _common
from alteruphono.features.ipa import (
    FEATURE_CATEGORIES,
    build_class_table,
    resolve_alias,
)


@dataclass(frozen=True)
class ScalarDimension:
    """A scalar dimension mapping IPA features to +1.0/-1.0."""

    name: str
    positive: frozenset[str]  # IPA features mapping to +1.0
    negative: frozenset[str]  # IPA features mapping to -1.0
    geometry_node: str  # node name in the tree


# Curated scalar dimensions grouped by geometry node
_SCALAR_DIMENSIONS: tuple[ScalarDimension, ...] = (
    # Laryngeal (3)
    ScalarDimension(
        name="voice",
        positive=frozenset({"voiced"}),
        negative=frozenset({"voiceless"}),
        geometry_node="Laryngeal",
    ),
    ScalarDimension(
        name="spread_glottis",
        positive=frozenset({"aspirated"}),
        negative=frozenset(),
        geometry_node="Laryngeal",
    ),
    ScalarDimension(
        name="constricted_glottis",
        positive=frozenset({"glottalized"}),
        negative=frozenset(),
        geometry_node="Laryngeal",
    ),
    # Manner (7)
    ScalarDimension(
        name="sonorant",
        positive=frozenset({"vowel", "nasal", "approximant", "lateral"}),
        negative=frozenset({"consonant"}),
        geometry_node="Manner",
    ),
    ScalarDimension(
        name="continuant",
        positive=frozenset({"fricative", "approximant"}),
        negative=frozenset({"stop", "affricate"}),
        geometry_node="Manner",
    ),
    ScalarDimension(
        name="nasal",
        positive=frozenset({"nasal"}),
        negative=frozenset(),
        geometry_node="Manner",
    ),
    ScalarDimension(
        name="lateral",
        positive=frozenset({"lateral"}),
        negative=frozenset(),
        geometry_node="Manner",
    ),
    ScalarDimension(
        name="strident",
        positive=frozenset({"sibilant"}),
        negative=frozenset(),
        geometry_node="Manner",
    ),
    ScalarDimension(
        name="delayed_release",
        positive=frozenset({"affricate"}),
        negative=frozenset(),
        geometry_node="Manner",
    ),
    ScalarDimension(
        name="tap_feature",
        positive=frozenset({"tap"}),
        negative=frozenset(),
        geometry_node="Manner",
    ),
    # Syllabic (1)
    ScalarDimension(
        name="syllabic",
        positive=frozenset({"vowel", "syllabic"}),
        negative=frozenset({"consonant", "non-syllabic"}),
        geometry_node="Manner",
    ),
    # Labial (2)
    ScalarDimension(
        name="labial",
        positive=frozenset({"bilabial", "labio-dental", "labio-velar", "labio-palatal", "labial"}),
        negative=frozenset(),
        geometry_node="Labial",
    ),
    ScalarDimension(
        name="round",
        positive=frozenset({"rounded"}),
        negative=frozenset({"unrounded"}),
        geometry_node="Labial",
    ),
    # Coronal (3)
    ScalarDimension(
        name="coronal",
        positive=frozenset(
            {
                "dental",
                "alveolar",
                "post-alveolar",
                "alveolo-palatal",
                "retroflex",
                "linguolabial",
            }
        ),
        negative=frozenset(),
        geometry_node="Coronal",
    ),
    ScalarDimension(
        name="anterior",
        positive=frozenset({"dental", "alveolar"}),
        negative=frozenset({"post-alveolar", "retroflex", "alveolo-palatal"}),
        geometry_node="Coronal",
    ),
    ScalarDimension(
        name="distributed",
        positive=frozenset({"post-alveolar", "alveolo-palatal"}),
        negative=frozenset({"alveolar", "retroflex"}),
        geometry_node="Coronal",
    ),
    # Dorsal (4)
    ScalarDimension(
        name="dorsal",
        positive=frozenset({"palatal", "palatal-velar", "velar", "uvular"}),
        negative=frozenset(),
        geometry_node="Dorsal",
    ),
    ScalarDimension(
        name="high",
        positive=frozenset({"close", "near-close"}),
        negative=frozenset({"open", "near-open"}),
        geometry_node="Dorsal",
    ),
    ScalarDimension(
        name="low",
        positive=frozenset({"open", "near-open"}),
        negative=frozenset({"close", "near-close"}),
        geometry_node="Dorsal",
    ),
    ScalarDimension(
        name="back",
        positive=frozenset({"back", "near-back"}),
        negative=frozenset({"front", "near-front"}),
        geometry_node="Dorsal",
    ),
    # Laryngeal phonation (2)
    ScalarDimension(
        name="breathy_voice",
        positive=frozenset({"breathy"}),
        negative=frozenset(),
        geometry_node="Laryngeal",
    ),
    ScalarDimension(
        name="creaky_voice",
        positive=frozenset({"creaky"}),
        negative=frozenset(),
        geometry_node="Laryngeal",
    ),
    # TongueRoot (1)
    ScalarDimension(
        name="atr",
        positive=frozenset({"advanced-tongue-root"}),
        negative=frozenset({"retracted-tongue-root"}),
        geometry_node="TongueRoot",
    ),
    # Coronal extra (1)
    ScalarDimension(
        name="apical",
        positive=frozenset({"apical"}),
        negative=frozenset({"laminal"}),
        geometry_node="Coronal",
    ),
    # Prosodic (8)
    ScalarDimension(
        name="long",
        positive=frozenset({"long"}),
        negative=frozenset(),
        geometry_node="Prosodic",
    ),
    ScalarDimension(
        name="nasalized",
        positive=frozenset({"nasalized"}),
        negative=frozenset(),
        geometry_node="Prosodic",
    ),
    ScalarDimension(
        name="labialized",
        positive=frozenset({"labialized"}),
        negative=frozenset(),
        geometry_node="Prosodic",
    ),
    ScalarDimension(
        name="palatalized",
        positive=frozenset({"palatalized"}),
        negative=frozenset(),
        geometry_node="Prosodic",
    ),
    ScalarDimension(
        name="pharyngealized",
        positive=frozenset({"pharyngealized"}),
        negative=frozenset(),
        geometry_node="Prosodic",
    ),
    ScalarDimension(
        name="ejective",
        positive=frozenset({"ejective"}),
        negative=frozenset(),
        geometry_node="Prosodic",
    ),
    ScalarDimension(
        name="rhotacized",
        positive=frozenset({"rhotacized"}),
        negative=frozenset(),
        geometry_node="Prosodic",
    ),
    ScalarDimension(
        name="velarized",
        positive=frozenset({"velarized"}),
        negative=frozenset(),
        geometry_node="Prosodic",
    ),
)


@cache
def _dimension_weights() -> dict[str, float]:
    """Geometry-based weights: inverse of node depth in tree."""
    from alteruphono.features.geometry import GEOMETRY, _node_depth

    weights: dict[str, float] = {}
    for dim in _SCALAR_DIMENSIONS:
        depth = _node_depth(GEOMETRY, dim.geometry_node, 1) or 2
        weights[dim.name] = 1.0 / depth
    return weights


def _features_to_scalar(features: frozenset[str]) -> dict[str, float]:
    """Convert categorical features to scalar representation."""
    result: dict[str, float] = {}
    for dim in _SCALAR_DIMENSIONS:
        if features & dim.positive:
            result[dim.name] = 1.0
        elif dim.negative and features & dim.negative:
            result[dim.name] = -1.0
    return result


def _scalar_to_features(scalars: dict[str, float]) -> frozenset[str]:
    """Convert scalar representation back to categorical features.

    For each dimension, maps +1.0 to the first positive feature
    and -1.0 to the first negative feature.
    """
    result: set[str] = set()
    dim_map = {d.name: d for d in _SCALAR_DIMENSIONS}
    for name, val in scalars.items():
        dim = dim_map.get(name)
        if dim is None:
            continue
        if val > 0 and dim.positive:
            # Take first positive feature as canonical
            result.add(next(iter(sorted(dim.positive))))
        elif val < 0 and dim.negative:
            result.add(next(iter(sorted(dim.negative))))
    return frozenset(result)


@cache
def _build_distinctive_table() -> dict[str, frozenset[str]]:
    """Build grapheme -> features table using scalar feature system."""
    sounds = resources.load_sounds()
    table: dict[str, frozenset[str]] = {}
    for grapheme, name in sounds.items():
        words = name.split()
        features: set[str] = set()
        for word in words:
            w = word.lower().strip()
            if not w.startswith("with_"):
                w = w.replace("_", "-")
            if w in FEATURE_CATEGORIES:
                features.add(w)
        if features:
            table[grapheme] = frozenset(features)
    return table


@cache
def _build_distinctive_reverse() -> dict[frozenset[str], str]:
    table = _build_distinctive_table()
    result: dict[frozenset[str], str] = {}
    for grapheme, features in table.items():
        if features not in result:
            result[features] = grapheme
    return result


class DistinctiveFeatureSystem:
    """Unified distinctive feature system using scalar values."""

    @property
    def name(self) -> str:
        return "distinctive"

    @property
    def dimensions(self) -> tuple[ScalarDimension, ...]:
        return _SCALAR_DIMENSIONS

    def grapheme_to_features(self, grapheme: str) -> frozenset[str] | None:
        return _build_distinctive_table().get(grapheme)

    def features_to_grapheme(self, features: frozenset[str]) -> str | None:
        return _build_distinctive_reverse().get(features)

    def grapheme_to_scalars(self, grapheme: str) -> dict[str, float] | None:
        """Get scalar feature representation for a grapheme."""
        features = self.grapheme_to_features(grapheme)
        if features is None:
            return None
        return _features_to_scalar(features)

    def scalars_to_features(self, scalars: dict[str, float]) -> frozenset[str]:
        """Convert scalar values to categorical features."""
        return _scalar_to_features(scalars)

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
        """Geometry-weighted distance using scalar dimensions."""
        if feats_a == feats_b:
            return 0.0

        weights = _dimension_weights()
        scalars_a = _features_to_scalar(feats_a)
        scalars_b = _features_to_scalar(feats_b)

        total_weight = 0.0
        total_diff = 0.0

        for dim in _SCALAR_DIMENSIONS:
            weight = weights[dim.name]
            val_a = scalars_a.get(dim.name, 0.0)
            val_b = scalars_b.get(dim.name, 0.0)

            if val_a == 0.0 and val_b == 0.0:
                continue

            total_weight += weight
            total_diff += weight * abs(val_a - val_b) / 2.0

        return total_diff / total_weight if total_weight > 0 else 0.0
