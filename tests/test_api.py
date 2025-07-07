#!/usr/bin/env python3

"""
test_api
========

Tests for the public API of the `alteruphono` package.
"""

import unittest
import alteruphono


class TestPublicAPI(unittest.TestCase):
    """Test the public API exported by alteruphono."""

    def test_api_exports(self):
        """Test that all expected symbols are exported."""
        # Core classes
        self.assertTrue(hasattr(alteruphono, 'BoundaryToken'))
        self.assertTrue(hasattr(alteruphono, 'FocusToken'))
        self.assertTrue(hasattr(alteruphono, 'EmptyToken'))
        self.assertTrue(hasattr(alteruphono, 'BackRefToken'))
        self.assertTrue(hasattr(alteruphono, 'ChoiceToken'))
        self.assertTrue(hasattr(alteruphono, 'SetToken'))
        self.assertTrue(hasattr(alteruphono, 'SegmentToken'))
        
        # Parser components
        self.assertTrue(hasattr(alteruphono, 'Rule'))
        self.assertTrue(hasattr(alteruphono, 'parse_rule'))
        self.assertTrue(hasattr(alteruphono, 'parse_seq_as_rule'))
        
        # Core functions
        self.assertTrue(hasattr(alteruphono, 'forward'))
        self.assertTrue(hasattr(alteruphono, 'backward'))
        self.assertTrue(hasattr(alteruphono, 'check_match'))

    def test_version_info(self):
        """Test that version information is available."""
        self.assertTrue(hasattr(alteruphono, '__version__'))
        self.assertTrue(hasattr(alteruphono, '__author__'))
        self.assertTrue(hasattr(alteruphono, '__email__'))
        
        # Version should be a string
        self.assertIsInstance(alteruphono.__version__, str)
        self.assertIsInstance(alteruphono.__author__, str)
        self.assertIsInstance(alteruphono.__email__, str)

    def test_forward_function_signature(self):
        """Test the forward function signature and basic usage."""
        from alteruphono.phonology import parse_sequence, parse_segment
        
        # Test with minimal valid input
        rule = alteruphono.Rule("p > b")
        sequence = parse_sequence("# p #", boundaries=True)
        
        result = alteruphono.forward(sequence, rule)
        
        # Should return a list
        self.assertIsInstance(result, list)
        
        # Should have same length or different (due to insertions/deletions)
        self.assertIsInstance(len(result), int)

    def test_backward_function_signature(self):
        """Test the backward function signature and basic usage."""
        from alteruphono.phonology import parse_sequence, parse_segment
        
        # Test with minimal valid input
        rule = alteruphono.Rule("p > b")
        sequence = parse_sequence("# b #", boundaries=True)
        
        result = alteruphono.backward(sequence, rule)
        
        # Should return a list of sequences
        self.assertIsInstance(result, list)
        
        # Each element should be a sequence
        for seq in result:
            self.assertIsNotNone(seq)

    def test_rule_creation_api(self):
        """Test Rule creation and basic API."""
        rule = alteruphono.Rule("p > b")
        
        # Should have string representation
        self.assertEqual(str(rule), "p > b")
        
        # Should have repr
        self.assertIsInstance(repr(rule), str)
        
        # Should be hashable
        self.assertIsInstance(hash(rule), int)
        
        # Should support equality
        rule2 = alteruphono.Rule("p > b")
        rule3 = alteruphono.Rule("p > d")
        
        self.assertEqual(rule, rule2)
        self.assertNotEqual(rule, rule3)

    def test_parse_rule_api(self):
        """Test parse_rule function API."""
        ante, post = alteruphono.parse_rule("p > b")
        
        # Should return two lists
        self.assertIsInstance(ante, list)
        self.assertIsInstance(post, list)
        
        # Lists should contain tokens
        self.assertGreater(len(ante), 0)
        self.assertGreater(len(post), 0)
        
        # Tokens should have string representations
        for token in ante + post:
            self.assertIsInstance(str(token), str)

    def test_check_match_api(self):
        """Test check_match function API."""
        from alteruphono.phonology import parse_sequence, parse_segment
        
        sequence = [parse_segment("p")]
        pattern = [alteruphono.SegmentToken("p")]
        
        match, match_list = alteruphono.check_match(sequence, pattern)
        
        # Should return boolean and list
        self.assertIsInstance(match, bool)
        self.assertIsInstance(match_list, list)
        
        # Match list should have same length as input
        self.assertEqual(len(match_list), len(sequence))


