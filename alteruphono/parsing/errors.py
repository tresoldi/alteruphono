"""
Error types and handling for the parsing module.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class ErrorType(Enum):
    """Types of parsing errors."""
    LEXICAL = "lexical"
    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    PHONOLOGICAL = "phonological"


@dataclass
class ParseError(Exception):
    """
    A parsing error with detailed position and context information.
    """
    type: ErrorType
    message: str
    position: int
    line: int = 1
    column: int = 1
    suggestions: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        """Format error message with position information."""
        error_type = self.type.value.title()
        msg = f"{error_type} Error at line {self.line}, column {self.column}:\n"
        msg += f"  {self.message}"
        
        if self.suggestions:
            msg += "\n  Suggestions:"
            for suggestion in self.suggestions:
                msg += f"\n    - {suggestion}"
                
        return msg


@dataclass
class LexicalError(ParseError):
    """Error during tokenization."""
    type: ErrorType = field(default=ErrorType.LEXICAL, init=False)


@dataclass
class SyntaxError(ParseError):
    """Error during parsing (invalid grammar)."""
    type: ErrorType = field(default=ErrorType.SYNTAX, init=False)


@dataclass
class SemanticError(ParseError):
    """Error in semantic analysis (e.g., invalid backreferences)."""
    type: ErrorType = field(default=ErrorType.SEMANTIC, init=False)


@dataclass
class PhonologicalError(ParseError):
    """Error in phonological constraints (e.g., contradictory features)."""
    type: ErrorType = field(default=ErrorType.PHONOLOGICAL, init=False)


class ErrorCollector:
    """
    Collects multiple errors during parsing to report them all at once.
    """
    
    def __init__(self):
        self.errors: List[ParseError] = []
    
    def add_error(self, error: ParseError) -> None:
        """Add an error to the collection."""
        self.errors.append(error)
    
    def has_errors(self) -> bool:
        """Check if any errors have been collected."""
        return len(self.errors) > 0
    
    def get_errors(self) -> List[ParseError]:
        """Get all collected errors."""
        return self.errors.copy()
    
    def clear(self) -> None:
        """Clear all collected errors."""
        self.errors.clear()
    
    def raise_if_errors(self) -> None:
        """Raise the first error if any errors have been collected."""
        if self.errors:
            raise self.errors[0]