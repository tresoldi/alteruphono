"""
Internal phonology module for alteruphono.

This module provides phonological primitives needed by alteruphono,
eliminating the dependency on external maniphono package.

The API is designed to be compatible with maniphono for seamless transition.

Phase 4 adds support for suprasegmental features (stress, tone, length),
numeric feature values, and prosodic hierarchy representation.
"""

from .sound import Sound
from .segment import Segment, SoundSegment, BoundarySegment
from .sequence import SegSequence
from .parsing import parse_segment, parse_sequence
from .prosody import (
    ProsodicBoundary,
    BoundaryType,
    Syllable,
    ProsodicWord,
    syllabify_sounds,
    parse_prosodic_string
)
from .models import (
    is_suprasegmental_feature,
    is_numeric_feature,
    get_numeric_value,
    increment_numeric_feature,
    decrement_numeric_feature
)

__all__ = [
    # Core phonology
    'Sound',
    'Segment', 
    'SoundSegment',
    'BoundarySegment',
    'SegSequence',
    'parse_segment',
    'parse_sequence',
    
    # Phase 4: Prosodic hierarchy
    'ProsodicBoundary',
    'BoundaryType',
    'Syllable',
    'ProsodicWord',
    'syllabify_sounds',
    'parse_prosodic_string',
    
    # Phase 4: Feature utilities
    'is_suprasegmental_feature',
    'is_numeric_feature',
    'get_numeric_value',
    'increment_numeric_feature',
    'decrement_numeric_feature'
]