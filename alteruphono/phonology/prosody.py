"""
Prosodic hierarchy support for alteruphono.

This module provides classes and functions for representing and manipulating
prosodic structure, including syllables, feet, and prosodic words.
"""

from typing import List, Optional, Union
from enum import Enum
from .sound import Sound


class BoundaryType(Enum):
    """Types of prosodic boundaries."""
    SYLLABLE = "σ"       # Syllable boundary
    FOOT = "Ft"          # Foot boundary  
    WORD = "#"           # Prosodic word boundary
    PHRASE = "φ"         # Phonological phrase boundary
    UTTERANCE = "U"      # Utterance boundary


class ProsodicBoundary:
    """
    Represents a prosodic boundary marker.
    
    Prosodic boundaries indicate divisions in the prosodic hierarchy
    and can be used in phonological rules.
    """
    
    def __init__(self, boundary_type: BoundaryType, strength: int = 1):
        """
        Initialize a prosodic boundary.
        
        Args:
            boundary_type: The type of boundary
            strength: Strength of the boundary (1-5, where 5 is strongest)
        """
        self.boundary_type = boundary_type
        self.strength = max(1, min(5, strength))  # Clamp to 1-5
    
    def __str__(self) -> str:
        """String representation of the boundary."""
        if self.strength == 1:
            return self.boundary_type.value
        else:
            return f"{self.boundary_type.value}{self.strength}"
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"ProsodicBoundary({self.boundary_type.name}, strength={self.strength})"
    
    def __eq__(self, other) -> bool:
        """Check equality with another boundary."""
        if not isinstance(other, ProsodicBoundary):
            return False
        return (self.boundary_type == other.boundary_type and 
                self.strength == other.strength)
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash((self.boundary_type, self.strength))


class Syllable:
    """
    Represents a syllable with onset, nucleus, and coda.
    
    Syllables are fundamental units in the prosodic hierarchy and can
    carry stress and tone information.
    """
    
    def __init__(self, 
                 onset: Optional[List[Sound]] = None,
                 nucleus: Optional[List[Sound]] = None, 
                 coda: Optional[List[Sound]] = None,
                 stress: int = 0,
                 tone: Optional[str] = None):
        """
        Initialize a syllable.
        
        Args:
            onset: List of sounds in the onset
            nucleus: List of sounds in the nucleus (required)
            coda: List of sounds in the coda
            stress: Stress level (0=unstressed, 1=primary, 2=secondary)
            tone: Tone specification (e.g., 'tone1', 'rising', 'falling')
        """
        self.onset = onset or []
        self.nucleus = nucleus or []
        self.coda = coda or []
        self.stress = stress
        self.tone = tone
        
        if not self.nucleus:
            raise ValueError("Syllable must have a nucleus")
    
    def __str__(self) -> str:
        """String representation of the syllable."""
        result = ""
        
        # Add onset
        if self.onset:
            result += "".join(str(sound) for sound in self.onset)
        
        # Add nucleus with stress marking
        nucleus_str = "".join(str(sound) for sound in self.nucleus)
        if self.stress == 1:
            nucleus_str = "ˈ" + nucleus_str  # Primary stress
        elif self.stress == 2:
            nucleus_str = "ˌ" + nucleus_str  # Secondary stress
        
        # Add tone marking to nucleus
        if self.tone:
            if self.tone == "tone1" or self.tone == "high":
                nucleus_str += "́"  # High tone
            elif self.tone == "tone2" or self.tone == "mid":
                nucleus_str += "̄"  # Mid tone
            elif self.tone == "tone3" or self.tone == "low":
                nucleus_str += "̀"  # Low tone
            elif self.tone == "rising":
                nucleus_str += "̌"  # Rising tone
            elif self.tone == "falling":
                nucleus_str += "̂"  # Falling tone
        
        result += nucleus_str
        
        # Add coda
        if self.coda:
            result += "".join(str(sound) for sound in self.coda)
        
        return result
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"Syllable(onset={self.onset}, nucleus={self.nucleus}, coda={self.coda}, stress={self.stress}, tone={self.tone})"
    
    def get_all_sounds(self) -> List[Sound]:
        """Get all sounds in the syllable."""
        return self.onset + self.nucleus + self.coda
    
    def is_heavy(self) -> bool:
        """Check if the syllable is heavy (has coda or long vowel)."""
        # Heavy if it has a coda
        if self.coda:
            return True
        
        # Heavy if nucleus contains long vowels
        for sound in self.nucleus:
            if 'long' in sound.fvalues:
                return True
        
        return False
    
    def is_stressed(self) -> bool:
        """Check if the syllable carries stress."""
        return self.stress > 0


