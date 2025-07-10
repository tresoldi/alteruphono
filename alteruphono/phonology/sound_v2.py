"""
Enhanced Sound class with pluggable feature system support.

This is the new Sound class that supports multiple feature systems
while maintaining backward compatibility with the existing API.
"""

from typing import FrozenSet, List, Optional, Union, TYPE_CHECKING
from .feature_systems import (
    FeatureBundle, 
    FeatureValue,
    FeatureValueType,
    get_feature_system,
    get_default_feature_system,
    DEFAULT_FEATURE_SYSTEM
)

if TYPE_CHECKING:
    from .feature_systems.base import FeatureSystem


class Sound:
    """
    Enhanced Sound class with pluggable feature system support.
    
    This class can work with different feature systems (IPA categorical,
    unified distinctive, etc.) while maintaining the same API for
    backward compatibility.
    """
    
    def __init__(
        self,
        grapheme: Optional[str] = None,
        description: Optional[str] = None,
        partial: Optional[bool] = None,
        feature_system: Optional[str] = None,
        features: Optional[FeatureBundle] = None
    ) -> None:
        """
        Initialize a Sound object.
        
        Args:
            grapheme: A grapheme like 'p', 'a', 'V' (sound class)
            description: Feature specification like 'voiced,bilabial' or '[voice=1.0,labial=0.8]'
            partial: Whether this is a partial/underspecified sound
            feature_system: Name of feature system to use (default: system default)
            features: Direct FeatureBundle (for internal use)
        """
        if sum(x is not None for x in [grapheme, description, features]) != 1:
            raise ValueError("Exactly one of grapheme, description, or features must be provided")
        
        # Get feature system
        if feature_system is not None:
            self._feature_system = get_feature_system(feature_system)
        else:
            self._feature_system = get_default_feature_system()
        
        self._feature_system_name = self._feature_system.name
        
        # Initialize features
        if features is not None:
            self._features = features
        elif grapheme is not None:
            self._features = self._feature_system.grapheme_to_features(grapheme)
            if self._features is None:
                raise ValueError(f"Unknown grapheme '{grapheme}' in feature system '{self._feature_system.name}'")
        else:  # description is not None
            self._features = self._feature_system.parse_feature_specification(description)
        
        # Set partial flag if specified
        if partial is not None:
            self._features = FeatureBundle(self._features.features, partial=partial)
        
        # Store original input for string representation
        self._original_grapheme = grapheme
        self._original_description = description
    
    @property
    def fvalues(self) -> FrozenSet[str]:
        """
        Get feature values as string set (backward compatibility).
        
        This converts the new FeatureBundle to the old string format
        for compatibility with existing code.
        """
        result = set()
        
        for fval in self._features.features:
            if fval.value_type == FeatureValueType.BINARY:
                prefix = '+' if fval.value else '-'
                result.add(f"{prefix}{fval.feature}")
            elif fval.value_type == FeatureValueType.CATEGORICAL:
                # For categorical features, the value is the feature name
                result.add(fval.value)
            elif fval.value_type == FeatureValueType.SCALAR:
                # For backward compatibility, convert scalar to categorical
                if abs(fval.value) > 0.5:  # Significant value
                    if fval.value > 0:
                        result.add(fval.feature)
                    else:
                        result.add(f"-{fval.feature}")
        
        return frozenset(result)
    
    @property
    def features(self) -> FeatureBundle:
        """Get the feature bundle (new API)."""
        return self._features
    
    @property
    def feature_system_name(self) -> str:
        """Get the name of the feature system used."""
        return self._feature_system_name
    
    @property
    def partial(self) -> bool:
        """Check if this is a partial sound."""
        return self._features.partial
    
    def grapheme(self) -> str:
        """Get the graphemic representation."""
        if self._original_grapheme is not None:
            return self._original_grapheme
        return self._feature_system.features_to_grapheme(self._features)
    
    def __str__(self) -> str:
        """String representation returns the grapheme."""
        return self.grapheme()
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"Sound('{self.grapheme()}', features={self._features}, system='{self._feature_system_name}')"
    
    def __eq__(self, other) -> bool:
        """
        Check equality with another Sound.
        
        Sounds are equal if they have compatible features and the same partial status.
        Cross-system comparison uses distance metrics.
        """
        if not isinstance(other, Sound):
            return False
        
        # Same system - direct comparison
        if self._feature_system_name == other._feature_system_name:
            return (self._features.features == other._features.features and
                    self._features.partial == other._features.partial)
        
        # Different systems - use distance
        try:
            distance = self._features.distance_to(other._features)
            return distance < 0.1  # Small threshold for "equality"
        except Exception:
            return False
    
    def __hash__(self) -> int:
        """Hash based on feature values and system."""
        return hash((self._features, self._feature_system_name))
    
    def __add__(self, features: Union[str, FeatureBundle]) -> 'Sound':
        """
        Add features to this sound, returning a new Sound.
        
        Args:
            features: Feature specification string or FeatureBundle
            
        Returns:
            New Sound with added features
        """
        if isinstance(features, str):
            additional_features = self._feature_system.parse_feature_specification(features)
        elif isinstance(features, FeatureBundle):
            additional_features = features
        else:
            raise ValueError(f"Cannot add features of type {type(features)}")
        
        # Use feature system's addition logic
        new_features = self._feature_system.add_features(self._features, additional_features)
        
        return Sound(
            features=new_features,
            feature_system=self._feature_system_name
        )
    
    def __ge__(self, other: 'Sound') -> bool:
        """
        Partial matching: check if this sound subsumes another.
        
        For partial sounds, checks if all features are present in other sound.
        For complete sounds, requires exact match.
        """
        if not isinstance(other, Sound):
            return False
        
        # Convert to same feature system if necessary
        if self._feature_system_name != other._feature_system_name:
            # This is complex - for now, fall back to string comparison
            return self.fvalues.issubset(other.fvalues)
        
        return self._features.matches(other._features)
    
    def set_fvalues(self, features: str) -> None:
        """
        Set feature values from a string description (backward compatibility).
        
        Args:
            features: Feature specification string
        """
        new_features = self._feature_system.parse_feature_specification(features)
        self._features = new_features
        # Clear cached grapheme
        self._original_grapheme = None
    
    def add_fvalues(self, features: str) -> None:
        """
        Add feature values to this sound (in-place modification).
        
        Args:
            features: Feature specification string to add
        """
        additional_features = self._feature_system.parse_feature_specification(features)
        self._features = self._feature_system.add_features(self._features, additional_features)
        # Clear cached grapheme
        self._original_grapheme = None
    
    def copy(self) -> 'Sound':
        """Create a copy of this sound."""
        return Sound(
            features=self._features,
            feature_system=self._feature_system_name
        )
    
    # New methods for enhanced functionality
    
    def distance_to(self, other: 'Sound') -> float:
        """
        Calculate phonological distance to another sound.
        
        Args:
            other: Sound to compare with
            
        Returns:
            Distance value (0.0 = identical, 1.0 = maximally different)
        """
        if not isinstance(other, Sound):
            raise ValueError("Can only calculate distance to another Sound")
        
        # Handle cross-system comparison
        if self._feature_system_name != other._feature_system_name:
            # Convert through grapheme representation (lossy but practical)
            try:
                other_converted = Sound(
                    grapheme=other.grapheme(),
                    feature_system=self._feature_system_name
                )
                return self._features.distance_to(other_converted._features)
            except Exception:
                return 1.0  # Maximum distance if conversion fails
        
        return self._features.distance_to(other._features)
    
    def get_feature_value(self, feature_name: str) -> Optional[Union[bool, str, float, int]]:
        """
        Get the value of a specific feature.
        
        Args:
            feature_name: Name of the feature
            
        Returns:
            Feature value or None if not present
        """
        fval = self._features.get_feature(feature_name)
        return fval.value if fval is not None else None
    
    def has_feature(self, feature_name: str) -> bool:
        """Check if this sound has a specific feature."""
        return self._features.has_feature(feature_name)
    
    def validate(self) -> List[str]:
        """
        Validate this sound according to feature system constraints.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        return self._feature_system.validate_features(self._features)
    
    def convert_to_system(self, target_system: str) -> 'Sound':
        """
        Convert this sound to a different feature system.
        
        Args:
            target_system: Name of target feature system
            
        Returns:
            New Sound in the target system
        """
        if target_system == self._feature_system_name:
            return self.copy()
        
        # Convert through grapheme (lossy but practical)
        try:
            grapheme = self.grapheme()
            return Sound(
                grapheme=grapheme,
                feature_system=target_system
            )
        except Exception:
            # Fallback to empty partial sound
            return Sound(
                description="",
                partial=True,
                feature_system=target_system
            )
    
    # Backward compatibility methods (suprasegmental features)
    
    def has_stress(self) -> bool:
        """Check if this sound has any stress marking."""
        return any(f.feature.startswith('stress') and f.value for f in self._features.features)
    
    def has_tone(self) -> bool:
        """Check if this sound has any tone marking."""
        tone_features = {'tone', 'rising', 'falling', 'level'}
        return any((f.feature.startswith('tone') or f.feature in tone_features) and f.value 
                  for f in self._features.features)
    
    def get_stress_level(self) -> int:
        """Get stress level (0=unstressed, 1=primary, 2=secondary)."""
        if self._feature_system_name == 'unified_distinctive':
            # For unified system, use stress feature value
            stress_val = self.get_feature_value('stress')
            if stress_val is not None and isinstance(stress_val, (int, float)):
                if stress_val > 0.7:
                    return 1  # Primary stress
                elif stress_val > 0.3:
                    return 2  # Secondary stress
                else:
                    return 0  # Unstressed
        else:
            # For categorical system
            if self.has_feature('stress1'):
                return 1
            elif self.has_feature('stress2'):
                return 2
        return 0
    
    def get_tone_value(self) -> int:
        """Get tone value (1-5), or 0 if no tone."""
        for f in self._features.features:
            if f.feature.startswith('tone') and len(f.feature) > 4:
                try:
                    return int(f.feature[4:])
                except ValueError:
                    pass
        return 0
    
    def increment_feature(self, feature_type: str, amount: Union[int, float] = 1) -> 'Sound':
        """
        Increment a numeric feature by the given amount.
        
        Args:
            feature_type: The feature type to increment
            amount: Amount to increment by
            
        Returns:
            New Sound with incremented feature
        """
        if self._feature_system_name == 'unified_distinctive':
            # For unified system, direct scalar arithmetic
            current_val = self.get_feature_value(feature_type) or 0.0
            new_val = max(-1.0, min(1.0, current_val + float(amount)))
            
            new_fval = FeatureValue(
                feature=feature_type,
                value=new_val,
                value_type=FeatureValueType.SCALAR
            )
            new_features = self._features.add_feature(new_fval)
            
            return Sound(features=new_features, feature_system=self._feature_system_name)
        else:
            # For categorical system, use legacy logic
            return self + f"{feature_type}_{int(amount)}"
    
    def decrement_feature(self, feature_type: str, amount: Union[int, float] = 1) -> 'Sound':
        """Decrement a numeric feature by the given amount."""
        return self.increment_feature(feature_type, -amount)
    
    def get_suprasegmental_features(self) -> FrozenSet[str]:
        """Get only the suprasegmental features (backward compatibility)."""
        result = set()
        for f in self._features.features:
            if self._feature_system.is_suprasegmental_feature(f.feature):
                if f.value_type == FeatureValueType.CATEGORICAL:
                    result.add(f.value)
                elif f.value_type == FeatureValueType.SCALAR and abs(f.value) > 0.5:
                    result.add(f.feature)
        return frozenset(result)
    
    def get_segmental_features(self) -> FrozenSet[str]:
        """Get only the segmental features (backward compatibility)."""
        result = set()
        for f in self._features.features:
            if not self._feature_system.is_suprasegmental_feature(f.feature):
                if f.value_type == FeatureValueType.CATEGORICAL:
                    result.add(f.value)
                elif f.value_type == FeatureValueType.SCALAR and abs(f.value) > 0.5:
                    result.add(f.feature)
        return frozenset(result)