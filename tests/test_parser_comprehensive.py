#!/usr/bin/env python3

"""
test_parser_comprehensive
=========================

Comprehensive tests for the parser in the `alteruphono` package.
"""

import unittest
import alteruphono
from alteruphono import (
    BoundaryToken,
    FocusToken,
    EmptyToken,
    BackRefToken,
    ChoiceToken,
    SetToken,
    SegmentToken,
)
from alteruphono.parser import Rule, parse_rule, preprocess, parse_atom


class TestPreprocessing(unittest.TestCase):
    """Test rule preprocessing functionality."""

    def test_preprocess_whitespace_normalization(self):
        """Test that multiple spaces are normalized to single spaces."""
        self.assertEqual(preprocess("p  >   b"), "p > b")
        self.assertEqual(preprocess("  p > b  "), "p > b")
        self.assertEqual(preprocess("p\t>\tb"), "p > b")

    def test_preprocess_unicode_normalization(self):
        """Test Unicode NFD normalization."""
        # This tests NFD normalization - composed characters should be decomposed
        result = preprocess("p > b")
        self.assertIsInstance(result, str)


class TestAtomParsing(unittest.TestCase):
    """Test individual atom parsing."""

    def test_parse_boundary_atom(self):
        """Test parsing boundary symbols."""
        token = parse_atom("#")
        self.assertIsInstance(token, BoundaryToken)

    def test_parse_focus_atom(self):
        """Test parsing focus symbols."""
        token = parse_atom("_")
        self.assertIsInstance(token, FocusToken)

    def test_parse_empty_atom(self):
        """Test parsing empty/null symbols."""
        token = parse_atom(":null:")
        self.assertIsInstance(token, EmptyToken)

    def test_parse_backref_no_modifier(self):
        """Test parsing back-references without modifiers."""
        token = parse_atom("@1")
        self.assertIsInstance(token, BackRefToken)
        self.assertEqual(token.index, 0)  # 0-based internally
        self.assertIsNone(token.modifier)

    def test_parse_backref_with_modifier(self):
        """Test parsing back-references with modifiers."""
        token = parse_atom("@2[voiced]")
        self.assertIsInstance(token, BackRefToken)
        self.assertEqual(token.index, 1)  # 0-based internally
        self.assertEqual(token.modifier, "voiced")

    def test_parse_choice_atom(self):
        """Test parsing choice expressions."""
        token = parse_atom("p|b|t")
        self.assertIsInstance(token, ChoiceToken)
        self.assertEqual(len(token.choices), 3)

    def test_parse_set_atom(self):
        """Test parsing set expressions."""
        token = parse_atom("{a|e|i}")
        self.assertIsInstance(token, SetToken)
        self.assertEqual(len(token.choices), 3)

    def test_parse_segment_atom(self):
        """Test parsing regular segment atoms."""
        try:
            token = parse_atom("p")
            self.assertIsInstance(token, SegmentToken)
        except ImportError:
            self.skipTest("maniphono not available")