class ProsodicWord:
    """
    Represents a prosodic word containing syllables and feet.
    
    Prosodic words are domains for stress assignment and certain
    phonological processes.
    """
    
    def __init__(self, syllables: List[Syllable]):
        """
        Initialize a prosodic word.
        
        Args:
            syllables: List of syllables in the word
        """
        self.syllables = syllables
        self.feet = self._build_feet()
    
    def _build_feet(self) -> List[List[int]]:
        """
        Build metrical feet from syllables.
        
        This is a simple implementation that creates trochaic feet
        (stressed-unstressed patterns) from left to right.
        
        Returns:
            List of foot indices (each foot is a list of syllable indices)
        """
        feet = []
        current_foot = []
        
        for i, syllable in enumerate(self.syllables):
            current_foot.append(i)
            
            # End foot if we have 2 syllables or if this is stressed and we have content
            if len(current_foot) == 2 or (syllable.is_stressed() and len(current_foot) > 0):
                feet.append(current_foot)
                current_foot = []
        
        # Add any remaining syllables as a foot
        if current_foot:
            feet.append(current_foot)
        
        return feet
    
    def __str__(self) -> str:
        """String representation of the prosodic word."""
        return ".".join(str(syllable) for syllable in self.syllables)
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"ProsodicWord({self.syllables})"
    
    def get_stress_pattern(self) -> List[int]:
        """Get the stress pattern of the word."""
        return [syllable.stress for syllable in self.syllables]
    
    def assign_stress(self, pattern: str) -> None:
        """
        Assign stress according to a pattern.
        
        Args:
            pattern: Stress pattern like "10" (trochee) or "01" (iamb)
        """
        if len(pattern) != len(self.syllables):
            raise ValueError(f"Pattern length {len(pattern)} doesn't match syllable count {len(self.syllables)}")
        
        for i, stress_char in enumerate(pattern):
            self.syllables[i].stress = int(stress_char)
    
    def get_main_stress_position(self) -> Optional[int]:
        """Get the position of the main stress (returns syllable index)."""
        for i, syllable in enumerate(self.syllables):
            if syllable.stress == 1:
                return i
        return None


def parse_prosodic_string(text: str) -> List[Union[Sound, ProsodicBoundary]]:
    """
    Parse a string with prosodic markings into sounds and boundaries.
    
    Recognizes:
    - σ for syllable boundaries
    - Ft for foot boundaries  
    - # for word boundaries
    - φ for phrase boundaries
    - U for utterance boundaries
    
    Args:
        text: Input string with prosodic markings
        
    Returns:
        List of Sound and ProsodicBoundary objects
    """
    result = []
    i = 0
    
    while i < len(text):
        char = text[i]
        
        # Check for prosodic boundaries
        if char == 'σ':
            result.append(ProsodicBoundary(BoundaryType.SYLLABLE))
            i += 1
        elif char == '#':
            result.append(ProsodicBoundary(BoundaryType.WORD))
            i += 1
        elif char == 'φ':
            result.append(ProsodicBoundary(BoundaryType.PHRASE))
            i += 1
        elif char == 'U':
            result.append(ProsodicBoundary(BoundaryType.UTTERANCE))
            i += 1
        elif i < len(text) - 1 and text[i:i+2] == 'Ft':
            result.append(ProsodicBoundary(BoundaryType.FOOT))
            i += 2
        elif char == ' ':
            # Skip spaces
            i += 1
        else:
            # Regular sound
            result.append(Sound(grapheme=char))
            i += 1
    
    return result


def syllabify_sounds(sounds: List[Sound]) -> List[Syllable]:
    """
    Basic syllabification of a sequence of sounds.
    
    This is a simplified algorithm that:
    1. Places vowels in nuclei
    2. Assigns consonants to onset/coda based on sonority
    
    Args:
        sounds: List of Sound objects
        
    Returns:
        List of Syllable objects
    """
    syllables = []
    current_onset = []
    current_nucleus = []
    current_coda = []
    
    for sound in sounds:
        if 'vowel' in sound.fvalues:
            # Vowel - start new nucleus
            if current_nucleus:
                # Complete previous syllable
                syllables.append(Syllable(
                    onset=current_onset[:],
                    nucleus=current_nucleus[:],
                    coda=[]  # Don't assign consonants to coda yet
                ))
                current_onset = current_coda[:]  # Coda becomes next onset
                current_nucleus = []
                current_coda = []
            
            current_nucleus.append(sound)
        else:
            # Consonant
            if not current_nucleus:
                # Before nucleus - add to onset
                current_onset.append(sound)
            else:
                # After nucleus - add to coda
                current_coda.append(sound)
    
    # Add final syllable
    if current_nucleus:
        syllables.append(Syllable(
            onset=current_onset,
            nucleus=current_nucleus,
            coda=current_coda
        ))
    
    return syllables