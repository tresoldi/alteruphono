"""
Environmental condition matching for sound change rules.

This module provides sophisticated pattern matching for phonological
environments, supporting feature-based conditions, boundaries, and
complex contextual patterns.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Union, Dict, Any, Pattern
import re

from ..sound_v2 import Sound
from ..feature_systems import FeatureBundle, get_feature_system


class EnvironmentMatcher(ABC):
    """Abstract base class for environment matchers."""
    
    @abstractmethod
    def matches(self, target_sound: Sound, left_context: List[Sound], 
                right_context: List[Sound]) -> bool:
        """Check if the environment matches."""
        pass


class SegmentMatcher(EnvironmentMatcher):
    """Matches specific segments by grapheme."""
    
    def __init__(self, grapheme: str):
        self.grapheme = grapheme
    
    def matches(self, target_sound: Sound, left_context: List[Sound], 
                right_context: List[Sound]) -> bool:
        """Match exact grapheme."""
        return target_sound.grapheme == self.grapheme


class FeatureMatcher(EnvironmentMatcher):
    """Matches sounds based on phonological features."""
    
    def __init__(self, feature_conditions: Dict[str, Any], 
                 feature_system_name: str = "unified_distinctive"):
        self.feature_conditions = feature_conditions
        self.feature_system_name = feature_system_name
        self.feature_system = get_feature_system(feature_system_name)
    
    def matches(self, target_sound: Sound, left_context: List[Sound], 
                right_context: List[Sound]) -> bool:
        """Match based on feature values."""
        for feature_name, required_value in self.feature_conditions.items():
            if not target_sound.has_feature(feature_name):
                return False
            
            actual_value = target_sound.get_feature_value(feature_name)
            if not self._values_match(actual_value, required_value):
                return False
        
        return True
    
    def _values_match(self, actual: Any, required: Any) -> bool:
        """Check if feature values match with support for +/- notation."""
        if isinstance(required, str):
            if required.startswith('+'):
                # Positive feature
                feature_name = required[1:]
                return actual is True or actual == feature_name or (
                    isinstance(actual, (int, float)) and float(actual) > 0
                )
            elif required.startswith('-'):
                # Negative feature  
                feature_name = required[1:]
                return actual is False or actual != feature_name or (
                    isinstance(actual, (int, float)) and float(actual) <= 0
                )
        
        # Direct value comparison
        if isinstance(actual, float) and isinstance(required, (int, float)):
            return abs(actual - float(required)) < 0.6  # More tolerant for scalar features
        
        return actual == required


class BoundaryMatcher(EnvironmentMatcher):
    """Matches word or morpheme boundaries."""
    
    def __init__(self, boundary_type: str = "word"):
        self.boundary_type = boundary_type  # "word", "morpheme", "syllable", etc.
    
    def matches(self, target_sound: Sound, left_context: List[Sound], 
                right_context: List[Sound]) -> bool:
        """Match boundary conditions."""
        if self.boundary_type == "word":
            # Word boundary - check if at beginning or end of context
            return len(left_context) == 0 or len(right_context) == 0
        
        # Additional boundary types can be implemented here
        return False


class SequenceMatcher(EnvironmentMatcher):
    """Matches sequences of sounds with complex patterns."""
    
    def __init__(self, pattern: str, feature_system_name: str = "unified_distinctive"):
        self.pattern = pattern
        self.feature_system_name = feature_system_name
        self.feature_system = get_feature_system(feature_system_name)
        self.compiled_pattern = self._compile_pattern(pattern)
    
    def _compile_pattern(self, pattern: str) -> List[EnvironmentMatcher]:
        """Compile pattern string into matcher objects."""
        matchers = []
        tokens = self._tokenize_pattern(pattern)
        
        for token in tokens:
            if token.startswith('[') and token.endswith(']'):
                # Feature specification
                feature_spec = token[1:-1]
                feature_conditions = self._parse_feature_spec(feature_spec)
                matchers.append(FeatureMatcher(feature_conditions, self.feature_system_name))
            elif token == '#':
                # Word boundary
                matchers.append(BoundaryMatcher("word"))
            elif token == '.':
                # Syllable boundary
                matchers.append(BoundaryMatcher("syllable"))
            elif token in ['V', 'C', 'S', 'O', 'N', 'L']:
                # Sound class - convert to feature specification
                sound_class_features = self.feature_system.get_sound_class_features(token)
                if sound_class_features:
                    feature_conditions = {fval.feature: fval.value for fval in sound_class_features.features}
                    matchers.append(FeatureMatcher(feature_conditions, self.feature_system_name))
                else:
                    # Fallback to literal if sound class not found
                    matchers.append(SegmentMatcher(token))
            else:
                # Literal segment
                matchers.append(SegmentMatcher(token))
        
        return matchers
    
    def _tokenize_pattern(self, pattern: str) -> List[str]:
        """Tokenize pattern string into components."""
        tokens = []
        i = 0
        
        while i < len(pattern):
            if pattern[i] == '[':
                # Find matching closing bracket
                bracket_count = 1
                j = i + 1
                while j < len(pattern) and bracket_count > 0:
                    if pattern[j] == '[':
                        bracket_count += 1
                    elif pattern[j] == ']':
                        bracket_count -= 1
                    j += 1
                
                if bracket_count == 0:
                    tokens.append(pattern[i:j])
                    i = j
                else:
                    # Unmatched bracket, treat as literal
                    tokens.append(pattern[i])
                    i += 1
            elif pattern[i] in '#.':
                # Special boundary symbols
                tokens.append(pattern[i])
                i += 1
            elif pattern[i].isspace():
                # Skip whitespace
                i += 1
            else:
                # Regular character
                tokens.append(pattern[i])
                i += 1
        
        return tokens
    
    def _parse_feature_spec(self, spec: str) -> Dict[str, Any]:
        """Parse feature specification string."""
        conditions = {}
        
        # Split by commas, but be careful with nested structures
        features = [f.strip() for f in spec.split(',')]
        
        for feature in features:
            if '=' in feature:
                # Feature with explicit value
                name, value = feature.split('=', 1)
                name = name.strip()
                value = value.strip()
                
                # Try to convert value to appropriate type
                try:
                    if value.lower() in ('true', 'false'):
                        conditions[name] = value.lower() == 'true'
                    else:
                        conditions[name] = float(value)
                except ValueError:
                    conditions[name] = value
            else:
                # Binary feature with +/- notation
                feature = feature.strip()
                if feature.startswith(('+', '-')):
                    conditions[feature[1:]] = feature
                else:
                    # Assume positive
                    conditions[feature] = f"+{feature}"
        
        return conditions
    
    def matches(self, target_sound: Sound, left_context: List[Sound], 
                right_context: List[Sound]) -> bool:
        """Match sequence pattern."""
        # This is a simplified implementation
        # A full implementation would need more sophisticated pattern matching
        if not self.compiled_pattern:
            return True
        
        # For now, just check if first matcher matches target
        if self.compiled_pattern:
            return self.compiled_pattern[0].matches(target_sound, left_context, right_context)
        
        return True


@dataclass
class PhonologicalEnvironment:
    """
    Represents a complete phonological environment for rule application.
    
    This combines multiple types of matchers to specify complex environmental
    conditions for sound change rules.
    """
    left_pattern: Optional[str] = None
    right_pattern: Optional[str] = None
    target_conditions: Optional[Dict[str, Any]] = None
    exclusion_conditions: Optional[List[str]] = None
    feature_system_name: str = "unified_distinctive"
    
    def __post_init__(self):
        """Compile patterns into matchers."""
        self.left_matcher = None
        self.right_matcher = None
        self.target_matcher = None
        self.exclusion_matchers = []
        
        if self.left_pattern:
            self.left_matcher = SequenceMatcher(self.left_pattern, self.feature_system_name)
        
        if self.right_pattern:
            self.right_matcher = SequenceMatcher(self.right_pattern, self.feature_system_name)
        
        if self.target_conditions:
            self.target_matcher = FeatureMatcher(self.target_conditions, self.feature_system_name)
        
        if self.exclusion_conditions:
            for condition in self.exclusion_conditions:
                if condition.startswith('[') and condition.endswith(']'):
                    feature_spec = condition[1:-1]
                    feature_conditions = self._parse_feature_spec(feature_spec)
                    self.exclusion_matchers.append(
                        FeatureMatcher(feature_conditions, self.feature_system_name)
                    )
    
    def matches(self, target_sound: Sound, left_context: List[Sound], 
                right_context: List[Sound]) -> bool:
        """Check if environment matches the given context."""
        
        # Check target conditions
        if self.target_matcher:
            if not self.target_matcher.matches(target_sound, left_context, right_context):
                return False
        
        # Check left context
        if self.left_matcher:
            if not left_context:
                return False
            # For simplicity, check against last sound in left context
            if not self.left_matcher.matches(left_context[-1], left_context[:-1], [target_sound]):
                return False
        
        # Check right context
        if self.right_matcher:
            if not right_context:
                return False
            # Check against first sound in right context  
            if not self.right_matcher.matches(right_context[0], [target_sound], right_context[1:]):
                return False
        
        # Check exclusion conditions
        for exclusion_matcher in self.exclusion_matchers:
            if exclusion_matcher.matches(target_sound, left_context, right_context):
                return False
        
        return True
    
    def _parse_feature_spec(self, spec: str) -> Dict[str, Any]:
        """Parse feature specification (same as SequenceMatcher)."""
        conditions = {}
        features = [f.strip() for f in spec.split(',')]
        
        for feature in features:
            if '=' in feature:
                name, value = feature.split('=', 1)
                name = name.strip()
                value = value.strip()
                
                try:
                    if value.lower() in ('true', 'false'):
                        conditions[name] = value.lower() == 'true'
                    else:
                        conditions[name] = float(value)
                except ValueError:
                    conditions[name] = value
            else:
                feature = feature.strip()
                if feature.startswith(('+', '-')):
                    conditions[feature[1:]] = feature
                else:
                    conditions[feature] = f"+{feature}"
        
        return conditions
    
    @classmethod
    def from_string(cls, environment_string: str, 
                   feature_system_name: str = "unified_distinctive") -> 'PhonologicalEnvironment':
        """
        Create environment from string representation.
        
        Format: "left_pattern _ right_pattern / [target_conditions] // [exclusions]"
        Example: "V _ V / [+consonantal] // [-voice]"
        """
        # Parse the environment string
        parts = environment_string.split('//')
        main_part = parts[0].strip()
        exclusions = parts[1].strip() if len(parts) > 1 else None
        
        # Split main part by '/'
        context_and_target = main_part.split('/')
        context_part = context_and_target[0].strip()
        target_part = context_and_target[1].strip() if len(context_and_target) > 1 else None
        
        # Parse context (left _ right)
        if '_' in context_part:
            left_pattern, right_pattern = context_part.split('_', 1)
            left_pattern = left_pattern.strip() if left_pattern.strip() else None
            right_pattern = right_pattern.strip() if right_pattern.strip() else None
        else:
            left_pattern = None
            right_pattern = None
        
        # Parse target conditions
        target_conditions = None
        if target_part and target_part.startswith('[') and target_part.endswith(']'):
            feature_spec = target_part[1:-1]
            target_conditions = cls._parse_feature_spec_static(feature_spec)
        
        # Parse exclusions
        exclusion_conditions = None
        if exclusions:
            exclusion_conditions = [exclusions]
        
        return cls(
            left_pattern=left_pattern,
            right_pattern=right_pattern,
            target_conditions=target_conditions,
            exclusion_conditions=exclusion_conditions,
            feature_system_name=feature_system_name
        )
    
    @staticmethod
    def _parse_feature_spec_static(spec: str) -> Dict[str, Any]:
        """Static version of feature spec parsing."""
        conditions = {}
        features = [f.strip() for f in spec.split(',')]
        
        for feature in features:
            if '=' in feature:
                name, value = feature.split('=', 1)
                name = name.strip()
                value = value.strip()
                
                try:
                    if value.lower() in ('true', 'false'):
                        conditions[name] = value.lower() == 'true'
                    else:
                        conditions[name] = float(value)
                except ValueError:
                    conditions[name] = value
            else:
                feature = feature.strip()
                if feature.startswith(('+', '-')):
                    conditions[feature[1:]] = feature
                else:
                    conditions[feature] = f"+{feature}"
        
        return conditions