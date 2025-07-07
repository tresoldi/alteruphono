"""
SegSequence implementation for alteruphono phonology.

This module provides the SegSequence class which represents sequences
of phonological segments. Compatible with maniphono SegSequence API.
"""

from typing import Iterator, List, Union
from .segment import Segment, SoundSegment, BoundarySegment


class SegSequence:
    """
    Class representing a sequence of phonological segments.
    
    A SegSequence contains an ordered list of segments (SoundSegment or
    BoundarySegment objects) and can optionally manage word boundaries
    automatically.
    """
    
    def __init__(self, segments: List[Segment], boundaries: bool = True) -> None:
        """
        Initialize a SegSequence.
        
        Args:
            segments: List of Segment objects
            boundaries: Whether to automatically manage word boundaries
        """
        if not isinstance(segments, list):
            raise ValueError("segments must be a list")
        
        self.segments: List[Segment] = list(segments)  # Make a copy
        self.boundaries: bool = boundaries
        
        # Update boundaries if requested
        self._update_boundaries()
    
    def _update_boundaries(self) -> None:
        """
        Update boundary segments according to the boundaries setting.
        
        If boundaries=True, ensures the sequence starts and ends with
        BoundarySegment objects. If boundaries=False, removes boundary
        segments from the ends.
        """
        if self.boundaries:
            # Ensure we start with a boundary
            if not self.segments or not isinstance(self.segments[0], BoundarySegment):
                self.segments.insert(0, BoundarySegment())
            
            # Ensure we end with a boundary
            if len(self.segments) < 2 or not isinstance(self.segments[-1], BoundarySegment):
                self.segments.append(BoundarySegment())
        else:
            # Remove boundary segments from ends
            while self.segments and isinstance(self.segments[0], BoundarySegment):
                self.segments.pop(0)
            while self.segments and isinstance(self.segments[-1], BoundarySegment):
                self.segments.pop()
    
    def __len__(self) -> int:
        """Return the number of segments."""
        return len(self.segments)
    
    def __getitem__(self, index: Union[int, slice]) -> Union[Segment, List[Segment]]:
        """
        Get segment(s) by index.
        
        Args:
            index: Integer index or slice
            
        Returns:
            Single segment for integer index, list of segments for slice
        """
        return self.segments[index]
    
    def __iter__(self) -> Iterator[Segment]:
        """Iterate over segments."""
        return iter(self.segments)
    
    def __str__(self) -> str:
        """
        String representation with space-separated segments.
        
        Returns:
            Space-separated string of segment representations
        """
        return " ".join(str(segment) for segment in self.segments)
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"SegSequence({self.segments}, boundaries={self.boundaries})"
    
    def __eq__(self, other) -> bool:
        """
        Check equality with another SegSequence or string.
        
        Args:
            other: SegSequence or string to compare with
            
        Returns:
            True if sequences are equal
        """
        if isinstance(other, SegSequence):
            return (self.segments == other.segments and 
                    self.boundaries == other.boundaries)
        elif isinstance(other, str):
            return str(self) == other
        else:
            return False
    
    def __hash__(self) -> int:
        """Hash based on segments and boundary setting."""
        return hash((tuple(self.segments), self.boundaries))
    
    def append(self, segment: Segment) -> None:
        """
        Add a segment to the end of the sequence.
        
        Args:
            segment: Segment to add
        """
        if not isinstance(segment, Segment):
            raise ValueError("Can only append Segment objects")
        
        if self.boundaries and isinstance(self.segments[-1], BoundarySegment):
            # Insert before the final boundary
            self.segments.insert(-1, segment)
        else:
            # Just append normally
            self.segments.append(segment)
            
        self._update_boundaries()
    
    def insert(self, index: int, segment: Segment) -> None:
        """
        Insert a segment at the specified index.
        
        Args:
            index: Position to insert at
            segment: Segment to insert
        """
        if not isinstance(segment, Segment):
            raise ValueError("Can only insert Segment objects")
            
        self.segments.insert(index, segment)
        self._update_boundaries()
    
    def extend(self, segments: List[Segment]) -> None:
        """
        Add multiple segments to the end of the sequence.
        
        Args:
            segments: List of segments to add
        """
        if not all(isinstance(s, Segment) for s in segments):
            raise ValueError("All elements must be Segment objects")
        
        if self.boundaries and self.segments and isinstance(self.segments[-1], BoundarySegment):
            # Insert before the final boundary
            for segment in reversed(segments):
                self.segments.insert(-1, segment)
        else:
            # Just extend normally
            self.segments.extend(segments)
            
        self._update_boundaries()
    
    def copy(self) -> 'SegSequence':
        """
        Create a copy of this sequence.
        
        Returns:
            New SegSequence with copied segments
        """
        return SegSequence(self.segments.copy(), self.boundaries)