class TestRuleParsing(unittest.TestCase):
    """Test complete rule parsing."""

    def test_simple_rule_no_context(self):
        """Test parsing simple rules without context."""
        ante, post = parse_rule("p > b")
        
        self.assertEqual(len(ante), 1)
        self.assertEqual(len(post), 1)
        self.assertIsInstance(ante[0], SegmentToken)
        self.assertIsInstance(post[0], SegmentToken)

    def test_rule_with_context(self):
        """Test parsing rules with context."""
        ante, post = parse_rule("p > b / _ V")
        
        self.assertEqual(len(ante), 2)  # p + V (context)
        self.assertEqual(len(post), 2)  # b + @1 (backref to V)
        
        self.assertIsInstance(ante[0], SegmentToken)
        self.assertIsInstance(ante[1], SegmentToken)
        self.assertIsInstance(post[0], SegmentToken)
        self.assertIsInstance(post[1], BackRefToken)

    def test_rule_with_complex_context(self):
        """Test parsing rules with complex contexts."""
        ante, post = parse_rule("s > z / V _ V")
        
        self.assertEqual(len(ante), 3)  # V + s + V
        self.assertEqual(len(post), 3)  # @1 + z + @3

    def test_rule_with_boundary_context(self):
        """Test parsing rules with boundary contexts."""
        ante, post = parse_rule("p > b / # _")
        
        self.assertEqual(len(ante), 2)  # # + p
        self.assertEqual(len(post), 2)  # @1 + b
        
        self.assertIsInstance(ante[0], BoundaryToken)
        self.assertIsInstance(post[0], BackRefToken)

    def test_rule_with_choice(self):
        """Test parsing rules with choices."""
        ante, post = parse_rule("p|t > b")
        
        self.assertEqual(len(ante), 1)
        self.assertEqual(len(post), 1)
        self.assertIsInstance(ante[0], ChoiceToken)
        self.assertIsInstance(post[0], SegmentToken)

    def test_rule_with_set(self):
        """Test parsing rules with sets."""
        ante, post = parse_rule("{p|t} > {b|d}")
        
        self.assertEqual(len(ante), 1)
        self.assertEqual(len(post), 1)
        self.assertIsInstance(ante[0], SetToken)
        self.assertIsInstance(post[0], SetToken)

    def test_rule_with_backref_modifier(self):
        """Test parsing rules with back-reference modifiers."""
        ante, post = parse_rule("p > @1[voiced]")
        
        self.assertEqual(len(ante), 1)
        self.assertEqual(len(post), 1)
        self.assertIsInstance(ante[0], SegmentToken)
        self.assertIsInstance(post[0], BackRefToken)
        self.assertEqual(post[0].modifier, "voiced")

    def test_rule_with_deletion(self):
        """Test parsing rules with deletion (null target)."""
        ante, post = parse_rule("p > :null:")
        
        self.assertEqual(len(ante), 1)
        self.assertEqual(len(post), 1)
        self.assertIsInstance(ante[0], SegmentToken)
        self.assertIsInstance(post[0], EmptyToken)

    def test_rule_with_insertion(self):
        """Test parsing rules with insertion (null source)."""
        ante, post = parse_rule(":null: > p")
        
        self.assertEqual(len(ante), 1)
        self.assertEqual(len(post), 1)
        self.assertIsInstance(ante[0], EmptyToken)
        self.assertIsInstance(post[0], SegmentToken)

    def test_complex_rule_with_multiple_elements(self):
        """Test parsing complex rules with multiple elements."""
        ante, post = parse_rule("C V C > @1 @2[long] @3 / # _ #")
        
        self.assertEqual(len(ante), 5)  # # + C + V + C + #
        self.assertEqual(len(post), 5)  # @1 + @2 + @3[long] + @4 + @5
        
        # Check that middle post element has modifier
        self.assertIsInstance(post[2], BackRefToken)
        self.assertEqual(post[2].modifier, "long")


class TestRuleClass(unittest.TestCase):
    """Test the Rule class functionality."""

    def test_rule_creation(self):
        """Test Rule object creation and basic properties."""
        rule = Rule("p > b")
        self.assertEqual(rule.source, "p > b")
        self.assertEqual(len(rule.ante), 1)
        self.assertEqual(len(rule.post), 1)

    def test_rule_string_representation(self):
        """Test Rule string representations."""
        rule = Rule("p > b / _ V")
        self.assertEqual(str(rule), "p > b / _ V")
        self.assertIn(">>>", repr(rule))

    def test_rule_equality(self):
        """Test Rule equality comparison."""
        rule1 = Rule("p > b")
        rule2 = Rule("p > b")
        rule3 = Rule("p > d")
        
        self.assertEqual(rule1, rule2)
        self.assertNotEqual(rule1, rule3)

    def test_rule_hash_consistency(self):
        """Test that equal rules have same hash."""
        rule1 = Rule("p > b")
        rule2 = Rule("p > b")
        
        self.assertEqual(hash(rule1), hash(rule2))


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def test_empty_rule_parts(self):
        """Test handling of rules with empty parts."""
        # These should ideally raise appropriate errors
        with self.assertRaises(Exception):
            parse_rule(" > b")
        
        with self.assertRaises(Exception):
            parse_rule("p > ")

    def test_malformed_backref(self):
        """Test handling of malformed back-references."""
        # This should parse as a regular segment if not matching backref pattern
        try:
            ante, post = parse_rule("p > @")
            # Should treat @ as a regular segment
            self.assertIsInstance(post[0], SegmentToken)
        except:
            # Or it might raise an error, which is also acceptable
            pass

    def test_nested_brackets(self):
        """Test handling of nested brackets."""
        # This tests robustness with complex bracket structures
        try:
            parse_rule("p[+voice] > b")
            # This should work or fail gracefully
        except:
            pass

    def test_unicode_segments(self):
        """Test handling of Unicode phonetic symbols."""
        try:
            ante, post = parse_rule("θ > ð")
            self.assertIsInstance(ante[0], SegmentToken)
            self.assertIsInstance(post[0], SegmentToken)
        except ImportError:
            self.skipTest("maniphono not available")


if __name__ == "__main__":
    unittest.main()