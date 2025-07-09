"""
Tests for the new parsing system - Lexer component.
"""

import unittest
from alteruphono.parsing.lexer import Lexer, Token, TokenType
from alteruphono.parsing.errors import LexicalError


class TestLexer(unittest.TestCase):
    """Test the lexer tokenization."""
    
    def setUp(self):
        """Set up test fixtures."""
        pass
    
    def tokenize(self, text: str) -> list:
        """Helper to tokenize text and return token values."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        # Remove EOF token for easier testing
        return [(t.type, t.value) for t in tokens if t.type != TokenType.EOF]
    
    def test_simple_rule(self):
        """Test tokenizing a simple rule."""
        tokens = self.tokenize("p > b")
        expected = [
            (TokenType.GRAPHEME, "p"),
            (TokenType.ARROW, ">"),
            (TokenType.GRAPHEME, "b")
        ]
        self.assertEqual(tokens, expected)
    
    def test_rule_with_context(self):
        """Test tokenizing a rule with context."""
        tokens = self.tokenize("p > b / a _ a")
        expected = [
            (TokenType.GRAPHEME, "p"),
            (TokenType.ARROW, ">"),
            (TokenType.GRAPHEME, "b"),
            (TokenType.SLASH, "/"),
            (TokenType.GRAPHEME, "a"),
            (TokenType.FOCUS, "_"),
            (TokenType.GRAPHEME, "a")
        ]
        self.assertEqual(tokens, expected)
    
    def test_sound_classes(self):
        """Test tokenizing sound classes."""
        tokens = self.tokenize("V > C")
        expected = [
            (TokenType.SOUND_CLASS, "V"),
            (TokenType.ARROW, ">"),
            (TokenType.SOUND_CLASS, "C")
        ]
        self.assertEqual(tokens, expected)
    
    def test_features(self):
        """Test tokenizing features."""
        tokens = self.tokenize("p[voiced] > b")
        expected = [
            (TokenType.GRAPHEME, "p"),
            (TokenType.LBRACKET, "["),
            (TokenType.FEATURE, "voiced"),
            (TokenType.RBRACKET, "]"),
            (TokenType.ARROW, ">"),
            (TokenType.GRAPHEME, "b")
        ]
        self.assertEqual(tokens, expected)
    
    def test_feature_polarity(self):
        """Test tokenizing feature polarity."""
        tokens = self.tokenize("p[+voiced,-nasal]")
        expected = [
            (TokenType.GRAPHEME, "p"),
            (TokenType.LBRACKET, "["),
            (TokenType.PLUS, "+"),
            (TokenType.FEATURE, "voiced"),
            (TokenType.COMMA, ","),
            (TokenType.MINUS, "-"),
            (TokenType.FEATURE, "nasal"),
            (TokenType.RBRACKET, "]")
        ]
        self.assertEqual(tokens, expected)
    
    def test_backreferences(self):
        """Test tokenizing backreferences."""
        tokens = self.tokenize("p a > @1 @2")
        expected = [
            (TokenType.GRAPHEME, "p"),
            (TokenType.GRAPHEME, "a"),
            (TokenType.ARROW, ">"),
            (TokenType.BACKREF, "@1"),
            (TokenType.BACKREF, "@2")
        ]
        self.assertEqual(tokens, expected)
    
    def test_backreferences_with_features(self):
        """Test tokenizing backreferences with features."""
        tokens = self.tokenize("p > @1[voiced]")
        expected = [
            (TokenType.GRAPHEME, "p"),
            (TokenType.ARROW, ">"),
            (TokenType.BACKREF, "@1"),
            (TokenType.LBRACKET, "["),
            (TokenType.FEATURE, "voiced"),
            (TokenType.RBRACKET, "]")
        ]
        self.assertEqual(tokens, expected)
    
    def test_choices(self):
        """Test tokenizing choices."""
        tokens = self.tokenize("p|t > b")
        expected = [
            (TokenType.GRAPHEME, "p"),
            (TokenType.PIPE, "|"),
            (TokenType.GRAPHEME, "t"),
            (TokenType.ARROW, ">"),
            (TokenType.GRAPHEME, "b")
        ]
        self.assertEqual(tokens, expected)
    
    def test_sets(self):
        """Test tokenizing sets."""
        tokens = self.tokenize("{p|t} > b")
        expected = [
            (TokenType.LBRACE, "{"),
            (TokenType.GRAPHEME, "p"),
            (TokenType.PIPE, "|"),
            (TokenType.GRAPHEME, "t"),
            (TokenType.RBRACE, "}"),
            (TokenType.ARROW, ">"),
            (TokenType.GRAPHEME, "b")
        ]
        self.assertEqual(tokens, expected)
    
    def test_boundaries(self):
        """Test tokenizing boundaries."""
        tokens = self.tokenize("p > b / # _")
        expected = [
            (TokenType.GRAPHEME, "p"),
            (TokenType.ARROW, ">"),
            (TokenType.GRAPHEME, "b"),
            (TokenType.SLASH, "/"),
            (TokenType.BOUNDARY, "#"),
            (TokenType.FOCUS, "_")
        ]
        self.assertEqual(tokens, expected)
    
    def test_null(self):
        """Test tokenizing null/deletion."""
        tokens = self.tokenize("p > :null:")
        expected = [
            (TokenType.GRAPHEME, "p"),
            (TokenType.ARROW, ">"),
            (TokenType.NULL, ":null:")
        ]
        self.assertEqual(tokens, expected)
    
    def test_complex_ipa_symbols(self):
        """Test tokenizing complex IPA symbols."""
        tokens = self.tokenize("tʃ dʒ sʼ")
        expected = [
            (TokenType.GRAPHEME, "tʃ"),
            (TokenType.GRAPHEME, "dʒ"),
            (TokenType.GRAPHEME, "sʼ")
        ]
        self.assertEqual(tokens, expected)
    
    def test_unicode_normalization(self):
        """Test that Unicode is properly normalized."""
        # Test with composed vs decomposed characters
        lexer1 = Lexer("é")  # composed
        lexer2 = Lexer("é")  # decomposed (e + combining acute)
        
        tokens1 = lexer1.tokenize()
        tokens2 = lexer2.tokenize()
        
        # Should tokenize the same way after normalization
        self.assertEqual(len(tokens1), len(tokens2))
    
    def test_numbers(self):
        """Test tokenizing numbers (for future numeric features)."""
        tokens = self.tokenize("120 3.14")
        expected = [
            (TokenType.NUMBER, "120"),
            (TokenType.NUMBER, "3.14")
        ]
        self.assertEqual(tokens, expected)
    
    def test_units(self):
        """Test tokenizing units (for future numeric features)."""
        tokens = self.tokenize("120Hz 50ms")
        expected = [
            (TokenType.NUMBER, "120"),
            (TokenType.UNIT, "Hz"),
            (TokenType.NUMBER, "50"),
            (TokenType.UNIT, "ms")
        ]
        self.assertEqual(tokens, expected)
    
    def test_whitespace_handling(self):
        """Test that whitespace is handled correctly."""
        tokens1 = self.tokenize("p>b")
        tokens2 = self.tokenize("p > b")
        tokens3 = self.tokenize("p  >   b")
        
        expected = [
            (TokenType.GRAPHEME, "p"),
            (TokenType.ARROW, ">"),
            (TokenType.GRAPHEME, "b")
        ]
        
        self.assertEqual(tokens1, expected)
        self.assertEqual(tokens2, expected)
        self.assertEqual(tokens3, expected)
    
    def test_position_tracking(self):
        """Test that token positions are tracked correctly."""
        lexer = Lexer("p > b")
        tokens = lexer.tokenize()
        
        # Check positions
        self.assertEqual(tokens[0].position, 0)  # p
        self.assertEqual(tokens[1].position, 2)  # >
        self.assertEqual(tokens[2].position, 4)  # b
    
    def test_line_column_tracking(self):
        """Test that line and column numbers are tracked correctly."""
        lexer = Lexer("p >\nb")
        tokens = lexer.tokenize()
        
        # Find the 'b' token
        b_token = None
        for token in tokens:
            if token.value == "b":
                b_token = token
                break
        
        self.assertIsNotNone(b_token)
        self.assertEqual(b_token.line, 2)
        self.assertEqual(b_token.column, 1)
    
    def test_error_handling(self):
        """Test error handling for invalid tokens."""
        with self.assertRaises(LexicalError):
            lexer = Lexer("@")  # Invalid backreference
            lexer.tokenize()
        
        with self.assertRaises(LexicalError):
            lexer = Lexer("@abc")  # Invalid backreference
            lexer.tokenize()
    
    def test_empty_input(self):
        """Test handling of empty input."""
        tokens = self.tokenize("")
        self.assertEqual(tokens, [])
    
    def test_iterator_interface(self):
        """Test that lexer can be used as an iterator."""
        lexer = Lexer("p > b")
        token_values = []
        
        for token in lexer:
            if token.type != TokenType.EOF:
                token_values.append(token.value)
        
        self.assertEqual(token_values, ["p", ">", "b"])


class TestLexerRealWorldExamples(unittest.TestCase):
    """Test lexer with real-world phonological rules."""
    
    def tokenize(self, text: str) -> list:
        """Helper to tokenize text and return token values."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        return [(t.type, t.value) for t in tokens if t.type != TokenType.EOF]
    
    def test_germanic_rules(self):
        """Test with Germanic sound change rules."""
        rules = [
            "p t k > b d g / V _ V",  # Lenition
            "s > z / V _ V",          # Voicing
            "ai > e / _ #",           # Monophthongization
        ]
        
        for rule in rules:
            tokens = self.tokenize(rule)
            self.assertGreater(len(tokens), 0)
            # Just check that it doesn't crash
    
    def test_romance_rules(self):
        """Test with Romance sound change rules."""
        rules = [
            "kt > tt",                # Simplification
            "V > V[+stress] / _ C #", # Final stress
            "s C > C / _ #",          # Cluster reduction
        ]
        
        for rule in rules:
            tokens = self.tokenize(rule)
            self.assertGreater(len(tokens), 0)
    
    def test_complex_features(self):
        """Test with complex feature specifications."""
        rules = [
            "C[+voice,-nasal] > C[-voice]",
            "V[high,front] > V[+tense]",
            "S[voiceless] a > @1[fricative] a",
        ]
        
        for rule in rules:
            tokens = self.tokenize(rule)
            self.assertGreater(len(tokens), 0)


if __name__ == "__main__":
    unittest.main()