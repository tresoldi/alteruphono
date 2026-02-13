"""Pluggable feature system registry for alteruphono v2."""

from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING

from alteruphono.features.distinctive import DistinctiveFeatureSystem
from alteruphono.features.ipa import IPAFeatureSystem
from alteruphono.features.tresoldi import TresoldiFeatureSystem
from alteruphono.types import Sound

# IPA equivalence map: common alternate codepoints -> canonical form (for lookup)
_IPA_EQUIVALENCES: dict[str, str] = {
    "\u0261": "g",  # ɡ (IPA) -> g (ASCII)
    "\u2019": "\u02bc",  # right single quotation mark -> modifier letter apostrophe
    "\u0027": "\u02bc",  # ASCII apostrophe -> modifier letter apostrophe
}

# Reverse map: canonical form -> IPA preferred output
_IPA_REVERSE: dict[str, str] = {v: k for k, v in _IPA_EQUIVALENCES.items()}

if TYPE_CHECKING:
    from alteruphono.features.protocol import FeatureSystem

_registry: dict[str, FeatureSystem] = {}
_default_name: str = "ipa"


def _ensure_builtins() -> None:
    """Register built-in systems on first access."""
    if not _registry:
        _registry["ipa"] = IPAFeatureSystem()
        _registry["tresoldi"] = TresoldiFeatureSystem()
        _registry["distinctive"] = DistinctiveFeatureSystem()


def register(name: str, system: FeatureSystem) -> None:
    """Register a feature system."""
    _ensure_builtins()
    _registry[name] = system


def get_system(name: str | None = None) -> FeatureSystem:
    """Get a feature system by name (default: 'ipa')."""
    _ensure_builtins()
    key = name or _default_name
    if key not in _registry:
        msg = f"Unknown feature system: {key!r}. Available: {list(_registry)}"
        raise KeyError(msg)
    return _registry[key]


def list_systems() -> list[str]:
    """List all registered feature system names."""
    _ensure_builtins()
    return list(_registry)


def set_default(name: str) -> None:
    """Set the default feature system name."""
    global _default_name  # noqa: PLW0603
    _ensure_builtins()
    if name not in _registry:
        msg = f"Unknown feature system: {name!r}. Available: {list(_registry)}"
        raise KeyError(msg)
    _default_name = name


def normalize_output(grapheme: str) -> str:
    """Normalize a grapheme for output, mapping canonical forms back to IPA.

    E.g., ASCII 'g' -> IPA 'ɡ' (U+0261).
    """
    result: list[str] = []
    for ch in grapheme:
        result.append(_IPA_REVERSE.get(ch, ch))
    return "".join(result)


def _normalize_grapheme(grapheme: str) -> str:
    """Normalize a grapheme with NFD and IPA equivalences."""
    g = unicodedata.normalize("NFD", grapheme)
    # Apply character-level IPA equivalences
    result: list[str] = []
    for ch in g:
        result.append(_IPA_EQUIVALENCES.get(ch, ch))
    return "".join(result)


def sound(grapheme: str, system_name: str | None = None) -> Sound:
    """Create a Sound from a grapheme using a feature system.

    If the grapheme is a sound class (like V, C, N), the Sound is
    created with partial=True and the class features.
    """
    sys = get_system(system_name)

    # Check if it's a sound class
    class_feats = sys.class_features(grapheme)
    if class_feats is not None:
        return Sound(grapheme=grapheme, features=class_feats, partial=True)

    # Regular grapheme lookup
    feats = sys.grapheme_to_features(grapheme)
    if feats is not None:
        return Sound(grapheme=grapheme, features=feats)

    # Try normalized form
    norm = _normalize_grapheme(grapheme)
    if norm != grapheme:
        feats = sys.grapheme_to_features(norm)
        if feats is not None:
            return Sound(grapheme=grapheme, features=feats)

    # Unknown grapheme — return with empty features
    return Sound(grapheme=grapheme)
