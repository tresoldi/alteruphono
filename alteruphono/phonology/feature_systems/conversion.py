"""
Feature system conversion utilities.

This module provides utilities for converting between different feature systems,
managing feature system contexts, and providing backward compatibility.
"""

from typing import Dict, List, Optional, Set, Union
from contextlib import contextmanager
from .base import FeatureBundle, FeatureValue, FeatureValueType
from .registry import get_feature_system, get_default_feature_system, set_default_feature_system


class FeatureSystemConverter:
    """
    Handles conversion between different feature systems.
    
    This class implements various strategies for converting sounds and
    feature bundles between different phonological representations.
    """
    
    def __init__(self):
        self._conversion_cache: Dict[str, Dict[str, FeatureBundle]] = {}
    
    def convert_sound(self, 
                     from_system: str, 
                     to_system: str, 
                     features: FeatureBundle) -> FeatureBundle:
        """
        Convert a sound from one feature system to another.
        
        Args:
            from_system: Source feature system name
            to_system: Target feature system name  
            features: Features to convert
            
        Returns:
            Converted feature bundle
        """
        if from_system == to_system:
            return features
        
        # Check cache first
        cache_key = f"{from_system}->{to_system}"
        feature_hash = str(hash(features))
        
        if cache_key in self._conversion_cache:
            if feature_hash in self._conversion_cache[cache_key]:
                return self._conversion_cache[cache_key][feature_hash]
        
        # Perform conversion
        from_sys = get_feature_system(from_system)
        to_sys = get_feature_system(to_system)
        
        converted = self._convert_via_grapheme(from_sys, to_sys, features)
        if converted is None:
            converted = self._convert_via_mapping(from_sys, to_sys, features)
        if converted is None:
            converted = FeatureBundle(frozenset(), partial=True)
        
        # Cache result
        if cache_key not in self._conversion_cache:
            self._conversion_cache[cache_key] = {}
        self._conversion_cache[cache_key][feature_hash] = converted
        
        return converted
    
    def _convert_via_grapheme(self, from_sys, to_sys, features: FeatureBundle) -> Optional[FeatureBundle]:
        """Convert by finding grapheme representation and re-parsing."""
        try:
            # Get grapheme from source system
            grapheme = from_sys.features_to_grapheme(features)
            if grapheme == '?':
                return None
            
            # Parse in target system
            converted = to_sys.grapheme_to_features(grapheme)
            return converted
        except Exception:
            return None
    
    def _convert_via_mapping(self, from_sys, to_sys, features: FeatureBundle) -> Optional[FeatureBundle]:
        """Convert using direct feature mapping (system-specific)."""
        # This would be implemented by feature systems that support direct conversion
        # For now, return None to indicate no direct mapping available
        return None
    
    def convert_ipa_to_unified(self, ipa_features: FeatureBundle) -> FeatureBundle:
        """
        Specialized conversion from IPA categorical to unified distinctive.
        
        This implements knowledge-based conversion rules for better accuracy.
        """
        # Get IPA string features for analysis
        from .ipa_categorical import IPACategoricalSystem
        ipa_sys = IPACategoricalSystem()
        string_features = ipa_sys._bundle_to_string_features(ipa_features)
        
        # Build unified feature values
        unified_features = set()
        
        # Major class features
        if 'vowel' in string_features:
            unified_features.add(FeatureValue('sonorant', 1.0, FeatureValueType.SCALAR))
            unified_features.add(FeatureValue('consonantal', -1.0, FeatureValueType.SCALAR))
            unified_features.add(FeatureValue('continuant', 1.0, FeatureValueType.SCALAR))
        elif 'consonant' in string_features:
            if 'stop' in string_features:
                unified_features.add(FeatureValue('sonorant', -0.9, FeatureValueType.SCALAR))
                unified_features.add(FeatureValue('consonantal', 1.0, FeatureValueType.SCALAR))
                unified_features.add(FeatureValue('continuant', -1.0, FeatureValueType.SCALAR))
            elif 'fricative' in string_features:
                unified_features.add(FeatureValue('sonorant', -0.8, FeatureValueType.SCALAR))
                unified_features.add(FeatureValue('consonantal', 0.8, FeatureValueType.SCALAR))
                unified_features.add(FeatureValue('continuant', 0.5, FeatureValueType.SCALAR))
            elif 'nasal' in string_features:
                unified_features.add(FeatureValue('sonorant', 0.8, FeatureValueType.SCALAR))
                unified_features.add(FeatureValue('consonantal', 0.9, FeatureValueType.SCALAR))
                unified_features.add(FeatureValue('nasal', 1.0, FeatureValueType.SCALAR))
        
        # Place features
        if 'bilabial' in string_features:
            unified_features.add(FeatureValue('labial', 1.0, FeatureValueType.SCALAR))
        elif 'alveolar' in string_features:
            unified_features.add(FeatureValue('coronal', 1.0, FeatureValueType.SCALAR))
            unified_features.add(FeatureValue('anterior', 1.0, FeatureValueType.SCALAR))
        elif 'velar' in string_features:
            unified_features.add(FeatureValue('dorsal', 1.0, FeatureValueType.SCALAR))
            unified_features.add(FeatureValue('high', 0.7, FeatureValueType.SCALAR))
        
        # Voicing
        if 'voiced' in string_features:
            unified_features.add(FeatureValue('voice', 1.0, FeatureValueType.SCALAR))
        elif 'voiceless' in string_features:
            unified_features.add(FeatureValue('voice', -1.0, FeatureValueType.SCALAR))
        
        # Vowel features
        if 'high' in string_features:
            unified_features.add(FeatureValue('high', 1.0, FeatureValueType.SCALAR))
        elif 'low' in string_features:
            unified_features.add(FeatureValue('low', 1.0, FeatureValueType.SCALAR))
        
        if 'front' in string_features:
            unified_features.add(FeatureValue('back', -1.0, FeatureValueType.SCALAR))
        elif 'back' in string_features:
            unified_features.add(FeatureValue('back', 1.0, FeatureValueType.SCALAR))
        elif 'central' in string_features:
            unified_features.add(FeatureValue('back', 0.0, FeatureValueType.SCALAR))
        
        if 'rounded' in string_features:
            unified_features.add(FeatureValue('round', 1.0, FeatureValueType.SCALAR))
        elif 'unrounded' in string_features:
            unified_features.add(FeatureValue('round', -1.0, FeatureValueType.SCALAR))
        
        # Suprasegmental features
        if 'stress1' in string_features:
            unified_features.add(FeatureValue('stress', 1.0, FeatureValueType.SCALAR))
        elif 'stress2' in string_features:
            unified_features.add(FeatureValue('stress', 0.5, FeatureValueType.SCALAR))
        elif 'unstressed' in string_features:
            unified_features.add(FeatureValue('stress', -1.0, FeatureValueType.SCALAR))
        
        # Tone features
        for feature in string_features:
            if feature.startswith('tone'):
                if feature == 'tone1':
                    unified_features.add(FeatureValue('tone', 1.0, FeatureValueType.SCALAR))
                elif feature == 'tone2':
                    unified_features.add(FeatureValue('tone', 0.5, FeatureValueType.SCALAR))
                elif feature == 'tone3':
                    unified_features.add(FeatureValue('tone', -0.5, FeatureValueType.SCALAR))
                elif feature == 'tone4':
                    unified_features.add(FeatureValue('tone', -1.0, FeatureValueType.SCALAR))
        
        return FeatureBundle(frozenset(unified_features), ipa_features.partial)
    
    def convert_unified_to_ipa(self, unified_features: FeatureBundle) -> FeatureBundle:
        """
        Specialized conversion from unified distinctive to IPA categorical.
        
        This converts scalar values back to categorical features.
        """
        categorical_features = set()
        
        for fval in unified_features.features:
            if fval.value_type != FeatureValueType.SCALAR:
                continue
            
            feature_name = fval.feature
            value = fval.value
            
            # Convert based on feature type and value
            if feature_name == 'sonorant':
                if value > 0.5:
                    # Don't add explicit sonorant feature (implicit in vowel/nasal/liquid)
                    pass
                elif value < -0.5:
                    categorical_features.add(FeatureValue('consonant', True, FeatureValueType.CATEGORICAL))
            
            elif feature_name == 'consonantal':
                if value > 0.5:
                    categorical_features.add(FeatureValue('consonant', True, FeatureValueType.CATEGORICAL))
                elif value < -0.5:
                    categorical_features.add(FeatureValue('vowel', True, FeatureValueType.CATEGORICAL))
            
            elif feature_name == 'voice':
                if value > 0.5:
                    categorical_features.add(FeatureValue('voiced', True, FeatureValueType.CATEGORICAL))
                elif value < -0.5:
                    categorical_features.add(FeatureValue('voiceless', True, FeatureValueType.CATEGORICAL))
            
            elif feature_name == 'continuant':
                if value < -0.5:
                    categorical_features.add(FeatureValue('stop', True, FeatureValueType.CATEGORICAL))
                elif value > 0.5:
                    # High continuant could be vowel or fricative - context dependent
                    pass
            
            elif feature_name == 'labial' and value > 0.5:
                categorical_features.add(FeatureValue('bilabial', True, FeatureValueType.CATEGORICAL))
            
            elif feature_name == 'coronal' and value > 0.5:
                categorical_features.add(FeatureValue('alveolar', True, FeatureValueType.CATEGORICAL))
            
            elif feature_name == 'dorsal' and value > 0.5:
                categorical_features.add(FeatureValue('velar', True, FeatureValueType.CATEGORICAL))
            
            elif feature_name == 'nasal' and value > 0.5:
                categorical_features.add(FeatureValue('nasal', True, FeatureValueType.CATEGORICAL))
            
            elif feature_name == 'high':
                if value > 0.5:
                    categorical_features.add(FeatureValue('high', True, FeatureValueType.CATEGORICAL))
                elif value < -0.5:
                    categorical_features.add(FeatureValue('low', True, FeatureValueType.CATEGORICAL))
            
            elif feature_name == 'back':
                if value > 0.5:
                    categorical_features.add(FeatureValue('back', True, FeatureValueType.CATEGORICAL))
                elif value < -0.5:
                    categorical_features.add(FeatureValue('front', True, FeatureValueType.CATEGORICAL))
                else:
                    categorical_features.add(FeatureValue('central', True, FeatureValueType.CATEGORICAL))
            
            elif feature_name == 'round':
                if value > 0.5:
                    categorical_features.add(FeatureValue('rounded', True, FeatureValueType.CATEGORICAL))
                elif value < -0.5:
                    categorical_features.add(FeatureValue('unrounded', True, FeatureValueType.CATEGORICAL))
            
            elif feature_name == 'stress':
                if value > 0.7:
                    categorical_features.add(FeatureValue('stress1', True, FeatureValueType.CATEGORICAL))
                elif value > 0.2:
                    categorical_features.add(FeatureValue('stress2', True, FeatureValueType.CATEGORICAL))
                elif value < -0.5:
                    categorical_features.add(FeatureValue('unstressed', True, FeatureValueType.CATEGORICAL))
            
            elif feature_name == 'tone':
                if value > 0.7:
                    categorical_features.add(FeatureValue('tone1', True, FeatureValueType.CATEGORICAL))
                elif value > 0.2:
                    categorical_features.add(FeatureValue('tone2', True, FeatureValueType.CATEGORICAL))
                elif value > -0.2:
                    categorical_features.add(FeatureValue('tone3', True, FeatureValueType.CATEGORICAL))
                else:
                    categorical_features.add(FeatureValue('tone4', True, FeatureValueType.CATEGORICAL))
        
        return FeatureBundle(frozenset(categorical_features), unified_features.partial)


