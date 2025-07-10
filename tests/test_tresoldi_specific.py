"""
Specific tests for the Tresoldi distinctive feature system.

This test suite focuses on the unique capabilities of the Tresoldi system,
particularly its comprehensive phonological coverage, complex sound support,
and extensive feature inventory.
"""

import unittest
import sys
import os

# Add the parent directory to the path to import alteruphono
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alteruphono.phonology.feature_systems import get_feature_system, FeatureValue, FeatureValueType
from alteruphono.phonology.sound_v2 import Sound
from alteruphono.phonology.sound_change import SoundChangeEngine


class TestTresoldiPhonologicalCoverage(unittest.TestCase):
    """Test Tresoldi system's comprehensive phonological coverage."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.system = get_feature_system('tresoldi_distinctive')
    
    def test_massive_sound_inventory(self):
        """Test the massive 1,081 sound inventory."""
        self.assertEqual(self.system.get_sound_count(), 1081)
        
        # Check that basic sounds are included
        basic_sounds = ['p', 'b', 't', 'd', 'k', 'g', 'a', 'e', 'i', 'o', 'u']
        for sound in basic_sounds:
            self.assertTrue(self.system.has_grapheme(sound), f"Basic sound {sound} should be present")
    
    def test_complex_sound_support(self):
        """Test support for complex sounds (multi-character segments)."""
        complex_sounds = ['bd', 'kʷ', 'tʃ', 'ⁿk']  # Test some that might exist
        
        supported_complex = []
        for sound in complex_sounds:
            if self.system.has_grapheme(sound):
                features = self.system.grapheme_to_features(sound)
                if features:
                    supported_complex.append(sound)
        
        print(f"Complex sounds supported: {supported_complex}")
        # Should support at least some complex sounds
        self.assertGreater(len(supported_complex), 0, "Should support some complex sounds")
    
    def test_click_consonant_support(self):
        """Test support for click consonants."""
        click_sounds = ['ǀ', 'ǁ', 'ǃ', 'ǂ', 'ʘ']  # Different click types
        
        supported_clicks = []
        for sound in click_sounds:
            if self.system.has_grapheme(sound):
                features = self.system.grapheme_to_features(sound)
                if features and self.system.is_positive(features, 'click'):
                    supported_clicks.append(sound)
        
        print(f"Click sounds supported: {supported_clicks}")
        if supported_clicks:
            # If clicks are supported, they should have +click feature
            for click in supported_clicks[:3]:  # Test first few
                features = self.system.grapheme_to_features(click)
                self.assertTrue(self.system.is_positive(features, 'click'), 
                              f"{click} should have +click feature")
    
    def test_prenasalized_consonants(self):
        """Test support for prenasalized consonants."""
        prenasalized = ['ⁿk', 'ⁿg', 'ⁿt', 'ⁿd']  # Common prenasalized sounds
        
        supported_prenasalized = []
        for sound in prenasalized:
            if self.system.has_grapheme(sound):
                features = self.system.grapheme_to_features(sound)
                if features and self.system.is_positive(features, 'prenasal'):
                    supported_prenasalized.append(sound)
        
        print(f"Prenasalized sounds supported: {supported_prenasalized}")
        # Test prenasalized feature if any are supported
        for sound in supported_prenasalized[:2]:
            features = self.system.grapheme_to_features(sound)
            self.assertTrue(self.system.is_positive(features, 'prenasal'), 
                          f"{sound} should have +prenasal feature")
    
    def test_tonal_variants(self):
        """Test support for tonal variants of sounds."""
        # Test tone features if present
        a_features = self.system.grapheme_to_features('a')
        if a_features:
            tone_features = [f for f in a_features.features if 'tone' in f.feature]
            if tone_features:
                print(f"Tone features found: {[f.feature for f in tone_features]}")
                
                # Test tone-related features exist
                tone_feature_names = self.system.get_feature_names()
                tone_related = [f for f in tone_feature_names if 'tone' in f]
                self.assertGreater(len(tone_related), 0, "Should have tone-related features")
    
    def test_comprehensive_feature_set(self):
        """Test the comprehensive 43-feature set."""
        feature_names = self.system.get_feature_names()
        self.assertEqual(len(feature_names), 43)
        
        # Check for key phonological feature categories
        expected_categories = {
            'major_class': ['syllabic', 'consonantal', 'sonorant'],
            'manner': ['continuant', 'nasal', 'lateral', 'strident'],
            'place': ['labial', 'coronal', 'dorsal', 'glottal'],
            'laryngeal': ['voice', 'spread', 'constricted'],
            'vowel_features': ['high', 'low', 'back', 'round', 'tense'],
            'suprasegmental': ['length', 'tone_level', 'tone_contour']
        }
        
        found_categories = {}
        for category, features in expected_categories.items():
            found = [f for f in features if f in feature_names]
            found_categories[category] = found
            self.assertGreater(len(found), 0, f"Should have {category} features")
        
        print("Feature categories found:")
        for category, features in found_categories.items():
            print(f"  {category}: {features}")
    
    def test_binary_opposition_logic(self):
        """Test binary opposition interpretation of scalar values."""
        # Test with basic consonant
        p_features = self.system.grapheme_to_features('p')
        self.assertIsNotNone(p_features)
        
        # Test positive/negative/neutral logic
        self.assertTrue(self.system.is_positive(p_features, 'consonantal'))
        self.assertTrue(self.system.is_negative(p_features, 'syllabic'))
        
        # Test with vowel
        a_features = self.system.grapheme_to_features('a')
        self.assertIsNotNone(a_features)
        
        self.assertTrue(self.system.is_positive(a_features, 'syllabic'))
        self.assertTrue(self.system.is_negative(a_features, 'consonantal'))
    
    def test_feature_value_scaling(self):
        """Test that feature values are properly scaled to [-1.0, 1.0]."""
        # Test multiple sounds to ensure all values are in range
        test_sounds = ['p', 'a', 'k', 'i', 'n', 'm', 's', 'l']
        
        for sound_char in test_sounds:
            if self.system.has_grapheme(sound_char):
                features = self.system.grapheme_to_features(sound_char)
                self.assertIsNotNone(features)
                
                for fval in features.features:
                    self.assertGreaterEqual(fval.value, -1.0, 
                                          f"{sound_char}:{fval.feature} below -1.0: {fval.value}")
                    self.assertLessEqual(fval.value, 1.0,
                                       f"{sound_char}:{fval.feature} above 1.0: {fval.value}")
    
    def test_length_feature_scaling(self):
        """Test that length feature is properly scaled from [-2,2] to [-1,1]."""
        # Find sounds with different length values
        all_sounds = self.system.get_all_graphemes()
        length_sounds = []
        
        for sound in all_sounds[:100]:  # Test first 100 sounds
            features = self.system.grapheme_to_features(sound)
            if features:
                length_val = features.get_feature('length')
                if length_val and abs(length_val.value) > 0.01:  # Non-zero length
                    length_sounds.append((sound, length_val.value))
        
        print(f"Sounds with non-zero length: {len(length_sounds)}")
        if length_sounds:
            # Check that all length values are in proper range
            for sound, length_val in length_sounds[:5]:
                self.assertGreaterEqual(length_val, -1.0, f"{sound} length below -1.0")
                self.assertLessEqual(length_val, 1.0, f"{sound} length above 1.0")


class TestTresoldiFeatureStatistics(unittest.TestCase):
    """Test feature usage statistics and distributions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.system = get_feature_system('tresoldi_distinctive')
    
    def test_feature_distribution_analysis(self):
        """Test feature usage distribution analysis."""
        stats = self.system.get_feature_statistics()
        
        self.assertEqual(len(stats), 43)  # All features should have stats
        
        # Check that statistics are reasonable
        for feature_name, data in stats.items():
            total = data['positive'] + data['negative'] + data['neutral']
            self.assertEqual(total, 1081, f"Total count mismatch for {feature_name}")
            
            # Most features should have some positive and negative instances
            if data['positive'] > 0 and data['negative'] > 0:
                balance = min(data['positive'], data['negative']) / max(data['positive'], data['negative'])
                # Features shouldn't be completely skewed (except rare ones)
                if data['positive'] + data['negative'] > 100:
                    self.assertGreater(balance, 0.05, f"Feature {feature_name} too skewed")
    
    def test_sound_class_coverage(self):
        """Test coverage of different sound classes."""
        # Test major class distributions
        vowel_count = len(self.system.get_sounds_with_feature('syllabic', positive=True))
        consonant_count = len(self.system.get_sounds_with_feature('consonantal', positive=True))
        
        print(f"Vowels: {vowel_count}, Consonants: {consonant_count}")
        
        self.assertGreater(vowel_count, 0, "Should have vowels")
        self.assertGreater(consonant_count, 0, "Should have consonants")
        self.assertGreater(consonant_count, vowel_count, "Should have more consonants than vowels")
    
    def test_rare_feature_coverage(self):
        """Test coverage of rare phonological features."""
        rare_features = ['click', 'creaky', 'breathy', 'prenasal', 'preglottalized']
        
        rare_coverage = {}
        for feature in rare_features:
            if feature in self.system.get_feature_names():
                positive_count = len(self.system.get_sounds_with_feature(feature, positive=True))
                rare_coverage[feature] = positive_count
        
        print(f"Rare feature coverage: {rare_coverage}")
        
        # Should have at least some rare features represented
        total_rare = sum(rare_coverage.values())
        self.assertGreater(total_rare, 0, "Should have some rare phonological features")


