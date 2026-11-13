"""Bundled resources.

- `sound_changes.tsv`: the catalogue of weighted rules, each with an attested
  test pair (TEST_ANTE -> TEST_POST, applied inside "# ... #").
- `classes.tsv`: the sound-class pack (name, description, features).
- `graphemes_1x.txt`: 1.x's grapheme universe, the graphemes the `ipa` system
  looks up and renders (DESIGN 4.3).

1.x's feature tables (`sounds.tsv` with its feature names, `features.tsv`) are
gone in 2.0: features come from merkmal. `load_sounds` and `load_features`
went with them; `feature_values` now reads the vocabulary.
"""

from __future__ import annotations

import csv
from functools import cache
from pathlib import Path

_RESOURCES_DIR = Path(__file__).resolve().parent.parent / "resources"


def _load_tsv(filename: str) -> list[dict[str, str]]:
    """Load a TSV file from the resources directory."""
    path = _RESOURCES_DIR / filename
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)


@cache
def load_graphemes() -> tuple[str, ...]:
    """1.x's grapheme universe, in its original order."""
    text = (_RESOURCES_DIR / "graphemes_1x.txt").read_text(encoding="utf-8")
    return tuple(text.splitlines())


@cache
def feature_values() -> dict[str, set[str]]:
    """Return category -> its label names (1.x's vocabulary, not a table)."""
    from alteruphono.features.vocabulary import FEATURE_CATEGORIES

    result: dict[str, set[str]] = {}
    for value, category in FEATURE_CATEGORIES.items():
        result.setdefault(category, set()).add(value)
    return result


@cache
def load_sound_changes() -> list[dict[str, str]]:
    """Return list of sound change rule dicts from sound_changes.tsv."""
    return _load_tsv("sound_changes.tsv")


@cache
def sound_class_features() -> dict[str, str]:
    """Return SOUND_CLASS -> FEATURES string."""
    return {row["SOUND_CLASS"]: row["FEATURES"] for row in _load_tsv("classes.tsv")}


@cache
def sound_class_graphemes() -> dict[str, frozenset[str]]:
    """Return SOUND_CLASS -> the universe graphemes whose features match it.

    1.x stored this as a column of classes.tsv, computed from its own feature
    table; here it is computed from merkmal's features, with 1.x's matching
    rule (positive features present, "-x" features absent).
    """
    from alteruphono.features import common, get_system

    system = get_system("ipa")
    feats = {g: system.grapheme_to_features(g) for g in load_graphemes()}
    out: dict[str, frozenset[str]] = {}
    for name in sound_class_features():
        cls = system.class_features(name)
        if cls is None:
            continue
        out[name] = frozenset(g for g, f in feats.items() if f and common.partial_match(cls, f))
    return out


@cache
def load_classes() -> dict[str, tuple[str, str, list[str]]]:
    """Return mapping of SOUND_CLASS -> (DESCRIPTION, FEATURES, [GRAPHEMES])."""
    members = sound_class_graphemes()
    return {
        row["SOUND_CLASS"]: (
            row["DESCRIPTION"],
            row["FEATURES"],
            sorted(members.get(row["SOUND_CLASS"], frozenset())),
        )
        for row in _load_tsv("classes.tsv")
    }
