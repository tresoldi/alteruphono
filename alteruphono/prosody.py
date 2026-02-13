"""Prosodic hierarchy — syllable, stress, tone.

Implements sonority-based syllabification following the Sonority Sequencing
Principle (SSP): onsets rise in sonority, codas fall.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from alteruphono.features import get_system

if TYPE_CHECKING:
    from alteruphono.types import Sound


# Default sonority scale (higher = more sonorous)
DEFAULT_SONORITY: dict[str, int] = {
    "vowel": 5,
    "approximant": 4,
    "lateral": 4,
    "trill": 3,
    "tap": 3,
    "nasal": 2,
    "fricative": 1,
    "affricate": 0,
    "stop": 0,
    "click": 0,
    "implosive": 0,
}


@dataclass(frozen=True)
class Syllable:
    """A syllable as a sequence of sounds."""

    onset: tuple[Sound, ...] = ()
    nucleus: tuple[Sound, ...] = ()
    coda: tuple[Sound, ...] = ()

    @property
    def sounds(self) -> tuple[Sound, ...]:
        return self.onset + self.nucleus + self.coda

    def __str__(self) -> str:
        return "".join(str(s) for s in self.sounds)


@dataclass
class ProsodicWord:
    """A prosodic word consisting of syllables."""

    syllables: list[Syllable] = field(default_factory=list)

    @property
    def sounds(self) -> tuple[Sound, ...]:
        result: list[Sound] = []
        for syl in self.syllables:
            result.extend(syl.sounds)
        return tuple(result)

    def __str__(self) -> str:
        return ".".join(str(s) for s in self.syllables)

    def __len__(self) -> int:
        return len(self.syllables)


@dataclass(frozen=True)
class SyllableConstraints:
    """Optional constraints for syllabification."""

    allow_s_cluster: bool = False  # Allow sC onsets (e.g., English /st/)
    max_onset: int = 3
    max_coda: int = 3
    sonority_scale: tuple[tuple[str, int], ...] = tuple(DEFAULT_SONORITY.items())


def sonority(
    sound: Sound,
    system_name: str | None = None,
    sonority_scale: dict[str, int] | None = None,
) -> int:
    """Return the sonority level of a sound (0-5)."""
    feats = sound.features
    if not feats:
        sys = get_system(system_name)
        feats = sys.grapheme_to_features(sound.grapheme) or frozenset()

    scale = sonority_scale or DEFAULT_SONORITY

    # Check manner features in order of sonority
    for feat, level in scale.items():
        if feat in feats:
            return level

    # Syllabic consonants get vowel-like sonority
    if "syllabic" in feats:
        return 5

    # Default: consonant with unknown manner
    if "consonant" in feats:
        return 0
    return 0


def _is_vowel(sound: Sound, system_name: str | None = None) -> bool:
    """Check if a sound is a vowel."""
    feats = sound.features
    if not feats:
        sys = get_system(system_name)
        feats = sys.grapheme_to_features(sound.grapheme) or frozenset()
    return "vowel" in feats or ("syllabic" in feats and "consonant" not in feats)


def _is_sibilant_fricative(sound: Sound, system_name: str | None = None) -> bool:
    """Check if a sound is a sibilant fricative (for s-cluster handling)."""
    feats = sound.features
    if not feats:
        sys = get_system(system_name)
        feats = sys.grapheme_to_features(sound.grapheme) or frozenset()
    return "fricative" in feats and "sibilant" in feats


def _is_legal_onset(
    consonants: list[Sound],
    system_name: str | None = None,
    constraints: SyllableConstraints | None = None,
) -> bool:
    """Check if a consonant sequence forms a legal onset (sonority strictly rises)."""
    if not consonants:
        return True
    if len(consonants) == 1:
        return True

    max_onset = constraints.max_onset if constraints else 3
    if len(consonants) > max_onset:
        return False

    scale = dict(constraints.sonority_scale) if constraints else None

    # Check strictly rising sonority
    for i in range(len(consonants) - 1):
        s_curr = sonority(consonants[i], system_name, scale)
        s_next = sonority(consonants[i + 1], system_name, scale)
        if s_next <= s_curr:
            # Allow s+C clusters if configured
            if (
                constraints
                and constraints.allow_s_cluster
                and i == 0
                and _is_sibilant_fricative(consonants[0], system_name)
            ):
                continue
            return False
    return True


def syllabify(
    sounds: tuple[Sound, ...],
    system_name: str | None = None,
    constraints: SyllableConstraints | None = None,
) -> ProsodicWord:
    """Syllabify a sequence of sounds using the Sonority Sequencing Principle.

    Algorithm:
    1. Find all nuclei (sonority peaks — vowels or syllabic consonants)
    2. Between nuclei, split consonants: maximal legal onset to next syllable
    3. Legal onset = sonority strictly rises left-to-right
    4. Remaining consonants = coda of previous syllable
    """
    if not sounds:
        return ProsodicWord()

    scale = dict(constraints.sonority_scale) if constraints else None
    n = len(sounds)

    # Classify each sound
    is_nuc: list[bool] = [_is_vowel(s, system_name) for s in sounds]

    # Find nucleus groups (consecutive vowels form one nucleus by default)
    # Handle diphthongs vs hiatus: falling/same sonority = diphthong, rising = hiatus
    nuclei: list[tuple[int, int]] = []  # (start, end) inclusive
    i = 0
    while i < n:
        if is_nuc[i]:
            start = i
            i += 1
            while i < n and is_nuc[i]:
                # Check for hiatus: if sonority rises, split
                prev_son = sonority(sounds[i - 1], system_name, scale)
                curr_son = sonority(sounds[i], system_name, scale)
                if curr_son > prev_son:
                    break  # Hiatus — new nucleus
                i += 1
            nuclei.append((start, i - 1))
        else:
            i += 1

    if not nuclei:
        # No vowels — all consonants in one syllable
        return ProsodicWord(syllables=[Syllable(onset=sounds)])

    # Build syllables from nuclei and intervening consonants
    syllables: list[Syllable] = []

    for idx, (nuc_start, nuc_end) in enumerate(nuclei):
        onset_sounds: list[Sound] = []
        coda_sounds: list[Sound] = []
        nucleus_sounds = sounds[nuc_start : nuc_end + 1]

        if idx == 0:
            # First nucleus: everything before it is onset
            onset_sounds = list(sounds[:nuc_start])
        else:
            # Between previous nucleus end and current nucleus start
            prev_nuc_end = nuclei[idx - 1][1]
            between = list(sounds[prev_nuc_end + 1 : nuc_start])

            # Split: maximal legal onset to current syllable, rest is coda of prev
            if between:
                # Try giving maximal onset to current syllable
                best_split = len(between)  # default: all go to coda of prev
                for split_at in range(len(between) + 1):
                    candidate_onset = between[split_at:]
                    if _is_legal_onset(candidate_onset, system_name, constraints):
                        best_split = split_at
                        break

                # Add coda to previous syllable
                prev_coda = between[:best_split]
                if prev_coda and syllables:
                    max_coda = constraints.max_coda if constraints else 3
                    prev_coda = prev_coda[-max_coda:] if len(prev_coda) > max_coda else prev_coda
                    prev = syllables[-1]
                    syllables[-1] = Syllable(
                        onset=prev.onset,
                        nucleus=prev.nucleus,
                        coda=prev.coda + tuple(prev_coda),
                    )
                elif prev_coda and not syllables:
                    # Edge case: consonants before first nucleus that don't
                    # form legal onset — treat as onset anyway
                    onset_sounds = prev_coda

                onset_sounds = between[best_split:]

        # Handle trailing consonants after last nucleus
        if idx == len(nuclei) - 1:
            coda_sounds = list(sounds[nuc_end + 1 :])

        syllables.append(
            Syllable(
                onset=tuple(onset_sounds),
                nucleus=tuple(nucleus_sounds),
                coda=tuple(coda_sounds),
            )
        )

    return ProsodicWord(syllables=syllables)
