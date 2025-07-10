#!/usr/bin/env python3

"""
test_model
==========

Tests for the model classes in the `alteruphono` package.
"""

import unittest
from unittest.mock import Mock

import alteruphono
from alteruphono.model import (
    Token,
    BoundaryToken,
    FocusToken, 
    EmptyToken,
    BackRefToken,
    ChoiceToken,
    SetToken,
    SegmentToken,
)


class TestTokens(unittest.TestCase):
    """Test cases for token classes."""

    def test_boundary_token(self):
        """Test BoundaryToken functionality."""
        token = BoundaryToken()
        self.assertEqual(str(token), "#")
        self.assertEqual(repr(token), "boundary_tok:#")
        self.assertEqual(hash(token), hash("#"))
        
        # Test equality
        token2 = BoundaryToken()
        self.assertEqual(hash(token), hash(token2))

    def test_focus_token(self):
        """Test FocusToken functionality."""
        token = FocusToken()
        self.assertEqual(str(token), "_")
        self.assertEqual(repr(token), "focus_tok:_")
        self.assertEqual(hash(token), hash(2))
        
        # Test equality
        token2 = FocusToken()
        self.assertEqual(hash(token), hash(token2))

    def test_empty_token(self):
        """Test EmptyToken functionality."""
        token = EmptyToken()
        self.assertEqual(str(token), ":null:")
        self.assertEqual(repr(token), "empty_tok::null:")
        self.assertEqual(hash(token), hash(3))
        
        # Test equality
        token2 = EmptyToken()
        self.assertEqual(hash(token), hash(token2))

    def test_backref_token_basic(self):
        """Test BackRefToken without modifier."""
        token = BackRefToken(1)
        self.assertEqual(str(token), "@2")  # 1-based indexing in string representation
        self.assertEqual(repr(token), "backref_tok:@2")
        self.assertEqual(token.index, 1)
        self.assertIsNone(token.modifier)

    def test_backref_token_with_modifier(self):
        """Test BackRefToken with modifier."""
        token = BackRefToken(0, "voiced")
        self.assertEqual(str(token), "@1[voiced]")
        self.assertEqual(repr(token), "backref_tok:@1[voiced]")
        self.assertEqual(token.index, 0)
        self.assertEqual(token.modifier, "voiced")

    def test_backref_token_arithmetic(self):
        """Test BackRefToken arithmetic operations."""
        token = BackRefToken(1)
        new_token = token + 2
        self.assertEqual(new_token.index, 3)
        self.assertEqual(token.index, 1)  # Original unchanged

    def test_backref_token_equality(self):
        """Test BackRefToken equality."""
        token1 = BackRefToken(1)
        token2 = BackRefToken(1)
        token3 = BackRefToken(2)
        token4 = BackRefToken(1, "voiced")
        
        self.assertEqual(token1, token2)
        self.assertNotEqual(token1, token3)
        self.assertNotEqual(token1, token4)

    def test_choice_token(self):
        """Test ChoiceToken functionality."""
        mock_choice1 = Mock()
        mock_choice1.__str__ = Mock(return_value="p")
        mock_choice2 = Mock()
        mock_choice2.__str__ = Mock(return_value="b")
        
        token = ChoiceToken([mock_choice1, mock_choice2])
        self.assertEqual(str(token), "p|b")
        self.assertEqual(repr(token), "choice_tok:p|b")
        self.assertEqual(token.choices, [mock_choice1, mock_choice2])

    def test_set_token(self):
        """Test SetToken functionality."""
        mock_choice1 = Mock()
        mock_choice1.__str__ = Mock(return_value="a")
        mock_choice2 = Mock()
        mock_choice2.__str__ = Mock(return_value="e")
        
        token = SetToken([mock_choice1, mock_choice2])
        self.assertEqual(str(token), "{a|e}")
        self.assertEqual(repr(token), "set_tok:{a|e}")
        self.assertEqual(token.choices, [mock_choice1, mock_choice2])

    def test_segment_token_string_input(self):
        """Test SegmentToken with string input."""
        try:
            token = SegmentToken("p")
            self.assertEqual(str(token), "p")
            self.assertEqual(repr(token), "segment_tok:p")
        except ImportError:
            # Skip if maniphono parse_segment not available
            self.skipTest("maniphono.parse_segment not available")

    def test_segment_token_equality(self):
        """Test SegmentToken equality."""
        try:
            token1 = SegmentToken("p")
            token2 = SegmentToken("p")
            token3 = SegmentToken("b")
            
            self.assertEqual(token1, token2)
            self.assertNotEqual(token1, token3)
        except ImportError:
            self.skipTest("maniphono not available")

    def test_segment_token_hash_consistency(self):
        """Test that equal tokens have same hash."""
        try:
            token1 = SegmentToken("p")
            token2 = SegmentToken("p")
            
            self.assertEqual(hash(token1), hash(token2))
        except ImportError:
            self.skipTest("maniphono not available")


if __name__ == "__main__":
    unittest.main()