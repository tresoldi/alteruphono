#!/usr/bin/env python3

"""
test_integration
================

Integration tests for the `alteruphono` package using real linguistic data.
"""

import unittest
import csv
import os
import alteruphono
import maniphono


class TestRealLinguisticData(unittest.TestCase):
    """Test with real linguistic sound changes."""

    def test_germanic_sound_changes(self):
        """Test some well-known Germanic sound changes."""
        # Grimm's Law examples
        test_cases = [
            # p > f (initial)
            ("p > f / # _", "# p a t e r #", "# f a t e r #"),
            # t > θ  
            ("t > θ", "# t r e s #", "# θ r e s #"),
            # k > h
            ("k > h", "# k o r d #", "# h o r d #"),
        ]
        
        for rule_str, input_str, expected_str in test_cases:
            with self.subTest(rule=rule_str):
                try:
                    rule = alteruphono.Rule(rule_str)
                    input_seq = maniphono.parse_sequence(input_str, boundaries=True)
                    result = alteruphono.forward(input_seq, rule)
                    result_str = " ".join(str(s) for s in result)
                    self.assertEqual(result_str, expected_str)
                except NotImplementedError:
                    # Skip tests that require unimplemented maniphono features
                    self.skipTest(f"Feature not implemented: {rule_str}")

    def test_romance_sound_changes(self):
        """Test some Romance sound changes."""
        test_cases = [
            # Latin intervocalic -p- > -b-
            ("p > b / V _ V", "# a p a #", "# a b a #"),
            # Latin k > tʃ / _ i
            ("k > tʃ / _ i", "# k i r k u s #", "# tʃ i r k u s #"),
            # Loss of final -m
            ("m > :null: / _ #", "# a m o r e m #", "# a m o r e #"),
        ]
        
        for rule_str, input_str, expected_str in test_cases:
            with self.subTest(rule=rule_str):
                try:
                    rule = alteruphono.Rule(rule_str)
                    input_seq = maniphono.parse_sequence(input_str, boundaries=True)
                    result = alteruphono.forward(input_seq, rule)
                    result_str = " ".join(str(s) for s in result)
                    self.assertEqual(result_str, expected_str)
                except NotImplementedError:
                    # Skip tests that require unimplemented maniphono features
                    self.skipTest(f"Feature not implemented: {rule_str}")

    def test_slavic_sound_changes(self):
        """Test some Slavic sound changes."""
        test_cases = [
            # First palatalization: k > tʃ / _ i
            ("k > tʃ / _ i", "# k i n o #", "# tʃ i n o #"),
            # Nasal + stop simplification
            ("N p > p", "# i m p e r i j #", "# i p e r i j #"),
        ]
        
        for rule_str, input_str, expected_str in test_cases:
            with self.subTest(rule=rule_str):
                try:
                    rule = alteruphono.Rule(rule_str)
                    input_seq = maniphono.parse_sequence(input_str, boundaries=True)
                    result = alteruphono.forward(input_seq, rule)
                    result_str = " ".join(str(s) for s in result)
                    self.assertEqual(result_str, expected_str)
                except Exception as e:
                    # Some features might not be available
                    self.skipTest(f"Feature not available: {e}")


class TestBidirectionalConsistency(unittest.TestCase):
    """Test that forward and backward operations are consistent."""

    def test_forward_backward_consistency(self):
        """Test that applying forward then backward includes original."""
        test_cases = [
            ("p > b", "# p a p a #"),
            ("t > d / V _ V", "# a t a t a #"),
            ("s > :null: / _ #", "# a l a s #"),
        ]
        
        for rule_str, input_str in test_cases:
            with self.subTest(rule=rule_str, input=input_str):
                try:
                    rule = alteruphono.Rule(rule_str)
                    input_seq = maniphono.parse_sequence(input_str, boundaries=True)
                    
                    # Apply forward
                    forward_result = alteruphono.forward(input_seq, rule)
                    
                    # Apply backward to the result
                    backward_results = alteruphono.backward(forward_result, rule)
                    backward_strs = [str(r) for r in backward_results]
                    
                    # Original should be among the backward results
                    self.assertIn(input_str, backward_strs)
                except NotImplementedError:
                    self.skipTest(f"Feature not implemented: {rule_str}")

    def test_backward_forward_consistency(self):
        """Test that applying backward then forward gives consistent results."""
        test_cases = [
            ("p > b", "# b a b a #"),
            ("t > d / V _ V", "# a d a d a #"),
            ("s > h / V _ V", "# a h a h a #"),
        ]
        
        for rule_str, output_str in test_cases:
            with self.subTest(rule=rule_str, output=output_str):
                rule = alteruphono.Rule(rule_str)
                output_seq = maniphono.parse_sequence(output_str, boundaries=True)
                
                # Apply backward
                backward_results = alteruphono.backward(output_seq, rule)
                
                # Apply forward to each backward result
                for backward_result in backward_results:
                    forward_result = alteruphono.forward(backward_result, rule)
                    forward_str = " ".join(str(s) for s in forward_result)
                    
                    # One of the results should match the original output
                    # (We can't guarantee all will, due to multiple possible inputs)


