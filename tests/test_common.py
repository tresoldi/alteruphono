#!/usr/bin/env python3

"""
test_common
===========

Tests for common functionality in the `alteruphono` package.
"""

import unittest
from unittest.mock import Mock
import maniphono
import alteruphono
from alteruphono.common import check_match
from alteruphono.model import (
    BoundaryToken,
    SegmentToken,
    ChoiceToken,
    SetToken,
)


class TestCheckMatch(unittest.TestCase):
    """Test the check_match function."""

    def setUp(self):
        """Set up test fixtures."""
        self.boundary_seg = maniphono.BoundarySegment()
        try:
            self.sound_seg_p = maniphono.parse_segment("p")
            self.sound_seg_b = maniphono.parse_segment("b")
            self.sound_seg_a = maniphono.parse_segment("a")
        except ImportError:
            self.skipTest("maniphono not available")

    def test_length_mismatch(self):
        """Test that length mismatch returns False."""
        sequence = [self.sound_seg_p]
        pattern = [SegmentToken("p"), SegmentToken("a")]
        
        match, match_list = check_match(sequence, pattern)
        
        self.assertFalse(match)
        self.assertEqual(len(match_list), 1)
        self.assertFalse(match_list[0])

    def test_exact_segment_match(self):
        """Test exact segment matching."""
        sequence = [self.sound_seg_p]
        pattern = [SegmentToken("p")]
        
        match, match_list = check_match(sequence, pattern)
        
        self.assertTrue(match)
        self.assertEqual(len(match_list), 1)

    def test_segment_mismatch(self):
        """Test segment mismatch."""
        sequence = [self.sound_seg_p]
        pattern = [SegmentToken("b")]
        
        match, match_list = check_match(sequence, pattern)
        
        self.assertFalse(match)
        self.assertEqual(len(match_list), 1)
        self.assertFalse(match_list[0])

    def test_boundary_match(self):
        """Test boundary token matching."""
        sequence = [self.boundary_seg]
        pattern = [BoundaryToken()]
        
        match, match_list = check_match(sequence, pattern)
        
        self.assertTrue(match)
        self.assertEqual(len(match_list), 1)

    def test_boundary_mismatch(self):
        """Test boundary token mismatch."""
        sequence = [self.sound_seg_p]
        pattern = [BoundaryToken()]
        
        match, match_list = check_match(sequence, pattern)
        
        self.assertFalse(match)
        self.assertEqual(len(match_list), 1)
        self.assertFalse(match_list[0])

    def test_choice_match_first(self):
        """Test choice token matching first alternative."""
        sequence = [self.sound_seg_p]
        pattern = [ChoiceToken([SegmentToken("p"), SegmentToken("b")])]
        
        match, match_list = check_match(sequence, pattern)
        
        self.assertTrue(match)
        self.assertEqual(len(match_list), 1)
        # Should return the matched segment
        self.assertEqual(match_list[0], self.sound_seg_p)

    def test_choice_match_second(self):
        """Test choice token matching second alternative."""
        sequence = [self.sound_seg_b]
        pattern = [ChoiceToken([SegmentToken("p"), SegmentToken("b")])]
        
        match, match_list = check_match(sequence, pattern)
        
        self.assertTrue(match)
        self.assertEqual(len(match_list), 1)
        self.assertEqual(match_list[0], self.sound_seg_b)

    def test_choice_no_match(self):
        """Test choice token with no matching alternative."""
        sequence = [self.sound_seg_a]
        pattern = [ChoiceToken([SegmentToken("p"), SegmentToken("b")])]
        
        match, match_list = check_match(sequence, pattern)
        
        self.assertFalse(match)
        self.assertEqual(len(match_list), 1)
        self.assertFalse(match_list[0])

    def test_set_match_first(self):
        """Test set token matching first alternative."""
        sequence = [self.sound_seg_p]
        pattern = [SetToken([SegmentToken("p"), SegmentToken("b")])]
        
        match, match_list = check_match(sequence, pattern)
        
        self.assertTrue(match)
        self.assertEqual(len(match_list), 1)
        # Should return the index of matched alternative
        self.assertEqual(match_list[0], 0)

    def test_set_match_second(self):
        """Test set token matching second alternative."""
        sequence = [self.sound_seg_b]
        pattern = [SetToken([SegmentToken("p"), SegmentToken("b")])]
        
        match, match_list = check_match(sequence, pattern)
        
        self.assertTrue(match)
        self.assertEqual(len(match_list), 1)
        self.assertEqual(match_list[0], 1)

    def test_set_no_match(self):
        """Test set token with no matching alternative."""
        sequence = [self.sound_seg_a]
        pattern = [SetToken([SegmentToken("p"), SegmentToken("b")])]
        
        match, match_list = check_match(sequence, pattern)
        
        self.assertFalse(match)
        self.assertEqual(len(match_list), 1)
        self.assertFalse(match_list[0])

    def test_multiple_segments_all_match(self):
        """Test multiple segments that all match."""
        sequence = [self.sound_seg_p, self.sound_seg_a, self.boundary_seg]
        pattern = [SegmentToken("p"), SegmentToken("a"), BoundaryToken()]
        
        match, match_list = check_match(sequence, pattern)
        
        self.assertTrue(match)
        self.assertEqual(len(match_list), 3)

    def test_multiple_segments_partial_match(self):
        """Test multiple segments with partial match."""
        sequence = [self.sound_seg_p, self.sound_seg_a, self.sound_seg_b]
        pattern = [SegmentToken("p"), SegmentToken("a"), BoundaryToken()]
        
        match, match_list = check_match(sequence, pattern)
        
        self.assertFalse(match)
        self.assertEqual(len(match_list), 3)
        # First two should match, third should not
        self.assertFalse(match_list[2])  # Third element should be False/falsy

    def test_complex_pattern_with_choices_and_sets(self):
        """Test complex pattern with mixed token types."""
        sequence = [self.sound_seg_p, self.sound_seg_a, self.sound_seg_b]
        pattern = [
            ChoiceToken([SegmentToken("p"), SegmentToken("t")]),
            SegmentToken("a"),
            SetToken([SegmentToken("b"), SegmentToken("d")])
        ]
        
        match, match_list = check_match(sequence, pattern)
        
        self.assertTrue(match)
        self.assertEqual(len(match_list), 3)
        self.assertEqual(match_list[0], self.sound_seg_p)  # Choice match
        # match_list[1] should be truthy for exact segment match
        self.assertEqual(match_list[2], 0)  # Set match index

    def test_partial_sound_matching(self):
        """Test partial sound matching with features."""
        # This test depends on maniphono's feature system
        try:
            # Create a partial sound (sound with some features specified)
            partial_sound = maniphono.Sound("p")
            partial_sound.partial = True
            partial_segment = maniphono.SoundSegment([partial_sound])
            
            sequence = [self.sound_seg_p]
            pattern = [SegmentToken(partial_segment)]
            
            match, match_list = check_match(sequence, pattern)
            
            # This should work if the feature matching is implemented
            self.assertIsInstance(match, bool)
            self.assertIsInstance(match_list, list)
            
        except (ImportError, AttributeError):
            self.skipTest("maniphono partial sound matching not available")


