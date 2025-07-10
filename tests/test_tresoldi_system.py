"""
Comprehensive tests for the Tresoldi distinctive feature system.

This test suite validates the loading, functionality, and integration
of Tresoldi's 43-feature system with 1,081 sounds.
"""

import unittest
import sys
import os

# Add the parent directory to the path to import alteruphono
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alteruphono.phonology.feature_systems import (
    get_feature_system,
    list_feature_systems,
    TresoldiDistinctiveSystem,
    FeatureBundle,
    FeatureValue,
    FeatureValueType
)
from alteruphono.phonology.sound_v2 import Sound


class TestTresoldiSystemLoading(unittest.TestCase):
    """Test loading and basic functionality of Tresoldi system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tresoldi = get_feature_system('tresoldi_distinctive')
        self.assertIsNotNone(self.tresoldi, "Tresoldi system should load successfully")
    
    def test_system_registration(self):
        """Test that Tresoldi system is properly registered."""
        systems = list_feature_systems()
        self.assertIn('tresoldi_distinctive', systems)
        self.assertEqual(len(systems), 3)  # IPA, Unified, Tresoldi
    
    def test_system_properties(self):
        """Test basic system properties."""
        self.assertEqual(self.tresoldi.name, 'tresoldi_distinctive')
        self.assertIn('43 features', self.tresoldi.description)
        self.assertIn('1,081 sounds', self.tresoldi.description)
        self.assertEqual(self.tresoldi.supported_value_types, {FeatureValueType.SCALAR})
    
    def test_feature_inventory(self):
        """Test feature inventory."""
        features = self.tresoldi.get_feature_names()
        self.assertEqual(len(features), 43)
        
        # Check for key features
        expected_features = [
            'anterior', 'approximant', 'atr', 'back', 'breathy',
            'consonantal', 'continuant', 'voice', 'high', 'low',
            'nasal', 'sonorant', 'syllabic', 'length', 'tone_level'
        ]
        
        for feature in expected_features:
            self.assertIn(feature, features, f"Feature '{feature}' should be present")
    
    def test_sound_inventory(self):
        """Test sound inventory."""
        self.assertEqual(self.tresoldi.get_sound_count(), 1081)
        
        # Test some basic sounds exist
        basic_sounds = ['a', 'e', 'i', 'o', 'u', 'p', 'b', 't', 'd', 'k', 'g']
        for sound in basic_sounds:
            self.assertTrue(self.tresoldi.has_grapheme(sound), 
                          f"Basic sound '{sound}' should be present")
    
    def test_complex_sounds(self):
        """Test that complex sounds are included."""
        complex_sounds = ['bd', 'ⁿk', 'kʷ', 'ǃ', 'ǃǃ']
        
        for sound in complex_sounds:
            if self.tresoldi.has_grapheme(sound):
                features = self.tresoldi.grapheme_to_features(sound)
                self.assertIsNotNone(features, f"Complex sound '{sound}' should have features")


class TestTresoldiFeatureValues(unittest.TestCase):
    """Test feature value handling and scaling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tresoldi = get_feature_system('tresoldi_distinctive')
    
    def test_value_range(self):
        """Test that all feature values are in [-1.0, 1.0] range."""
        all_graphemes = self.tresoldi.get_all_graphemes()
        
        # Test a sample of sounds (testing all 1081 would be slow)
        test_graphemes = all_graphemes[::50]  # Every 50th sound
        
        for grapheme in test_graphemes:
            features = self.tresoldi.grapheme_to_features(grapheme)
            self.assertIsNotNone(features)
            
            for fval in features.features:
                self.assertGreaterEqual(fval.value, -1.0, 
                                      f"Feature {fval.feature} in '{grapheme}' below -1.0: {fval.value}")
                self.assertLessEqual(fval.value, 1.0,
                                   f"Feature {fval.feature} in '{grapheme}' above 1.0: {fval.value}")
    
    def test_length_scaling(self):
        """Test that length feature is properly scaled."""
        # Find sounds with different length values
        sounds_with_length = []
        for grapheme in ['a', 'aː', 'aːː', 'aˑ', 'ă']:
            if self.tresoldi.has_grapheme(grapheme):
                features = self.tresoldi.grapheme_to_features(grapheme)
                if features:
                    length_feature = features.get_feature('length')
                    if length_feature:
                        sounds_with_length.append((grapheme, length_feature.value))
        
        # Should have different length values
        length_values = [val for _, val in sounds_with_length]
        self.assertGreater(len(set(length_values)), 1, "Should have different length values")
        
        # All should be in valid range
        for _, val in sounds_with_length:
            self.assertGreaterEqual(val, -1.0)
            self.assertLessEqual(val, 1.0)
    
    def test_binary_interpretation(self):
        """Test binary opposition logic."""
        # Test vowel vs consonant
        a_features = self.tresoldi.grapheme_to_features('a')
        p_features = self.tresoldi.grapheme_to_features('p')
        
        self.assertIsNotNone(a_features)
        self.assertIsNotNone(p_features)
        
        # /a/ should be +syllabic, -consonantal
        self.assertTrue(self.tresoldi.is_positive(a_features, 'syllabic'))
        self.assertTrue(self.tresoldi.is_negative(a_features, 'consonantal'))
        
        # /p/ should be -syllabic, +consonantal
        self.assertTrue(self.tresoldi.is_negative(p_features, 'syllabic'))
        self.assertTrue(self.tresoldi.is_positive(p_features, 'consonantal'))


