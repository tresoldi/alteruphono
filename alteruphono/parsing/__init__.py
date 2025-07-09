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

__all__ = [
    'Lexer', 'Token', 'TokenType',
    'Parser', 
    'ASTNode', 'RuleNode',
    'ParseError', 'ErrorType',
    'ASTToModelConverter',
    'parse_rule_new'
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
    
    # Convert to current model
    converter = ASTToModelConverter()
    return converter.convert_rule(ast)