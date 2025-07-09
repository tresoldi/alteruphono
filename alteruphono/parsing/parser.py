"""
Recursive descent parser for phonological rule syntax.

This module implements a recursive descent parser that converts tokens
into an Abstract Syntax Tree representing phonological rules.
"""

from typing import List, Optional, Union
from .lexer import Token, TokenType
from .errors import SyntaxError, ErrorCollector, ParseError, ErrorType
from .ast_nodes import *


class Parser:
    """
    Recursive descent parser for phonological rules.
    
    Parses a stream of tokens into an Abstract Syntax Tree following
    the grammar for phonological rule syntax.
    """
    
    def __init__(self, tokens: List[Token]):
        """
        Initialize parser with a list of tokens.
        
        Args:
            tokens: List of tokens from the lexer
        """
        self.tokens = tokens
        self.position = 0
        self.errors = ErrorCollector()
    
    def current_token(self) -> Token:
        """Get the current token."""
        if self.position >= len(self.tokens):
            # Return EOF token if we're past the end
            return Token(TokenType.EOF, "", self.position, 1, 1)
        return self.tokens[self.position]
    
    def peek_token(self, offset: int = 1) -> Token:
        """Peek at a token ahead without advancing position."""
        pos = self.position + offset
        if pos >= len(self.tokens):
            return Token(TokenType.EOF, "", pos, 1, 1)
        return self.tokens[pos]
    
    def advance(self) -> Token:
        """Advance to the next token and return the consumed token."""
        token = self.current_token()
        if self.position < len(self.tokens):
            self.position += 1
        return token
    
    def match(self, *token_types: TokenType) -> bool:
        """Check if current token matches any of the given types."""
        return self.current_token().type in token_types
    
    def consume(self, token_type: TokenType, error_message: str = None) -> Token:
        """
        Consume a token of the expected type or raise an error.
        
        Args:
            token_type: Expected token type
            error_message: Custom error message
            
        Returns:
            The consumed token
            
        Raises:
            SyntaxError: If the current token doesn't match expected type
        """
        token = self.current_token()
        
        if token.type != token_type:
            if error_message is None:
                error_message = f"Expected {token_type.value}, got {token.type.value}"
            
            raise SyntaxError(
                message=error_message,
                position=token.position,
                line=token.line,
                column=token.column,
                suggestions=[f"Use {token_type.value} here"]
            )
        
        return self.advance()
    
    def synchronize(self) -> None:
        """
        Synchronize parser after an error.
        
        Advances to the next likely recovery point to continue parsing.
        """
        while not self.match(TokenType.EOF):
            # Look for synchronization points
            if self.match(TokenType.ARROW, TokenType.SLASH, TokenType.NEWLINE):
                break
            self.advance()
    
    def parse_rule(self) -> RuleNode:
        """
        Parse a complete phonological rule.
        
        Grammar: rule ::= ante ARROW post (SLASH context)?
        
        Returns:
            RuleNode representing the parsed rule
        """
        start_token = self.current_token()
        
        # Parse ante (left side of rule)
        ante = self.parse_atom_sequence()
        
        # Consume arrow
        if not self.match(TokenType.ARROW):
            current = self.current_token()
            raise ParseError(
                type=ErrorType.SYNTAX,
                message="Expected '>' after ante part of rule",
                position=current.position,
                line=current.line,
                column=current.column,
                suggestions=["Add '>' to separate ante and post parts"]
            )
        
        # Check for empty ante (starting with >)
        if len(ante.atoms) == 0:
            current = self.current_token()
            raise ParseError(
                type=ErrorType.SYNTAX,
                message="Expected ante part of rule before '>'",
                position=current.position,
                line=current.line,
                column=current.column,
                suggestions=["Add a segment, sound class, or other atom before '>'"]
            )
        
        self.advance()  # consume >
        
        # Parse post (right side of rule)
        post = self.parse_atom_sequence()
        
        # Check for empty post
        if len(post.atoms) == 0:
            current = self.current_token()
            raise ParseError(
                type=ErrorType.SYNTAX,
                message="Expected post part of rule after '>'",
                position=current.position,
                line=current.line,
                column=current.column,
                suggestions=["Add a segment, sound class, or other atom after '>'"]
            )
        
        # Parse optional context
        context = None
        if self.match(TokenType.SLASH):
            self.advance()  # consume /
            context = self.parse_context()
        
        # Should be at end of rule
        if not self.match(TokenType.EOF, TokenType.NEWLINE):
            current = self.current_token()
            raise ParseError(
                type=ErrorType.SYNTAX,
                message="Unexpected tokens after rule",
                position=current.position,
                line=current.line,
                column=current.column,
                suggestions=["Rules should end after context or post part"]
            )
        
        return RuleNode(
            ante=ante,
            post=post,
            context=context,
            position=start_token.position,
            line=start_token.line,
            column=start_token.column
        )
    
    def parse_context(self) -> ContextNode:
        """
        Parse a rule context.
        
        Grammar: context ::= atom_sequence FOCUS atom_sequence
        
        Returns:
            ContextNode representing the context
        """
        start_token = self.current_token()
        
        # Parse left context (before focus)
        left_atoms = []
        focus_position = 0
        
        while not self.match(TokenType.FOCUS, TokenType.EOF):
            atom = self.parse_atom()
            if atom:
                left_atoms.append(atom)
            focus_position += 1
        
        # Consume focus
        if not self.match(TokenType.FOCUS):
            current = self.current_token()
            raise ParseError(
                type=ErrorType.SYNTAX,
                message="Expected '_' (focus) in context",
                position=current.position,
                line=current.line,
                column=current.column,
                suggestions=["Contexts must have a focus position marked with '_'"]
            )
        
        self.advance()  # consume _
        
        # Parse right context (after focus)
        right_atoms = []
        while not self.match(TokenType.EOF, TokenType.NEWLINE):
            atom = self.parse_atom()
            if atom:
                right_atoms.append(atom)
        
        return ContextNode(
            left_context=AtomSequenceNode(left_atoms, start_token.position),
            right_context=AtomSequenceNode(right_atoms, start_token.position),
            focus_position=focus_position,
            position=start_token.position,
            line=start_token.line,
            column=start_token.column
        )
    
    def parse_atom_sequence(self) -> AtomSequenceNode:
        """
        Parse a sequence of atoms.
        
        Grammar: atom_sequence ::= atom*
        
        Returns:
            AtomSequenceNode containing the parsed atoms
        """
        start_token = self.current_token()
        atoms = []
        
        # Parse atoms until we hit a delimiter
        while not self.match(TokenType.ARROW, TokenType.SLASH, TokenType.EOF, TokenType.NEWLINE, TokenType.FOCUS):
            # Check if we have a choice starting at this position
            if self.has_choice_ahead():
                atoms.append(self.parse_choice())
            else:
                atom = self.parse_atom()
                if atom:
                    atoms.append(atom)
        
        return AtomSequenceNode(
            atoms=atoms,
            position=start_token.position,
            line=start_token.line,
            column=start_token.column
        )
    
    def parse_atom(self) -> Optional[AtomNode]:
        """
        Parse a single atom.
        
        Grammar: atom ::= segment | sound_class | set | backref | boundary | focus | null
        
        Returns:
            AtomNode representing the parsed atom, or None if no valid atom found
        """
        token = self.current_token()
        
        if token.type == TokenType.GRAPHEME:
            return self.parse_segment()
        elif token.type == TokenType.SOUND_CLASS:
            return self.parse_sound_class()
        elif token.type == TokenType.LBRACE:
            return self.parse_set()
        elif token.type == TokenType.BACKREF:
            return self.parse_backref()
        elif token.type == TokenType.BOUNDARY:
            return self.parse_boundary()
        elif token.type == TokenType.FOCUS:
            return self.parse_focus()
        elif token.type == TokenType.NULL:
            return self.parse_null()
        else:
            # Skip unknown token and continue
            self.advance()
            return None
    
    def has_choice_ahead(self) -> bool:
        """Check if there's a choice (pipe) ahead in the current sequence."""
        # Look ahead for a pipe within the current atom sequence
        temp_pos = self.position
        bracket_depth = 0
        brace_depth = 0
        
        while temp_pos < len(self.tokens):
            t = self.tokens[temp_pos]
            
            if t.type in (TokenType.ARROW, TokenType.SLASH, TokenType.EOF):
                break
            elif t.type == TokenType.LBRACKET:
                bracket_depth += 1
            elif t.type == TokenType.RBRACKET:
                bracket_depth -= 1
            elif t.type == TokenType.LBRACE:
                brace_depth += 1
            elif t.type == TokenType.RBRACE:
                brace_depth -= 1
            elif t.type == TokenType.PIPE and bracket_depth == 0 and brace_depth == 0:
                return True
                
            temp_pos += 1
        
        return False
    
    def parse_segment(self) -> SegmentNode:
        """
        Parse a phonological segment.
        
        Grammar: segment ::= GRAPHEME feature_spec?
        
        Returns:
            SegmentNode representing the segment
        """
        token = self.consume(TokenType.GRAPHEME)
        
        # Parse optional feature specification
        features = None
        if self.match(TokenType.LBRACKET):
            features = self.parse_feature_spec()
        
        return SegmentNode(
            grapheme=token.value,
            features=features,
            position=token.position,
            line=token.line,
            column=token.column
        )
    
    def parse_sound_class(self) -> SoundClassNode:
        """
        Parse a sound class.
        
        Grammar: sound_class ::= SOUND_CLASS feature_spec?
        
        Returns:
            SoundClassNode representing the sound class
        """
        token = self.consume(TokenType.SOUND_CLASS)
        
        # Parse optional feature specification
        features = None
        if self.match(TokenType.LBRACKET):
            features = self.parse_feature_spec()
        
        return SoundClassNode(
            class_name=token.value,
            features=features,
            position=token.position,
            line=token.line,
            column=token.column
        )
    
    def parse_choice(self) -> ChoiceNode:
        """
        Parse a choice expression.
        
        Grammar: choice ::= atom (PIPE atom)+
        
        Returns:
            ChoiceNode representing the choice
        """
        start_token = self.current_token()
        alternatives = []
        
        # Parse first alternative (we know it's not a pipe)
        if self.match(TokenType.GRAPHEME):
            alternatives.append(self.parse_segment())
        elif self.match(TokenType.SOUND_CLASS):
            alternatives.append(self.parse_sound_class())
        elif self.match(TokenType.BACKREF):
            alternatives.append(self.parse_backref())
        elif self.match(TokenType.BOUNDARY):
            alternatives.append(self.parse_boundary())
        elif self.match(TokenType.NULL):
            alternatives.append(self.parse_null())
        else:
            raise SyntaxError(
                message="Expected atom at start of choice",
                position=start_token.position,
                line=start_token.line,
                column=start_token.column
            )
        
        # Parse remaining alternatives
        while self.match(TokenType.PIPE):
            self.advance()  # consume |
            
            if self.match(TokenType.GRAPHEME):
                alternatives.append(self.parse_segment())
            elif self.match(TokenType.SOUND_CLASS):
                alternatives.append(self.parse_sound_class())
            elif self.match(TokenType.BACKREF):
                alternatives.append(self.parse_backref())
            elif self.match(TokenType.BOUNDARY):
                alternatives.append(self.parse_boundary())
            elif self.match(TokenType.NULL):
                alternatives.append(self.parse_null())
            else:
                raise SyntaxError(
                    message="Expected atom after '|' in choice",
                    position=self.current_token().position,
                    line=self.current_token().line,
                    column=self.current_token().column
                )
        
        return ChoiceNode(
            alternatives=alternatives,
            position=start_token.position,
            line=start_token.line,
            column=start_token.column
        )
    
    def parse_set(self) -> SetNode:
        """
        Parse a set expression.
        
        Grammar: set ::= LBRACE atom (PIPE atom)+ RBRACE
        
        Returns:
            SetNode representing the set
        """
        start_token = self.consume(TokenType.LBRACE)
        alternatives = []
        
        # Parse first alternative
        if self.match(TokenType.RBRACE):
            raise SyntaxError(
                message="Empty set not allowed",
                position=self.current_token().position,
                line=self.current_token().line,
                column=self.current_token().column,
                suggestions=["Add at least one alternative inside { }"]
            )
        
        alternatives.append(self.parse_atom_no_set())
        
        # Parse remaining alternatives
        while self.match(TokenType.PIPE):
            self.advance()  # consume |
            alternatives.append(self.parse_atom_no_set())
        
        self.consume(TokenType.RBRACE, "Expected '}' to close set")
        
        return SetNode(
            alternatives=alternatives,
            position=start_token.position,
            line=start_token.line,
            column=start_token.column
        )
    
    def parse_atom_no_set(self) -> AtomNode:
        """Parse an atom that cannot be a set (to avoid recursion in set parsing)."""
        token = self.current_token()
        
        if token.type == TokenType.GRAPHEME:
            return self.parse_segment()
        elif token.type == TokenType.SOUND_CLASS:
            return self.parse_sound_class()
        elif token.type == TokenType.BACKREF:
            return self.parse_backref()
        elif token.type == TokenType.BOUNDARY:
            return self.parse_boundary()
        elif token.type == TokenType.NULL:
            return self.parse_null()
        else:
            raise SyntaxError(
                message=f"Unexpected token in set: {token.value}",
                position=token.position,
                line=token.line,
                column=token.column,
                suggestions=["Use segment, sound class, backref, boundary, or null in sets"]
            )
    
    def parse_backref(self) -> BackRefNode:
        """
        Parse a backreference.
        
        Grammar: backref ::= BACKREF feature_spec?
        
        Returns:
            BackRefNode representing the backreference
        """
        token = self.consume(TokenType.BACKREF)
        
        # Extract index from @1, @2, etc.
        index_str = token.value[1:]  # Remove @
        try:
            index = int(index_str) - 1  # Convert to 0-based indexing
        except ValueError:
            raise SyntaxError(
                message=f"Invalid backreference index: {token.value}",
                position=token.position,
                line=token.line,
                column=token.column
            )
        
        # Parse optional feature specification
        features = None
        if self.match(TokenType.LBRACKET):
            features = self.parse_feature_spec()
        
        return BackRefNode(
            index=index,
            features=features,
            position=token.position,
            line=token.line,
            column=token.column
        )
    
    def parse_boundary(self) -> BoundaryNode:
        """Parse a boundary marker."""
        token = self.consume(TokenType.BOUNDARY)
        return BoundaryNode(
            position=token.position,
            line=token.line,
            column=token.column
        )
    
    def parse_focus(self) -> FocusNode:
        """Parse a focus marker."""
        token = self.consume(TokenType.FOCUS)
        return FocusNode(
            position=token.position,
            line=token.line,
            column=token.column
        )
    
    def parse_null(self) -> NullNode:
        """Parse a null marker."""
        token = self.consume(TokenType.NULL)
        return NullNode(
            position=token.position,
            line=token.line,
            column=token.column
        )
    
    def parse_feature_spec(self) -> FeatureSpecNode:
        """
        Parse a feature specification.
        
        Grammar: feature_spec ::= LBRACKET feature_list RBRACKET
        Grammar: feature_list ::= feature (COMMA feature)*
        
        Returns:
            FeatureSpecNode representing the feature specification
        """
        start_token = self.consume(TokenType.LBRACKET)
        features = []
        
        # Parse first feature
        if self.match(TokenType.RBRACKET):
            raise SyntaxError(
                message="Empty feature specification not allowed",
                position=self.current_token().position,
                line=self.current_token().line,
                column=self.current_token().column,
                suggestions=["Add at least one feature inside [ ]"]
            )
        
        features.append(self.parse_feature())
        
        # Parse remaining features
        while self.match(TokenType.COMMA):
            self.advance()  # consume ,
            features.append(self.parse_feature())
        
        self.consume(TokenType.RBRACKET, "Expected ']' to close feature specification")
        
        return FeatureSpecNode(
            features=features,
            position=start_token.position,
            line=start_token.line,
            column=start_token.column
        )
    
    def parse_feature(self) -> FeatureNode:
        """
        Parse a single feature.
        
        Grammar: feature ::= feature_name | PLUS feature_name | MINUS feature_name | feature_name EQUALS feature_value
        
        Returns:
            FeatureNode representing the feature
        """
        start_token = self.current_token()
        polarity = None
        
        # Check for polarity
        if self.match(TokenType.PLUS):
            polarity = '+'
            self.advance()
        elif self.match(TokenType.MINUS):
            polarity = '-'
            self.advance()
        
        # Get feature name
        if not self.match(TokenType.FEATURE):
            raise SyntaxError(
                message="Expected feature name",
                position=self.current_token().position,
                line=self.current_token().line,
                column=self.current_token().column,
                suggestions=["Use a valid feature name like 'voiced', 'bilabial', etc."]
            )
        
        name_token = self.advance()
        name = name_token.value
        
        # Check for feature value
        value = None
        if self.match(TokenType.EQUALS):
            self.advance()  # consume =
            value = self.parse_feature_value()
        
        return FeatureNode(
            name=name,
            polarity=polarity,
            value=value,
            position=start_token.position,
            line=start_token.line,
            column=start_token.column
        )
    
    def parse_feature_value(self) -> FeatureValueNode:
        """
        Parse a feature value.
        
        Grammar: feature_value ::= FEATURE | NUMBER | NUMBER UNIT | GRAPHEME
        
        Returns:
            FeatureValueNode representing the value
        """
        token = self.current_token()
        
        if token.type == TokenType.NUMBER:
            value = self.advance().value
            unit = None
            
            # Check for unit
            if self.match(TokenType.UNIT):
                unit = self.advance().value
            
            return FeatureValueNode(
                value=value,
                unit=unit,
                position=token.position,
                line=token.line,
                column=token.column
            )
        elif token.type in (TokenType.FEATURE, TokenType.GRAPHEME):
            value = self.advance().value
            return FeatureValueNode(
                value=value,
                position=token.position,
                line=token.line,
                column=token.column
            )
        else:
            raise SyntaxError(
                message="Expected feature value",
                position=token.position,
                line=token.line,
                column=token.column,
                suggestions=["Use a number, feature name, or grapheme as value"]
            )