class TestTresoldiSoundOperations(unittest.TestCase):
    """Test sound operations with Tresoldi system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tresoldi = get_feature_system('tresoldi_distinctive')
    
    def test_sound_creation(self):
        """Test creating sounds with Tresoldi system."""
        sound_a = Sound(grapheme='a', feature_system='tresoldi_distinctive')
        self.assertEqual(sound_a.feature_system_name, 'tresoldi_distinctive')
        self.assertEqual(sound_a.grapheme(), 'a')
        
        # Should have all 43 features
        self.assertEqual(len(sound_a.features.features), 43)
    
    def test_feature_access(self):
        """Test accessing features through Sound interface."""
        sound_p = Sound(grapheme='p', feature_system='tresoldi_distinctive')
        
        # Test feature existence
        self.assertTrue(sound_p.has_feature('consonantal'))
        self.assertTrue(sound_p.has_feature('voice'))
        self.assertTrue(sound_p.has_feature('labial'))
        
        # Test feature values
        consonantal_val = sound_p.get_feature_value('consonantal')
        self.assertGreater(consonantal_val, 0.0, "/p/ should be +consonantal")
        
        voice_val = sound_p.get_feature_value('voice')
        self.assertLess(voice_val, 0.0, "/p/ should be -voice")
    
    def test_sound_distance(self):
        """Test distance calculations between sounds."""
        sound_p = Sound(grapheme='p', feature_system='tresoldi_distinctive')
        sound_b = Sound(grapheme='b', feature_system='tresoldi_distinctive')
        sound_a = Sound(grapheme='a', feature_system='tresoldi_distinctive')
        
        # /p/ and /b/ should be closer than /p/ and /a/
        dist_pb = sound_p.distance_to(sound_b)
        dist_pa = sound_p.distance_to(sound_a)
        
        self.assertLess(dist_pb, dist_pa, "/p/ should be closer to /b/ than to /a/")
        
        # Distance should be symmetric
        dist_bp = sound_b.distance_to(sound_p)
        self.assertAlmostEqual(dist_pb, dist_bp, places=5)
    
    def test_feature_arithmetic(self):
        """Test feature modification operations."""
        sound_p = Sound(grapheme='p', feature_system='tresoldi_distinctive')
        
        # Add voicing
        voiced_p = sound_p + 'voice=1.0'
        
        voice_val = voiced_p.get_feature_value('voice')
        self.assertGreater(voice_val, 0.0, "After adding voice=1.0, should be positive")
        
        # Should be closer to /b/ now
        sound_b = Sound(grapheme='b', feature_system='tresoldi_distinctive')
        dist_original = sound_p.distance_to(sound_b)
        dist_voiced = voiced_p.distance_to(sound_b)
        
        self.assertLess(dist_voiced, dist_original, "Voiced /p/ should be closer to /b/")


class TestTresoldiFeatureSpecification(unittest.TestCase):
    """Test feature specification parsing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tresoldi = get_feature_system('tresoldi_distinctive')
    
    def test_explicit_values(self):
        """Test parsing explicit feature values."""
        spec = "[voice=0.5, consonantal=1.0, high=-0.3]"
        features = self.tresoldi.parse_feature_specification(spec)
        
        voice_val = features.get_feature('voice')
        self.assertIsNotNone(voice_val)
        self.assertAlmostEqual(voice_val.value, 0.5)
        
        consonantal_val = features.get_feature('consonantal')
        self.assertIsNotNone(consonantal_val)
        self.assertAlmostEqual(consonantal_val.value, 1.0)
    
    def test_binary_notation(self):
        """Test parsing +/- notation."""
        spec = "[+voice, -nasal, +consonantal]"
        features = self.tresoldi.parse_feature_specification(spec)
        
        voice_val = features.get_feature('voice')
        self.assertEqual(voice_val.value, 1.0)
        
        nasal_val = features.get_feature('nasal')
        self.assertEqual(nasal_val.value, -1.0)
        
        consonantal_val = features.get_feature('consonantal')
        self.assertEqual(consonantal_val.value, 1.0)
    
    def test_length_scaling_in_specification(self):
        """Test that length values are scaled in specifications."""
        spec = "[length=2.0]"  # Should be scaled to 1.0
        features = self.tresoldi.parse_feature_specification(spec)
        
        length_val = features.get_feature('length')
        self.assertIsNotNone(length_val)
        self.assertEqual(length_val.value, 1.0)  # Scaled from 2.0


