"""
Sound class implementation for alteruphono phonology.

This module provides the Sound class which represents phonological sounds
as bundles of feature values. Compatible with maniphono Sound API.
"""

from typing import FrozenSet, Optional, Union
from .models import (
    get_grapheme_features, 
    get_class_features, 
    parse_features, 
    features_to_grapheme,
    normalize_feature
)


class Sound:
    """
    Class for representing a sound as a bundle of feature values.
    
    A sound can be initialized with either a grapheme (like 'p') or a 
    feature description (like 'bilabial,stop,voiceless'). Sounds support
    feature arithmetic and partial matching operations.
    """
    
    def __init__(
        self, 
        grapheme: Optional[str] = None, 
        description: Optional[str] = None, 
        partial: Optional[bool] = None
    ) -> None:
        """
        Initialize a Sound object.
        
        Args:
            grapheme: A single grapheme like 'p', 'a', 'V' (sound class)
            description: Comma-separated feature description like 'voiced,bilabial'
            partial: Whether this is a partial/underspecified sound
        """
        if not any([grapheme, description]) or all([grapheme, description]):
            raise ValueError("Either grapheme or description must be provided")
        
        self._fvalues: FrozenSet[str] = frozenset()
        self._partial: bool = partial if partial is not None else False
        self._grapheme: Optional[str] = None
        
        if grapheme is not None:
            self._grapheme = grapheme
            
            # Check if it's a sound class (like V, C, S)
            class_features = get_class_features(grapheme)
            if class_features:
                self._fvalues = class_features
                self._partial = True  # Sound classes are partial by default
            else:
                # Regular grapheme
                grapheme_features = get_grapheme_features(grapheme)
                if grapheme_features:
                    self._fvalues = grapheme_features
                else:
                    # Unknown grapheme - store as is
                    self._fvalues = frozenset([grapheme])
        else:
            # Initialize from description
            self._fvalues = parse_features(description)
            self._grapheme = features_to_grapheme(self._fvalues)
    
    @property
    def fvalues(self) -> FrozenSet[str]:
        """Get the feature values of this sound."""
        return self._fvalues
    
    @property
    def partial(self) -> bool:
        """Check if this is a partial (underspecified) sound."""
        return self._partial
    
    def grapheme(self) -> str:
        """Get the graphemic representation of this sound."""
        return self._grapheme or features_to_grapheme(self._fvalues)
    
    def __str__(self) -> str:
        """String representation returns the grapheme."""
        return self.grapheme()
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"Sound('{self.grapheme()}', {sorted(self._fvalues)}, partial={self._partial})"
    
    def __eq__(self, other) -> bool:
        """
        Check equality with another Sound.
        
        Two sounds are equal if they have the same feature values
        and the same partial status.
        """
        if not isinstance(other, Sound):
            return False
        return (self._fvalues == other._fvalues and 
                self._partial == other._partial)
    
    def __hash__(self) -> int:
        """Hash based on feature values and partial status."""
        return hash((self._fvalues, self._partial))
    
    def __add__(self, features: Union[str, FrozenSet[str]]) -> 'Sound':
        """
        Add features to this sound, returning a new Sound.
        
        This implements feature arithmetic like: p + voiced = b
        
        Args:
            features: Either a string like 'voiced,long' or a feature set
            
        Returns:
            New Sound with added features
        """
        if isinstance(features, str):
            new_features = parse_features(features)
        else:
            new_features = features
        
        # Start with existing features
        combined_features = set(self._fvalues)
        
        # Add new features, handling oppositions
        for feature in new_features:
            if feature == 'voiced':
                combined_features.discard('voiceless')
                combined_features.add('voiced')
            elif feature == 'voiceless':
                combined_features.discard('voiced')
                combined_features.add('voiceless')
            elif feature.startswith('-'):
                # Negative feature - remove the positive version
                positive_feature = feature[1:]
                combined_features.discard(positive_feature)
            else:
                # Regular feature addition
                combined_features.add(feature)
        
        # Create new sound with combined features
        new_sound = Sound.__new__(Sound)
        new_sound._fvalues = frozenset(combined_features)
        new_sound._partial = self._partial
        new_sound._grapheme = features_to_grapheme(new_sound._fvalues)
        
        return new_sound
    
    def __ge__(self, other: 'Sound') -> bool:
        """
        Partial matching: check if this sound subsumes another.
        
        A partial sound (like [consonant]) matches a more specific sound
        (like [consonant, voiced, bilabial]) if all its features are present
        in the other sound.
        
        Args:
            other: Sound to check against
            
        Returns:
            True if this sound's features are a subset of other's features
        """
        if not isinstance(other, Sound):
            return False
        
        # If this is not partial, require exact match
        if not self._partial:
            return self._fvalues == other._fvalues
        
        # Partial matching: all our features must be in the other sound
        return self._fvalues.issubset(other._fvalues)
    
    def set_fvalues(self, features: str) -> None:
        """
        Set feature values from a string description.
        
        Args:
            features: Comma-separated feature string
        """
        self._fvalues = parse_features(features)
        self._grapheme = features_to_grapheme(self._fvalues)
    
    def add_fvalues(self, features: str) -> None:
        """
        Add feature values to this sound (in-place modification).
        
        Args:
            features: Comma-separated feature string to add
        """
        new_features = parse_features(features)
        self._fvalues = self._fvalues | new_features
        self._grapheme = features_to_grapheme(self._fvalues)
    
    def copy(self) -> 'Sound':
        """Create a copy of this sound."""
        new_sound = Sound.__new__(Sound)
        new_sound._fvalues = self._fvalues
        new_sound._partial = self._partial
        new_sound._grapheme = self._grapheme
        return new_sound