"""
Gradient and probabilistic sound change modeling.

This module provides specialized tools for modeling gradient phonological
changes using the unified distinctive feature system's scalar capabilities.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable, Any
from enum import Enum
import math
import random
# import numpy as np  # Optional dependency

from .rules import FeatureChange, SoundChangeRule, ChangeType
from ..sound_v2 import Sound
from ..feature_systems import FeatureValue, FeatureValueType, get_feature_system


class ChangeStrength(Enum):
    """Predefined change strength levels."""
    MINIMAL = 0.1
    WEAK = 0.25
    MODERATE = 0.5
    STRONG = 0.75
    COMPLETE = 1.0


@dataclass
class GradientChange:
    """
    Represents a gradient change in phonological features.
    
    This enables modeling of partial sound changes, such as:
    - Partial voicing (voice=0.3 instead of full voice=1.0)
    - Gradual formant shifts
    - Progressive articulatory changes
    """
    feature_name: str
    source_value: float
    target_value: float
    change_rate: float = 0.1  # How much change per application
    min_threshold: float = 0.05  # Minimum change to be noticeable
    max_change: float = 1.0  # Maximum total change possible
    
    def apply_step(self, current_value: float, strength: float = 1.0) -> float:
        """Apply one step of the gradient change."""
        # Calculate direction and magnitude
        direction = 1 if self.target_value > self.source_value else -1
        magnitude = abs(self.target_value - current_value)
        
        # Apply change with rate and strength
        change_amount = min(
            self.change_rate * strength,
            magnitude,
            self.max_change
        )
        
        new_value = current_value + (direction * change_amount)
        
        # Clamp to valid range for unified distinctive system
        return max(-1.0, min(1.0, new_value))
    
    def is_complete(self, current_value: float) -> bool:
        """Check if the change has reached completion."""
        return abs(current_value - self.target_value) < self.min_threshold
    
    def get_progress(self, current_value: float) -> float:
        """Get progress of change as percentage (0.0-1.0)."""
        total_change = abs(self.target_value - self.source_value)
        if total_change == 0:
            return 1.0
        
        completed_change = abs(current_value - self.source_value)
        return min(1.0, completed_change / total_change)


@dataclass
class FeatureShift:
    """
    Models systematic shifts in feature values across multiple features.
    
    This can model phenomena like:
    - Vowel chain shifts
    - Consonant system reorganization
    - Prosodic changes
    """
    shifts: Dict[str, GradientChange] = field(default_factory=dict)
    correlation_matrix: Optional[Dict[Tuple[str, str], float]] = None
    
    def add_shift(self, feature_name: str, source_value: float, 
                  target_value: float, **kwargs) -> None:
        """Add a feature shift to the system."""
        self.shifts[feature_name] = GradientChange(
            feature_name=feature_name,
            source_value=source_value,
            target_value=target_value,
            **kwargs
        )
    
    def add_correlation(self, feature1: str, feature2: str, correlation: float) -> None:
        """Add correlation between two feature changes."""
        if self.correlation_matrix is None:
            self.correlation_matrix = {}
        
        self.correlation_matrix[(feature1, feature2)] = correlation
        self.correlation_matrix[(feature2, feature1)] = correlation
    
    def apply_to_sound(self, sound: Sound, strength: float = 1.0) -> Sound:
        """Apply the feature shift to a sound."""
        current_features = {f.feature: f.value for f in sound.features.features}
        modified_features = set()
        
        # Track which features are being modified
        changes_applied = {}
        
        # Apply each shift
        for feature_name, gradient_change in self.shifts.items():
            feature_value = sound.get_feature_value(feature_name)
            if feature_value is not None and isinstance(feature_value, (int, float)):
                current_val = float(feature_value)
                
                # Apply correlation adjustments
                adjusted_strength = strength
                if self.correlation_matrix:
                    for other_feature, other_change in changes_applied.items():
                        correlation_key = (feature_name, other_feature)
                        if correlation_key in self.correlation_matrix:
                            correlation = self.correlation_matrix[correlation_key]
                            adjusted_strength *= (1.0 + correlation * other_change)
                
                new_val = gradient_change.apply_step(current_val, adjusted_strength)
                change_amount = abs(new_val - current_val)
                changes_applied[feature_name] = change_amount
                
                # Create new feature value
                new_feature = FeatureValue(
                    feature=feature_name,
                    value=new_val,
                    value_type=FeatureValueType.SCALAR
                )
                modified_features.add(new_feature)
            else:
                # Keep original feature if not scalar
                original_feature = sound.features.get_feature(feature_name)
                if original_feature:
                    modified_features.add(original_feature)
        
        # Add all other features that weren't modified
        for feature in sound.features.features:
            if feature.feature not in self.shifts:
                modified_features.add(feature)
        
        # Create new sound with modified features
        from ..feature_systems import FeatureBundle
        new_bundle = FeatureBundle(frozenset(modified_features))
        return Sound(features=new_bundle, feature_system=sound.feature_system_name)


@dataclass
class PartialApplication:
    """
    Models partial application of sound change rules.
    
    This enables modeling of:
    - Variable rule application in sociolinguistics  
    - Incomplete sound changes
    - Gradient rule implementation
    """
    rule: SoundChangeRule
    application_probability: float = 1.0
    strength_distribution: Callable[[], float] = lambda: 1.0
    social_factors: Dict[str, float] = field(default_factory=dict)
    linguistic_factors: Dict[str, float] = field(default_factory=dict)
    
    def should_apply(self, sound: Sound, context: Dict[str, Any] = None) -> bool:
        """Determine if rule should apply based on probability and factors."""
        base_probability = self.application_probability
        
        # Adjust for social factors
        for factor, weight in self.social_factors.items():
            if context and factor in context:
                factor_value = context[factor]
                base_probability *= (1.0 + weight * factor_value)
        
        # Adjust for linguistic factors
        for factor, weight in self.linguistic_factors.items():
            if hasattr(sound, factor):
                factor_value = getattr(sound, factor, 0.0)
                base_probability *= (1.0 + weight * factor_value)
        
        return random.random() < base_probability
    
    def get_application_strength(self) -> float:
        """Get the strength of rule application."""
        return self.strength_distribution()
    
    def apply_to_sound(self, sound: Sound, context: Dict[str, Any] = None) -> Sound:
        """Apply the rule with partial strength."""
        if not self.should_apply(sound, context):
            return sound
        
        # Get application strength
        strength = self.get_application_strength()
        
        # Apply rule with modified strength
        original_strength = self.rule.change_strength
        self.rule.change_strength = strength
        
        try:
            result = self.rule.apply_to(sound)
        finally:
            # Restore original strength
            self.rule.change_strength = original_strength
        
        return result


class GradientRuleBuilder:
    """
    Builder class for creating gradient sound change rules.
    
    This provides a fluent interface for constructing complex gradient changes.
    """
    
    def __init__(self, feature_system_name: str = "unified_distinctive"):
        self.feature_system_name = feature_system_name
        self.feature_changes = []
        self.conditions = {}
        self.environment = None
        self.probability = 1.0
        self.strength = 1.0
    
    def shift_feature(self, feature_name: str, target_value: float, 
                     change_strength: float = 1.0) -> 'GradientRuleBuilder':
        """Add a feature shift to the rule."""
        change = FeatureChange(
            feature_name=feature_name,
            target_value=target_value,
            change_strength=change_strength,
            change_type=ChangeType.GRADIENT
        )
        self.feature_changes.append(change)
        return self
    
    def with_condition(self, feature_name: str, value: Any) -> 'GradientRuleBuilder':
        """Add a condition for rule application."""
        self.conditions[feature_name] = value
        return self
    
    def with_probability(self, prob: float) -> 'GradientRuleBuilder':
        """Set application probability."""
        self.probability = prob
        return self
    
    def with_strength(self, strength: float) -> 'GradientRuleBuilder':
        """Set change strength."""
        self.strength = strength
        return self
    
    def in_environment(self, env_string: str) -> 'GradientRuleBuilder':
        """Set environmental conditions."""
        from .environments import PhonologicalEnvironment
        self.environment = PhonologicalEnvironment.from_string(
            env_string, self.feature_system_name
        )
        return self
    
    def build(self, name: str) -> SoundChangeRule:
        """Build the final rule."""
        from .rules import FeatureChangeRule, EnvironmentalCondition
        
        # Convert environment to EnvironmentalCondition if needed
        env_condition = None
        if self.environment:
            env_condition = EnvironmentalCondition(
                feature_conditions=self.conditions
            )
        
        return FeatureChangeRule(
            name=name,
            source_pattern="",  # Will be determined by conditions
            target_pattern=self.feature_changes,
            environment=env_condition,
            probability=self.probability,
            change_strength=self.strength,
            feature_system_name=self.feature_system_name,
            feature_conditions=self.conditions,
            feature_changes=self.feature_changes
        )


def create_lenition_rule(strength: float = 0.5) -> SoundChangeRule:
    """
    Create a gradient lenition rule.
    
    This demonstrates how to create a rule that gradually increases
    continuancy and decreases consonantal values.
    """
    builder = GradientRuleBuilder()
    
    rule = (builder
            .shift_feature("continuant", 1.0, strength)
            .shift_feature("consonantal", -1.0, strength)
            .with_condition("consonantal", "+consonantal")
            .with_probability(0.8)
            .build("gradient_lenition"))
    
    return rule


def create_vowel_raising_rule(height_increase: float = 0.3) -> SoundChangeRule:
    """
    Create a gradient vowel raising rule.
    
    This demonstrates vowel height changes in chain shifts.
    """
    builder = GradientRuleBuilder()
    
    rule = (builder
            .shift_feature("high", height_increase)
            .shift_feature("low", -height_increase)
            .with_condition("sonorant", "+sonorant")
            .with_condition("consonantal", "-consonantal")
            .build("vowel_raising"))
    
    return rule


def create_voicing_assimilation_rule(strength: float = 0.7) -> SoundChangeRule:
    """
    Create a gradient voicing assimilation rule.
    
    This demonstrates how voicing can spread gradually between sounds.
    """
    builder = GradientRuleBuilder()
    
    rule = (builder
            .shift_feature("voice", 1.0, strength)
            .with_condition("consonantal", "+consonantal")
            .in_environment("_ [+voice]")
            .with_probability(0.9)
            .build("voicing_assimilation"))
    
    return rule


def model_sound_change_diffusion(initial_sounds: List[Sound], 
                                rule: SoundChangeRule,
                                generations: int = 100,
                                population_size: int = 1000,
                                innovation_rate: float = 0.01) -> Dict[str, Any]:
    """
    Model how a sound change diffuses through a population over time.
    
    This uses S-curve diffusion modeling to simulate realistic spread
    of phonological innovations.
    """
    # Track adoption of the change over time
    adoption_history = []
    current_adopters = 0
    
    for generation in range(generations):
        # Calculate adoption probability using S-curve
        adoption_pressure = current_adopters / population_size
        adoption_probability = innovation_rate * (1 - adoption_pressure) * adoption_pressure * 4
        
        # New adopters this generation
        new_adopters = sum(1 for _ in range(population_size - current_adopters) 
                          if random.random() < adoption_probability)
        
        current_adopters += new_adopters
        current_adopters = min(current_adopters, population_size)
        
        adoption_history.append({
            'generation': generation,
            'adopters': current_adopters,
            'percentage': current_adopters / population_size,
            'adoption_rate': new_adopters
        })
        
        # Stop if everyone has adopted
        if current_adopters >= population_size:
            break
    
    return {
        'adoption_history': adoption_history,
        'final_adoption_rate': current_adopters / population_size,
        'generations_to_completion': generation if current_adopters >= population_size else None,
        'peak_adoption_rate': max(h['adoption_rate'] for h in adoption_history)
    }