# Global converter instance
_converter = FeatureSystemConverter()


def convert_sound_between_systems(from_system: str, 
                                 to_system: str, 
                                 features: FeatureBundle) -> FeatureBundle:
    """
    Convert a sound between feature systems.
    
    Args:
        from_system: Source feature system name
        to_system: Target feature system name
        features: Features to convert
        
    Returns:
        Converted feature bundle
    """
    return _converter.convert_sound(from_system, to_system, features)


@contextmanager
def feature_system_context(system_name: str):
    """
    Context manager for temporarily changing the default feature system.
    
    Usage:
        with feature_system_context('unified_distinctive'):
            sound = Sound(grapheme='p')  # Uses unified system
        # Default system restored
    """
    old_default = get_default_feature_system().name
    try:
        set_default_feature_system(system_name)
        yield
    finally:
        set_default_feature_system(old_default)


def create_feature_mapping(source_features: Set[str], 
                          target_system: str) -> Dict[str, FeatureBundle]:
    """
    Create a mapping from categorical features to target system features.
    
    This is useful for bulk conversion of feature specifications.
    
    Args:
        source_features: Set of categorical feature names
        target_system: Target feature system name
        
    Returns:
        Mapping from feature names to FeatureBundle objects
    """
    target_sys = get_feature_system(target_system)
    mapping = {}
    
    for feature in source_features:
        # Create a simple categorical bundle
        from .base import FeatureValue, FeatureValueType
        categorical_fval = FeatureValue(
            feature=feature,
            value=True,
            value_type=FeatureValueType.CATEGORICAL
        )
        categorical_bundle = FeatureBundle(frozenset([categorical_fval]))
        
        # Convert to target system
        converted = _converter.convert_sound("ipa_categorical", target_system, categorical_bundle)
        mapping[feature] = converted
    
    return mapping


def get_conversion_recommendations(from_system: str, to_system: str) -> List[str]:
    """
    Get recommendations for converting between systems.
    
    Returns a list of notes and warnings about the conversion process.
    """
    recommendations = []
    
    if from_system == to_system:
        recommendations.append("No conversion needed - systems are identical")
        return recommendations
    
    if from_system == "ipa_categorical" and to_system == "unified_distinctive":
        recommendations.extend([
            "Converting from categorical to scalar features",
            "Some feature distinctions may be mapped to intermediate scalar values",
            "Suprasegmental features will be mapped to stress/tone scalars",
            "Consider reviewing converted values for phonological accuracy"
        ])
    
    elif from_system == "unified_distinctive" and to_system == "ipa_categorical":
        recommendations.extend([
            "Converting from scalar to categorical features",
            "Intermediate scalar values will be thresholded to binary distinctions",
            "Some gradient information will be lost",
            "Check that converted features match intended phonological categories"
        ])
    
    else:
        recommendations.extend([
            f"Converting between {from_system} and {to_system}",
            "Conversion performed via grapheme representation (may be lossy)",
            "Verify that key phonological distinctions are preserved",
            "Consider implementing direct conversion rules for better accuracy"
        ])
    
    return recommendations