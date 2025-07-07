"""
Parsing functions for alteruphono phonology.

This module provides functions to parse strings into phonological objects.
Compatible with maniphono parsing API.
"""

import re
from typing import Union
from .sound import Sound
from .segment import Segment, SoundSegment, BoundarySegment
from .sequence import SegSequence


# Regular expression for parsing segments with optional feature specifications
# Matches patterns like: p, p[voiced], V[long], etc.
SEGMENT_PATTERN = re.compile(r'^([^[\]]+)(?:\[([^\]]+)\])?$')


def parse_segment(segment_str: str) -> Segment:
    """
    Parse a string into a Segment object.
    
    Args:
        segment_str: String representation like 'p', 'p[voiced]', '#', etc.
        
    Returns:
        SoundSegment or BoundarySegment object
        
    Examples:
        >>> parse_segment('p')
        SoundSegment([Sound('p')])
        >>> parse_segment('p[voiced]')
        SoundSegment([Sound('b')])  # p + voiced = b
        >>> parse_segment('#')
        BoundarySegment()
    """
    segment_str = segment_str.strip()
    
    if not segment_str:
        raise ValueError("Empty segment string")
    
    # Handle boundary markers
    if segment_str == '#':
        return BoundarySegment()
    
    # Parse segment with optional features
    match = SEGMENT_PATTERN.match(segment_str)
    if not match:
        raise ValueError(f"Invalid segment format: {segment_str}")
    
    base_segment = match.group(1)
    features = match.group(2)
    
    # Create base sound
    try:
        sound = Sound(grapheme=base_segment)
    except ValueError:
        # If grapheme is not recognized, create it anyway
        sound = Sound(grapheme=base_segment)
    
    # Apply features if specified
    if features:
        sound = sound + features
    
    return SoundSegment(sound)


def parse_sequence(sequence_str: str, boundaries: bool = True) -> SegSequence:
    """
    Parse a space-separated string into a SegSequence.
    
    Args:
        sequence_str: Space-separated segment string like "# p a t e #"
        boundaries: Whether to automatically manage word boundaries
        
    Returns:
        SegSequence object containing parsed segments
        
    Examples:
        >>> parse_sequence("p a t e")
        SegSequence([BoundarySegment(), SoundSegment('p'), 
                    SoundSegment('a'), SoundSegment('t'), 
                    SoundSegment('e'), BoundarySegment()])
        >>> parse_sequence("# p a #", boundaries=False)
        SegSequence([BoundarySegment(), SoundSegment('p'), 
                    SoundSegment('a'), BoundarySegment()])
    """
    sequence_str = sequence_str.strip()
    
    if not sequence_str:
        # Empty sequence
        return SegSequence([], boundaries=boundaries)
    
    # Split on whitespace and parse each segment
    segment_strings = sequence_str.split()
    segments = []
    
    for segment_str in segment_strings:
        try:
            segment = parse_segment(segment_str)
            segments.append(segment)
        except ValueError as e:
            raise ValueError(f"Error parsing segment '{segment_str}': {e}")
    
    return SegSequence(segments, boundaries=boundaries)


def parse_features(feature_str: str) -> str:
    """
    Parse and normalize a feature specification string.
    
    This function handles various feature notation formats and
    normalizes them to a consistent form.
    
    Args:
        feature_str: Feature string like "voiced,bilabial" or "+voice,-nasal"
        
    Returns:
        Normalized feature string
        
    Examples:
        >>> parse_features("voiced,bilabial")
        "voiced,bilabial"
        >>> parse_features("+voice,-nasal")
        "voiced,-nasal"
    """
    if not feature_str:
        return ""
    
    # Split on commas and normalize each feature
    features = []
    for feature in feature_str.split(','):
        feature = feature.strip()
        if feature:
            # Handle +/- notation
            if feature.startswith('+'):
                feature = feature[1:]  # Remove + prefix
            elif feature.startswith('-'):
                # Keep - prefix for negative features
                pass
            
            features.append(feature)
    
    return ','.join(features)


def segment_to_string(segment: Segment) -> str:
    """
    Convert a segment back to its string representation.
    
    Args:
        segment: Segment object to convert
        
    Returns:
        String representation of the segment
    """
    return str(segment)


def sequence_to_string(sequence: SegSequence) -> str:
    """
    Convert a sequence back to its string representation.
    
    Args:
        sequence: SegSequence object to convert
        
    Returns:
        Space-separated string representation
    """
    return str(sequence)