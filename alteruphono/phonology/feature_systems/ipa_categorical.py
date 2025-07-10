"""
IPA-based categorical feature system.

This implements the traditional categorical feature system based on IPA symbols
and articulatory/acoustic features. This was the default system in alteruphono
before the pluggable architecture.
"""

from typing import Dict, FrozenSet, List, Optional, Set
from .base import (
    FeatureSystem, 
    FeatureValue, 
    FeatureBundle, 
    FeatureValueType
)


class IPACategoricalSystem(FeatureSystem):
    """
    Traditional IPA-based categorical feature system.
    
    Features are categorical labels like 'voiced', 'bilabial', 'vowel', etc.
    This maintains backward compatibility with the original alteruphono system.
    """
    
    def __init__(self):
        self._grapheme_features = self._build_grapheme_features()
        self._class_features = self._build_class_features()
        self._feature_mappings = self._build_feature_mappings()
    
    @property
    def name(self) -> str:
        return "ipa_categorical"
    
    @property
    def description(self) -> str:
        return "Traditional IPA-based categorical feature system with articulatory and acoustic features"
    
    @property
    def supported_value_types(self) -> Set[FeatureValueType]:
        return {FeatureValueType.CATEGORICAL, FeatureValueType.BINARY}
    
    def _build_grapheme_features(self) -> Dict[str, FrozenSet[str]]:
        """Build the grapheme-to-features mapping (from models.py)."""
        return {
            # Consonants - Stops
            'p': frozenset(['consonant', 'bilabial', 'stop', 'voiceless']),
            'b': frozenset(['consonant', 'bilabial', 'stop', 'voiced']),
            't': frozenset(['consonant', 'alveolar', 'stop', 'voiceless']),
            'd': frozenset(['consonant', 'alveolar', 'stop', 'voiced']),
            'k': frozenset(['consonant', 'velar', 'stop', 'voiceless']),
            'g': frozenset(['consonant', 'velar', 'stop', 'voiced']),
            'q': frozenset(['consonant', 'uvular', 'stop', 'voiceless']),
            'ʔ': frozenset(['consonant', 'glottal', 'stop', 'voiceless']),
            
            # Consonants - Fricatives
            'f': frozenset(['consonant', 'labiodental', 'fricative', 'voiceless']),
            'v': frozenset(['consonant', 'labiodental', 'fricative', 'voiced']),
            'θ': frozenset(['consonant', 'dental', 'fricative', 'voiceless']),
            'ð': frozenset(['consonant', 'dental', 'fricative', 'voiced']),
            's': frozenset(['consonant', 'alveolar', 'fricative', 'voiceless']),
            'z': frozenset(['consonant', 'alveolar', 'fricative', 'voiced']),
            'ʃ': frozenset(['consonant', 'postalveolar', 'fricative', 'voiceless']),
            'ʒ': frozenset(['consonant', 'postalveolar', 'fricative', 'voiced']),
            'x': frozenset(['consonant', 'velar', 'fricative', 'voiceless']),
            'ɣ': frozenset(['consonant', 'velar', 'fricative', 'voiced']),
            'h': frozenset(['consonant', 'glottal', 'fricative', 'voiceless']),
            
            # Consonants - Nasals
            'm': frozenset(['consonant', 'bilabial', 'nasal', 'voiced']),
            'n': frozenset(['consonant', 'alveolar', 'nasal', 'voiced']),
            'ŋ': frozenset(['consonant', 'velar', 'nasal', 'voiced']),
            
            # Consonants - Liquids
            'l': frozenset(['consonant', 'alveolar', 'lateral', 'voiced']),
            'r': frozenset(['consonant', 'alveolar', 'rhotic', 'voiced']),
            
            # Consonants - Approximants
            'w': frozenset(['consonant', 'labial', 'approximant', 'voiced']),
            'j': frozenset(['consonant', 'palatal', 'approximant', 'voiced']),
            
            # Vowels
            'i': frozenset(['vowel', 'high', 'front', 'unrounded']),
            'e': frozenset(['vowel', 'mid', 'front', 'unrounded']),
            'ɛ': frozenset(['vowel', 'low-mid', 'front', 'unrounded']),
            'a': frozenset(['vowel', 'low', 'central', 'unrounded']),
            'ɑ': frozenset(['vowel', 'low', 'back', 'unrounded']),
            'ɔ': frozenset(['vowel', 'low-mid', 'back', 'rounded']),
            'o': frozenset(['vowel', 'mid', 'back', 'rounded']),
            'u': frozenset(['vowel', 'high', 'back', 'rounded']),
            'ə': frozenset(['vowel', 'mid', 'central', 'unrounded']),
            
            # Additional symbols
            'ɸ': frozenset(['consonant', 'bilabial', 'fricative', 'voiceless']),
            'β': frozenset(['consonant', 'bilabial', 'fricative', 'voiced']),
            'tʃ': frozenset(['consonant', 'postalveolar', 'affricate', 'voiceless']),
            'dʒ': frozenset(['consonant', 'postalveolar', 'affricate', 'voiced']),
            'sʼ': frozenset(['consonant', 'alveolar', 'fricative', 'voiceless', 'ejective']),
        }
    
    def _build_class_features(self) -> Dict[str, FrozenSet[str]]:
        """Build the sound class mappings."""
        return {
            'V': frozenset(['vowel']),                          # Any vowel
            'C': frozenset(['consonant']),                      # Any consonant
            'S': frozenset(['consonant', 'fricative']),         # Fricatives
            'N': frozenset(['consonant', 'nasal']),             # Nasals
            'L': frozenset(['consonant', 'liquid']),            # Liquids (l, r)
            'K': frozenset(['consonant', 'velar']),             # Velar consonants
            'SVL': frozenset(['consonant', 'voiceless']),       # Voiceless consonants
            'VD': frozenset(['consonant', 'voiced']),           # Voiced consonants
        }
    
    def _build_feature_mappings(self) -> Dict[str, str]:
        """Build feature normalization mappings."""
        return {
            # Voice alternations
            'voiced': 'voiced',
            'voiceless': 'voiceless',
            '+voiced': 'voiced',
            '-voiced': 'voiceless',
            '+voice': 'voiced',
            '-voice': 'voiceless',
            
            # Place alternations
            'bilabial': 'bilabial',
            'alveolar': 'alveolar',
            'velar': 'velar',
            
            # Manner alternations
            'fricative': 'fricative',
            'stop': 'stop',
            'nasal': 'nasal',
            
            # Length features
            'long': 'long',
            '+long': 'long',
            '-long': 'short',
            
            # Stress features (suprasegmental)
            'stress1': 'stress1',
            'stress2': 'stress2',
            'unstressed': 'unstressed',
            '+stress': 'stress1',
            '-stress': 'unstressed',
            
            # Tone features (suprasegmental)
            'tone1': 'tone1',
            'tone2': 'tone2',
            'tone3': 'tone3',
            'tone4': 'tone4',
            'tone5': 'tone5',
            'rising': 'rising',
            'falling': 'falling',
            'level': 'level',
            'high': 'tone1',
            'mid': 'tone2',
            'low': 'tone3',
            
            # Numeric features (for gradience)
            'f0_1': 'f0_1',
            'f0_2': 'f0_2',
            'f0_3': 'f0_3',
            'f0_4': 'f0_4',
            'f0_5': 'f0_5',
            'duration_1': 'duration_1',
            'duration_2': 'duration_2',
            'duration_3': 'duration_3',
            
            # Other features
            'ejective': 'ejective',
            '+ejective': 'ejective',
            '-ejective': 'plain',
        }
    
    def _string_features_to_bundle(self, feature_strings: FrozenSet[str]) -> FeatureBundle:
        """Convert old-style string features to new FeatureBundle."""
        feature_values = set()
        
        for feature_str in feature_strings:
            # Normalize the feature name
            normalized = self.normalize_feature_name(feature_str)
            
            # Determine if it's binary or categorical
            if normalized.startswith('+') or normalized.startswith('-'):
                # Binary feature
                polarity = normalized[0] == '+'
                feature_name = normalized[1:]
                feature_values.add(FeatureValue(
                    feature=feature_name,
                    value=polarity,
                    value_type=FeatureValueType.BINARY
                ))
            else:
                # Categorical feature - use string value
                feature_values.add(FeatureValue(
                    feature=normalized,
                    value=normalized,  # Use feature name as value for categorical
                    value_type=FeatureValueType.CATEGORICAL
                ))
        
        return FeatureBundle(frozenset(feature_values))
    
    def _bundle_to_string_features(self, bundle: FeatureBundle) -> FrozenSet[str]:
        """Convert FeatureBundle back to old-style string features."""
        result = set()
        
        for fval in bundle.features:
            if fval.value_type == FeatureValueType.BINARY:
                prefix = '+' if fval.value else '-'
                result.add(f"{prefix}{fval.feature}")
            elif fval.value_type == FeatureValueType.CATEGORICAL:
                # For categorical features, the value is the feature name
                result.add(fval.value)
        
        return frozenset(result)
    
    def grapheme_to_features(self, grapheme: str) -> Optional[FeatureBundle]:
        """Convert a grapheme to its feature representation."""
        # Check regular graphemes
        if grapheme in self._grapheme_features:
            feature_strings = self._grapheme_features[grapheme]
            return self._string_features_to_bundle(feature_strings)
        
        # Check sound classes
        if grapheme in self._class_features:
            feature_strings = self._class_features[grapheme]
            bundle = self._string_features_to_bundle(feature_strings)
            # Sound classes are partial by definition
            return FeatureBundle(bundle.features, partial=True)
        
        return None
    
    def features_to_grapheme(self, features: FeatureBundle) -> str:
        """Convert features back to best-matching grapheme."""
        # Convert to old-style string features for lookup
        feature_strings = self._bundle_to_string_features(features)
        
        # Find exact matches first
        for grapheme, grapheme_features in self._grapheme_features.items():
            if feature_strings == grapheme_features:
                return grapheme
        
        # Find best partial match (most features in common)
        best_match = None
        best_score = 0
        
        for grapheme, grapheme_features in self._grapheme_features.items():
            common_features = feature_strings & grapheme_features
            if len(common_features) > best_score:
                best_score = len(common_features)
                best_match = grapheme
        
        return best_match or '?'
    
    def parse_feature_specification(self, spec: str) -> FeatureBundle:
        """Parse a feature specification string like '[voiced,bilabial]'."""
        # Remove brackets
        if spec.startswith('[') and spec.endswith(']'):
            spec = spec[1:-1]
        
        if not spec.strip():
            return FeatureBundle(frozenset())
        
        features = set()
        for feature in spec.split(','):
            feature = feature.strip()
            if not feature:
                continue
            
            # Normalize feature name
            normalized = self.normalize_feature_name(feature)
            
            # Parse binary features
            if normalized.startswith('+') or normalized.startswith('-'):
                polarity = normalized[0] == '+'
                feature_name = normalized[1:]
                features.add(FeatureValue(
                    feature=feature_name,
                    value=polarity,
                    value_type=FeatureValueType.BINARY
                ))
            else:
                # Categorical feature (present)
                features.add(FeatureValue(
                    feature=normalized,
                    value=normalized,
                    value_type=FeatureValueType.CATEGORICAL
                ))
        
        return FeatureBundle(frozenset(features))
    
    def get_sound_class_features(self, sound_class: str) -> Optional[FeatureBundle]:
        """Get features for a sound class."""
        if sound_class in self._class_features:
            feature_strings = self._class_features[sound_class]
            bundle = self._string_features_to_bundle(feature_strings)
            return FeatureBundle(bundle.features, partial=True)
        return None
    
    def add_features(self, base: FeatureBundle, additional: FeatureBundle) -> FeatureBundle:
        """Add features to a base bundle with IPA-specific rules."""
        result_features = set(base.features)
        
        # Apply additional features with conflict resolution
        for add_fval in additional.features:
            if add_fval.feature == 'voiced':
                # Remove conflicting voicing
                result_features = {f for f in result_features if f.feature != 'voiceless'}
                result_features.add(add_fval)
            elif add_fval.feature == 'voiceless':
                # Remove conflicting voicing
                result_features = {f for f in result_features if f.feature != 'voiced'}
                result_features.add(add_fval)
            elif add_fval.feature in ['fricative', 'stop', 'nasal', 'lateral', 'rhotic', 'approximant']:
                # Manner features are mutually exclusive
                manner_features = {'fricative', 'stop', 'nasal', 'lateral', 'rhotic', 'approximant', 'affricate'}
                result_features = {f for f in result_features if f.feature not in manner_features}
                result_features.add(add_fval)
            elif add_fval.feature.startswith('stress'):
                # Remove other stress features
                result_features = {f for f in result_features 
                                 if not f.feature.startswith('stress') and f.feature != 'unstressed'}
                result_features.add(add_fval)
            elif add_fval.feature == 'unstressed':
                # Remove stress features
                result_features = {f for f in result_features if not f.feature.startswith('stress')}
                result_features.add(add_fval)
            elif add_fval.feature.startswith('tone'):
                # Remove other tone features
                result_features = {f for f in result_features 
                                 if not (f.feature.startswith('tone') or f.feature in ['rising', 'falling', 'level'])}
                result_features.add(add_fval)
            elif add_fval.feature in ['rising', 'falling', 'level']:
                # Tone contour features
                result_features = {f for f in result_features 
                                 if f.feature not in ['rising', 'falling', 'level']}
                result_features.add(add_fval)
            else:
                # Regular feature addition (replace if exists)
                result_features = {f for f in result_features if f.feature != add_fval.feature}
                result_features.add(add_fval)
        
        return FeatureBundle(frozenset(result_features), base.partial)
    
    def validate_features(self, features: FeatureBundle) -> List[str]:
        """Validate feature bundle according to IPA constraints."""
        errors = []
        
        # Check for contradictory voicing
        has_voiced = any(f.feature == 'voiced' and f.value for f in features.features)
        has_voiceless = any(f.feature == 'voiceless' and f.value for f in features.features)
        if has_voiced and has_voiceless:
            errors.append("Contradictory voicing: cannot be both voiced and voiceless")
        
        # Check for multiple manner features
        manner_features = {'fricative', 'stop', 'nasal', 'lateral', 'rhotic', 'approximant', 'affricate'}
        active_manner = [f.feature for f in features.features 
                        if f.feature in manner_features and f.value]
        if len(active_manner) > 1:
            errors.append(f"Multiple manner features: {', '.join(active_manner)}")
        
        # Check for multiple stress levels
        stress_features = [f.feature for f in features.features 
                          if f.feature.startswith('stress') and f.value]
        if len(stress_features) > 1:
            errors.append(f"Multiple stress levels: {', '.join(stress_features)}")
        
        return errors
    
    def normalize_feature_name(self, feature: str) -> str:
        """Normalize feature name using the mapping table."""
        return self._feature_mappings.get(feature, feature)
    
    def is_suprasegmental_feature(self, feature_name: str) -> bool:
        """Check if a feature is suprasegmental."""
        suprasegmental_prefixes = ['stress', 'tone', 'f0_', 'duration_', 'rising', 'falling', 'level', 'unstressed']
        return any(feature_name.startswith(prefix) or feature_name == prefix 
                  for prefix in suprasegmental_prefixes)