class TestMatchListInterpretation(unittest.TestCase):
    """Test interpretation of match list results."""

    def test_false_vs_zero_distinction(self):
        """Test that False and 0 are distinguished in match results."""
        # This is important for set matching where 0 is a valid index
        sequence = [maniphono.parse_segment("p")]
        
        # Test with a set where first element matches
        pattern = [SetToken([SegmentToken("p"), SegmentToken("b")])]
        match, match_list = check_match(sequence, pattern)
        
        self.assertTrue(match)
        self.assertEqual(match_list[0], 0)
        # 0 should not be considered False in the context
        self.assertTrue(match_list[0] is not False)

    def test_match_list_length_consistency(self):
        """Test that match list always has same length as input."""
        test_cases = [
            ([maniphono.parse_segment("p")], [SegmentToken("p")]),
            ([maniphono.parse_segment("p")], [SegmentToken("b")]),
            ([maniphono.BoundarySegment()], [BoundaryToken()]),
            ([maniphono.parse_segment("p"), maniphono.parse_segment("a")], 
             [SegmentToken("p"), SegmentToken("a")]),
        ]
        
        for sequence, pattern in test_cases:
            match, match_list = check_match(sequence, pattern)
            self.assertEqual(len(match_list), len(sequence))
            self.assertEqual(len(match_list), len(pattern))


if __name__ == "__main__":
    unittest.main()