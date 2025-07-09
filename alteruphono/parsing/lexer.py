"""
Lexer (tokenizer) for phonological rule syntax.

This module handles the tokenization of input strings into meaningful symbols
for phonological rules, including IPA symbols, operators, brackets, and features.
"""

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Iterator, Set
from .errors import LexicalError


class TokenType(Enum):
    """Types of tokens in phonological rule syntax."""
    
    # Basic symbols
    GRAPHEME = "grapheme"           # p, a, ɸ, ʧ, etc.
    SOUND_CLASS = "sound_class"     # V, C, S, N, etc.
    
    # Operators
    ARROW = "arrow"                 # >
    PIPE = "pipe"                   # |
    FOCUS = "focus"                 # _
    BOUNDARY = "boundary"           # #
    
    # Brackets and delimiters
    LBRACKET = "lbracket"          # [
    RBRACKET = "rbracket"          # ]
    LPAREN = "lparen"              # (
    RPAREN = "rparen"              # )
    LBRACE = "lbrace"              # {
    RBRACE = "rbrace"              # }
    
    # Context
    SLASH = "slash"                # /
    
    # Features and modifiers
    FEATURE = "feature"            # voiced, bilabial, etc.
    PLUS = "plus"                  # +
    MINUS = "minus"                # -
    EQUALS = "equals"              # =
    
    # Numbers and units (for future numeric features)
    NUMBER = "number"              # 120, 0.15
    UNIT = "unit"                  # Hz, ms, s
    
    # Special tokens
    BACKREF = "backref"            # @1, @2
    NULL = "null"                  # :null:
    COMMA = "comma"                # ,
    COLON = "colon"                # :
    
    # Prosodic units (for future extensions)
    MORA = "mora"                  # μ
    SYLLABLE = "syllable"          # σ
    FOOT = "foot"                  # Ft
    WORD = "word"                  # ω
    PHRASE = "phrase"              # φ
    
    # Control
    EOF = "eof"
    NEWLINE = "newline"
    WHITESPACE = "whitespace"


@dataclass
class Token:
    """
    A token representing a meaningful unit in the input.
    """
    type: TokenType
    value: str
    position: int
    line: int = 1
    column: int = 1
    
    def __str__(self) -> str:
        return f"{self.type.value}:{self.value}"
    
    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value!r}, pos={self.position})"


