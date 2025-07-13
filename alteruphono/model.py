"""
Module holding the classes for the manipulation of sound changes.
"""

from abc import ABC, abstractmethod
from typing import Union

from .exceptions import AlteruPhonoError
from .phonology import parse_segment, Sound, SoundSegment
from .phonology.prosody import ProsodicBoundary, BoundaryType

# TODO: all tokens should have a method to return a corresponding segment

class Token(ABC):
    """
    Abstract base class for all token types in sound change rules.
    
    Tokens represent different elements in sound change rules such as
    segments, boundaries, back-references, etc.
    """
    
    def __init__(self):
        # TODO: applies only to back-ref or should we reuse if possible for set/choice?
        self.index = None

    @abstractmethod
    def __str__(self) -> str:
        """Return string representation of the token."""
        pass

    @abstractmethod
    def __hash__(self) -> int:
        """Return hash value for the token."""
        pass

    def __eq__(self, other) -> bool:
        """Check equality with another token."""
        if not isinstance(other, Token):
            return False
        return str(self) == str(other) and type(self) == type(other)

    def __ne__(self, other) -> bool:
        """Check inequality with another token."""
        return not self.__eq__(other)


class BoundaryToken(Token):
    """Token representing word or morpheme boundaries (#)."""
    def __init__(self, boundary_type: str = "#"):
        super().__init__()
        self.boundary_type = boundary_type

    def __str__(self) -> str:
        return self.boundary_type

    def __repr__(self) -> str:
        return f"boundary_tok:{str(self)}"

    def __hash__(self) -> int:
        return hash(self.boundary_type)


class ProsodicBoundaryToken(Token):
    """Token representing prosodic boundaries (syllable, foot, etc.)."""
    def __init__(self, boundary: ProsodicBoundary):
        super().__init__()
        self.boundary = boundary

    def __str__(self) -> str:
        return str(self.boundary)

    def __repr__(self) -> str:
        return f"prosodic_boundary_tok:{str(self)}"

    def __hash__(self) -> int:
        return hash(self.boundary)


class FocusToken(Token):
    def __init__(self):
        super().__init__()

    def __str__(self) -> str:
        return "_"

    def __repr__(self) -> str:
        return f"focus_tok:{str(self)}"

    def __hash__(self) -> int:
        # TODO: all focus are equal here
        return hash(2)


class EmptyToken(Token):
    def __init__(self):
        super().__init__()

    def __str__(self) -> str:
        return ":null:"

    def __repr__(self) -> str:
        return f"empty_tok:{str(self)}"

    def __hash__(self) -> int:
        # TODO: all empty are equal here (but should they be?)
        return hash(3)


class BackRefToken(Token):
    def __init__(self, index: int, modifier=None):
        super().__init__()

        self.index = index
        self.modifier = modifier

    def __str__(self) -> str:
        if self.modifier:
            return f"@{self.index + 1}[{self.modifier}]"

        return f"@{self.index + 1}"

    def __repr__(self) -> str:
        return f"backref_tok:{str(self)}"

    def __add__(self, other):
        return BackRefToken(self.index + other, self.modifier)

    def __hash__(self):
        if not self.modifier:
            return hash(self.index)

        return hash(tuple([tuple(self.modifier), self.index]))

    def __eq__(self, other) -> bool:
        return hash(self) == hash(other)

    def __ne__(self, other) -> bool:
        return hash(self) != hash(other)


class ChoiceToken(Token):
    def __init__(self, choices):
        super().__init__()
        self.choices = choices

    def __str__(self) -> str:
        return "|".join([str(choice) for choice in self.choices])

    def __repr__(self) -> str:
        return f"choice_tok:{str(self)}"

    def __hash__(self):
        return hash(tuple(self.choices))

    def __eq__(self, other) -> bool:
        return hash(self) == hash(other)

    def __ne__(self, other) -> bool:
        return hash(self) != hash(other)


class SetToken(Token):
    def __init__(self, choices):
        super().__init__()
        self.choices = choices

    def __str__(self) -> str:
        return "{" + "|".join([str(choice) for choice in self.choices]) + "}"

    def __repr__(self) -> str:
        return f"set_tok:{str(self)}"

    def __hash__(self):
        return hash(tuple(self.choices))

    def __eq__(self, other) -> bool:
        return hash(self) == hash(other)

    def __ne__(self, other) -> bool:
        return hash(self) != hash(other)


# named segment token to distinguish from the maniphono SoundSegment
# TODO: rename `segment` argument
class SegmentToken(Token):
    """Token representing a phonological segment."""
    def __init__(self, segment: Union[str, Sound, SoundSegment]):
        super().__init__()

        if isinstance(segment, str):
            self.segment = parse_segment(segment)
        elif isinstance(segment, Sound):
            self.segment = SoundSegment(segment)
        else:
            self.segment = segment

    def __str__(self) -> str:
        return str(self.segment)

    def __repr__(self) -> str:
        return f"segment_tok:{str(self)}"

    def __hash__(self):
        return hash(self.segment)

    def __eq__(self, other) -> bool:
        return hash(self) == hash(other)

    def __ne__(self, other) -> bool:
        return hash(self) != hash(other)

    def add_modifier(self, modifier):
        # TODO: properly implement with the __add__ operation from maniphono
        # hack using graphemic representation...
        grapheme = str(self.segment.sounds[0])
        sound = Sound(grapheme) + modifier
        segment = SoundSegment(sound)
        self.segment = segment
    
    def has_suprasegmental_features(self) -> bool:
        """Check if this segment has suprasegmental features."""
        from .phonology.models import is_suprasegmental_feature
        return any(is_suprasegmental_feature(str(feature)) 
                  for sound in self.segment.sounds 
                  for feature in sound.fvalues)
    
    def get_stress_level(self) -> int:
        """Get stress level of this segment (0=unstressed, 1=primary, 2=secondary)."""
        for sound in self.segment.sounds:
            if sound.has_stress():
                return sound.get_stress_level()
        return 0
    
    def get_tone_value(self) -> int:
        """Get tone value of this segment (1-5), or 0 if no tone."""
        for sound in self.segment.sounds:
            if sound.has_tone():
                return sound.get_tone_value()
        return 0
