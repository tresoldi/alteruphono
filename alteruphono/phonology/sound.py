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
    normalize_feature,
    is_suprasegmental_feature,
    is_numeric_feature,
    get_numeric_value,
    increment_numeric_feature,
    decrement_numeric_feature
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
        Also supports suprasegmental and numeric features.
        
        Args:
            features: Either a string like 'voiced,long' or a feature set
            
        Returns:
            New Sound with added features
        """
        if isinstance(features, str):
            new_features = parse_features(features)
        elif features is None:
            new_features = frozenset()
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
            elif feature == 'fricative':
                # Fricative opposes stop, affricate, nasal, etc.
                combined_features.discard('stop')
                combined_features.discard('affricate')
                combined_features.discard('nasal')
                combined_features.discard('lateral')
                combined_features.discard('rhotic')
                combined_features.discard('approximant')
                combined_features.add('fricative')
            elif feature == 'stop':
                # Stop opposes fricative, nasal, etc.
                combined_features.discard('fricative')
                combined_features.discard('affricate')
                combined_features.discard('nasal')
                combined_features.discard('lateral')
                combined_features.discard('rhotic')
                combined_features.discard('approximant')
                combined_features.add('stop')
            elif feature == 'nasal':
                # Nasal opposes other manner features
                combined_features.discard('stop')
                combined_features.discard('fricative')
                combined_features.discard('affricate')
                combined_features.discard('lateral')
                combined_features.discard('rhotic')
                combined_features.discard('approximant')
                combined_features.add('nasal')
            elif feature.startswith('stress'):
                # Remove other stress features when adding new one
                combined_features = {f for f in combined_features if not f.startswith('stress') and f != 'unstressed'}
                combined_features.add(feature)
            elif feature == 'unstressed':
                # Remove stress features when making unstressed
                combined_features = {f for f in combined_features if not f.startswith('stress')}
                combined_features.add('unstressed')
            elif feature.startswith('tone'):
                # Remove other tone features when adding new one
                combined_features = {f for f in combined_features if not (f.startswith('tone') or f in ['rising', 'falling', 'level'])}
                combined_features.add(feature)
            elif feature in ['rising', 'falling', 'level']:
                # Tone contour features - remove conflicting ones
                combined_features.discard('rising')
                combined_features.discard('falling') 
                combined_features.discard('level')
                combined_features.add(feature)
            elif is_numeric_feature(feature):
                # Handle numeric features - replace similar ones
                prefix = feature.split('_')[0] if '_' in feature else feature.rstrip('0123456789')
                combined_features = {f for f in combined_features if not f.startswith(prefix)}
                combined_features.add(feature)
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
        
        # If original was a sound class, preserve that nature
        if self._grapheme and len(self._grapheme) == 1 and get_class_features(self._grapheme):
            # This was a sound class like S, V, C - keep it as such
            new_sound._grapheme = self._grapheme
        else:
            # Regular grapheme - find best match
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
        # Use the same logic as __add__ but modify in place
        new_sound = self + features
        self._fvalues = new_sound._fvalues
        self._grapheme = new_sound._grapheme
    
    def copy(self) -> 'Sound':
        """Create a copy of this sound."""
        new_sound = Sound.__new__(Sound)
        new_sound._fvalues = self._fvalues
        new_sound._partial = self._partial
        new_sound._grapheme = self._grapheme
        return new_sound
    
    def increment_feature(self, feature_type: str, amount: int = 1) -> 'Sound':
        """
        Increment a numeric feature by the given amount.
        
        Args:
            feature_type: The feature type to increment (e.g., 'tone', 'f0', 'duration')
            amount: Amount to increment by (default 1)
            
        Returns:
            New Sound with incremented feature
        """
        new_sound = self.copy()
        combined_features = set(new_sound._fvalues)
        
        # Find existing feature of this type
        for feature in list(combined_features):
            if feature.startswith(feature_type):
                combined_features.remove(feature)
                new_feature = increment_numeric_feature(feature, amount)
                combined_features.add(new_feature)
                break
        else:
            # No existing feature, add the base one
            if feature_type in ['tone', 'f0', 'duration']:
                combined_features.add(f"{feature_type}_{amount}")
        
        new_sound._fvalues = frozenset(combined_features)
        return new_sound
    
    def decrement_feature(self, feature_type: str, amount: int = 1) -> 'Sound':
        """
        Decrement a numeric feature by the given amount.
        
        Args:
            feature_type: The feature type to decrement (e.g., 'tone', 'f0', 'duration')
            amount: Amount to decrement by (default 1)
            
        Returns:
            New Sound with decremented feature
        """
        return self.increment_feature(feature_type, -amount)
    
    def get_suprasegmental_features(self) -> FrozenSet[str]:
        """Get only the suprasegmental features of this sound."""
        return frozenset(f for f in self._fvalues if is_suprasegmental_feature(f))
    
    def get_segmental_features(self) -> FrozenSet[str]:
        """Get only the segmental (non-suprasegmental) features of this sound."""
        return frozenset(f for f in self._fvalues if not is_suprasegmental_feature(f))
    
    def has_stress(self) -> bool:
        """Check if this sound has any stress marking."""
        return any(f.startswith('stress') for f in self._fvalues)
    
    def has_tone(self) -> bool:
        """Check if this sound has any tone marking."""
        return any(f.startswith('tone') or f in ['rising', 'falling', 'level'] for f in self._fvalues)
    
    def get_stress_level(self) -> int:
        """Get the stress level (0=unstressed, 1=primary, 2=secondary)."""
        if 'stress1' in self._fvalues:
            return 1
        elif 'stress2' in self._fvalues:
            return 2
        else:
            return 0
    
    def get_tone_value(self) -> int:
        """Get the tone value (1-5), or 0 if no tone."""
        for feature in self._fvalues:
            if feature.startswith('tone') and len(feature) > 4:
                return get_numeric_value(feature)
        return 0