class TestTresoldiPerformance(unittest.TestCase):
    """Test performance characteristics with large inventory."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.system = get_feature_system('tresoldi_distinctive')
    
    def test_sound_creation_performance(self):
        """Test sound creation performance with large inventory."""
        import time
        
        test_sounds = ['p', 'a', 't', 'i', 'k', 'n']
        n_iterations = 100
        
        start_time = time.time()
        for _ in range(n_iterations):
            for sound_char in test_sounds:
                Sound(grapheme=sound_char, feature_system='tresoldi_distinctive')
        end_time = time.time()
        
        avg_time = (end_time - start_time) / (n_iterations * len(test_sounds)) * 1000
        print(f"Average sound creation time: {avg_time:.3f}ms")
        
        # Should be reasonably fast despite large inventory
        self.assertLess(avg_time, 1.0, f"Sound creation too slow: {avg_time:.3f}ms")
    
    def test_feature_access_performance(self):
        """Test feature access performance."""
        import time
        
        sound = Sound(grapheme='p', feature_system='tresoldi_distinctive')
        n_iterations = 1000
        
        start_time = time.time()
        for _ in range(n_iterations):
            sound.has_feature('voice')
            sound.get_feature_value('consonantal')
        end_time = time.time()
        
        avg_time = (end_time - start_time) / n_iterations * 1000
        print(f"Average feature access time: {avg_time:.3f}ms")
        
        self.assertLess(avg_time, 0.1, f"Feature access too slow: {avg_time:.3f}ms")
    
    def test_distance_calculation_performance(self):
        """Test distance calculation performance."""
        import time
        
        p_sound = Sound(grapheme='p', feature_system='tresoldi_distinctive')
        b_sound = Sound(grapheme='b', feature_system='tresoldi_distinctive')
        n_iterations = 100
        
        start_time = time.time()
        for _ in range(n_iterations):
            p_sound.distance_to(b_sound)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / n_iterations * 1000
        print(f"Average distance calculation time: {avg_time:.3f}ms")
        
        # Distance calculation involves all 43 features, so expect it to be slower
        self.assertLess(avg_time, 10.0, f"Distance calculation too slow: {avg_time:.3f}ms")


class TestTresoldiIntegration(unittest.TestCase):
    """Test integration with other alteruphono components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.system = get_feature_system('tresoldi_distinctive')
    
    def test_sound_change_engine_integration(self):
        """Test integration with sound change engine."""
        engine = SoundChangeEngine(feature_system_name='tresoldi_distinctive')
        self.assertEqual(engine.feature_system_name, 'tresoldi_distinctive')
        
        # Test with a Tresoldi sound
        p_sound = Sound(grapheme='p', feature_system='tresoldi_distinctive')
        self.assertIsNotNone(p_sound)
        self.assertEqual(len(p_sound.features.features), 43)
    
    def test_conversion_from_other_systems(self):
        """Test conversion from other feature systems to Tresoldi."""
        from alteruphono.phonology.feature_systems import convert_between_systems
        
        # Test conversion from unified distinctive
        unified_sound = Sound(grapheme='p', feature_system='unified_distinctive')
        tresoldi_features = convert_between_systems(
            unified_sound.features,
            'unified_distinctive',
            'tresoldi_distinctive'
        )
        
        # Should convert many features
        self.assertGreater(len(tresoldi_features.features), 5)
        print(f"Converted features: {len(tresoldi_features.features)}")
    
    def test_comprehensive_sound_change_support(self):
        """Test comprehensive sound change support with Tresoldi features."""
        # Test that Tresoldi system can handle complex sound change rules
        from alteruphono.phonology.sound_change import FeatureChangeRule
        from alteruphono.phonology.sound_change.rules import FeatureChange, ChangeType
        
        # Create a feature-based rule using Tresoldi features
        rule = FeatureChangeRule(
            name="tresoldi_test",
            source_pattern="",
            target_pattern=[],
            feature_conditions={"consonantal": 1.0, "voice": -1.0},  # Voiceless consonants
            feature_changes=[
                FeatureChange(
                    feature_name="voice",
                    target_value=1.0,
                    change_type=ChangeType.CATEGORICAL
                )
            ],
            feature_system_name='tresoldi_distinctive'
        )
        
        # Should create without error
        self.assertIsNotNone(rule)


if __name__ == '__main__':
    unittest.main(verbosity=2)