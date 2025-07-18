"""
Pluggable feature system architecture for alteruphono.

This module provides a flexible framework for supporting different phonological
feature systems, from traditional IPA-based categorical features to modern
unified distinctive feature systems with continuous values.

The architecture allows:
1. Multiple feature systems to coexist
2. Easy switching between systems
3. Feature system-specific operations and constraints
4. Conversion between compatible systems
"""

from .base import (
    FeatureSystem,
    FeatureValue,
    FeatureBundle,
    FeatureSystemRegistry,
    FeatureValueType
)
from .ipa_categorical import IPACategoricalSystem
from .unified_distinctive import UnifiedDistinctiveSystem
from .tresoldi_distinctive import TresoldiDistinctiveSystem
from .registry import get_feature_system, register_feature_system, list_feature_systems, get_default_feature_system, set_default_feature_system
from .conversion_utils import (
    convert_between_systems,
    get_system_compatibility_matrix,
    convert_sound_between_systems,
    analyze_conversion_quality,
    FeatureSystemConverter
)

# Import to trigger registration
from . import registry_init

# Default feature system (backward compatibility)
DEFAULT_FEATURE_SYSTEM = "ipa_categorical"

__all__ = [
    # Core architecture
    'FeatureSystem',
    'FeatureValue', 
    'FeatureBundle',
    'FeatureSystemRegistry',
    'FeatureValueType',
    
    # Built-in systems
    'IPACategoricalSystem',
    'UnifiedDistinctiveSystem',
    'TresoldiDistinctiveSystem',
    
    # Registry functions
    'get_feature_system',
    'register_feature_system', 
    'list_feature_systems',
    'get_default_feature_system',
    'set_default_feature_system',
    
    # Conversion utilities
    'convert_between_systems',
    'get_system_compatibility_matrix',
    'convert_sound_between_systems',
    'analyze_conversion_quality',
    'FeatureSystemConverter',
    
    # Configuration
    'DEFAULT_FEATURE_SYSTEM'
]