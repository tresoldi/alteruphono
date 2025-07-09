"""
Abstract Syntax Tree node definitions for phonological rules.

This module defines the AST node hierarchy that represents the structure
of parsed phonological rules.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Union, Any


class ASTNode(ABC):
    """
    Base class for all AST nodes.
    
    All nodes track their position in the source for error reporting.
    """
    
    def __init__(self, position: int = 0, line: int = 1, column: int = 1):
        self.position = position
        self.line = line
        self.column = column
    
    @abstractmethod
    def accept(self, visitor):
        """Accept a visitor for the visitor pattern."""
        pass


class RuleNode(ASTNode):
    """
    Root node representing a complete phonological rule.
    
    Structure: ante > post / context
    """
    
    def __init__(self, ante: 'AtomSequenceNode', post: 'AtomSequenceNode', 
                 context: Optional['ContextNode'] = None, position: int = 0, 
                 line: int = 1, column: int = 1):
        super().__init__(position, line, column)
        self.ante = ante
        self.post = post
        self.context = context
    
    def accept(self, visitor):
        return visitor.visit_rule(self)


class ContextNode(ASTNode):
    """
    Node representing the context of a rule.
    
    Structure: left_context _ right_context
    """
    
    def __init__(self, left_context: 'AtomSequenceNode', right_context: 'AtomSequenceNode',
                 focus_position: int, position: int = 0, line: int = 1, column: int = 1):
        super().__init__(position, line, column)
        self.left_context = left_context
        self.right_context = right_context
        self.focus_position = focus_position
    
    def accept(self, visitor):
        return visitor.visit_context(self)


class AtomSequenceNode(ASTNode):
    """
    Node representing a sequence of atoms (segments, classes, etc.).
    """
    
    def __init__(self, atoms: List['AtomNode'], position: int = 0, line: int = 1, column: int = 1):
        super().__init__(position, line, column)
        self.atoms = atoms
    
    def accept(self, visitor):
        return visitor.visit_atom_sequence(self)


# Base class for all atom types
class AtomNode(ASTNode):
    """Base class for individual atoms in a rule."""
    pass


class SegmentNode(AtomNode):
    """
    Node representing a phonological segment.
    
    Examples: p, a, ɸ, p[voiced]
    """
    
    def __init__(self, grapheme: str, features: Optional['FeatureSpecNode'] = None,
                 position: int = 0, line: int = 1, column: int = 1):
        super().__init__(position, line, column)
        self.grapheme = grapheme
        self.features = features
    
    def accept(self, visitor):
        return visitor.visit_segment(self)


class SoundClassNode(AtomNode):
    """
    Node representing a sound class.
    
    Examples: V, C, S, S[voiceless]
    """
    
    def __init__(self, class_name: str, features: Optional['FeatureSpecNode'] = None,
                 position: int = 0, line: int = 1, column: int = 1):
        super().__init__(position, line, column)
        self.class_name = class_name
        self.features = features
    
    def accept(self, visitor):
        return visitor.visit_sound_class(self)


class ChoiceNode(AtomNode):
    """
    Node representing a choice between alternatives.
    
    Examples: p|t, V|C, a|e|i
    """
    
    def __init__(self, alternatives: List[AtomNode], position: int = 0, line: int = 1, column: int = 1):
        super().__init__(position, line, column)
        self.alternatives = alternatives
    
    def accept(self, visitor):
        return visitor.visit_choice(self)


class SetNode(AtomNode):
    """
    Node representing a set of alternatives.
    
    Examples: {p|t}, {a|e|i}
    """
    
    def __init__(self, alternatives: List[AtomNode], position: int = 0, line: int = 1, column: int = 1):
        super().__init__(position, line, column)
        self.alternatives = alternatives
    
    def accept(self, visitor):
        return visitor.visit_set(self)


class BackRefNode(AtomNode):
    """
    Node representing a backreference.
    
    Examples: @1, @2, @1[voiced]
    """
    
    def __init__(self, index: int, features: Optional['FeatureSpecNode'] = None,
                 position: int = 0, line: int = 1, column: int = 1):
        super().__init__(position, line, column)
        self.index = index
        self.features = features
    
    def accept(self, visitor):
        return visitor.visit_backref(self)


class BoundaryNode(AtomNode):
    """
    Node representing a word/morpheme boundary.
    
    Example: #
    """
    
    def __init__(self, position: int = 0, line: int = 1, column: int = 1):
        super().__init__(position, line, column)
    
    def accept(self, visitor):
        return visitor.visit_boundary(self)


class FocusNode(AtomNode):
    """
    Node representing the focus position in a context.
    
    Example: _
    """
    
    def __init__(self, position: int = 0, line: int = 1, column: int = 1):
        super().__init__(position, line, column)
    
    def accept(self, visitor):
        return visitor.visit_focus(self)


class NullNode(AtomNode):
    """
    Node representing deletion/insertion.
    
    Example: :null:
    """
    
    def __init__(self, position: int = 0, line: int = 1, column: int = 1):
        super().__init__(position, line, column)
    
    def accept(self, visitor):
        return visitor.visit_null(self)


# Feature-related nodes

class FeatureSpecNode(ASTNode):
    """
    Node representing a feature specification.
    
    Examples: [voiced], [voiced,bilabial], [+voice,-nasal]
    """
    
    def __init__(self, features: List['FeatureNode'], position: int = 0, line: int = 1, column: int = 1):
        super().__init__(position, line, column)
        self.features = features
    
    def accept(self, visitor):
        return visitor.visit_feature_spec(self)


class FeatureNode(ASTNode):
    """
    Node representing a single feature.
    
    Examples: voiced, +voiced, -voiced, F0=120
    """
    
    def __init__(self, name: str, polarity: Optional[str] = None,
                 value: Optional['FeatureValueNode'] = None,
                 position: int = 0, line: int = 1, column: int = 1):
        super().__init__(position, line, column)
        self.name = name
        self.polarity = polarity
        self.value = value
    
    def accept(self, visitor):
        return visitor.visit_feature(self)


class FeatureValueNode(ASTNode):
    """
    Node representing a feature value.
    
    Examples: 120, 120Hz, high, voiced
    """
    
    def __init__(self, value: str, unit: Optional[str] = None,
                 position: int = 0, line: int = 1, column: int = 1):
        super().__init__(position, line, column)
        self.value = value
        self.unit = unit
    
    def accept(self, visitor):
        return visitor.visit_feature_value(self)


# Future extension nodes (for advanced features)

class ProsodicUnitNode(AtomNode):
    """
    Node representing a prosodic unit.
    
    Examples: μ (mora), σ (syllable), Ft (foot), ω (word)
    """
    
    def __init__(self, unit_type: str, features: Optional[FeatureSpecNode] = None,
                 position: int = 0, line: int = 1, column: int = 1):
        super().__init__(position, line, column)
        self.unit_type = unit_type
        self.features = features
    
    def accept(self, visitor):
        return visitor.visit_prosodic_unit(self)


class VariableLengthNode(AtomNode):
    """
    Node representing variable-length sequences.
    
    Examples: C₀₋₃ (0-3 consonants), V+ (one or more vowels)
    """
    
    def __init__(self, atom: AtomNode, min_length: int, max_length: Optional[int] = None,
                 position: int = 0, line: int = 1, column: int = 1):
        super().__init__(position, line, column)
        self.atom = atom
        self.min_length = min_length
        self.max_length = max_length
    
    def accept(self, visitor):
        return visitor.visit_variable_length(self)


class ConditionalNode(ASTNode):
    """
    Node representing conditional rules.
    
    Example: if [stress=+] then p > b
    """
    
    def __init__(self, condition: 'ConditionNode', then_rule: RuleNode,
                 else_rule: Optional[RuleNode] = None,
                 position: int = 0, line: int = 1, column: int = 1):
        super().__init__(position, line, column)
        self.condition = condition
        self.then_rule = then_rule
        self.else_rule = else_rule
    
    def accept(self, visitor):
        return visitor.visit_conditional(self)


class ConditionNode(ASTNode):
    """
    Node representing a condition in a conditional rule.
    """
    
    def __init__(self, feature: FeatureNode, operator: str,
                 position: int = 0, line: int = 1, column: int = 1):
        super().__init__(position, line, column)
        self.feature = feature
        self.operator = operator
    
    def accept(self, visitor):
        return visitor.visit_condition(self)


# Visitor interface for AST traversal

class ASTVisitor(ABC):
    """
    Abstract base class for AST visitors.
    
    Implement this interface to traverse and process AST nodes.
    """
    
    @abstractmethod
    def visit_rule(self, node: RuleNode) -> Any:
        pass
    
    @abstractmethod
    def visit_context(self, node: ContextNode) -> Any:
        pass
    
    @abstractmethod
    def visit_atom_sequence(self, node: AtomSequenceNode) -> Any:
        pass
    
    @abstractmethod
    def visit_segment(self, node: SegmentNode) -> Any:
        pass
    
    @abstractmethod
    def visit_sound_class(self, node: SoundClassNode) -> Any:
        pass
    
    @abstractmethod
    def visit_choice(self, node: ChoiceNode) -> Any:
        pass
    
    @abstractmethod
    def visit_set(self, node: SetNode) -> Any:
        pass
    
    @abstractmethod
    def visit_backref(self, node: BackRefNode) -> Any:
        pass
    
    @abstractmethod
    def visit_boundary(self, node: BoundaryNode) -> Any:
        pass
    
    @abstractmethod
    def visit_focus(self, node: FocusNode) -> Any:
        pass
    
    @abstractmethod
    def visit_null(self, node: NullNode) -> Any:
        pass
    
    @abstractmethod
    def visit_feature_spec(self, node: FeatureSpecNode) -> Any:
        pass
    
    @abstractmethod
    def visit_feature(self, node: FeatureNode) -> Any:
        pass
    
    @abstractmethod
    def visit_feature_value(self, node: FeatureValueNode) -> Any:
        pass
    
    # Future extension methods
    def visit_prosodic_unit(self, node: ProsodicUnitNode) -> Any:
        """Visit prosodic unit node (future extension)."""
        raise NotImplementedError("Prosodic units not yet implemented")
    
    def visit_variable_length(self, node: VariableLengthNode) -> Any:
        """Visit variable length node (future extension)."""
        raise NotImplementedError("Variable length not yet implemented")
    
    def visit_conditional(self, node: ConditionalNode) -> Any:
        """Visit conditional node (future extension)."""
        raise NotImplementedError("Conditionals not yet implemented")
    
    def visit_condition(self, node: ConditionNode) -> Any:
        """Visit condition node (future extension)."""
        raise NotImplementedError("Conditions not yet implemented")


class BaseASTVisitor(ASTVisitor):
    """
    Base visitor that provides default implementations.
    
    Subclasses only need to override the methods they care about.
    """
    
    def visit_rule(self, node: RuleNode) -> Any:
        self.visit(node.ante)
        self.visit(node.post)
        if node.context:
            self.visit(node.context)
    
    def visit_context(self, node: ContextNode) -> Any:
        self.visit(node.left_context)
        self.visit(node.right_context)
    
    def visit_atom_sequence(self, node: AtomSequenceNode) -> Any:
        for atom in node.atoms:
            self.visit(atom)
    
    def visit_segment(self, node: SegmentNode) -> Any:
        if node.features:
            self.visit(node.features)
    
    def visit_sound_class(self, node: SoundClassNode) -> Any:
        if node.features:
            self.visit(node.features)
    
    def visit_choice(self, node: ChoiceNode) -> Any:
        for alt in node.alternatives:
            self.visit(alt)
    
    def visit_set(self, node: SetNode) -> Any:
        for alt in node.alternatives:
            self.visit(alt)
    
    def visit_backref(self, node: BackRefNode) -> Any:
        if node.features:
            self.visit(node.features)
    
    def visit_boundary(self, node: BoundaryNode) -> Any:
        pass
    
    def visit_focus(self, node: FocusNode) -> Any:
        pass
    
    def visit_null(self, node: NullNode) -> Any:
        pass
    
    def visit_feature_spec(self, node: FeatureSpecNode) -> Any:
        for feature in node.features:
            self.visit(feature)
    
    def visit_feature(self, node: FeatureNode) -> Any:
        if node.value:
            self.visit(node.value)
    
    def visit_feature_value(self, node: FeatureValueNode) -> Any:
        pass
    
    def visit(self, node: ASTNode) -> Any:
        """Generic visit method that dispatches to specific visit methods."""
        return node.accept(self)