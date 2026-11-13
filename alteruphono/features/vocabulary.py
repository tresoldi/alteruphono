"""alteruphono 1.x's label vocabulary: names, categories, aliases, tones.

These fix the names a rule may use and the replacement rule of feature
modifiers (`@1[+voiced]` removes the other labels of `voiced`'s category).
They are not a feature table: every value comes from merkmal. No imports, so
scripts/gen_compat1x.py can read it without the compiled engine.
"""

from __future__ import annotations

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
