"""
Sound change rule definitions and representations.

This module defines the core rule types for the sound change engine,
supporting both traditional categorical changes and gradient modifications
using the unified distinctive feature system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Tuple, Any, Set
from enum import Enum
import random
import math

from ..feature_systems import (
    FeatureSystem, 
    FeatureValue, 
    FeatureBundle,
    FeatureValueType,
    get_feature_system
)
from ..sound_v2 import Sound


class ChangeType(Enum):
    """Types of sound changes."""
    CATEGORICAL = "categorical"      # Traditional A → B changes
    GRADIENT = "gradient"           # Gradual feature shifts
    PROBABILISTIC = "probabilistic"  # Changes with probability
    CONDITIONED = "conditioned"     # Environment-dependent changes


class ApplicationMode(Enum):
    """Modes of rule application."""
    IMMEDIATE = "immediate"         # Apply change completely
    GRADUAL = "gradual"            # Apply change incrementally
    PROBABILISTIC = "probabilistic" # Apply with given probability
    VARIABLE = "variable"          # Variable application strength


@dataclass
class FeatureChange:
    """Represents a change to a single feature."""
    feature_name: str
    target_value: Union[float, str, bool]
    change_strength: float = 1.0  # How much of the change to apply (0.0-1.0)
    change_type: ChangeType = ChangeType.CATEGORICAL
    
    def apply_to_feature(self, current_value: FeatureValue, 
                        feature_system: FeatureSystem) -> FeatureValue:
        """Apply this change to a feature value."""
        if current_value.feature != self.feature_name:
            return current_value
        
        if self.change_type == ChangeType.CATEGORICAL:
            # Simple replacement
            return FeatureValue(
                feature=self.feature_name,
                value=self.target_value,
                value_type=current_value.value_type
            )
        
        elif self.change_type == ChangeType.GRADIENT:
            # Gradient change for scalar features
            if current_value.value_type == FeatureValueType.SCALAR:
                current_val = float(current_value.value)
                target_val = float(self.target_value)
                
                # Apply partial change based on strength
                new_value = current_val + (target_val - current_val) * self.change_strength
                
                return FeatureValue(
                    feature=self.feature_name,
                    value=new_value,
                    value_type=FeatureValueType.SCALAR
                )
            else:
                # For non-scalar, fall back to categorical
                return FeatureValue(
                    feature=self.feature_name,
                    value=self.target_value,
                    value_type=current_value.value_type
                )
        
        return current_value


@dataclass
class EnvironmentalCondition:
    """Represents environmental conditions for rule application."""
    left_context: Optional[str] = None     # What comes before the target
    right_context: Optional[str] = None    # What comes after the target
    feature_conditions: Dict[str, Any] = field(default_factory=dict)  # Feature requirements
    boundary_conditions: List[str] = field(default_factory=list)     # Boundary requirements
    negative_conditions: List[str] = field(default_factory=list)     # What must NOT be present
    
    def matches(self, target_sound: Sound, left_sounds: List[Sound], 
                right_sounds: List[Sound], feature_system: FeatureSystem) -> bool:
        """Check if this condition matches the given context."""
        
        # Check left context
        if self.left_context:
            if not left_sounds or not self._matches_context_pattern(
                self.left_context, left_sounds[-1], feature_system):
                return False
        
        # Check right context  
        if self.right_context:
            if not right_sounds or not self._matches_context_pattern(
                self.right_context, right_sounds[0], feature_system):
                return False
        
        # Check feature conditions on target
        for feature_name, required_value in self.feature_conditions.items():
            if not target_sound.has_feature(feature_name):
                return False
            
            actual_value = target_sound.get_feature_value(feature_name)
            if not self._values_match(actual_value, required_value):
                return False
        
        # Check negative conditions
        for neg_condition in self.negative_conditions:
            if self._matches_negative_condition(neg_condition, target_sound, 
                                              left_sounds, right_sounds, feature_system):
                return False
        
        return True
    
    def _matches_context_pattern(self, pattern: str, sound: Sound, 
                                feature_system: FeatureSystem) -> bool:
        """Check if a sound matches a context pattern."""
        if pattern.startswith('[') and pattern.endswith(']'):
            # Feature specification like [+voiced, bilabial]
            feature_spec = pattern[1:-1]
            try:
                required_features = feature_system.parse_feature_specification(f"[{feature_spec}]")
                return self._sound_matches_features(sound, required_features)
            except (ValueError, KeyError, AttributeError) as e:
                # Failed to parse feature specification or feature system error
                return False
        else:
            # Simple grapheme match
            return sound.grapheme == pattern
    
    def _sound_matches_features(self, sound: Sound, required_features: FeatureBundle) -> bool:
        """Check if a sound matches required features."""
        for required_feature in required_features.features:
            if not sound.has_feature(required_feature.feature):
                return False
            
            actual_value = sound.get_feature_value(required_feature.feature)
            if not self._values_match(actual_value, required_feature.value):
                return False
        
        return True
    
    def _values_match(self, actual: Any, required: Any) -> bool:
        """Check if two feature values match."""
        if isinstance(required, str) and required.startswith('+'):
            # Positive feature specification
            return actual is True or actual == required[1:]
        elif isinstance(required, str) and required.startswith('-'):
            # Negative feature specification  
            return actual is False or actual != required[1:]
        else:
            # Direct value comparison
            if isinstance(actual, float) and isinstance(required, (int, float)):
                return abs(actual - float(required)) < 0.1  # Tolerance for scalar features
            return actual == required
    
    def _matches_negative_condition(self, condition: str, target_sound: Sound,
                                   left_sounds: List[Sound], right_sounds: List[Sound],
                                   feature_system: FeatureSystem) -> bool:
        """Check if a negative condition is violated."""
        # Implementation depends on specific negative condition format
        # For now, simple feature-based negative conditions
        if condition.startswith('[') and condition.endswith(']'):
            feature_spec = condition[1:-1]
            try:
                prohibited_features = feature_system.parse_feature_specification(f"[{feature_spec}]")
                return self._sound_matches_features(target_sound, prohibited_features)
            except (ValueError, KeyError, AttributeError) as e:
                # Failed to parse feature specification or feature system error
                return False
        return False


@dataclass
class SoundChangeRule:
    """
    Represents a sound change rule.
    
    This is the core rule type that can handle both traditional categorical
    changes (like p → f) and gradient changes using feature modifications.
    """
    name: str
    source_pattern: Union[str, FeatureBundle]  # What sounds this rule applies to
    target_pattern: Union[str, FeatureBundle, List[FeatureChange]]  # What they become
    environment: Optional[EnvironmentalCondition] = None
    probability: float = 1.0  # Probability of application (0.0-1.0)
    change_strength: float = 1.0  # Strength of gradient changes (0.0-1.0)
    application_mode: ApplicationMode = ApplicationMode.IMMEDIATE
    feature_system_name: str = "unified_distinctive"
    
    def __post_init__(self):
        """Initialize rule and validate parameters."""
        if not 0.0 <= self.probability <= 1.0:
            raise ValueError("Probability must be between 0.0 and 1.0")
        if not 0.0 <= self.change_strength <= 1.0:
            raise ValueError("Change strength must be between 0.0 and 1.0")
    
    def applies_to(self, sound: Sound, left_context: List[Sound], 
                   right_context: List[Sound]) -> bool:
        """Check if this rule applies to the given sound in context."""
        feature_system = get_feature_system(self.feature_system_name)
        
        # Check if sound matches source pattern
        if not self._matches_source_pattern(sound, feature_system):
            return False
        
        # Check environmental conditions
        if self.environment:
            if not self.environment.matches(sound, left_context, right_context, feature_system):
                return False
        
        # Check probability
        if self.probability < 1.0:
            return random.random() < self.probability
        
        return True
    
    def apply_to(self, sound: Sound) -> Sound:
        """Apply this rule to a sound, returning the changed sound."""
        feature_system = get_feature_system(self.feature_system_name)
        
        if isinstance(self.target_pattern, str):
            # Simple grapheme replacement
            return Sound(grapheme=self.target_pattern, feature_system=self.feature_system_name)
        
        elif isinstance(self.target_pattern, FeatureBundle):
            # Feature bundle replacement
            return Sound(features=self.target_pattern, feature_system=self.feature_system_name)
        
        elif isinstance(self.target_pattern, list):
            # List of feature changes
            current_features = sound.features
            modified_features = set(current_features.features)
            
            for feature_change in self.target_pattern:
                # Find and modify the relevant feature
                old_feature = current_features.get_feature(feature_change.feature_name)
                if old_feature:
                    modified_features.discard(old_feature)
                    new_feature = feature_change.apply_to_feature(old_feature, feature_system)
                    modified_features.add(new_feature)
                else:
                    # Add new feature if it doesn't exist
                    new_feature = FeatureValue(
                        feature=feature_change.feature_name,
                        value=feature_change.target_value,
                        value_type=FeatureValueType.SCALAR  # Default for unified system
                    )
                    modified_features.add(new_feature)
            
            new_bundle = FeatureBundle(frozenset(modified_features))
            return Sound(features=new_bundle, feature_system=self.feature_system_name)
        
        return sound  # No change if pattern type not recognized
    
    def _matches_source_pattern(self, sound: Sound, feature_system: FeatureSystem) -> bool:
        """Check if a sound matches the source pattern."""
        if isinstance(self.source_pattern, str):
            # Simple grapheme match
            return sound.grapheme() == self.source_pattern
        
        elif isinstance(self.source_pattern, FeatureBundle):
            # Feature bundle match - check if sound has all required features
            for required_feature in self.source_pattern.features:
                if not sound.has_feature(required_feature.feature):
                    return False
                
                actual_value = sound.get_feature_value(required_feature.feature)
                if isinstance(actual_value, float) and isinstance(required_feature.value, (int, float)):
                    # Tolerance for scalar features
                    if abs(actual_value - float(required_feature.value)) > 0.1:
                        return False
                elif actual_value != required_feature.value:
                    return False
            
            return True
        
        return False


@dataclass
class FeatureChangeRule(SoundChangeRule):
    """
    Specialized rule for pure feature-based changes.
    
    This is optimized for changes that modify specific features without
    regard to the original sound's identity.
    """
    feature_conditions: Dict[str, Any] = field(default_factory=dict)
    feature_changes: List[FeatureChange] = field(default_factory=list)
    
    def __post_init__(self):
        super().__post_init__()
        # Convert feature conditions and changes to appropriate target pattern
        self.target_pattern = self.feature_changes
    
    def applies_to(self, sound: Sound, left_context: List[Sound], 
                   right_context: List[Sound]) -> bool:
        """Check if this rule applies based on feature conditions."""
        # Check feature conditions
        for feature_name, required_value in self.feature_conditions.items():
            if not sound.has_feature(feature_name):
                return False
            
            actual_value = sound.get_feature_value(feature_name)
            if not self._values_match(actual_value, required_value):
                return False
        
        # Check environment and probability
        return super().applies_to(sound, left_context, right_context)
    
    def _values_match(self, actual: Any, required: Any) -> bool:
        """Check if feature values match (same logic as EnvironmentalCondition)."""
        if isinstance(required, str) and required.startswith('+'):
            return actual is True or actual == required[1:]
        elif isinstance(required, str) and required.startswith('-'):
            return actual is False or actual != required[1:]
        else:
            if isinstance(actual, float) and isinstance(required, (int, float)):
                return abs(actual - float(required)) < 0.1
            return actual == required


@dataclass
class RuleSet:
    """A collection of sound change rules with ordering and interaction."""
    rules: List[SoundChangeRule] = field(default_factory=list)
    name: str = "RuleSet"
    ordered: bool = True  # Whether rules are applied in order
    iterative: bool = False  # Whether to reapply rules until no changes
    max_iterations: int = 10  # Maximum iterations for iterative application
    
    def add_rule(self, rule: SoundChangeRule) -> None:
        """Add a rule to the set."""
        self.rules.append(rule)
    
    def remove_rule(self, rule_name: str) -> None:
        """Remove a rule by name."""
        self.rules = [r for r in self.rules if r.name != rule_name]
    
    def get_rule(self, rule_name: str) -> Optional[SoundChangeRule]:
        """Get a rule by name."""
        for rule in self.rules:
            if rule.name == rule_name:
                return rule
        return None
    
    def apply_to_sequence(self, sounds: List[Sound]) -> List[Sound]:
        """Apply all rules in the set to a sequence of sounds."""
        current_sounds = sounds.copy()
        
        if self.iterative:
            # Apply rules iteratively until no changes or max iterations
            for iteration in range(self.max_iterations):
                changed = False
                for rule in self.rules:
                    new_sounds, rule_changed = self._apply_rule_to_sequence(rule, current_sounds)
                    if rule_changed:
                        changed = True
                        current_sounds = new_sounds
                
                if not changed:
                    break
        else:
            # Apply rules once in order
            for rule in self.rules:
                current_sounds, _ = self._apply_rule_to_sequence(rule, current_sounds)
        
        return current_sounds
    
    def _apply_rule_to_sequence(self, rule: SoundChangeRule, 
                               sounds: List[Sound]) -> Tuple[List[Sound], bool]:
        """Apply a single rule to a sequence, returning modified sequence and whether changes occurred."""
        changed = False
        result_sounds = []
        
        for i, sound in enumerate(sounds):
            left_context = sounds[max(0, i-2):i] if i > 0 else []
            right_context = sounds[i+1:i+3] if i < len(sounds)-1 else []
            
            if rule.applies_to(sound, left_context, right_context):
                modified_sound = rule.apply_to(sound)
                result_sounds.append(modified_sound)
                if modified_sound != sound:  # Check if actually changed
                    changed = True
            else:
                result_sounds.append(sound)
        
        return result_sounds, changed


@dataclass
class RuleApplication:
    """Records the application of a rule to a specific sound."""
    rule_name: str
    original_sound: Sound
    modified_sound: Sound
    context_left: List[Sound] = field(default_factory=list)
    context_right: List[Sound] = field(default_factory=list)
    application_strength: float = 1.0
    timestamp: Optional[str] = None
    
    @property
    def changed(self) -> bool:
        """Whether the rule actually changed the sound."""
        return self.original_sound != self.modified_sound
    
    def get_feature_changes(self) -> Dict[str, Tuple[Any, Any]]:
        """Get a dictionary of feature changes (feature_name -> (old_value, new_value))."""
        changes = {}
        
        orig_features = {f.feature: f.value for f in self.original_sound.features.features}
        mod_features = {f.feature: f.value for f in self.modified_sound.features.features}
        
        all_features = set(orig_features.keys()) | set(mod_features.keys())
        
        for feature in all_features:
            old_val = orig_features.get(feature, None)
            new_val = mod_features.get(feature, None)
            
            if old_val != new_val:
                changes[feature] = (old_val, new_val)
        
        return changes