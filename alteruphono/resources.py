"""Lazy TSV resource loader for alteruphono v2."""

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
def load_sounds() -> dict[str, str]:
    """Return mapping of GRAPHEME -> NAME from sounds.tsv."""
    rows = _load_tsv("sounds.tsv")
    return {row["GRAPHEME"]: row["NAME"] for row in rows}


@cache
def load_features() -> list[tuple[str, str]]:
    """Return list of (VALUE, FEATURE) pairs from features.tsv."""
    rows = _load_tsv("features.tsv")
    return [(row["VALUE"], row["FEATURE"]) for row in rows]


@cache
def load_classes() -> dict[str, tuple[str, str, list[str]]]:
    """Return mapping of SOUND_CLASS -> (DESCRIPTION, FEATURES, [GRAPHEMES])."""
    rows = _load_tsv("classes.tsv")
    result: dict[str, tuple[str, str, list[str]]] = {}
    for row in rows:
        graphemes = row["GRAPHEMES"].split("|") if row["GRAPHEMES"] else []
        result[row["SOUND_CLASS"]] = (row["DESCRIPTION"], row["FEATURES"], graphemes)
    return result


@cache
def load_sound_changes() -> list[dict[str, str]]:
    """Return list of sound change rule dicts from sound_changes.tsv."""
    return _load_tsv("sound_changes.tsv")


@cache
def feature_values() -> dict[str, set[str]]:
    """Return FEATURE -> set of VALUES mapping from features.tsv."""
    result: dict[str, set[str]] = {}
    for value, feature in load_features():
        result.setdefault(feature, set()).add(value)
    return result


@cache
def sound_class_graphemes() -> dict[str, frozenset[str]]:
    """Return SOUND_CLASS -> frozenset of graphemes."""
    classes = load_classes()
    return {k: frozenset(v[2]) for k, v in classes.items()}


@cache
def sound_class_features() -> dict[str, str]:
    """Return SOUND_CLASS -> FEATURES string."""
    classes = load_classes()
    return {k: v[1] for k, v in classes.items()}
