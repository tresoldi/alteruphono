"""
Converter from AST to current Token-based model.

This module provides backward compatibility by converting the new AST
representation back to the current Token-based model used by the rest
of the alteruphono system.
"""

from typing import List, Tuple, Optional
from ..model import (
    Token as ModelToken,
    SegmentToken,
    BoundaryToken,
    FocusToken,
    EmptyToken,
    BackRefToken,
    ChoiceToken,
    SetToken,
)
from .ast_nodes import *


class ASTToModelConverter(BaseASTVisitor):
    """
    Converts AST nodes to current Token-based model for backward compatibility.
    
    This ensures that the new parser can be used as a drop-in replacement
    for the old parser without breaking existing code.
    """
    
    def __init__(self):
        """Initialize the converter."""
        self.current_tokens = []
        
    def convert_rule(self, rule_node: RuleNode) -> Tuple[List[ModelToken], List[ModelToken]]:
        """
        Convert a RuleNode to ante and post token sequences.
        
        Args:
            rule_node: The parsed rule AST
            
        Returns:
            Tuple of (ante_tokens, post_tokens) compatible with current model
        """
        # Convert ante sequence
        self.current_tokens = []
        self.visit(rule_node.ante)
        ante_tokens = self.current_tokens.copy()
        
        # Convert post sequence
        self.current_tokens = []
        self.visit(rule_node.post)
        post_tokens = self.current_tokens.copy()
        
        # Handle context by merging it into ante and post sequences
        if rule_node.context:
            ante_tokens, post_tokens = self._merge_context(
                ante_tokens, post_tokens, rule_node.context
            )
        
        return ante_tokens, post_tokens
    
    def _merge_context(
        self,
        ante_tokens: List[ModelToken],
        post_tokens: List[ModelToken],
        context: ContextNode
    ) -> Tuple[List[ModelToken], List[ModelToken]]:
        """
        Merge context into ante and post sequences.
        
        This replicates the behavior of the old parser where context
        is merged into the main rule sequences.
        """
        # Convert left context
        self.current_tokens = []
        self.visit(context.left_context)
        left_tokens = self.current_tokens.copy()
        
        # Convert right context  
        self.current_tokens = []
        self.visit(context.right_context)
        right_tokens = self.current_tokens.copy()
        
        # Calculate offsets for backreference adjustment
        offset_left = len(left_tokens)
        offset_ante = len(ante_tokens)
        
        # Adjust backreferences in ante and post
        ante_tokens = self._adjust_backrefs(ante_tokens, offset_left)
        post_tokens = self._adjust_backrefs(post_tokens, offset_left)
        
        # Build new ante sequence: left + ante + right (with adjusted backrefs)
        new_ante = left_tokens + ante_tokens
        new_ante += self._adjust_backrefs(right_tokens, offset_left + offset_ante)
        
        # Build new post sequence: backref for each left + post + backref for each right
        new_post = []
        for i in range(len(left_tokens)):
            new_post.append(BackRefToken(i))
        new_post += post_tokens
        for i in range(len(right_tokens)):
            new_post.append(BackRefToken(i + offset_left + offset_ante))
        
        return new_ante, new_post
    
    def _adjust_backrefs(self, tokens: List[ModelToken], offset: int) -> List[ModelToken]:
        """Adjust backreference indices by adding an offset."""
        adjusted = []
        for token in tokens:
            if isinstance(token, BackRefToken):
                # Create new BackRefToken with adjusted index
                adjusted.append(BackRefToken(token.index + offset, token.modifier))
            else:
                adjusted.append(token)
        return adjusted
    
    # Visitor methods for converting AST nodes to tokens
    
    def visit_atom_sequence(self, node: AtomSequenceNode) -> None:
        """Convert atom sequence to list of tokens."""
        for atom in node.atoms:
            self.visit(atom)
    
    def visit_segment(self, node: SegmentNode) -> None:
        """Convert segment node to SegmentToken."""
        # Build the segment string with features
        segment_str = node.grapheme
        if node.features:
            feature_str = self._build_feature_string(node.features)
            if feature_str:
                segment_str += f"[{feature_str}]"
        
        self.current_tokens.append(SegmentToken(segment_str))
    
    def visit_sound_class(self, node: SoundClassNode) -> None:
        """Convert sound class node to SegmentToken."""
        # Build the sound class string with features
        class_str = node.class_name
        if node.features:
            feature_str = self._build_feature_string(node.features)
            if feature_str:
                class_str += f"[{feature_str}]"
        
        self.current_tokens.append(SegmentToken(class_str))
    
    def visit_choice(self, node: ChoiceNode) -> None:
        """Convert choice node to ChoiceToken."""
        # Convert each alternative to a token
        choice_tokens = []
        for alt in node.alternatives:
            self.current_tokens = []
            self.visit(alt)
            if self.current_tokens:
                # For now, assume each alternative produces exactly one token
                choice_tokens.append(self.current_tokens[0])
        
        self.current_tokens = [ChoiceToken(choice_tokens)]
    
    def visit_set(self, node: SetNode) -> None:
        """Convert set node to SetToken."""
        # Convert each alternative to a token
        set_tokens = []
        for alt in node.alternatives:
            self.current_tokens = []
            self.visit(alt)
            if self.current_tokens:
                # For now, assume each alternative produces exactly one token
                set_tokens.append(self.current_tokens[0])
        
        self.current_tokens = [SetToken(set_tokens)]
    
    def visit_backref(self, node: BackRefNode) -> None:
        """Convert backref node to BackRefToken."""
        # Build modifier string from features
        modifier = None
        if node.features:
            modifier = self._build_feature_string(node.features)
        
        self.current_tokens.append(BackRefToken(node.index, modifier))
    
    def visit_boundary(self, node: BoundaryNode) -> None:
        """Convert boundary node to BoundaryToken."""
        self.current_tokens.append(BoundaryToken())
    
    def visit_focus(self, node: FocusNode) -> None:
        """Convert focus node to FocusToken."""
        self.current_tokens.append(FocusToken())
    
    def visit_null(self, node: NullNode) -> None:
        """Convert null node to EmptyToken."""
        self.current_tokens.append(EmptyToken())
    
    def _build_feature_string(self, feature_spec: FeatureSpecNode) -> str:
        """
        Build a feature string from a FeatureSpecNode.
        
        Args:
            feature_spec: The feature specification node
            
        Returns:
            String representation of features (e.g., "voiced,bilabial")
        """
        feature_strings = []
        
        for feature in feature_spec.features:
            feature_str = ""
            
            # Add polarity
            if feature.polarity:
                feature_str += feature.polarity
            
            # Add feature name
            feature_str += feature.name
            
            # Add value if present
            if feature.value:
                feature_str += f"={feature.value.value}"
                if feature.value.unit:
                    feature_str += feature.value.unit
            
            feature_strings.append(feature_str)
        
        return ",".join(feature_strings)


class ModelToStringConverter:
    """
    Helper class to convert token sequences back to string representation.
    
    Useful for debugging and testing the conversion process.
    """
    
    @staticmethod
    def tokens_to_string(tokens: List[ModelToken]) -> str:
        """Convert a list of tokens back to string representation."""
        return " ".join(str(token) for token in tokens)
    
    @staticmethod
    def rule_to_string(ante_tokens: List[ModelToken], post_tokens: List[ModelToken]) -> str:
        """Convert ante and post token sequences to rule string."""
        ante_str = ModelToStringConverter.tokens_to_string(ante_tokens)
        post_str = ModelToStringConverter.tokens_to_string(post_tokens)
        return f"{ante_str} > {post_str}"