"""
Segment classes implementation for alteruphono phonology.

This module provides Segment, SoundSegment, and BoundarySegment classes
which represent phonological segments. Compatible with maniphono Segment API.
"""

from typing import List, Union
from .sound import Sound


class Segment:
    """
    Base class for all phonological segments.
    
    Segments are atomic units in phonological sequences, including
    sound segments and boundary markers.
    """
    
    def add_fvalues(self, fvalues: str) -> None:
        """
        Add feature values to this segment.
        
        Base implementation raises NotImplementedError.
        Subclasses should override if they support feature modification.
        
        Args:
            fvalues: Comma-separated feature string
        """
        raise NotImplementedError("Base Segment class does not support feature modification")
    
    def __str__(self) -> str:
        """String representation of the segment."""
        raise NotImplementedError("Subclasses must implement __str__")
    
    def __eq__(self, other) -> bool:
        """Check equality with another segment."""
        raise NotImplementedError("Subclasses must implement __eq__")
    
    def __hash__(self) -> int:
        """Hash value for the segment."""
        raise NotImplementedError("Subclasses must implement __hash__")


class SoundSegment(Segment):
    """
    Segment containing one or more Sound objects.
    
    In most cases, a SoundSegment contains a single Sound, but it can
    represent diphthongs or other complex segments with multiple sounds.
    """
    
    def __init__(self, sounds: Union[str, Sound, List[Sound]]) -> None:
        """
        Initialize a SoundSegment.
        
        Args:
            sounds: Can be:
                - String: parsed as a single sound grapheme
                - Sound: single sound object
                - List[Sound]: multiple sounds for complex segments
        """
        if isinstance(sounds, str):
            # Parse string as a single sound
            self._sounds = [Sound(grapheme=sounds)]
        elif isinstance(sounds, Sound):
            # Single sound object
            self._sounds = [sounds]
        elif isinstance(sounds, list):
            # List of sound objects
            if not sounds:
                raise ValueError("SoundSegment cannot be empty")
            if not all(isinstance(s, Sound) for s in sounds):
                raise ValueError("All elements must be Sound objects")
            self._sounds = list(sounds)  # Make a copy
        else:
            raise ValueError(f"Invalid type for sounds: {type(sounds)}")
    
    @property
    def sounds(self) -> List[Sound]:
        """Get the list of sounds in this segment."""
        return self._sounds.copy()  # Return a copy to prevent modification
    
    def add_fvalues(self, fvalues: str) -> None:
        """
        Add feature values to the sound(s) in this segment.
        
        For monosonic segments (single sound), adds features to that sound.
        For multisonic segments, this is not supported.
        
        Args:
            fvalues: Comma-separated feature string
        """
        if len(self._sounds) == 1:
            # Monosonic segment - modify the single sound
            self._sounds[0].add_fvalues(fvalues)
        else:
            # Multisonic segment - not supported
            raise NotImplementedError("Feature modification not supported for multisonic segments")
    
    def __str__(self) -> str:
        """String representation shows all sounds."""
        if len(self._sounds) == 1:
            return str(self._sounds[0])
        else:
            # For multisonic segments, concatenate without spaces
            return ''.join(str(sound) for sound in self._sounds)
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"SoundSegment({self._sounds})"
    
    def __eq__(self, other) -> bool:
        """
        Check equality with another object.
        
        Can compare with:
        - Other SoundSegment objects
        - Sound objects (if this is monosonic)
        - String representations
        """
        if isinstance(other, SoundSegment):
            return self._sounds == other._sounds
        elif isinstance(other, Sound):
            # Compare with Sound if we're monosonic
            if len(self._sounds) == 1:
                return self._sounds[0] == other
            return False
        elif isinstance(other, str):
            return str(self) == other
        else:
            return False
    
    def __hash__(self) -> int:
        """Hash based on the sounds."""
        return hash(tuple(self._sounds))


class BoundarySegment(Segment):
    """
    Segment representing word or morpheme boundaries.
    
    Boundary segments mark the edges of phonological words or morphemes.
    They are represented as '#' in string form.
    """
    
    def __init__(self) -> None:
        """Initialize a boundary segment."""
        pass
    
    def add_fvalues(self, fvalues: str) -> None:
        """
        Boundary segments do not support feature modification.
        
        Args:
            fvalues: Ignored
        """
        # Boundaries don't have features, so this is a no-op
        pass
    
    def __str__(self) -> str:
        """String representation is always '#'."""
        return "#"
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return "BoundarySegment()"
    
    def __eq__(self, other) -> bool:
        """
        Check equality with another object.
        
        Equal to other BoundarySegment objects or the string '#'.
        """
        if isinstance(other, BoundarySegment):
            return True
        elif isinstance(other, str):
            return other == "#"
        else:
            return False
    
    def __hash__(self) -> int:
        """All boundary segments have the same hash."""
        return hash("boundary")