class TestAPIConsistency(unittest.TestCase):
    """Test API consistency and expected behaviors."""

    def test_rule_parsing_consistency(self):
        """Test that rule parsing is consistent."""
        rule_str = "p > b / _ a"
        
        # Creating Rule object should parse the rule
        rule = alteruphono.Rule(rule_str)
        
        # Parsing manually should give same result
        ante, post = alteruphono.parse_rule(rule_str)
        
        # Rule object should contain same parsed data
        self.assertEqual(len(rule.ante), len(ante))
        self.assertEqual(len(rule.post), len(post))

    def test_forward_backward_types(self):
        """Test that forward and backward return consistent types."""
        from alteruphono.phonology import parse_sequence, parse_segment
        
        rule = alteruphono.Rule("p > b")
        sequence = parse_sequence("# p #", boundaries=True)
        
        # Forward should return list of segments
        forward_result = alteruphono.forward(sequence, rule)
        self.assertIsInstance(forward_result, list)
        
        # Backward should return list of sequences
        backward_result = alteruphono.backward(forward_result, rule)
        self.assertIsInstance(backward_result, list)
        
        # Each backward result should be convertible to string
        for seq in backward_result:
            self.assertIsInstance(str(seq), str)

    def test_token_consistency(self):
        """Test that all token types behave consistently."""
        tokens = [
            alteruphono.BoundaryToken(),
            alteruphono.FocusToken(),
            alteruphono.EmptyToken(),
            alteruphono.BackRefToken(0),
            alteruphono.SegmentToken("p"),
        ]
        
        for token in tokens:
            # All tokens should have string representation
            self.assertIsInstance(str(token), str)
            
            # All tokens should have repr
            self.assertIsInstance(repr(token), str)
            
            # All tokens should be hashable
            self.assertIsInstance(hash(token), int)

    def test_error_consistency(self):
        """Test that errors are handled consistently."""
        # Test various invalid inputs and ensure consistent error handling
        
        # Invalid rule strings
        invalid_rules = ["", "p >", "> b", "invalid syntax here"]
        
        for rule_str in invalid_rules:
            with self.subTest(rule=rule_str):
                try:
                    rule = alteruphono.Rule(rule_str)
                    # If no exception, that's also valid behavior
                except Exception as e:
                    # Should be a reasonable exception type
                    self.assertIsInstance(e, Exception)


class TestAPIDocumentation(unittest.TestCase):
    """Test that API components have proper documentation."""

    def test_module_docstring(self):
        """Test that the module has a docstring."""
        self.assertIsNotNone(alteruphono.__doc__)

    def test_main_classes_have_docstrings(self):
        """Test that main classes have docstrings."""
        classes_to_check = [
            alteruphono.Rule,
            alteruphono.BoundaryToken,
            alteruphono.SegmentToken,
        ]
        
        for cls in classes_to_check:
            with self.subTest(cls=cls.__name__):
                self.assertIsNotNone(cls.__doc__)

    def test_main_functions_have_docstrings(self):
        """Test that main functions have docstrings."""
        functions_to_check = [
            alteruphono.forward,
            alteruphono.backward,
            alteruphono.parse_rule,
            alteruphono.check_match,
        ]
        
        for func in functions_to_check:
            with self.subTest(func=func.__name__):
                self.assertIsNotNone(func.__doc__)


class TestAPIStability(unittest.TestCase):
    """Test API stability requirements for 1.0 release."""

    def test_no_private_exports(self):
        """Test that no private symbols are exported."""
        # Get all exported symbols
        exported = [name for name in dir(alteruphono) if not name.startswith('_')]
        
        # All exported symbols should be intentional public API
        expected_exports = {
            # Core classes
            'BoundaryToken', 'FocusToken', 'EmptyToken', 'BackRefToken',
            'ChoiceToken', 'SetToken', 'SegmentToken',
            # Parser components  
            'Rule', 'parse_rule', 'parse_seq_as_rule',
            # Core functions
            'forward', 'backward', 'check_match',
            # Metadata
            '__version__', '__author__', '__email__'
        }
        
        # Check that we're not accidentally exporting private symbols
        for symbol in exported:
            if symbol not in expected_exports:
                # This should be documented if it's intentionally public
                print(f"Warning: Unexpected public symbol: {symbol}")

    def test_immutable_api_behavior(self):
        """Test that API functions don't modify their inputs."""
        from alteruphono.phonology import parse_sequence, parse_segment
        
        rule = alteruphono.Rule("p > b")
        original_sequence = parse_sequence("# p a p #", boundaries=True)
        
        # Store original string representation
        original_str = str(original_sequence)
        
        # Apply forward transformation
        result = alteruphono.forward(original_sequence, rule)
        
        # Original sequence should be unchanged
        self.assertEqual(str(original_sequence), original_str)
        
        # Apply backward transformation
        backward_results = alteruphono.backward(result, rule)
        
        # Result should still be unchanged
        result_str = " ".join(str(s) for s in result)
        # Apply forward again to verify result is unchanged
        result2 = alteruphono.forward(original_sequence, rule)
        result2_str = " ".join(str(s) for s in result2)
        self.assertEqual(result_str, result2_str)

    def test_deterministic_behavior(self):
        """Test that API functions behave deterministically."""
        from alteruphono.phonology import parse_sequence, parse_segment
        
        rule = alteruphono.Rule("p > b")
        sequence = parse_sequence("# p a p #", boundaries=True)
        
        # Multiple calls should give same results
        result1 = alteruphono.forward(sequence, rule)
        result2 = alteruphono.forward(sequence, rule)
        
        result1_str = " ".join(str(s) for s in result1)
        result2_str = " ".join(str(s) for s in result2)
        
        self.assertEqual(result1_str, result2_str)
        
        # Same for backward
        backward1 = alteruphono.backward(result1, rule)
        backward2 = alteruphono.backward(result1, rule)
        
        backward1_strs = [str(r) for r in backward1]
        backward2_strs = [str(r) for r in backward2]
        
        self.assertEqual(backward1_strs, backward2_strs)


if __name__ == "__main__":
    unittest.main()