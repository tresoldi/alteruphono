"""
Base classes for the pluggable feature system architecture.

This module defines the abstract interfaces that all feature systems must implement,
providing a common API for different phonological theories and representations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, FrozenSet, List, Optional, Set, Union, Tuple
from dataclasses import dataclass
from enum import Enum


class FeatureValueType(Enum):
    """Types of feature values supported by the system."""
    BINARY = "binary"           # Traditional +/- features
    CATEGORICAL = "categorical"  # Named categories (e.g., 'bilabial', 'alveolar')
    SCALAR = "scalar"           # Continuous values (e.g., -1.0 to +1.0)
    ORDINAL = "ordinal"         # Ordered discrete values (e.g., 1, 2, 3, 4, 5)


@dataclass(frozen=True)
class FeatureValue:
    """
    Represents a single feature value in any feature system.
    
    This is the atomic unit of phonological features, supporting different
    value types and operations.
    """
    feature: str                    # Feature name (e.g., 'voiced', 'height', 'place')
    value: Any                      # The actual value (bool, str, float, int, etc.)
    value_type: FeatureValueType    # Type of the value
    
    def __post_init__(self):
        """Validate value type consistency."""
        if self.value_type == FeatureValueType.BINARY and not isinstance(self.value, bool):
            raise ValueError(f"Binary feature {self.feature} must have boolean value, got {type(self.value)}")
        elif self.value_type == FeatureValueType.CATEGORICAL and not isinstance(self.value, str):
            raise ValueError(f"Categorical feature {self.feature} must have string value, got {type(self.value)}")
        elif self.value_type == FeatureValueType.SCALAR and not isinstance(self.value, (int, float)):
            raise ValueError(f"Scalar feature {self.feature} must have numeric value, got {type(self.value)}")
        elif self.value_type == FeatureValueType.ORDINAL and not isinstance(self.value, int):
            raise ValueError(f"Ordinal feature {self.feature} must have integer value, got {type(self.value)}")
    
    def __str__(self) -> str:
        """String representation for display."""
        if self.value_type == FeatureValueType.BINARY:
            return f"{'+' if self.value else '-'}{self.feature}"
        elif self.value_type == FeatureValueType.SCALAR:
            return f"{self.feature}={self.value:.2f}"
        else:
            return f"{self.feature}={self.value}"
    
    def is_compatible_with(self, other: 'FeatureValue') -> bool:
        """Check if this feature value can coexist with another."""
        return (self.feature != other.feature or 
                self.value == other.value)
    
    def distance_to(self, other: 'FeatureValue') -> float:
        """Calculate distance to another feature value (0.0 = identical, 1.0 = maximally different)."""
        if self.feature != other.feature:
            raise ValueError(f"Cannot compare different features: {self.feature} vs {other.feature}")
        
        if self.value_type != other.value_type:
            raise ValueError(f"Cannot compare different value types: {self.value_type} vs {other.value_type}")
        
        if self.value_type == FeatureValueType.BINARY:
            return 0.0 if self.value == other.value else 1.0
        elif self.value_type == FeatureValueType.CATEGORICAL:
            return 0.0 if self.value == other.value else 1.0
        elif self.value_type == FeatureValueType.SCALAR:
            # Assume scalar values are normalized to [-1, 1] or [0, 1]
            return abs(float(self.value) - float(other.value)) / 2.0
        elif self.value_type == FeatureValueType.ORDINAL:
            # Assume ordinal values have a meaningful scale
            max_val = max(self.value, other.value, 5)  # Assume max 5 unless higher values present
            return abs(self.value - other.value) / max_val
        
        return 1.0  # Default to maximally different


@dataclass(frozen=True)
class FeatureBundle:
    """
    A collection of feature values representing a complete phonological description.
    
    This replaces the simple frozenset[str] approach with a more structured
    representation that can handle different feature types and values.
    """
    features: FrozenSet[FeatureValue]
    partial: bool = False  # Whether this is a partial/underspecified bundle
    
    def __post_init__(self):
        """Validate feature bundle consistency and build optimization caches."""
        # Check for conflicting features (same feature name, different values)
        feature_names = {}
        for fval in self.features:
            if fval.feature in feature_names:
                existing = feature_names[fval.feature]
                if not fval.is_compatible_with(existing):
                    raise ValueError(f"Conflicting values for feature {fval.feature}: {existing.value} vs {fval.value}")
            feature_names[fval.feature] = fval
        
        # Build optimization caches
        object.__setattr__(self, '_feature_dict', feature_names)
        object.__setattr__(self, '_feature_names', frozenset(feature_names.keys()))
    
    def get_feature(self, feature_name: str) -> Optional[FeatureValue]:
        """Get a specific feature value by name."""
        return getattr(self, '_feature_dict', {}).get(feature_name)
    
    def has_feature(self, feature_name: str) -> bool:
        """Check if bundle contains a specific feature."""
        return feature_name in getattr(self, '_feature_names', set())
    
    def add_feature(self, feature_value: FeatureValue) -> 'FeatureBundle':
        """Add or replace a feature value, returning new bundle."""
        new_features = set()
        found = False
        
        for fval in self.features:
            if fval.feature == feature_value.feature:
                new_features.add(feature_value)  # Replace existing
                found = True
            else:
                new_features.add(fval)
        
        if not found:
            new_features.add(feature_value)  # Add new
        
        return FeatureBundle(frozenset(new_features), self.partial)
    
    def remove_feature(self, feature_name: str) -> 'FeatureBundle':
        """Remove a feature, returning new bundle."""
        new_features = {fval for fval in self.features if fval.feature != feature_name}
        return FeatureBundle(frozenset(new_features), self.partial)
    
    def merge_with(self, other: 'FeatureBundle') -> 'FeatureBundle':
        """Merge with another bundle, other's values take precedence."""
        result_features = set(self.features)
        
        for other_fval in other.features:
            # Remove any existing feature with same name
            result_features = {fval for fval in result_features if fval.feature != other_fval.feature}
            # Add the new feature value
            result_features.add(other_fval)
        
        return FeatureBundle(frozenset(result_features), self.partial or other.partial)
    
    def matches(self, other: 'FeatureBundle') -> bool:
        """
        Check if this bundle matches another (for pattern matching).
        
        For partial bundles, all features must be present in other.
        For complete bundles, all features must match exactly.
        """
        if self.partial:
            # Partial matching: all our features must be in other
            for self_fval in self.features:
                other_fval = other.get_feature(self_fval.feature)
                if other_fval is None or other_fval.value != self_fval.value:
                    return False
            return True
        else:
            # Exact matching: same feature sets
            return self.features == other.features
    
    def distance_to(self, other: 'FeatureBundle') -> float:
        """Calculate phonological distance to another bundle."""
        # Get all feature names from both bundles
        all_features = {fval.feature for fval in self.features} | {fval.feature for fval in other.features}
        
        total_distance = 0.0
        compared_features = 0
        
        for feature_name in all_features:
            self_fval = self.get_feature(feature_name)
            other_fval = other.get_feature(feature_name)
            
            if self_fval is None or other_fval is None:
                # Missing feature - treat as maximal distance
                total_distance += 1.0
            else:
                # Both have feature - calculate distance
                total_distance += self_fval.distance_to(other_fval)
            
            compared_features += 1
        
        return total_distance / compared_features if compared_features > 0 else 0.0
    
    def __str__(self) -> str:
        """String representation for display."""
        feature_strs = sorted(str(fval) for fval in self.features)
        result = "[" + ",".join(feature_strs) + "]"
        if self.partial:
            result += "?"
        return result