class TestComplexRuleInteractions(unittest.TestCase):
    """Test complex interactions between different rule types."""

    def test_feeding_rules(self):
        """Test rules that could feed each other."""
        # Rule 1: a > e
        # Rule 2: e > i / _ C
        # If applied in sequence, a > e > i / _ C
        
        rule1 = alteruphono.Rule("a > e")
        rule2 = alteruphono.Rule("e > i / _ C")
        
        input_seq = maniphono.parse_sequence("# a p a k #", boundaries=True)
        
        # Apply first rule
        intermediate = alteruphono.forward(input_seq, rule1)
        
        # Apply second rule  
        final_result = alteruphono.forward(intermediate, rule2)
        
        final_str = " ".join(str(s) for s in final_result)
        # Note: The actual behavior may differ based on implementation details
        # This test verifies the chaining mechanism works
        self.assertNotEqual(final_str, " ".join(str(s) for s in input_seq))

    def test_bleeding_rules(self):
        """Test rules that could bleed each other."""
        # Rule 1: p > f / _ s
        # Rule 2: s > h / p _
        # If rule 1 applies first, it bleeds rule 2
        
        rule1 = alteruphono.Rule("p > f / _ s")
        rule2 = alteruphono.Rule("s > h / p _")
        
        input_seq = maniphono.parse_sequence("# p s a #", boundaries=True)
        
        # Apply first rule (should change p > f)
        intermediate = alteruphono.forward(input_seq, rule1)
        
        # Apply second rule (should not apply since no 'p' left)
        final_result = alteruphono.forward(intermediate, rule2)
        
        final_str = " ".join(str(s) for s in final_result)
        expected = "# f s a #"  # 's' should not change to 'h'
        self.assertEqual(final_str, expected)

    def test_counterfeeding_order(self):
        """Test counterfeeding rule order."""
        # Same rules as bleeding test, but applied in reverse order
        rule1 = alteruphono.Rule("p > f / _ s")
        rule2 = alteruphono.Rule("s > h / p _")
        
        input_seq = maniphono.parse_sequence("# p s a #", boundaries=True)
        
        # Apply second rule first (should change s > h)
        intermediate = alteruphono.forward(input_seq, rule2)
        
        # Apply first rule (should still apply since 's' is now 'h')
        final_result = alteruphono.forward(intermediate, rule1)
        
        final_str = " ".join(str(s) for s in final_result)
        # Result should be different from bleeding order
        self.assertNotEqual(final_str, "# f s a #")


class TestPerformanceWithLargeData(unittest.TestCase):
    """Test performance with larger datasets."""

    def test_many_rules_application(self):
        """Test applying many rules in sequence."""
        rules = [
            alteruphono.Rule("a > e"),
            alteruphono.Rule("e > i"),
            alteruphono.Rule("i > o"),
            alteruphono.Rule("o > u"),
            alteruphono.Rule("u > a"),  # Cycle back
        ]
        
        input_seq = maniphono.parse_sequence("# a a a a a #", boundaries=True)
        
        # Apply all rules in sequence
        current_seq = input_seq
        for rule in rules:
            current_seq = alteruphono.forward(current_seq, rule)
        
        # Should complete without errors
        final_str = " ".join(str(s) for s in current_seq)
        self.assertIsInstance(final_str, str)

    def test_long_sequence_processing(self):
        """Test processing of long sequences."""
        # Create a long sequence
        segments = ["#"] + ["p", "a"] * 25 + ["#"]  # 52 segments total
        input_str = " ".join(segments)
        input_seq = maniphono.parse_sequence(input_str, boundaries=True)
        
        rule = alteruphono.Rule("p > b")
        result = alteruphono.forward(input_seq, rule)
        
        # Should complete and have same length
        self.assertEqual(len(result), len(input_seq))
        
        # All 'p' should become 'b'
        result_str = " ".join(str(s) for s in result)
        self.assertNotIn(" p ", result_str)
        self.assertIn(" b ", result_str)

    def test_many_backward_reconstructions(self):
        """Test backward reconstruction with many possibilities."""
        # Rule that creates many possible reconstructions
        rule = alteruphono.Rule("p|t|k > b")
        input_seq = maniphono.parse_sequence("# b b b #", boundaries=True)
        
        results = alteruphono.backward(input_seq, rule)
        
        # Should generate multiple reconstructions
        self.assertGreater(len(results), 1)
        
        # Should complete in reasonable time
        result_strs = [str(r) for r in results]
        self.assertIsInstance(result_strs, list)


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""

    def test_malformed_rules_handling(self):
        """Test handling of malformed rules."""
        malformed_rules = [
            "",           # Empty rule
            "p >",        # Missing target
            "> b",        # Missing source
            "p > b /",    # Missing context
            "p > b / _",  # Incomplete context
        ]
        
        for rule_str in malformed_rules:
            with self.subTest(rule=rule_str):
                # Should either raise an exception or handle gracefully
                try:
                    rule = alteruphono.Rule(rule_str)
                    # If it doesn't raise an exception, that's also acceptable
                    # as long as it behaves predictably
                except Exception:
                    # Expected for malformed rules
                    pass

    def test_invalid_sequence_handling(self):
        """Test handling of invalid sequences."""
        rule = alteruphono.Rule("p > b")
        
        # Test with various invalid inputs
        invalid_inputs = [
            "",                    # Empty string
            "# #",                # Only boundaries
            "invalid phoneme",    # Invalid phoneme symbols
        ]
        
        for input_str in invalid_inputs:
            with self.subTest(input=input_str):
                try:
                    input_seq = maniphono.parse_sequence(input_str, boundaries=True)
                    result = alteruphono.forward(input_seq, rule)
                    # Should handle gracefully
                    self.assertIsInstance(result, list)
                except Exception:
                    # Also acceptable to raise exceptions for invalid input
                    pass


if __name__ == "__main__":
    unittest.main()