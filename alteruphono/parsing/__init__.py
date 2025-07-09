"""
Parsing module for alteruphono.

This module provides a robust, extensible parser for phonological rule syntax
that supports current features and enables future extensions like suprasegmentals
and numeric features.
"""

from .lexer import Lexer, Token, TokenType
from .parser import Parser
from .ast_nodes import ASTNode, RuleNode
from .errors import ParseError, ErrorType
from .converter import ASTToModelConverter
from .validator import PhonologicalValidator

__all__ = [
    'Lexer', 'Token', 'TokenType',
    'Parser', 
    'ASTNode', 'RuleNode',
    'ParseError', 'ErrorType',
    'ASTToModelConverter',
    'PhonologicalValidator',
    'parse_rule_new',
    'parse_rule_enhanced'
]

def parse_rule_new(rule_string: str):
    """
    Parse a phonological rule using the new parser.
    
    This is the main entry point for the new parsing system.
    Eventually this will replace the old parse_rule function.
    
    Args:
        rule_string: The rule string to parse (e.g., "p > b / a _ a")
        
    Returns:
        Tuple of (ante_tokens, post_tokens) compatible with current model
        
    Raises:
        ParseError: If the rule cannot be parsed
    """
    # Tokenize
    lexer = Lexer(rule_string)
    tokens = lexer.tokenize()
    
    # Parse
    parser = Parser(tokens)
    ast = parser.parse_rule()
    
    # Validate
    validator = PhonologicalValidator()
    errors = validator.validate(ast)
    if errors:
        raise errors[0]  # Raise first error
    
    # Convert to current model
    converter = ASTToModelConverter()
    return converter.convert_rule(ast)


def parse_rule_enhanced(rule_string: str):
    """
    Parse a phonological rule using the enhanced parser system with full validation.
    
    This function provides access to the full new parser capabilities including
    enhanced error messages and validation.
    
    Args:
        rule_string: The rule string to parse
        
    Returns:
        Tuple of (ante_tokens, post_tokens, validation_errors) where:
        - ante_tokens: List of ante tokens
        - post_tokens: List of post tokens  
        - validation_errors: List of validation errors (empty if valid)
    """
    # Tokenize
    lexer = Lexer(rule_string)
    tokens = lexer.tokenize()
    
    # Parse
    parser = Parser(tokens)
    ast = parser.parse_rule()
    
    # Validate
    validator = PhonologicalValidator()
    errors = validator.validate(ast)
    
    # Convert to current model
    converter = ASTToModelConverter()
    ante_tokens, post_tokens = converter.convert_rule(ast)
    
    return ante_tokens, post_tokens, errors