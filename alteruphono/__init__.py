# __init__.py

"""
__init__ module for the `alteruphono` package.
"""

# Version of the alteruphono package  
__version__ = "0.8.0"  # Pluggable feature systems with unified distinctive features
__author__ = "Tiago Tresoldi"
__email__ = "tiago.tresoldi@lingfil.uu.se"

# Build the namespace
from alteruphono.model import (
    BoundaryToken,
    ProsodicBoundaryToken,  # Phase 4: Prosodic boundaries
    FocusToken,
    EmptyToken,
    BackRefToken,
    ChoiceToken,
    SetToken,
    SegmentToken,
)
from alteruphono.parser import Rule, parse_rule, parse_seq_as_rule
from alteruphono.common import check_match
from alteruphono.forward import forward
from alteruphono.backward import backward

# Feature system imports (new in v0.8.0)
from alteruphono.phonology.feature_systems import (
    # Core classes
    FeatureSystem,
    FeatureValue,
    FeatureBundle,
    FeatureValueType,
    
    # Built-in systems
    IPACategoricalSystem,
    UnifiedDistinctiveSystem,
    
    # Registry functions
    get_feature_system,
    register_feature_system,
    list_feature_systems,
    get_default_feature_system,
    set_default_feature_system,
)

# Enhanced Sound class
from alteruphono.phonology.sound_v2 import Sound as EnhancedSound

# Conversion utilities
from alteruphono.phonology.feature_systems.conversion import (
    convert_sound_between_systems,
    feature_system_context,
    get_conversion_recommendations
)