class Lexer:
    """
    Tokenizer for phonological rule syntax.
    
    Converts input strings into streams of tokens while tracking position
    information for error reporting.
    """
    
    # Sound classes recognized by the lexer
    SOUND_CLASSES = {'V', 'C', 'S', 'N', 'L', 'K', 'SVL', 'VD', 'P', 'R', 'F'}
    
    # Known feature names (can be extended)
    FEATURE_NAMES = {
        # Voicing
        'voiced', 'voiceless', 'voice',
        # Place
        'bilabial', 'labiodental', 'dental', 'alveolar', 'postalveolar',
        'retroflex', 'palatal', 'velar', 'uvular', 'pharyngeal', 'glottal',
        'labial', 'coronal', 'dorsal', 'radical',
        # Manner
        'stop', 'fricative', 'affricate', 'nasal', 'lateral', 'rhotic',
        'approximant', 'tap', 'trill',
        # Vowel features
        'high', 'mid', 'low', 'front', 'central', 'back',
        'rounded', 'unrounded', 'tense', 'lax',
        # Other
        'long', 'short', 'ejective', 'plain', 'aspirated',
        'stress', 'unstress', 'primary', 'secondary',
        'tone', 'pitch', 'rising', 'falling', 'level'
    }
    
    # Units for numeric features (future extension)
    UNITS = {'Hz', 'ms', 'khz', 'Khz', 'KHz'}
    
    # Prosodic unit symbols (future extension) 
    PROSODIC_SYMBOLS = {
        'μ': TokenType.MORA,
        'σ': TokenType.SYLLABLE, 
        'Ft': TokenType.FOOT,
        'ω': TokenType.WORD,
        'φ': TokenType.PHRASE
    }
    
    def __init__(self, text: str):
        """
        Initialize lexer with input text.
        
        Args:
            text: The input string to tokenize
        """
        # Normalize Unicode to NFD for consistent processing
        self.text = unicodedata.normalize("NFD", text)
        self.position = 0
        self.line = 1
        self.column = 1
        self.length = len(self.text)
        
    def current_char(self) -> Optional[str]:
        """Get the current character, or None if at end."""
        if self.position >= self.length:
            return None
        return self.text[self.position]
    
    def peek_char(self, offset: int = 1) -> Optional[str]:
        """Peek at a character ahead without advancing position."""
        pos = self.position + offset
        if pos >= self.length:
            return None
        return self.text[pos]
    
    def advance(self) -> Optional[str]:
        """Advance position and return the character that was consumed."""
        if self.position >= self.length:
            return None
            
        char = self.text[self.position]
        self.position += 1
        
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
            
        return char
    
    def skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.current_char() and self.current_char().isspace():
            self.advance()
    
    def read_while(self, predicate) -> str:
        """Read characters while predicate is true."""
        start_pos = self.position
        while self.current_char() and predicate(self.current_char()):
            self.advance()
        return self.text[start_pos:self.position]
    
    def read_grapheme(self) -> str:
        """
        Read a single grapheme, which may be multiple Unicode characters.
        
        This handles complex IPA symbols like affricates (ʧ, ʤ), 
        diacritics (tʃ, dʒ), and other multi-character sequences.
        """
        if not self.current_char():
            return ""
            
        # Start with the current character
        grapheme = self.advance()
        
        # Handle common multi-character IPA symbols
        if grapheme == 't' and self.current_char() == 'ʃ':
            grapheme += self.advance()  # tʃ
        elif grapheme == 'd' and self.current_char() == 'ʒ':
            grapheme += self.advance()  # dʒ
        elif grapheme == 's' and self.current_char() == 'ʼ':
            grapheme += self.advance()  # sʼ (ejective)
        
        # Add any combining diacritics
        while (self.current_char() and 
               unicodedata.category(self.current_char()) == 'Mn'):
            grapheme += self.advance()
            
        return grapheme
    
    def read_number(self) -> str:
        """Read a numeric value (integer or decimal)."""
        number = ""
        
        # Read integer part
        while self.current_char() and self.current_char().isdigit():
            number += self.advance()
            
        # Read decimal part if present
        if self.current_char() == '.':
            number += self.advance()
            while self.current_char() and self.current_char().isdigit():
                number += self.advance()
                
        return number
    
    def read_identifier(self) -> str:
        """Read an identifier (feature name, unit, etc.)."""
        return self.read_while(lambda c: c.isalnum() or c in '_')
    
    def tokenize_backref(self) -> Token:
        """Tokenize a backreference like @1, @2."""
        start_pos = self.position
        start_col = self.column
        
        # Skip the @
        self.advance()
        
        # Read the number
        if not (self.current_char() and self.current_char().isdigit()):
            raise LexicalError(
                message="Expected digit after '@'",
                position=self.position,
                line=self.line,
                column=self.column,
                suggestions=["Use @1, @2, @3, etc. for backreferences"]
            )
        
        number = self.read_while(lambda c: c.isdigit())
        value = f"@{number}"
        
        return Token(
            type=TokenType.BACKREF,
            value=value,
            position=start_pos,
            line=self.line,
            column=start_col
        )
    
    def tokenize_null(self) -> Token:
        """Tokenize :null: token."""
        start_pos = self.position
        start_col = self.column
        
        # Read :null:
        if self.text[self.position:self.position+6] == ":null:":
            for _ in range(6):
                self.advance()
            return Token(
                type=TokenType.NULL,
                value=":null:",
                position=start_pos,
                line=self.line,
                column=start_col
            )
        else:
            raise LexicalError(
                message="Invalid token starting with ':'",
                position=self.position,
                line=self.line,
                column=self.column,
                suggestions=["Use :null: for deletion/insertion"]
            )
    
    def classify_identifier(self, identifier: str) -> TokenType:
        """Classify an identifier as sound class, feature, unit, etc."""
        
        # Check if it's a sound class
        if identifier in self.SOUND_CLASSES:
            return TokenType.SOUND_CLASS
            
        # Check if it's a prosodic unit
        if identifier in self.PROSODIC_SYMBOLS:
            return self.PROSODIC_SYMBOLS[identifier]
            
        # Check if it's a unit
        if identifier in self.UNITS:
            return TokenType.UNIT
            
        # Check if it's a known feature name
        if identifier in self.FEATURE_NAMES:
            return TokenType.FEATURE
            
        # Default to grapheme (single letters, IPA symbols, etc.)
        return TokenType.GRAPHEME
    
    def next_token(self) -> Token:
        """Get the next token from the input."""
        
        # Skip whitespace
        self.skip_whitespace()
        
        # Check for end of input
        if not self.current_char():
            return Token(
                type=TokenType.EOF,
                value="",
                position=self.position,
                line=self.line,
                column=self.column
            )
        
        start_pos = self.position
        start_col = self.column
        char = self.current_char()
        
        # Single-character tokens
        if char == '>':
            self.advance()
            return Token(TokenType.ARROW, '>', start_pos, self.line, start_col)
        elif char == '|':
            self.advance()
            return Token(TokenType.PIPE, '|', start_pos, self.line, start_col)
        elif char == '_':
            self.advance()
            return Token(TokenType.FOCUS, '_', start_pos, self.line, start_col)
        elif char == '#':
            self.advance()
            return Token(TokenType.BOUNDARY, '#', start_pos, self.line, start_col)
        elif char == '[':
            self.advance()
            return Token(TokenType.LBRACKET, '[', start_pos, self.line, start_col)
        elif char == ']':
            self.advance()
            return Token(TokenType.RBRACKET, ']', start_pos, self.line, start_col)
        elif char == '(':
            self.advance()
            return Token(TokenType.LPAREN, '(', start_pos, self.line, start_col)
        elif char == ')':
            self.advance()
            return Token(TokenType.RPAREN, ')', start_pos, self.line, start_col)
        elif char == '{':
            self.advance()
            return Token(TokenType.LBRACE, '{', start_pos, self.line, start_col)
        elif char == '}':
            self.advance()
            return Token(TokenType.RBRACE, '}', start_pos, self.line, start_col)
        elif char == '/':
            self.advance()
            return Token(TokenType.SLASH, '/', start_pos, self.line, start_col)
        elif char == '+':
            self.advance()
            return Token(TokenType.PLUS, '+', start_pos, self.line, start_col)
        elif char == '-':
            self.advance()
            return Token(TokenType.MINUS, '-', start_pos, self.line, start_col)
        elif char == '=':
            self.advance()
            return Token(TokenType.EQUALS, '=', start_pos, self.line, start_col)
        elif char == ',':
            self.advance()
            return Token(TokenType.COMMA, ',', start_pos, self.line, start_col)
        elif char == ':':
            # Could be :null: or just a colon
            if self.text[self.position:].startswith(":null:"):
                return self.tokenize_null()
            else:
                self.advance()
                return Token(TokenType.COLON, ':', start_pos, self.line, start_col)
        elif char == '\n':
            self.advance()
            return Token(TokenType.NEWLINE, '\n', start_pos, self.line, start_col - 1)
        
        # Multi-character tokens
        elif char == '@':
            return self.tokenize_backref()
        elif char.isdigit():
            number = self.read_number()
            return Token(TokenType.NUMBER, number, start_pos, self.line, start_col)
        elif char.isalpha() or char == '_':
            identifier = self.read_identifier()
            token_type = self.classify_identifier(identifier)
            return Token(token_type, identifier, start_pos, self.line, start_col)
        elif char in self.PROSODIC_SYMBOLS:
            symbol = self.advance()
            return Token(
                self.PROSODIC_SYMBOLS[symbol],
                symbol,
                start_pos,
                self.line,
                start_col
            )
        else:
            # Assume it's a grapheme (IPA symbol)
            grapheme = self.read_grapheme()
            return Token(TokenType.GRAPHEME, grapheme, start_pos, self.line, start_col)
    
    def tokenize(self) -> List[Token]:
        """
        Tokenize the entire input and return a list of tokens.
        
        Returns:
            List of tokens representing the input
            
        Raises:
            LexicalError: If invalid characters are encountered
        """
        tokens = []
        
        while True:
            token = self.next_token()
            
            # Skip whitespace tokens in the output
            if token.type != TokenType.WHITESPACE:
                tokens.append(token)
            
            if token.type == TokenType.EOF:
                break
                
        return tokens
    
    def __iter__(self) -> Iterator[Token]:
        """Make lexer iterable."""
        while True:
            token = self.next_token()
            if token.type != TokenType.WHITESPACE:
                yield token
            if token.type == TokenType.EOF:
                break