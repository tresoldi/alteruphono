"""
Feature system registration and initialization.

This module registers all built-in feature systems and sets up defaults.
It should be imported once during package initialization.
"""

from .registry import register_feature_system, set_default_feature_system
from .ipa_categorical import IPACategoricalSystem
from .unified_distinctive import UnifiedDistinctiveSystem
from .tresoldi_distinctive import TresoldiDistinctiveSystem


def initialize_feature_systems():
    """Register all built-in feature systems and set defaults."""
    
    # Register IPA categorical system (backward compatibility default)
    ipa_system = IPACategoricalSystem()
    register_feature_system(ipa_system)
    
    # Register unified distinctive system
    unified_system = UnifiedDistinctiveSystem()
    register_feature_system(unified_system)
    
    # Register Tresoldi distinctive system
    try:
        tresoldi_system = TresoldiDistinctiveSystem()
        register_feature_system(tresoldi_system)
    except Exception as e:
        print(f"Warning: Could not load Tresoldi feature system: {e}")
    
    # Set IPA as default for backward compatibility
    set_default_feature_system("ipa_categorical")


# Auto-initialize when module is imported
initialize_feature_systems()