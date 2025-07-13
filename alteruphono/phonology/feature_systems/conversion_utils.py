"""
Enhanced feature system conversion utilities.

This module provides sophisticated conversion between different feature systems,
including direct feature mapping and compatibility analysis.
"""

from typing import Dict, List, Optional, Set, Tuple
from .base import FeatureSystem, FeatureBundle, FeatureValue, FeatureValueType
from .registry import get_registry


class FeatureSystemConverter:
    """
    Advanced converter between feature systems with intelligent mapping.
    """
    
    def __init__(self):
        self._conversion_cache = {}
        self._compatibility_cache = {}
    
    def convert_bundle(self, 
                      bundle: FeatureBundle, 
                      from_system: str, 
                      to_system: str) -> FeatureBundle:
        """
        Convert a feature bundle between systems with multiple strategies.
        """
        cache_key = (frozenset(bundle.features), from_system, to_system)
        if cache_key in self._conversion_cache:
            return self._conversion_cache[cache_key]
        
        registry = get_registry()
        from_sys = registry.get(from_system)
        to_sys = registry.get(to_system)
        
        # Strategy 1: Direct feature mapping for compatible features
        result = self._convert_by_feature_mapping(bundle, from_sys, to_sys)
        
        if not result.partial or len(result.features) == 0:
            # Strategy 2: Grapheme-based conversion
            grapheme_result = self._convert_by_grapheme(bundle, from_sys, to_sys)
            if len(grapheme_result.features) > len(result.features):
                result = grapheme_result
        
        # Cache the result
        self._conversion_cache[cache_key] = result
        return result
    
    def _convert_by_feature_mapping(self, 
                                   bundle: FeatureBundle, 
                                   from_sys: FeatureSystem, 
                                   to_sys: FeatureSystem) -> FeatureBundle:
        """Convert by mapping common features between systems."""
        # Get actual feature overlap by testing a common sound
        common_features = self._get_actual_feature_overlap(from_sys, to_sys)
        
        # Convert compatible features
        converted_features = set()
        for fval in bundle.features:
            if fval.feature in common_features:
                # Check if both systems support the same value type
                if self._are_feature_types_compatible(from_sys, to_sys, fval.feature):
                    converted_features.add(fval)
        
        return FeatureBundle(frozenset(converted_features), 
                           partial=len(converted_features) < len(bundle.features))
    
    def _get_actual_feature_overlap(self, from_sys: FeatureSystem, to_sys: FeatureSystem) -> Set[str]:
        """Get actual feature overlap by testing with common sounds."""
        # Test with common sounds to find actual feature overlap
        test_sounds = ['p', 'a', 't', 'i', 'k', 'n', 'm']
        overlapping_features = set()
        
        for sound in test_sounds:
            try:
                from_features = from_sys.grapheme_to_features(sound)
                to_features = to_sys.grapheme_to_features(sound)
                
                if from_features and to_features:
                    from_names = {f.feature for f in from_features.features}
                    to_names = {f.feature for f in to_features.features}
                    overlapping_features.update(from_names & to_names)
            except (ValueError, KeyError, AttributeError) as e:
                # Feature system doesn't support this sound or conversion failed
                continue
        
        return overlapping_features
    
    def _convert_by_grapheme(self, 
                           bundle: FeatureBundle, 
                           from_sys: FeatureSystem, 
                           to_sys: FeatureSystem) -> FeatureBundle:
        """Convert through grapheme representation."""
        try:
            grapheme = from_sys.features_to_grapheme(bundle)
            converted = to_sys.grapheme_to_features(grapheme)
            if converted is not None:
                return converted
        except Exception:
            pass
        
        return FeatureBundle(frozenset(), partial=True)
    
    def _are_feature_types_compatible(self, 
                                    from_sys: FeatureSystem, 
                                    to_sys: FeatureSystem, 
                                    feature_name: str) -> bool:
        """Check if a feature has compatible types between systems."""
        # For now, assume scalar features are compatible between systems
        # This could be enhanced with more sophisticated type checking
        from_types = from_sys.supported_value_types
        to_types = to_sys.supported_value_types
        
        # If both support scalar, they're compatible
        if FeatureValueType.SCALAR in from_types and FeatureValueType.SCALAR in to_types:
            return True
        
        # If both support binary, they're compatible
        if FeatureValueType.BINARY in from_types and FeatureValueType.BINARY in to_types:
            return True
        
        return False
    
    def get_compatibility_matrix(self) -> Dict[Tuple[str, str], Dict[str, any]]:
        """
        Get compatibility matrix between all registered systems.
        """
        registry = get_registry()
        systems = registry.list_systems()
        matrix = {}
        
        for from_system in systems:
            for to_system in systems:
                if from_system != to_system:
                    compatibility = self._analyze_system_compatibility(from_system, to_system)
                    matrix[(from_system, to_system)] = compatibility
        
        return matrix
    
    def _analyze_system_compatibility(self, from_system: str, to_system: str) -> Dict[str, any]:
        """Analyze compatibility between two specific systems."""
        registry = get_registry()
        from_sys = registry.get(from_system)
        to_sys = registry.get(to_system)
        
        # Get feature sets if available
        from_features = set()
        to_features = set()
        
        try:
            from_features = set(from_sys.get_feature_names())
        except (AttributeError, NotImplementedError) as e:
            # Feature system doesn't support get_feature_names method
            pass
        
        try:
            to_features = set(to_sys.get_feature_names())
        except (AttributeError, NotImplementedError) as e:
            # Feature system doesn't support get_feature_names method
            pass
        
        common_features = from_features & to_features
        from_only = from_features - to_features
        to_only = to_features - from_features
        
        # Calculate compatibility score
        total_features = len(from_features | to_features)
        compatibility_score = len(common_features) / total_features if total_features > 0 else 0
        
        return {
            'common_features': list(common_features),
            'from_only_features': list(from_only),
            'to_only_features': list(to_only),
            'compatibility_score': compatibility_score,
            'from_system_size': len(from_features),
            'to_system_size': len(to_features),
            'conversion_strategy': 'feature_mapping' if compatibility_score > 0.5 else 'grapheme_based'
        }
    
    def convert_sound_cross_system(self, 
                                  grapheme: str, 
                                  from_system: str, 
                                  to_system: str) -> Optional[FeatureBundle]:
        """
        Convert a sound from one system to another by grapheme.
        """
        registry = get_registry()
        from_sys = registry.get(from_system)
        
        # Get features in source system
        source_features = from_sys.grapheme_to_features(grapheme)
        if source_features is None:
            return None
        
        # Convert to target system
        return self.convert_bundle(source_features, from_system, to_system)