class FeatureSystem(ABC):
    """
    Abstract base class for all feature systems.
    
    A feature system defines:
    1. How graphemes map to feature bundles
    2. How feature arithmetic works
    3. How features are parsed and serialized
    4. What constraints and validations apply
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this feature system."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of this feature system."""
        pass
    
    @property
    @abstractmethod
    def supported_value_types(self) -> Set[FeatureValueType]:
        """Set of feature value types supported by this system."""
        pass
    
    @abstractmethod
    def grapheme_to_features(self, grapheme: str) -> Optional[FeatureBundle]:
        """Convert a grapheme to its feature representation."""
        pass
    
    @abstractmethod
    def features_to_grapheme(self, features: FeatureBundle) -> str:
        """Convert features back to best-matching grapheme."""
        pass
    
    @abstractmethod
    def parse_feature_specification(self, spec: str) -> FeatureBundle:
        """Parse a feature specification string (e.g., '[voiced,bilabial]')."""
        pass
    
    @abstractmethod
    def get_sound_class_features(self, sound_class: str) -> Optional[FeatureBundle]:
        """Get features for a sound class (e.g., 'V', 'C', 'S')."""
        pass
    
    @abstractmethod
    def add_features(self, base: FeatureBundle, additional: FeatureBundle) -> FeatureBundle:
        """
        Add features to a base bundle (feature arithmetic).
        
        This implements system-specific rules for feature combination,
        including handling of conflicts and constraints.
        """
        pass
    
    @abstractmethod
    def validate_features(self, features: FeatureBundle) -> List[str]:
        """
        Validate a feature bundle according to system constraints.
        
        Returns list of validation error messages (empty if valid).
        """
        pass
    
    def normalize_feature_name(self, feature: str) -> str:
        """Normalize a feature name to standard form (default: identity)."""
        return feature
    
    def is_suprasegmental_feature(self, feature_name: str) -> bool:
        """Check if a feature is suprasegmental (default: check common patterns)."""
        suprasegmental_patterns = ['stress', 'tone', 'f0_', 'duration_', 'pitch', 'length']
        return any(feature_name.startswith(pattern) for pattern in suprasegmental_patterns)
    
    def create_partial_bundle(self, features: Set[FeatureValue]) -> FeatureBundle:
        """Create a partial feature bundle for pattern matching."""
        return FeatureBundle(frozenset(features), partial=True)
    
    def create_complete_bundle(self, features: Set[FeatureValue]) -> FeatureBundle:
        """Create a complete feature bundle for a specific sound."""
        return FeatureBundle(frozenset(features), partial=False)


