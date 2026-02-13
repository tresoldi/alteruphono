"""Default IPA categorical feature system.

Reads grapheme->name from sounds.tsv and extracts features from the NAME column.
Also includes hardcoded sound classes and a core grapheme feature table for fast lookup.
"""

from __future__ import annotations

from functools import cache

from alteruphono import resources
from alteruphono.features import common as _common

# Aliases for common feature names (e.g., "plosive" -> "stop")
FEATURE_ALIASES: dict[str, str] = {
    "plosive": "stop",
}


def resolve_alias(feat: str) -> str:
    """Resolve a feature alias to its canonical name."""
    return FEATURE_ALIASES.get(feat, feat)


# Feature categories used for grouping
FEATURE_CATEGORIES: dict[str, str] = {
    # Manner
    "plosive": "manner",
    "stop": "manner",
    "fricative": "manner",
    "affricate": "manner",
    "nasal": "manner",
    "approximant": "manner",
    "trill": "manner",
    "tap": "manner",
    "lateral": "manner",
    "click": "manner",
    "implosive": "manner",
    "nasal-click": "manner",
    # Place
    "bilabial": "place",
    "labio-dental": "place",
    "labio-velar": "place",
    "labio-palatal": "place",
    "dental": "place",
    "alveolar": "place",
    "post-alveolar": "place",
    "alveolo-palatal": "place",
    "retroflex": "place",
    "palatal": "place",
    "palatal-velar": "place",
    "velar": "place",
    "uvular": "place",
    "pharyngeal": "place",
    "epiglottal": "place",
    "glottal": "place",
    "linguolabial": "place",
    "labial": "place",
    # Height
    "close": "height",
    "near-close": "height",
    "close-mid": "height",
    "mid": "height",
    "open-mid": "height",
    "near-open": "height",
    "open": "height",
    # Backness
    "front": "centrality",
    "near-front": "centrality",
    "central": "centrality",
    "near-back": "centrality",
    "back": "centrality",
    # Roundness
    "rounded": "roundedness",
    "unrounded": "roundedness",
    "less-rounded": "rounding",
    "more-rounded": "rounding",
    # Phonation
    "voiced": "phonation",
    "voiceless": "phonation",
    # Type
    "consonant": "type",
    "vowel": "type",
    # Secondary articulations & modifications
    "long": "duration",
    "mid-long": "duration",
    "ultra-long": "duration",
    "ultra-short": "duration",
    "nasalized": "nasalization",
    "labialized": "labialization",
    "palatalized": "palatalization",
    "labio-palatalized": "palatalization",
    "velarized": "velarization",
    "pharyngealized": "pharyngealization",
    "aspirated": "aspiration",
    "glottalized": "glottalization",
    "breathy": "breathiness",
    "creaky": "creakiness",
    "ejective": "ejection",
    "rhotacized": "rhotacization",
    "syllabic": "syllabicity",
    "non-syllabic": "syllabicity",
    "sibilant": "sibilancy",
    "devoiced": "voicing",
    "revoiced": "voicing",
    "advanced": "relative_articulation",
    "retracted": "relative_articulation",
    "centralized": "relative_articulation",
    "mid-centralized": "relative_articulation",
    "raised": "raising",
    "lowered": "raising",
    "strong": "articulation",
    "unreleased": "release",
    "with-lateral-release": "release",
    "with-nasal-release": "release",
    "with-mid-central-vowel-release": "release",
    "with-frication": "frication",
    "advanced-tongue-root": "tongue_root",
    "retracted-tongue-root": "tongue_root",
    "apical": "laminality",
    "laminal": "laminality",
    "pre-aspirated": "preceding",
    "pre-glottalized": "preceding",
    "pre-labialized": "preceding",
    "pre-nasalized": "preceding",
    "pre-palatalized": "preceding",
    "primary-stress": "stress",
    "secondary-stress": "stress",
}

# Tone features
_TONE_VALUES = frozenset(
    {
        "with_downstep",
        "with_extra-high_tone",
        "with_extra-low_tone",
        "with_falling_tone",
        "with_global_fall",
        "with_global_rise",
        "with_high_tone",
        "with_low_tone",
        "with_mid_tone",
        "with_rising_tone",
        "with_upstep",
    }
)


def _parse_name_to_features(name: str) -> frozenset[str]:
    """Parse a sound NAME string from sounds.tsv into feature set."""
    words = name.split()
    features: set[str] = set()
    for word in words:
        w = word.lower().strip()
        # Check raw word for tone values (they use underscores like with_high_tone)
        if w in _TONE_VALUES:
            features.add(w)
        else:
            # Replace underscores with hyphens for feature categories
            w = w.replace("_", "-")
            if w in FEATURE_CATEGORIES:
                features.add(w)
    return frozenset(features)


@cache
def _build_grapheme_table() -> dict[str, frozenset[str]]:
    """Build grapheme -> features table from sounds.tsv."""
    sounds = resources.load_sounds()
    table: dict[str, frozenset[str]] = {}
    for grapheme, name in sounds.items():
        features = _parse_name_to_features(name)
        if features:
            table[grapheme] = features
    return table


@cache
def build_class_table() -> dict[str, frozenset[str]]:
    """Build class table exclusively from TSV resources."""
    result: dict[str, frozenset[str]] = {}
    try:
        tsv_classes = resources.sound_class_features()
        for cls_name, feat_str in tsv_classes.items():
            if feat_str:
                features = frozenset(f.strip() for f in feat_str.split(",") if f.strip())
                if features:
                    result[cls_name] = features
    except Exception:  # noqa: BLE001
        pass
    return result


@cache
def _build_features_to_grapheme() -> dict[frozenset[str], str]:
    """Build reverse table: features -> grapheme (first match)."""
    table = _build_grapheme_table()
    result: dict[frozenset[str], str] = {}
    for grapheme, features in table.items():
        if features not in result:
            result[features] = grapheme
    return result


class IPAFeatureSystem:
    """IPA categorical feature system backed by TSV data."""

    @property
    def name(self) -> str:
        return "ipa"

    def grapheme_to_features(self, grapheme: str) -> frozenset[str] | None:
        table = _build_grapheme_table()
        return table.get(grapheme)

    def features_to_grapheme(self, features: frozenset[str]) -> str | None:
        reverse = _build_features_to_grapheme()
        return reverse.get(features)

    def is_class(self, grapheme: str) -> bool:
        table = build_class_table()
        return grapheme in table

    def class_features(self, grapheme: str) -> frozenset[str] | None:
        table = build_class_table()
        return table.get(grapheme)

    def add_features(self, base: frozenset[str], added: frozenset[str]) -> frozenset[str]:
        return _common.add_features(base, added, FEATURE_CATEGORIES, resolve_alias)

    def partial_match(self, pattern: frozenset[str], target: frozenset[str]) -> bool:
        return _common.partial_match(pattern, target)

    def feature_distance(self, feat_a: str, feat_b: str) -> float:
        return _common.feature_distance(feat_a, feat_b)

    def sound_distance(self, feats_a: frozenset[str], feats_b: frozenset[str]) -> float:
        return _common.sound_distance(feats_a, feats_b)