class TestTresoldiSoundClasses(unittest.TestCase):
    """Test sound class functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tresoldi = get_feature_system('tresoldi_distinctive')
    
    def test_vowel_class(self):
        """Test vowel sound class."""
        vowel_features = self.tresoldi.get_sound_class_features('V')
        self.assertIsNotNone(vowel_features)
        
        # Should be +syllabic, -consonantal, +sonorant
        syllabic_val = vowel_features.get_feature('syllabic')
        self.assertEqual(syllabic_val.value, 1.0)
        
        consonantal_val = vowel_features.get_feature('consonantal')
        self.assertEqual(consonantal_val.value, -1.0)
        
        sonorant_val = vowel_features.get_feature('sonorant')
        self.assertEqual(sonorant_val.value, 1.0)
    
    def test_consonant_class(self):
        """Test consonant sound class."""
        consonant_features = self.tresoldi.get_sound_class_features('C')
        self.assertIsNotNone(consonant_features)
        
        # Should be +consonantal, -syllabic
        consonantal_val = consonant_features.get_feature('consonantal')
        self.assertEqual(consonantal_val.value, 1.0)
        
        syllabic_val = consonant_features.get_feature('syllabic')
        self.assertEqual(syllabic_val.value, -1.0)
    
    def test_nasal_class(self):
        """Test nasal sound class."""
        nasal_features = self.tresoldi.get_sound_class_features('N')
        self.assertIsNotNone(nasal_features)
        
        # Should be +nasal, +sonorant, +consonantal
        nasal_val = nasal_features.get_feature('nasal')
        self.assertEqual(nasal_val.value, 1.0)
        
        sonorant_val = nasal_features.get_feature('sonorant')
        self.assertEqual(sonorant_val.value, 1.0)
        
        consonantal_val = nasal_features.get_feature('consonantal')
        self.assertEqual(consonantal_val.value, 1.0)


class TestTresoldiStatistics(unittest.TestCase):
    """Test statistical functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tresoldi = get_feature_system('tresoldi_distinctive')
    
    def test_feature_statistics(self):
        """Test feature usage statistics."""
        stats = self.tresoldi.get_feature_statistics()
        
        self.assertEqual(len(stats), 43)  # All features should have stats
        
        # Check syllabic feature distribution
        syllabic_stats = stats['syllabic']
        self.assertIn('positive', syllabic_stats)
        self.assertIn('negative', syllabic_stats)
        self.assertIn('neutral', syllabic_stats)
        self.assertEqual(syllabic_stats['total_sounds'], 1081)
        
        # Should have some vowels (positive syllabic)
        self.assertGreater(syllabic_stats['positive'], 0)
        
        # Should have some consonants (negative syllabic)
        self.assertGreater(syllabic_stats['negative'], 0)
    
    def test_sounds_with_feature(self):
        """Test finding sounds with specific features."""
        # Find voiced sounds
        voiced_sounds = self.tresoldi.get_sounds_with_feature('voice', positive=True)
        self.assertGreater(len(voiced_sounds), 0, "Should have some voiced sounds")
        
        # Find voiceless sounds
        voiceless_sounds = self.tresoldi.get_sounds_with_feature('voice', positive=False)
        self.assertGreater(len(voiceless_sounds), 0, "Should have some voiceless sounds")
        
        # Should have 'b' in voiced and 'p' in voiceless (if present)
        if 'b' in self.tresoldi.get_all_graphemes():
            self.assertIn('b', voiced_sounds)
        if 'p' in self.tresoldi.get_all_graphemes():
            self.assertIn('p', voiceless_sounds)


