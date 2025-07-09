"""
Semantic validator for phonological rules.

This module validates phonological and semantic constraints in parsed rules,
such as feature compatibility, backreference validity, and context well-formedness.
"""

from typing import List, Set, Dict, Tuple
from .ast_nodes import *
from .errors import PhonologicalError, SemanticError, ErrorCollector, ParseError


class PhonologicalValidator(BaseASTVisitor):
    """
    Validates phonological and semantic constraints in parsed rules.
    
    This ensures that rules are not only syntactically correct but also
    make phonological sense and don't have semantic errors like invalid
    backreferences.
    """
    
    # Feature oppositions - features that cannot coexist
    FEATURE_OPPOSITIONS = {
        ('voiced', 'voiceless'),
        ('high', 'low'),
        ('front', 'back'),
        ('rounded', 'unrounded'),
        ('tense', 'lax'),
        ('stop', 'fricative'),
        ('stop', 'nasal'),
        ('fricative', 'nasal'),
        ('fricative', 'approximant'),
        ('stop', 'approximant'),
    }
    
    # Feature dependencies - features that require other features
    # Note: sound classes like V (vowel) and C (consonant) implicitly have these features
    FEATURE_DEPENDENCIES = {
        'high': 'vowel',
        'low': 'vowel', 
        'front': 'vowel',
        'back': 'vowel',
        'rounded': 'vowel',
        'unrounded': 'vowel',
        'tense': 'vowel',
        'lax': 'vowel',
        'bilabial': 'consonant',
        'alveolar': 'consonant',
        'velar': 'consonant',
        'voiced': None,  # Can apply to vowels or consonants
        'voiceless': None,
    }
    
    # Sound classes that implicitly have certain features
    IMPLICIT_FEATURES = {
        'V': ['vowel'],  # Vowel sound class
        'C': ['consonant'],  # Consonant sound class
    }
    
    def __init__(self):
        """Initialize the validator."""
        self.errors = ErrorCollector()
        self.ante_length = 0
        self.context_left_length = 0
        self.context_right_length = 0
        
    def validate(self, rule_node: RuleNode) -> List[ParseError]:
        """
        Validate a complete rule and return any errors found.
        
        Args:
            rule_node: The rule AST to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        self.errors.clear()
        
        # Calculate sequence lengths for backreference validation
        self.ante_length = len(rule_node.ante.atoms)
        if rule_node.context:
            self.context_left_length = len(rule_node.context.left_context.atoms)
            self.context_right_length = len(rule_node.context.right_context.atoms)
        
        # Validate the rule
        self.visit(rule_node)
        
        return self.errors.get_errors()
    
    def visit_rule(self, node: RuleNode) -> None:
        """Validate a complete rule."""
        # Validate ante and post sequences
        self.visit(node.ante)
        self.visit(node.post)
        
        # Validate context if present
        if node.context:
            self.visit(node.context)
            
        # Check that rule makes phonological sense
        self._validate_rule_coherence(node)
    
    def visit_context(self, node: ContextNode) -> None:
        """Validate context structure."""
        # Context must have a focus position
        # (This is already enforced by the parser, but we double-check)
        
        # Validate left and right context sequences
        self.visit(node.left_context)
        self.visit(node.right_context)
    
    def visit_segment(self, node: SegmentNode) -> None:
        """Validate a segment node."""
        if node.features:
            self._validate_feature_spec(node.features, node.grapheme)
    
    def visit_sound_class(self, node: SoundClassNode) -> None:
        """Validate a sound class node."""
        if node.features:
            self._validate_feature_spec(node.features, node.class_name, node.class_name)
    
    def visit_backref(self, node: BackRefNode) -> None:
        """Validate a backreference node."""
        # Check that backreference index is valid
        total_length = (self.context_left_length + 
                       self.ante_length + 
                       self.context_right_length)
        
        if node.index < 0 or node.index >= total_length:
            self.errors.add_error(SemanticError(
                message=f"Backreference @{node.index + 1} is invalid: only {total_length} segments available",
                position=node.position,
                line=node.line,
                column=node.column,
                suggestions=[
                    f"Use @1 through @{total_length} for valid backreferences",
                    "Check that you have enough segments in the ante and context"
                ]
            ))
        
        # Validate features if present
        if node.features:
            self._validate_feature_spec(node.features, f"@{node.index + 1}")
    
    def visit_choice(self, node: ChoiceNode) -> None:
        """Validate a choice node."""
        if len(node.alternatives) < 2:
            self.errors.add_error(SemanticError(
                message="Choice must have at least 2 alternatives",
                position=node.position,
                line=node.line,
                column=node.column,
                suggestions=["Use 'a|b' format with at least two options"]
            ))
        
        # Validate each alternative
        for alt in node.alternatives:
            self.visit(alt)
    
    def visit_set(self, node: SetNode) -> None:
        """Validate a set node."""
        if len(node.alternatives) < 2:
            self.errors.add_error(SemanticError(
                message="Set must have at least 2 alternatives",
                position=node.position,
                line=node.line,
                column=node.column,
                suggestions=["Use '{a|b}' format with at least two options"]
            ))
        
        # Validate each alternative
        for alt in node.alternatives:
            self.visit(alt)
    
    def _validate_feature_spec(self, feature_spec: FeatureSpecNode, context: str, sound_class: str = None) -> None:
        """
        Validate a feature specification.
        
        Args:
            feature_spec: The feature specification to validate
            context: Description of where this feature spec appears (for error messages)
            sound_class: The sound class name (if applicable) to check for implicit features
        """
        features = {}
        
        # Check if we have a sound class with implicit features
        implicit_features = set()
        if sound_class and sound_class in self.IMPLICIT_FEATURES:
            implicit_features.update(self.IMPLICIT_FEATURES[sound_class])
        
        for feature_node in feature_spec.features:
            feature_name = feature_node.name
            polarity = feature_node.polarity
            
            # Check for contradictory features
            for existing_name, existing_polarity in features.items():
                if self._are_contradictory(
                    (feature_name, polarity), 
                    (existing_name, existing_polarity)
                ):
                    self.errors.add_error(PhonologicalError(
                        message=f"Contradictory features in {context}: {self._format_feature(existing_name, existing_polarity)} and {self._format_feature(feature_name, polarity)}",
                        position=feature_node.position,
                        line=feature_node.line,
                        column=feature_node.column,
                        suggestions=[
                            f"Remove one of the contradictory features",
                            f"Use either {self._format_feature(feature_name, '+')} or {self._format_feature(feature_name, '-')}"
                        ]
                    ))
            
            # Check feature dependencies (considering implicit features)
            dependency = self.FEATURE_DEPENDENCIES.get(feature_name)
            if dependency and dependency not in [f for f, _ in features.items()] and dependency not in implicit_features:
                self.errors.add_error(PhonologicalError(
                    message=f"Feature '{feature_name}' in {context} requires '{dependency}' feature",
                    position=feature_node.position,
                    line=feature_node.line,
                    column=feature_node.column,
                    suggestions=[f"Add '{dependency}' feature or remove '{feature_name}'"]
                ))
            
            features[feature_name] = polarity
    
    def _are_contradictory(
        self, 
        feature1: Tuple[str, str], 
        feature2: Tuple[str, str]
    ) -> bool:
        """
        Check if two features are contradictory.
        
        Args:
            feature1: (name, polarity) tuple for first feature
            feature2: (name, polarity) tuple for second feature
            
        Returns:
            True if features contradict each other
        """
        name1, pol1 = feature1
        name2, pol2 = feature2
        
        # Same feature with opposite polarities
        if name1 == name2 and pol1 and pol2 and pol1 != pol2:
            return True
        
        # Check feature oppositions
        for opp1, opp2 in self.FEATURE_OPPOSITIONS:
            if ((name1 == opp1 and name2 == opp2) or 
                (name1 == opp2 and name2 == opp1)):
                # Both features are positive (or have no polarity)
                if (pol1 != '-' and pol2 != '-'):
                    return True
        
        return False
    
    def _format_feature(self, name: str, polarity: str) -> str:
        """Format a feature with its polarity for display."""
        if polarity:
            return f"{polarity}{name}"
        return name
    
    def _validate_rule_coherence(self, rule_node: RuleNode) -> None:
        """
        Validate that the rule as a whole makes phonological sense.
        
        This checks for things like:
        - Reasonable feature changes
        - Consistent use of sound classes
        - Proper context structure
        """
        # Check that ante and post have compatible length
        # (accounting for insertions and deletions)
        ante_atoms = rule_node.ante.atoms
        post_atoms = rule_node.post.atoms
        
        # Count non-backreference atoms in post
        post_non_backref = sum(1 for atom in post_atoms if not isinstance(atom, BackRefNode))
        
        # For now, just check that we don't have obvious mismatches
        # More sophisticated checks can be added later
        if len(ante_atoms) == 0 and post_non_backref > 1:
            self.errors.add_error(SemanticError(
                message="Cannot insert multiple segments with empty ante",
                position=rule_node.position,
                line=rule_node.line,
                column=rule_node.column,
                suggestions=["Use specific contexts for multi-segment insertion"]
            ))


class FeatureValidator:
    """
    Specialized validator for feature systems.
    
    This can be extended with language-specific feature systems
    and more sophisticated phonological constraints.
    """
    
    def __init__(self, feature_system: str = "standard"):
        """
        Initialize with a specific feature system.
        
        Args:
            feature_system: Name of the feature system to use
        """
        self.feature_system = feature_system
        self.load_feature_system()
    
    def load_feature_system(self) -> None:
        """Load the specified feature system."""
        # For now, use the standard system
        # Future versions can load language-specific systems
        pass
    
    def validate_feature_combination(self, features: List[str]) -> List[str]:
        """
        Validate a combination of features.
        
        Args:
            features: List of feature names
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Check for basic contradictions
        if 'voiced' in features and 'voiceless' in features:
            errors.append("Cannot be both voiced and voiceless")
        
        if 'high' in features and 'low' in features:
            errors.append("Cannot be both high and low")
        
        # Add more sophisticated checks here
        
        return errors