class FeatureSystemRegistry:
    """
    Registry for managing multiple feature systems.
    
    Allows registration, retrieval, and switching between different
    phonological feature systems.
    """
    
    def __init__(self):
        self._systems: Dict[str, FeatureSystem] = {}
        self._default_system: Optional[str] = None
    
    def register(self, system: FeatureSystem) -> None:
        """Register a new feature system."""
        if system.name in self._systems:
            raise ValueError(f"Feature system '{system.name}' already registered")
        
        self._systems[system.name] = system
        
        # Set as default if it's the first system
        if self._default_system is None:
            self._default_system = system.name
    
    def get(self, name: str) -> FeatureSystem:
        """Get a feature system by name."""
        if name not in self._systems:
            available = ", ".join(self._systems.keys())
            raise ValueError(f"Unknown feature system '{name}'. Available: {available}")
        
        return self._systems[name]
    
    def list_systems(self) -> List[str]:
        """Get list of all registered system names."""
        return list(self._systems.keys())
    
    def get_default(self) -> FeatureSystem:
        """Get the default feature system."""
        if self._default_system is None:
            raise ValueError("No default feature system set")
        
        return self.get(self._default_system)
    
    def set_default(self, name: str) -> None:
        """Set the default feature system."""
        if name not in self._systems:
            raise ValueError(f"Cannot set unknown system '{name}' as default")
        
        self._default_system = name
    
    def convert_between_systems(self, 
                               bundle: FeatureBundle, 
                               from_system: str, 
                               to_system: str) -> FeatureBundle:
        """
        Convert a feature bundle between systems (best-effort).
        
        This is a complex operation that may not always be possible
        or may result in information loss.
        """
        from_sys = self.get(from_system)
        to_sys = self.get(to_system)
        
        # Strategy 1: Convert through grapheme representation
        try:
            grapheme = from_sys.features_to_grapheme(bundle)
            converted = to_sys.grapheme_to_features(grapheme)
            if converted is not None:
                return converted
        except Exception:
            pass
        
        # Strategy 2: Direct feature mapping (system-specific)
        # This would need to be implemented by systems that support conversion
        
        # Fallback: Return empty bundle
        return FeatureBundle(frozenset(), partial=True)


# Global registry instance
_registry = FeatureSystemRegistry()


def get_registry() -> FeatureSystemRegistry:
    """Get the global feature system registry."""
    return _registry