"""
Sound change rule engine for alteruphono.

This module provides comprehensive tools for modeling phonological sound changes
using the unified distinctive feature system. It supports:

- Gradient sound changes with scalar feature modifications
- Probabilistic rule application
- Environmental conditioning
- Rule ordering and interaction
- Historical sound change simulation
"""

from .rules import (
    SoundChangeRule,
    FeatureChangeRule,
    EnvironmentalCondition,
    RuleSet,
    RuleApplication,
    ChangeType,
    ApplicationMode
)

from .engine import (
    SoundChangeEngine,
    RuleApplicationResult,
    ChangeSimulation
)

from .environments import (
    PhonologicalEnvironment,
    SegmentMatcher,
    FeatureMatcher,
    BoundaryMatcher,
    SequenceMatcher
)

from .gradients import (
    GradientChange,
    FeatureShift,
    PartialApplication,
    ChangeStrength
)

__all__ = [
    # Rule definitions
    'SoundChangeRule',
    'FeatureChangeRule', 
    'EnvironmentalCondition',
    'RuleSet',
    'RuleApplication',
    'ChangeType',
    'ApplicationMode',
    
    # Engine
    'SoundChangeEngine',
    'RuleApplicationResult',
    'ChangeSimulation',
    
    # Environment matching
    'PhonologicalEnvironment',
    'SegmentMatcher',
    'FeatureMatcher', 
    'BoundaryMatcher',
    'SequenceMatcher',
    
    # Gradient changes
    'GradientChange',
    'FeatureShift',
    'PartialApplication',
    'ChangeStrength'
]