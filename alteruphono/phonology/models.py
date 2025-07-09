"""
Minimal phonological models for alteruphono.

This module provides basic grapheme-to-feature mappings and sound class definitions
needed for alteruphono's phonological operations.
"""

from typing import Dict, FrozenSet

# Basic grapheme-to-features mapping
# Based on common IPA symbols and their phonological features
GRAPHEME_FEATURES: Dict[str, FrozenSet[str]] = {
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
    
    # Additional common symbols
    'ɸ': frozenset(['consonant', 'bilabial', 'fricative', 'voiceless']),
    'β': frozenset(['consonant', 'bilabial', 'fricative', 'voiced']),
    'tʃ': frozenset(['consonant', 'postalveolar', 'affricate', 'voiceless']),
    'dʒ': frozenset(['consonant', 'postalveolar', 'affricate', 'voiced']),
    'sʼ': frozenset(['consonant', 'alveolar', 'fricative', 'voiceless', 'ejective']),
}

# Sound class mappings for common phonological notation
# These are used for pattern matching in rules
CLASS_FEATURES: Dict[str, FrozenSet[str]] = {
    'V': frozenset(['vowel']),                          # Any vowel
    'C': frozenset(['consonant']),                      # Any consonant
    'S': frozenset(['consonant', 'fricative']),         # Fricatives
    'N': frozenset(['consonant', 'nasal']),             # Nasals
    'L': frozenset(['consonant', 'liquid']),            # Liquids (l, r)
    'K': frozenset(['consonant', 'velar']),             # Velar consonants
    'SVL': frozenset(['consonant', 'voiceless']),       # Voiceless consonants
    'VD': frozenset(['consonant', 'voiced']),           # Voiced consonants
}

# Feature value mappings for feature arithmetic
FEATURE_MAPPINGS: Dict[str, str] = {
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
    'stress1': 'stress1',      # Primary stress
    'stress2': 'stress2',      # Secondary stress
    'unstressed': 'unstressed',
    '+stress': 'stress1',
    '-stress': 'unstressed',
    
    # Tone features (suprasegmental)
    'tone1': 'tone1',          # High tone
    'tone2': 'tone2',          # Mid tone  
    'tone3': 'tone3',          # Low tone
    'tone4': 'tone4',          # Extra low tone
    'tone5': 'tone5',          # Extra high tone
    'rising': 'rising',
    'falling': 'falling',
    'level': 'level',
    'high': 'tone1',
    'mid': 'tone2',
    'low': 'tone3',
    
    # Numeric features (for gradience)
    'f0_1': 'f0_1',            # Fundamental frequency level 1
    'f0_2': 'f0_2',            # Fundamental frequency level 2
    'f0_3': 'f0_3',            # Fundamental frequency level 3
    'f0_4': 'f0_4',            # Fundamental frequency level 4
    'f0_5': 'f0_5',            # Fundamental frequency level 5
    'duration_1': 'duration_1', # Duration level 1 (shortest)
    'duration_2': 'duration_2', # Duration level 2
    'duration_3': 'duration_3', # Duration level 3 (longest)
    
    # Other common features
    'ejective': 'ejective',
    '+ejective': 'ejective',
    '-ejective': 'plain',
}

def get_grapheme_features(grapheme: str) -> FrozenSet[str]:
    """Get feature set for a grapheme."""
    return GRAPHEME_FEATURES.get(grapheme, frozenset())

def get_class_features(sound_class: str) -> FrozenSet[str]:
    """Get feature set for a sound class."""
    return CLASS_FEATURES.get(sound_class, frozenset())

def normalize_feature(feature: str) -> str:
    """Normalize feature name to standard form."""
    return FEATURE_MAPPINGS.get(feature, feature)

def parse_features(feature_str: str) -> FrozenSet[str]:
    """Parse comma-separated feature string into normalized feature set."""
    if not feature_str:
        return frozenset()
    
    features = set()
    for feature in feature_str.split(','):
        feature = feature.strip()
        if feature:
            features.add(normalize_feature(feature))
    
    return frozenset(features)

def features_to_grapheme(features: FrozenSet[str]) -> str:
    """Find best grapheme match for a feature set."""
    # Find exact matches first
    for grapheme, grapheme_features in GRAPHEME_FEATURES.items():
        if features == grapheme_features:
            return grapheme
    
    # Find best partial match (most features in common)
    best_match = None
    best_score = 0
    
    for grapheme, grapheme_features in GRAPHEME_FEATURES.items():
        common_features = features & grapheme_features
        if len(common_features) > best_score:
            best_score = len(common_features)
            best_match = grapheme
    
    return best_match or '?'

def is_suprasegmental_feature(feature: str) -> bool:
    """Check if a feature is suprasegmental (stress, tone, etc.)."""
    suprasegmental_prefixes = ['stress', 'tone', 'f0_', 'duration_', 'rising', 'falling', 'level', 'unstressed']
    return any(feature.startswith(prefix) or feature == prefix for prefix in suprasegmental_prefixes)

def is_numeric_feature(feature: str) -> bool:
    """Check if a feature has numeric values."""
    numeric_prefixes = ['f0_', 'duration_', 'tone']
    return any(feature.startswith(prefix) for prefix in numeric_prefixes)

def get_numeric_value(feature: str) -> int:
    """Extract numeric value from a numeric feature."""
    if '_' in feature:
        parts = feature.split('_')
        if len(parts) == 2 and parts[1].isdigit():
            return int(parts[1])
    elif feature.startswith('tone') and len(feature) > 4 and feature[4:].isdigit():
        return int(feature[4:])
    return 0

def increment_numeric_feature(feature: str, amount: int = 1) -> str:
    """Increment a numeric feature by the given amount."""
    if not is_numeric_feature(feature):
        return feature
    
    current_value = get_numeric_value(feature)
    new_value = max(1, current_value + amount)  # Minimum value is 1
    
    if '_' in feature:
        prefix = feature.split('_')[0]
        return f"{prefix}_{new_value}"
    elif feature.startswith('tone'):
        return f"tone{new_value}"
    
    return feature

def decrement_numeric_feature(feature: str, amount: int = 1) -> str:
    """Decrement a numeric feature by the given amount."""
    return increment_numeric_feature(feature, -amount)