# Global converter instance
_converter = FeatureSystemConverter()


def convert_between_systems(bundle: FeatureBundle, 
                          from_system: str, 
                          to_system: str) -> FeatureBundle:
    """Convert a feature bundle between systems (convenience function)."""
    return _converter.convert_bundle(bundle, from_system, to_system)


def get_system_compatibility_matrix() -> Dict[Tuple[str, str], Dict[str, any]]:
    """Get compatibility matrix between all systems (convenience function)."""
    return _converter.get_compatibility_matrix()


def convert_sound_between_systems(grapheme: str, 
                                from_system: str, 
                                to_system: str) -> Optional[FeatureBundle]:
    """Convert a sound between systems (convenience function)."""
    return _converter.convert_sound_cross_system(grapheme, from_system, to_system)


def analyze_conversion_quality(grapheme: str, systems: List[str]) -> Dict[str, any]:
    """
    Analyze how well a sound converts between different systems.
    """
    results = {}
    
    for i, from_system in enumerate(systems):
        for j, to_system in enumerate(systems):
            if i != j:
                key = f"{from_system}→{to_system}"
                
                try:
                    # Get original features
                    registry = get_registry()
                    from_sys = registry.get(from_system)
                    original = from_sys.grapheme_to_features(grapheme)
                    
                    if original is None:
                        results[key] = {'status': 'source_not_found'}
                        continue
                    
                    # Convert
                    converted = convert_between_systems(original, from_system, to_system)
                    
                    # Analyze quality
                    results[key] = {
                        'status': 'success',
                        'partial': converted.partial,
                        'original_features': len(original.features),
                        'converted_features': len(converted.features),
                        'feature_retention': len(converted.features) / len(original.features) if len(original.features) > 0 else 0,
                        'features_lost': len(original.features) - len(converted.features)
                    }
                
                except Exception as e:
                    results[key] = {'status': 'error', 'error': str(e)}
    
    return results