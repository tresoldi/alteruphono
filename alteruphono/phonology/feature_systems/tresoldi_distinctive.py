"""
Tresoldi distinctive feature system.

This implements Tresoldi's comprehensive distinctive feature system with 43 features
covering 1,081 sounds including complex segments, clicks, prenasals, and tonal variants.
All features are represented as scalar values in the range [-1.0, 1.0].
"""

import csv
import os
from typing import Dict, List, Optional, Set, Tuple
from .base import (
    FeatureSystem,
    FeatureValue,
    FeatureBundle,
    FeatureValueType
)


class TresoldiDistinctiveSystem(FeatureSystem):
    """
    Tresoldi's distinctive feature system with comprehensive phonological coverage.
    
    Features:
    - 43 distinctive features covering all aspects of phonology
    - 1,081 sounds including complex segments and variants  
    - Scalar values normalized to [-1.0, 1.0] range
    - Binary opposition interpretation (positive/negative)
    - Support for gradient modifications in sound change
    """
    
    def __init__(self):
        self._load_feature_data()
        
        # Performance optimizations
        self._grapheme_cache = {}
        self._features_cache = {}
    
    @property
    def name(self) -> str:
        return "tresoldi_distinctive"
    
    @property
    def description(self) -> str:
        return "Tresoldi's comprehensive distinctive feature system with 43 features for 1,081 sounds"
    
    @property
    def supported_value_types(self) -> Set[FeatureValueType]:
        return {FeatureValueType.SCALAR}
    
    def _load_feature_data(self) -> None:
        """Load feature data from CSV file."""
        # Find the CSV file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(current_dir, '..', '..', '..', 'data', 'feature_systems', 'tresoldi_features.csv')
        csv_path = os.path.normpath(csv_path)
        
        self._grapheme_features = {}
        self._feature_definitions = {}
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Get feature names (skip 'sound' and 'description')
                feature_names = [name for name in reader.fieldnames if name not in ['sound', 'description']]
                
                # Initialize feature definitions
                for feature_name in feature_names:
                    self._feature_definitions[feature_name] = f"Tresoldi distinctive feature: {feature_name}"
                
                # Load sound data
                for row in reader:
                    sound = row['sound']
                    features = {}
                    
                    for feature_name in feature_names:
                        raw_value = row[feature_name]
                        
                        try:
                            numeric_value = float(raw_value)
                            # Scale length feature from [-2.0, 2.0] to [-1.0, 1.0]
                            if feature_name == 'length':
                                numeric_value = numeric_value / 2.0
                            
                            # Ensure all values are in [-1.0, 1.0] range
                            numeric_value = max(-1.0, min(1.0, numeric_value))
                            features[feature_name] = numeric_value
                            
                        except ValueError:
                            # Skip non-numeric values (shouldn't happen in this dataset)
                            continue
                    
                    self._grapheme_features[sound] = features
        
        except FileNotFoundError:
            raise FileNotFoundError(f"Tresoldi feature data not found at: {csv_path}")
        except Exception as e:
            raise ValueError(f"Error loading Tresoldi feature data: {e}")
        
        print(f"Loaded Tresoldi feature system: {len(self._grapheme_features)} sounds, {len(self._feature_definitions)} features")
    
    def grapheme_to_features(self, grapheme: str) -> Optional[FeatureBundle]:
        """Convert a grapheme to Tresoldi distinctive features."""
        # Check cache first
        if grapheme in self._grapheme_cache:
            return self._grapheme_cache[grapheme]
        
        result = None
        if grapheme in self._grapheme_features:
            feature_dict = self._grapheme_features[grapheme]
            feature_values = {
                FeatureValue(
                    feature=fname,
                    value=fvalue,
                    value_type=FeatureValueType.SCALAR
                )
                for fname, fvalue in feature_dict.items()
            }
            result = FeatureBundle(frozenset(feature_values))
        
        # Cache the result (including None)
        self._grapheme_cache[grapheme] = result
        return result
    
    def features_to_grapheme(self, features: FeatureBundle) -> str:
        """Convert features to best-matching grapheme using distance metrics."""
        # Check cache first
        features_key = frozenset(features.features)
        if features_key in self._features_cache:
            return self._features_cache[features_key]
        
        best_grapheme = '?'
        best_distance = float('inf')
        
        for grapheme, grapheme_features in self._grapheme_features.items():
            # Create bundle for this grapheme
            grapheme_bundle = self.grapheme_to_features(grapheme)
            if grapheme_bundle is None:
                continue
            
            # Calculate distance
            distance = features.distance_to(grapheme_bundle)
            if distance < best_distance:
                best_distance = distance
                best_grapheme = grapheme
        
        # Cache the result
        self._features_cache[features_key] = best_grapheme
        return best_grapheme
    
    def parse_feature_specification(self, spec: str) -> FeatureBundle:
        """Parse feature specification with scalar values."""
        # Remove brackets if present
        if spec.startswith('[') and spec.endswith(']'):
            spec = spec[1:-1]
        
        feature_values = set()
        
        # Split by commas
        feature_specs = [f.strip() for f in spec.split(',')]
        
        for feature_spec in feature_specs:
            if '=' in feature_spec:
                # Explicit value: feature=value
                feature_name, value_str = feature_spec.split('=', 1)
                feature_name = feature_name.strip()
                value_str = value_str.strip()
                
                try:
                    value = float(value_str)
                    # Apply length scaling if needed
                    if feature_name == 'length':
                        value = value / 2.0
                    value = max(-1.0, min(1.0, value))
                    
                    feature_values.add(FeatureValue(
                        feature=feature_name,
                        value=value,
                        value_type=FeatureValueType.SCALAR
                    ))
                except ValueError:
                    raise ValueError(f"Invalid numeric value for feature {feature_name}: {value_str}")
            
            elif feature_spec.startswith('+'):
                # Positive feature: +feature
                feature_name = feature_spec[1:].strip()
                feature_values.add(FeatureValue(
                    feature=feature_name,
                    value=1.0,
                    value_type=FeatureValueType.SCALAR
                ))
            
            elif feature_spec.startswith('-'):
                # Negative feature: -feature
                feature_name = feature_spec[1:].strip()
                feature_values.add(FeatureValue(
                    feature=feature_name,
                    value=-1.0,
                    value_type=FeatureValueType.SCALAR
                ))
            
            else:
                # Default to positive
                feature_name = feature_spec.strip()
                if feature_name:
                    feature_values.add(FeatureValue(
                        feature=feature_name,
                        value=1.0,
                        value_type=FeatureValueType.SCALAR
                    ))
        
        return FeatureBundle(frozenset(feature_values))
    
    def add_features(self, base: FeatureBundle, additional: FeatureBundle) -> FeatureBundle:
        """Add features using scalar arithmetic."""
        # Start with base features
        result_features = dict()
        for fval in base.features:
            result_features[fval.feature] = fval
        
        # Add or modify with additional features
        for fval in additional.features:
            if fval.feature in result_features:
                # For Tresoldi system, replacement rather than addition
                # (can be modified for gradient arithmetic later)
                result_features[fval.feature] = fval
            else:
                result_features[fval.feature] = fval
        
        return FeatureBundle(frozenset(result_features.values()))
    
    def get_sound_class_features(self, sound_class: str) -> Optional[FeatureBundle]:
        """Get features for a sound class (e.g., 'V', 'C', 'S')."""
        # Define common sound classes using Tresoldi features
        sound_classes = {
            'V': {  # Vowels
                'syllabic': 1.0,
                'consonantal': -1.0,
                'sonorant': 1.0
            },
            'C': {  # Consonants
                'consonantal': 1.0,
                'syllabic': -1.0
            },
            'S': {  # Sonorants
                'sonorant': 1.0
            },
            'O': {  # Obstruents  
                'sonorant': -1.0,
                'consonantal': 1.0
            },
            'N': {  # Nasals
                'nasal': 1.0,
                'sonorant': 1.0,
                'consonantal': 1.0
            },
            'L': {  # Liquids
                'sonorant': 1.0,
                'consonantal': 1.0,
                'nasal': -1.0
            }
        }
        
        if sound_class in sound_classes:
            feature_dict = sound_classes[sound_class]
            feature_values = {
                FeatureValue(
                    feature=fname,
                    value=fvalue,
                    value_type=FeatureValueType.SCALAR
                )
                for fname, fvalue in feature_dict.items()
            }
            return FeatureBundle(frozenset(feature_values))
        
        return None
    
    def subtract_features(self, base: FeatureBundle, to_remove: FeatureBundle) -> FeatureBundle:
        """Remove features from base bundle."""
        result_features = set()
        
        remove_features = {fval.feature for fval in to_remove.features}
        
        for fval in base.features:
            if fval.feature not in remove_features:
                result_features.add(fval)
        
        return FeatureBundle(frozenset(result_features))
    
    def validate_features(self, features: FeatureBundle) -> List[str]:
        """Validate feature bundle for consistency."""
        errors = []
        
        for fval in features.features:
            # Check if feature exists in our system
            if fval.feature not in self._feature_definitions:
                errors.append(f"Unknown feature: {fval.feature}")
            
            # Check value range
            if not isinstance(fval.value, (int, float)):
                errors.append(f"Feature {fval.feature} must have numeric value")
            elif not -1.0 <= float(fval.value) <= 1.0:
                errors.append(f"Feature {fval.feature} value {fval.value} outside [-1.0, 1.0] range")
        
        return errors
    
    def is_positive(self, features: FeatureBundle, feature_name: str) -> bool:
        """Check if a feature has positive value (binary opposition logic)."""
        feature_value = features.get_feature(feature_name)
        if feature_value is None:
            return False
        return float(feature_value.value) > 0.0
    
    def is_negative(self, features: FeatureBundle, feature_name: str) -> bool:
        """Check if a feature has negative value (binary opposition logic)."""
        feature_value = features.get_feature(feature_name)
        if feature_value is None:
            return False
        return float(feature_value.value) < 0.0
    
    def is_neutral(self, features: FeatureBundle, feature_name: str) -> bool:
        """Check if a feature has neutral (zero) value."""
        feature_value = features.get_feature(feature_name)
        if feature_value is None:
            return True  # Missing feature is considered neutral
        return abs(float(feature_value.value)) < 0.01  # Small tolerance for floating point
    
    def get_feature_names(self) -> List[str]:
        """Get list of all feature names in the system."""
        return list(self._feature_definitions.keys())
    
    def get_feature_definition(self, feature_name: str) -> Optional[str]:
        """Get description of a feature."""
        return self._feature_definitions.get(feature_name)
    
    def get_sound_count(self) -> int:
        """Get total number of sounds in the system."""
        return len(self._grapheme_features)
    
    def get_all_graphemes(self) -> List[str]:
        """Get list of all graphemes in the system."""
        return list(self._grapheme_features.keys())
    
    def has_grapheme(self, grapheme: str) -> bool:
        """Check if a grapheme is defined in the system."""
        return grapheme in self._grapheme_features
    
    def get_sounds_with_feature(self, feature_name: str, positive: bool = True) -> List[str]:
        """Get all sounds that have a feature with positive or negative value."""
        sounds = []
        
        for grapheme, features_dict in self._grapheme_features.items():
            if feature_name in features_dict:
                value = features_dict[feature_name]
                if positive and value > 0.0:
                    sounds.append(grapheme)
                elif not positive and value < 0.0:
                    sounds.append(grapheme)
        
        return sounds
    
    def get_feature_statistics(self) -> Dict[str, Dict[str, int]]:
        """Get statistics about feature usage across all sounds."""
        stats = {}
        
        for feature_name in self._feature_definitions:
            stats[feature_name] = {
                'positive': 0,
                'negative': 0, 
                'neutral': 0,
                'total_sounds': len(self._grapheme_features)
            }
            
            for grapheme, features_dict in self._grapheme_features.items():
                if feature_name in features_dict:
                    value = features_dict[feature_name]
                    if value > 0.0:
                        stats[feature_name]['positive'] += 1
                    elif value < 0.0:
                        stats[feature_name]['negative'] += 1
                    else:
                        stats[feature_name]['neutral'] += 1
                else:
                    stats[feature_name]['neutral'] += 1
        
        return stats