class TestTresoldiValidation(unittest.TestCase):
    """Test validation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tresoldi = get_feature_system('tresoldi_distinctive')
    
    def test_valid_features(self):
        """Test validation of valid features."""
        # Create valid feature bundle
        features = FeatureBundle(frozenset([
            FeatureValue('voice', 0.5, FeatureValueType.SCALAR),
            FeatureValue('consonantal', 1.0, FeatureValueType.SCALAR),
            FeatureValue('high', -0.3, FeatureValueType.SCALAR)
        ]))
        
        errors = self.tresoldi.validate_features(features)
        self.assertEqual(len(errors), 0, "Valid features should have no errors")
    
    def test_invalid_feature_names(self):
        """Test validation of invalid feature names."""
        features = FeatureBundle(frozenset([
            FeatureValue('nonexistent_feature', 1.0, FeatureValueType.SCALAR)
        ]))
        
        errors = self.tresoldi.validate_features(features)
        self.assertGreater(len(errors), 0, "Unknown feature should cause validation error")
        self.assertIn('Unknown feature', errors[0])
    
    def test_invalid_value_range(self):
        """Test validation of out-of-range values."""
        features = FeatureBundle(frozenset([
            FeatureValue('voice', 2.0, FeatureValueType.SCALAR)  # Out of range
        ]))
        
        errors = self.tresoldi.validate_features(features)
        self.assertGreater(len(errors), 0, "Out-of-range value should cause validation error")
        self.assertIn('outside [-1.0, 1.0] range', errors[0])


if __name__ == '__main__':
    # Run specific test groups
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', choices=['loading', 'values', 'operations', 'specification', 
                                          'classes', 'statistics', 'validation', 'all'],
                       default='all', help='Which test group to run')
    args = parser.parse_args()
    
    if args.test == 'all':
        unittest.main(argv=[''])
    else:
        suite = unittest.TestSuite()
        
        if args.test == 'loading':
            suite.addTest(unittest.makeSuite(TestTresoldiSystemLoading))
        elif args.test == 'values':
            suite.addTest(unittest.makeSuite(TestTresoldiFeatureValues))
        elif args.test == 'operations':
            suite.addTest(unittest.makeSuite(TestTresoldiSoundOperations))
        elif args.test == 'specification':
            suite.addTest(unittest.makeSuite(TestTresoldiFeatureSpecification))
        elif args.test == 'classes':
            suite.addTest(unittest.makeSuite(TestTresoldiSoundClasses))
        elif args.test == 'statistics':
            suite.addTest(unittest.makeSuite(TestTresoldiStatistics))
        elif args.test == 'validation':
            suite.addTest(unittest.makeSuite(TestTresoldiValidation))
        
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)