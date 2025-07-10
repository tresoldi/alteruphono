"""
Unified distinctive feature system with scalar values.

This implements a modern distinctive feature system where all sounds
(vowels and consonants) can be described using the same set of features
with continuous values from -1.0 to +1.0.

This system eliminates the traditional vowel/consonant distinction and
provides a more unified phonological representation suitable for
computational analysis and gradient phonological phenomena.
"""

import math
import functools
from typing import Dict, List, Optional, Set, Tuple
from .base import (
    FeatureSystem,
    FeatureValue,
    FeatureBundle,
    FeatureValueType
)


class UnifiedDistinctiveSystem(FeatureSystem):
    """
    Unified distinctive feature system with scalar values.
    
    Features:
    - All sounds use the same feature set
    - Feature values range from -1.0 to +1.0
    - No categorical distinction between vowels and consonants
    - Supports gradient and categorical phenomena
    - Based on articulatory and acoustic principles
    """
    
    def __init__(self):
        self._feature_definitions = self._build_feature_definitions()
        self._grapheme_features = self._build_grapheme_features()
        self._sound_classes = self._build_sound_classes()
        
        # Performance optimizations
        self._grapheme_cache = {}
        self._features_cache = {}
        self._distance_cache = {}
    
    @property
    def name(self) -> str:
        return "unified_distinctive"
    
    @property
    def description(self) -> str:
        return "Unified distinctive feature system with scalar values (-1.0 to +1.0) for all sounds"
    
    @property
    def supported_value_types(self) -> Set[FeatureValueType]:
        return {FeatureValueType.SCALAR}
    
    def _build_feature_definitions(self) -> Dict[str, str]:
        """Define the universal feature set with descriptions."""
        return {
            # Major class features
            'sonorant': 'Degree of sonority (-1.0=obstruent, +1.0=vowel)',
            'consonantal': 'Degree of constriction (-1.0=vowel, +1.0=stop)',
            'continuant': 'Degree of airflow continuity (-1.0=stop, +1.0=vowel)',
            
            # Place features (articulatory)
            'labial': 'Lip involvement (-1.0=none, +1.0=primary)',
            'coronal': 'Tongue tip/blade involvement (-1.0=none, +1.0=primary)',
            'dorsal': 'Tongue body involvement (-1.0=none, +1.0=primary)',
            'pharyngeal': 'Pharynx constriction (-1.0=none, +1.0=primary)',
            'laryngeal': 'Larynx involvement (-1.0=none, +1.0=glottal)',
            
            # Coronal subfeatures
            'anterior': 'Articulation forward of alveopalatal region',
            'distributed': 'Extended tongue contact area',
            
            # Dorsal subfeatures  
            'high': 'Tongue body height (-1.0=low, +1.0=high)',
            'low': 'Tongue body lowering (-1.0=high, +1.0=low)',
            'back': 'Tongue body backness (-1.0=front, +1.0=back)',
            'tense': 'Articulatory tension (-1.0=lax, +1.0=tense)',
            
            # Manner features
            'nasal': 'Nasal airflow (-1.0=oral, +1.0=nasal)',
            'lateral': 'Lateral airflow (-1.0=central, +1.0=lateral)',
            'strident': 'Acoustic stridency (-1.0=mellow, +1.0=strident)',
            
            # Laryngeal features
            'voice': 'Vocal fold vibration (-1.0=voiceless, +1.0=voiced)',
            'spread_glottis': 'Glottal spreading (-1.0=none, +1.0=aspirated)',
            'constricted_glottis': 'Glottal constriction (-1.0=none, +1.0=ejective)',
            
            # Vocalic features (apply to all sounds)
            'round': 'Lip rounding (-1.0=unrounded, +1.0=rounded)',
            'atr': 'Advanced tongue root (-1.0=retracted, +1.0=advanced)',
            
            # Prosodic features (suprasegmental)
            'stress': 'Stress level (-1.0=unstressed, +1.0=primary)',
            'tone': 'Tone level (-1.0=low, +1.0=high)',
            'length': 'Segmental duration (-1.0=short, +1.0=long)',
            
            # Acoustic features
            'f0': 'Fundamental frequency (normalized)',
            'f1': 'First formant (normalized)', 
            'f2': 'Second formant (normalized)',
            'f3': 'Third formant (normalized)',
            'intensity': 'Acoustic intensity (normalized)',
        }
    
    def _build_grapheme_features(self) -> Dict[str, Dict[str, float]]:
        """Map IPA graphemes to unified distinctive features."""
        return {
            # Stops
            'p': {
                'sonorant': -0.9, 'consonantal': 1.0, 'continuant': -1.0,
                'labial': 1.0, 'voice': -1.0, 'nasal': -1.0
            },
            'b': {
                'sonorant': -0.9, 'consonantal': 1.0, 'continuant': -1.0,
                'labial': 1.0, 'voice': 1.0, 'nasal': -1.0
            },
            't': {
                'sonorant': -0.9, 'consonantal': 1.0, 'continuant': -1.0,
                'coronal': 1.0, 'anterior': 1.0, 'voice': -1.0, 'nasal': -1.0
            },
            'd': {
                'sonorant': -0.9, 'consonantal': 1.0, 'continuant': -1.0,
                'coronal': 1.0, 'anterior': 1.0, 'voice': 1.0, 'nasal': -1.0
            },
            'k': {
                'sonorant': -0.9, 'consonantal': 1.0, 'continuant': -1.0,
                'dorsal': 1.0, 'high': 0.7, 'voice': -1.0, 'nasal': -1.0
            },
            'g': {
                'sonorant': -0.9, 'consonantal': 1.0, 'continuant': -1.0,
                'dorsal': 1.0, 'high': 0.7, 'voice': 1.0, 'nasal': -1.0
            },
            'ʔ': {
                'sonorant': -0.9, 'consonantal': 1.0, 'continuant': -1.0,
                'laryngeal': 1.0, 'constricted_glottis': 1.0, 'voice': -1.0
            },
            
            # Fricatives
            'f': {
                'sonorant': -0.8, 'consonantal': 0.8, 'continuant': 0.5,
                'labial': 1.0, 'voice': -1.0, 'strident': 0.6
            },
            'v': {
                'sonorant': -0.8, 'consonantal': 0.8, 'continuant': 0.5,
                'labial': 1.0, 'voice': 1.0, 'strident': 0.6
            },
            's': {
                'sonorant': -0.8, 'consonantal': 0.8, 'continuant': 0.5,
                'coronal': 1.0, 'anterior': 1.0, 'voice': -1.0, 'strident': 1.0
            },
            'z': {
                'sonorant': -0.8, 'consonantal': 0.8, 'continuant': 0.5,
                'coronal': 1.0, 'anterior': 1.0, 'voice': 1.0, 'strident': 1.0
            },
            'ʃ': {
                'sonorant': -0.8, 'consonantal': 0.8, 'continuant': 0.5,
                'coronal': 1.0, 'anterior': -0.5, 'voice': -1.0, 'strident': 1.0
            },
            'ʒ': {
                'sonorant': -0.8, 'consonantal': 0.8, 'continuant': 0.5,
                'coronal': 1.0, 'anterior': -0.5, 'voice': 1.0, 'strident': 1.0
            },
            'x': {
                'sonorant': -0.8, 'consonantal': 0.8, 'continuant': 0.5,
                'dorsal': 1.0, 'high': 0.7, 'voice': -1.0, 'strident': -0.5
            },
            'h': {
                'sonorant': -0.8, 'consonantal': 0.3, 'continuant': 1.0,
                'laryngeal': 1.0, 'voice': -1.0, 'spread_glottis': 0.8
            },
            
            # Nasals
            'm': {
                'sonorant': 0.8, 'consonantal': 0.9, 'continuant': -0.3,
                'labial': 1.0, 'voice': 1.0, 'nasal': 1.0
            },
            'n': {
                'sonorant': 0.8, 'consonantal': 0.9, 'continuant': -0.3,
                'coronal': 1.0, 'anterior': 1.0, 'voice': 1.0, 'nasal': 1.0
            },
            'ŋ': {
                'sonorant': 0.8, 'consonantal': 0.9, 'continuant': -0.3,
                'dorsal': 1.0, 'high': 0.7, 'voice': 1.0, 'nasal': 1.0
            },
            
            # Liquids
            'l': {
                'sonorant': 0.9, 'consonantal': 0.7, 'continuant': 0.3,
                'coronal': 1.0, 'anterior': 1.0, 'voice': 1.0, 'lateral': 1.0
            },
            'r': {
                'sonorant': 0.9, 'consonantal': 0.6, 'continuant': 0.5,
                'coronal': 1.0, 'anterior': 1.0, 'voice': 1.0, 'lateral': -1.0
            },
            
            # Approximants
            'w': {
                'sonorant': 1.0, 'consonantal': -0.3, 'continuant': 1.0,
                'labial': 1.0, 'dorsal': 0.7, 'voice': 1.0, 'round': 1.0, 'high': 0.8
            },
            'j': {
                'sonorant': 1.0, 'consonantal': -0.3, 'continuant': 1.0,
                'dorsal': 1.0, 'high': 1.0, 'voice': 1.0, 'back': -1.0
            },
            
            # Vowels
            'i': {
                'sonorant': 1.0, 'consonantal': -1.0, 'continuant': 1.0,
                'dorsal': 1.0, 'high': 1.0, 'low': -1.0, 'back': -1.0,
                'voice': 1.0, 'tense': 1.0, 'round': -1.0
            },
            'ɪ': {
                'sonorant': 1.0, 'consonantal': -1.0, 'continuant': 1.0,
                'dorsal': 1.0, 'high': 0.7, 'low': -0.8, 'back': -0.8,
                'voice': 1.0, 'tense': -0.5, 'round': -1.0
            },
            'e': {
                'sonorant': 1.0, 'consonantal': -1.0, 'continuant': 1.0,
                'dorsal': 1.0, 'high': 0.3, 'low': -0.5, 'back': -1.0,
                'voice': 1.0, 'tense': 1.0, 'round': -1.0
            },
            'ɛ': {
                'sonorant': 1.0, 'consonantal': -1.0, 'continuant': 1.0,
                'dorsal': 1.0, 'high': -0.3, 'low': 0.2, 'back': -0.8,
                'voice': 1.0, 'tense': -0.5, 'round': -1.0
            },
            'æ': {
                'sonorant': 1.0, 'consonantal': -1.0, 'continuant': 1.0,
                'dorsal': 1.0, 'high': -0.8, 'low': 0.8, 'back': -0.5,
                'voice': 1.0, 'tense': -0.5, 'round': -1.0
            },
            'a': {
                'sonorant': 1.0, 'consonantal': -1.0, 'continuant': 1.0,
                'dorsal': 1.0, 'high': -1.0, 'low': 1.0, 'back': 0.0,
                'voice': 1.0, 'tense': 0.0, 'round': -1.0
            },
            'ɑ': {
                'sonorant': 1.0, 'consonantal': -1.0, 'continuant': 1.0,
                'dorsal': 1.0, 'high': -1.0, 'low': 1.0, 'back': 1.0,
                'voice': 1.0, 'tense': 0.0, 'round': -1.0
            },
            'ɔ': {
                'sonorant': 1.0, 'consonantal': -1.0, 'continuant': 1.0,
                'dorsal': 1.0, 'high': -0.3, 'low': 0.2, 'back': 0.8,
                'voice': 1.0, 'tense': -0.5, 'round': 1.0
            },
            'o': {
                'sonorant': 1.0, 'consonantal': -1.0, 'continuant': 1.0,
                'dorsal': 1.0, 'high': 0.3, 'low': -0.5, 'back': 1.0,
                'voice': 1.0, 'tense': 1.0, 'round': 1.0
            },
            'ʊ': {
                'sonorant': 1.0, 'consonantal': -1.0, 'continuant': 1.0,
                'dorsal': 1.0, 'high': 0.7, 'low': -0.8, 'back': 0.8,
                'voice': 1.0, 'tense': -0.5, 'round': 1.0
            },
            'u': {
                'sonorant': 1.0, 'consonantal': -1.0, 'continuant': 1.0,
                'dorsal': 1.0, 'high': 1.0, 'low': -1.0, 'back': 1.0,
                'voice': 1.0, 'tense': 1.0, 'round': 1.0
            },
            'ə': {
                'sonorant': 1.0, 'consonantal': -1.0, 'continuant': 1.0,
                'dorsal': 1.0, 'high': 0.0, 'low': 0.0, 'back': 0.0,
                'voice': 1.0, 'tense': -0.8, 'round': -0.5
            },
        }
    
    def _build_sound_classes(self) -> Dict[str, Dict[str, float]]:
        """Define sound classes in terms of unified features."""
        return {
            # Traditional vowel/consonant distinction
            'V': {'sonorant': 0.8, 'consonantal': -0.5},  # Vowel-like
            'C': {'sonorant': -0.3, 'consonantal': 0.5},  # Consonant-like
            
            # More specific classes
            'STOP': {'consonantal': 0.8, 'continuant': -0.8},
            'FRIC': {'consonantal': 0.5, 'continuant': 0.3, 'strident': 0.5},
            'NAS': {'nasal': 0.8, 'sonorant': 0.6},
            'LIQ': {'sonorant': 0.8, 'consonantal': 0.3},
            
            # Place classes
            'LAB': {'labial': 0.8},
            'COR': {'coronal': 0.8},
            'DORS': {'dorsal': 0.8},
            
            # Voicing
            'VD': {'voice': 0.5},
            'VL': {'voice': -0.5},
            
            # Vowel height (gradient)
            'HIGH_V': {'sonorant': 0.8, 'high': 0.7},
            'MID_V': {'sonorant': 0.8, 'high': 0.0, 'low': 0.0},
            'LOW_V': {'sonorant': 0.8, 'low': 0.7},
            
            # Vowel backness
            'FRONT_V': {'sonorant': 0.8, 'back': -0.7},
            'CENTRAL_V': {'sonorant': 0.8, 'back': 0.0},
            'BACK_V': {'sonorant': 0.8, 'back': 0.7},
        }
    
    def grapheme_to_features(self, grapheme: str) -> Optional[FeatureBundle]:
        """Convert a grapheme to unified distinctive features."""
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
        
        # Check sound classes
        elif grapheme in self._sound_classes:
            feature_dict = self._sound_classes[grapheme]
            feature_values = {
                FeatureValue(
                    feature=fname,
                    value=fvalue,
                    value_type=FeatureValueType.SCALAR
                )
                for fname, fvalue in feature_dict.items()
            }
            result = FeatureBundle(frozenset(feature_values), partial=True)
        
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
        # Remove brackets
        if spec.startswith('[') and spec.endswith(']'):
            spec = spec[1:-1]
        
        if not spec.strip():
            return FeatureBundle(frozenset())
        
        features = set()
        for feature_spec in spec.split(','):
            feature_spec = feature_spec.strip()
            if not feature_spec:
                continue
            
            # Parse feature=value or +feature or -feature
            if '=' in feature_spec:
                fname, fvalue_str = feature_spec.split('=', 1)
                fname = fname.strip()
                try:
                    fvalue = float(fvalue_str.strip())
                    # Clamp to valid range
                    fvalue = max(-1.0, min(1.0, fvalue))
                    features.add(FeatureValue(
                        feature=fname,
                        value=fvalue,
                        value_type=FeatureValueType.SCALAR
                    ))
                except ValueError:
                    # If not a number, treat as categorical (but convert to scalar)
                    if fvalue_str.strip().lower() in ['true', 'yes', '+']:
                        fvalue = 1.0
                    elif fvalue_str.strip().lower() in ['false', 'no', '-']:
                        fvalue = -1.0
                    else:
                        fvalue = 0.0  # Default neutral value
                    features.add(FeatureValue(
                        feature=fname,
                        value=fvalue,
                        value_type=FeatureValueType.SCALAR
                    ))
            elif feature_spec.startswith('+'):
                fname = feature_spec[1:].strip()
                features.add(FeatureValue(
                    feature=fname,
                    value=1.0,
                    value_type=FeatureValueType.SCALAR
                ))
            elif feature_spec.startswith('-'):
                fname = feature_spec[1:].strip()
                features.add(FeatureValue(
                    feature=fname,
                    value=-1.0,
                    value_type=FeatureValueType.SCALAR
                ))
            else:
                # Plain feature name - assume positive
                features.add(FeatureValue(
                    feature=feature_spec,
                    value=1.0,
                    value_type=FeatureValueType.SCALAR
                ))
        
        return FeatureBundle(frozenset(features))
    
    def get_sound_class_features(self, sound_class: str) -> Optional[FeatureBundle]:
        """Get features for a sound class."""
        if sound_class in self._sound_classes:
            feature_dict = self._sound_classes[sound_class]
            feature_values = {
                FeatureValue(
                    feature=fname,
                    value=fvalue,
                    value_type=FeatureValueType.SCALAR
                )
                for fname, fvalue in feature_dict.items()
            }
            return FeatureBundle(frozenset(feature_values), partial=True)
        return None
    
    def add_features(self, base: FeatureBundle, additional: FeatureBundle) -> FeatureBundle:
        """Add features with scalar arithmetic and constraints."""
        result_features = set(base.features)
        
        for add_fval in additional.features:
            # Find existing feature with same name
            existing_fval = None
            for fval in result_features:
                if fval.feature == add_fval.feature:
                    existing_fval = fval
                    break
            
            if existing_fval is not None:
                # Combine values (additive model with saturation)
                result_features.remove(existing_fval)
                new_value = existing_fval.value + add_fval.value
                # Saturate at boundaries
                new_value = max(-1.0, min(1.0, new_value))
                
                result_features.add(FeatureValue(
                    feature=add_fval.feature,
                    value=new_value,
                    value_type=FeatureValueType.SCALAR
                ))
            else:
                # Add new feature
                result_features.add(add_fval)
        
        return FeatureBundle(frozenset(result_features), base.partial)
    
    def validate_features(self, features: FeatureBundle) -> List[str]:
        """Validate feature bundle with unified distinctive constraints."""
        errors = []
        
        # Check value ranges
        for fval in features.features:
            if fval.value_type == FeatureValueType.SCALAR:
                if not (-1.0 <= fval.value <= 1.0):
                    errors.append(f"Feature {fval.feature} value {fval.value} outside valid range [-1.0, 1.0]")
        
        # Check for phonologically impossible combinations
        high_val = None
        low_val = None
        for fval in features.features:
            if fval.feature == 'high':
                high_val = fval.value
            elif fval.feature == 'low':
                low_val = fval.value
        
        if high_val is not None and low_val is not None:
            if high_val > 0.5 and low_val > 0.5:
                errors.append("Cannot be both high and low simultaneously")
        
        # Check consonantal/sonorant relationship
        cons_val = None
        son_val = None
        for fval in features.features:
            if fval.feature == 'consonantal':
                cons_val = fval.value
            elif fval.feature == 'sonorant':
                son_val = fval.value
        
        if cons_val is not None and son_val is not None:
            # Very high consonantal should correlate with low sonorant
            if cons_val > 0.8 and son_val > 0.8:
                errors.append("High consonantal value inconsistent with high sonorant value")
        
        return errors
    
    def get_feature_definitions(self) -> Dict[str, str]:
        """Get descriptions of all features in this system."""
        return self._feature_definitions.copy()
    
    def interpolate_sounds(self, sound1: FeatureBundle, sound2: FeatureBundle, ratio: float) -> FeatureBundle:
        """
        Create an intermediate sound between two sounds.
        
        Args:
            sound1: First sound 
            sound2: Second sound
            ratio: Interpolation ratio (0.0 = sound1, 1.0 = sound2)
            
        Returns:
            Interpolated sound
        """
        ratio = max(0.0, min(1.0, ratio))  # Clamp ratio
        
        # Get all features from both sounds
        all_features = {f.feature for f in sound1.features} | {f.feature for f in sound2.features}
        
        result_features = set()
        for fname in all_features:
            val1 = 0.0  # Default neutral value
            val2 = 0.0
            
            # Get values from each sound
            for fval in sound1.features:
                if fval.feature == fname:
                    val1 = fval.value
                    break
            
            for fval in sound2.features:
                if fval.feature == fname:
                    val2 = fval.value
                    break
            
            # Interpolate
            interpolated_value = val1 * (1.0 - ratio) + val2 * ratio
            
            result_features.add(FeatureValue(
                feature=fname,
                value=interpolated_value,
                value_type=FeatureValueType.SCALAR
            ))
        
        return FeatureBundle(frozenset(result_features))
    
    def is_vowel_like(self, features: FeatureBundle, threshold: float = 0.5) -> bool:
        """Check if a sound is vowel-like based on sonorant and consonantal values."""
        sonorant_val = 0.0
        consonantal_val = 0.0
        
        for fval in features.features:
            if fval.feature == 'sonorant':
                sonorant_val = fval.value
            elif fval.feature == 'consonantal':
                consonantal_val = fval.value
        
        return sonorant_val > threshold and consonantal_val < -threshold
    
    def is_consonant_like(self, features: FeatureBundle, threshold: float = 0.3) -> bool:
        """Check if a sound is consonant-like."""
        consonantal_val = 0.0
        
        for fval in features.features:
            if fval.feature == 'consonantal':
                consonantal_val = fval.value
                break
        
        return consonantal_val > threshold