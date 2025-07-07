"""
Internal phonology module for alteruphono.

This module provides phonological primitives needed by alteruphono,
eliminating the dependency on external maniphono package.

The API is designed to be compatible with maniphono for seamless transition.
"""

from .sound import Sound
from .segment import Segment, SoundSegment, BoundarySegment
from .sequence import SegSequence
from .parsing import parse_segment, parse_sequence

__all__ = [
    'Sound',
    'Segment', 
    'SoundSegment',
    'BoundarySegment',
    'SegSequence',
    'parse_segment',
    'parse_sequence'
]