"""
Tests for the pluggable feature system architecture.

This module tests the new feature system architecture including:
- Feature system registry
- IPA categorical system 
- Unified distinctive system
- Sound class with multiple systems
- Feature system conversion
"""

import unittest
from alteruphono.phonology.feature_systems import (
    FeatureSystem,
    FeatureValue,
    FeatureBundle,
    FeatureValueType,
    IPACategoricalSystem,
    UnifiedDistinctiveSystem,
    get_feature_system,
    register_feature_system,
    list_feature_systems,
    get_default_feature_system,
    set_default_feature_system
)
from alteruphono.phonology.feature_systems.conversion import (
    convert_sound_between_systems,
    feature_system_context,
    get_conversion_recommendations
)
from alteruphono.phonology.sound_v2 import Sound


class TestFeatureSystemArchitecture(unittest.TestCase):
    """Test the basic feature system architecture."""
    
    def test_feature_value_creation(self):
        """Test FeatureValue creation and validation."""
        # Binary feature
        binary_fval = FeatureValue('voiced', True, FeatureValueType.BINARY)
        self.assertEqual(binary_fval.feature, 'voiced')
        self.assertEqual(binary_fval.value, True)
        self.assertEqual(binary_fval.value_type, FeatureValueType.BINARY)
        
        # Categorical feature  
        cat_fval = FeatureValue('bilabial', True, FeatureValueType.CATEGORICAL)
        self.assertEqual(cat_fval.feature, 'bilabial')
        self.assertEqual(cat_fval.value, True)
        
        # Scalar feature
        scalar_fval = FeatureValue('voice', 0.8, FeatureValueType.SCALAR)
        self.assertEqual(scalar_fval.feature, 'voice')
        self.assertEqual(scalar_fval.value, 0.8)
        
        # Test validation
        with self.assertRaises(ValueError):
            FeatureValue('voiced', 'invalid', FeatureValueType.BINARY)
    
    def test_feature_value_compatibility(self):
        """Test feature value compatibility checking."""
        fval1 = FeatureValue('voiced', True, FeatureValueType.BINARY)
        fval2 = FeatureValue('voiced', True, FeatureValueType.BINARY)
        fval3 = FeatureValue('voiced', False, FeatureValueType.BINARY)
        fval4 = FeatureValue('bilabial', True, FeatureValueType.CATEGORICAL)
        
        self.assertTrue(fval1.is_compatible_with(fval2))
        self.assertFalse(fval1.is_compatible_with(fval3))
        self.assertTrue(fval1.is_compatible_with(fval4))  # Different features
    
    def test_feature_value_distance(self):
        """Test distance calculations between feature values."""
        # Binary features
        fval1 = FeatureValue('voiced', True, FeatureValueType.BINARY)
        fval2 = FeatureValue('voiced', True, FeatureValueType.BINARY)
        fval3 = FeatureValue('voiced', False, FeatureValueType.BINARY)
        
        self.assertEqual(fval1.distance_to(fval2), 0.0)
        self.assertEqual(fval1.distance_to(fval3), 1.0)
        
        # Scalar features
        fval4 = FeatureValue('voice', 0.8, FeatureValueType.SCALAR)
        fval5 = FeatureValue('voice', 0.4, FeatureValueType.SCALAR)
        
        self.assertEqual(fval4.distance_to(fval5), 0.2)  # |0.8 - 0.4| / 2
    
    def test_feature_bundle_creation(self):
        """Test FeatureBundle creation and validation."""
        fval1 = FeatureValue('voiced', True, FeatureValueType.BINARY)
        fval2 = FeatureValue('bilabial', True, FeatureValueType.CATEGORICAL)
        
        bundle = FeatureBundle(frozenset([fval1, fval2]))
        self.assertEqual(len(bundle.features), 2)
        self.assertFalse(bundle.partial)
        
        # Test conflicting features
        fval3 = FeatureValue('voiced', False, FeatureValueType.BINARY)
        with self.assertRaises(ValueError):
            FeatureBundle(frozenset([fval1, fval3]))
    
    def test_feature_bundle_operations(self):
        """Test FeatureBundle operations."""
        fval1 = FeatureValue('voiced', True, FeatureValueType.BINARY)
        fval2 = FeatureValue('bilabial', True, FeatureValueType.CATEGORICAL)
        
        bundle = FeatureBundle(frozenset([fval1, fval2]))
        
        # Test get_feature
        self.assertEqual(bundle.get_feature('voiced'), fval1)
        self.assertIsNone(bundle.get_feature('nonexistent'))
        
        # Test has_feature
        self.assertTrue(bundle.has_feature('voiced'))
        self.assertFalse(bundle.has_feature('nonexistent'))
        
        # Test add_feature
        fval3 = FeatureValue('stop', True, FeatureValueType.CATEGORICAL)
        new_bundle = bundle.add_feature(fval3)
        self.assertEqual(len(new_bundle.features), 3)
        self.assertTrue(new_bundle.has_feature('stop'))
        
        # Test remove_feature
        reduced_bundle = bundle.remove_feature('voiced')
        self.assertEqual(len(reduced_bundle.features), 1)
        self.assertFalse(reduced_bundle.has_feature('voiced'))


class TestIPACategoricalSystem(unittest.TestCase):
    """Test the IPA categorical feature system."""
    
    def setUp(self):
        self.system = IPACategoricalSystem()
    
    def test_system_properties(self):
        """Test basic system properties."""
        self.assertEqual(self.system.name, "ipa_categorical")
        self.assertIn("IPA", self.system.description)
        self.assertIn(FeatureValueType.CATEGORICAL, self.system.supported_value_types)
        self.assertIn(FeatureValueType.BINARY, self.system.supported_value_types)
    
    def test_grapheme_to_features(self):
        """Test grapheme to feature conversion."""
        # Test consonant
        p_features = self.system.grapheme_to_features('p')
        self.assertIsNotNone(p_features)
        self.assertTrue(p_features.has_feature('consonant'))
        self.assertTrue(p_features.has_feature('bilabial'))
        self.assertTrue(p_features.has_feature('stop'))
        self.assertTrue(p_features.has_feature('voiceless'))
        
        # Test vowel
        a_features = self.system.grapheme_to_features('a')
        self.assertIsNotNone(a_features)
        self.assertTrue(a_features.has_feature('vowel'))
        self.assertTrue(a_features.has_feature('low'))
        self.assertTrue(a_features.has_feature('central'))
        
        # Test sound class
        v_features = self.system.grapheme_to_features('V')
        self.assertIsNotNone(v_features)
        self.assertTrue(v_features.partial)
        self.assertTrue(v_features.has_feature('vowel'))
        
        # Test unknown grapheme
        unknown_features = self.system.grapheme_to_features('xyz')
        self.assertIsNone(unknown_features)
    
    def test_features_to_grapheme(self):
        """Test feature to grapheme conversion."""
        # Create features for 'p'
        p_features = self.system.grapheme_to_features('p')
        grapheme = self.system.features_to_grapheme(p_features)
        self.assertEqual(grapheme, 'p')
        
        # Test partial match
        fval = FeatureValue('voiced', True, FeatureValueType.CATEGORICAL)
        partial_bundle = FeatureBundle(frozenset([fval]))
        grapheme = self.system.features_to_grapheme(partial_bundle)
        self.assertIn(grapheme, ['b', 'd', 'g', 'z', 'v'])  # Should be voiced sound
    
    def test_feature_parsing(self):
        """Test feature specification parsing."""
        # Test simple features
        bundle = self.system.parse_feature_specification('[voiced,bilabial]')
        self.assertTrue(bundle.has_feature('voiced'))
        self.assertTrue(bundle.has_feature('bilabial'))
        
        # Test binary features
        bundle = self.system.parse_feature_specification('[+voiced,-long]')
        voiced_fval = bundle.get_feature('voiced')
        self.assertIsNotNone(voiced_fval)
        self.assertTrue(voiced_fval.value)
        
        # Test empty specification
        bundle = self.system.parse_feature_specification('[]')
        self.assertEqual(len(bundle.features), 0)
    
    def test_feature_addition(self):
        """Test feature addition logic."""
        # Start with 'p'
        p_features = self.system.grapheme_to_features('p')
        
        # Add voicing
        voiced_fval = FeatureValue('voiced', True, FeatureValueType.CATEGORICAL)
        voiced_bundle = FeatureBundle(frozenset([voiced_fval]))
        
        result = self.system.add_features(p_features, voiced_bundle)
        
        # Should have voiced, not voiceless
        self.assertTrue(result.has_feature('voiced'))
        self.assertFalse(result.has_feature('voiceless'))
        
        # Other features should remain
        self.assertTrue(result.has_feature('bilabial'))
        self.assertTrue(result.has_feature('stop'))
    
    def test_feature_validation(self):
        """Test feature validation."""
        # Valid features
        valid_features = self.system.grapheme_to_features('p')
        errors = self.system.validate_features(valid_features)
        self.assertEqual(len(errors), 0)
        
        # Contradictory voicing
        fval1 = FeatureValue('voiced', True, FeatureValueType.CATEGORICAL)
        fval2 = FeatureValue('voiceless', True, FeatureValueType.CATEGORICAL)
        # This should be caught at FeatureBundle level, not system level
        try:
            invalid_bundle = FeatureBundle(frozenset([fval1, fval2]))
            self.fail("Should have raised ValueError for contradictory features")
        except ValueError:
            pass  # Expected


class TestUnifiedDistinctiveSystem(unittest.TestCase):
    """Test the unified distinctive feature system."""
    
    def setUp(self):
        self.system = UnifiedDistinctiveSystem()
    
    def test_system_properties(self):
        """Test basic system properties."""
        self.assertEqual(self.system.name, "unified_distinctive")
        self.assertIn("unified", self.system.description.lower())
        self.assertIn(FeatureValueType.SCALAR, self.system.supported_value_types)
    
    def test_grapheme_to_features(self):
        """Test grapheme to feature conversion."""
        # Test stop consonant
        p_features = self.system.grapheme_to_features('p')
        self.assertIsNotNone(p_features)
        
        # Should have negative sonorant, positive consonantal
        sonorant_val = p_features.get_feature('sonorant')
        self.assertIsNotNone(sonorant_val)
        self.assertLess(sonorant_val.value, 0)
        
        consonantal_val = p_features.get_feature('consonantal')
        self.assertIsNotNone(consonantal_val)
        self.assertGreater(consonantal_val.value, 0)
        
        # Test vowel
        a_features = self.system.grapheme_to_features('a')
        self.assertIsNotNone(a_features)
        
        # Should have positive sonorant, negative consonantal
        sonorant_val = a_features.get_feature('sonorant')
        self.assertIsNotNone(sonorant_val)
        self.assertGreater(sonorant_val.value, 0)
        
        consonantal_val = a_features.get_feature('consonantal')
        self.assertIsNotNone(consonantal_val)
        self.assertLess(consonantal_val.value, 0)
    
    def test_scalar_feature_parsing(self):
        """Test parsing of scalar feature specifications."""
        # Test explicit scalar values
        bundle = self.system.parse_feature_specification('[voice=0.8,high=-0.5]')
        
        voice_fval = bundle.get_feature('voice')
        self.assertIsNotNone(voice_fval)
        self.assertEqual(voice_fval.value, 0.8)
        
        high_fval = bundle.get_feature('high')
        self.assertIsNotNone(high_fval)
        self.assertEqual(high_fval.value, -0.5)
        
        # Test binary notation
        bundle = self.system.parse_feature_specification('[+voice,-continuant]')
        
        voice_fval = bundle.get_feature('voice')
        self.assertIsNotNone(voice_fval)
        self.assertEqual(voice_fval.value, 1.0)
        
        continuant_fval = bundle.get_feature('continuant')
        self.assertIsNotNone(continuant_fval)
        self.assertEqual(continuant_fval.value, -1.0)
    
    def test_feature_addition(self):
        """Test scalar feature addition."""
        # Start with neutral values
        base_bundle = self.system.parse_feature_specification('[voice=0.0]')
        additional_bundle = self.system.parse_feature_specification('[voice=0.5]')
        
        result = self.system.add_features(base_bundle, additional_bundle)
        
        voice_fval = result.get_feature('voice')
        self.assertIsNotNone(voice_fval)
        self.assertEqual(voice_fval.value, 0.5)  # 0.0 + 0.5 = 0.5
        
        # Test saturation
        high_bundle = self.system.parse_feature_specification('[voice=0.8]')
        result = self.system.add_features(high_bundle, additional_bundle)
        
        voice_fval = result.get_feature('voice')
        self.assertIsNotNone(voice_fval)
        self.assertEqual(voice_fval.value, 1.0)  # 0.8 + 0.5 = 1.3 -> 1.0 (saturated)
    
    def test_vowel_consonant_detection(self):
        """Test vowel-like and consonant-like detection."""
        # Test vowel
        a_features = self.system.grapheme_to_features('a')
        self.assertTrue(self.system.is_vowel_like(a_features))
        self.assertFalse(self.system.is_consonant_like(a_features))
        
        # Test consonant
        p_features = self.system.grapheme_to_features('p')
        self.assertFalse(self.system.is_vowel_like(p_features))
        self.assertTrue(self.system.is_consonant_like(p_features))
        
        # Test sonorant consonant (might be ambiguous)
        n_features = self.system.grapheme_to_features('n')
        self.assertTrue(self.system.is_consonant_like(n_features))
    
    def test_sound_interpolation(self):
        """Test sound interpolation functionality."""
        p_features = self.system.grapheme_to_features('p')
        b_features = self.system.grapheme_to_features('b')
        
        # Interpolate halfway
        interpolated = self.system.interpolate_sounds(p_features, b_features, 0.5)
        
        # Voice should be halfway between p (-1.0) and b (1.0)
        voice_fval = interpolated.get_feature('voice')
        self.assertIsNotNone(voice_fval)
        self.assertEqual(voice_fval.value, 0.0)  # (-1.0 + 1.0) / 2 = 0.0
        
        # Other features should be the same (both bilabial stops)
        labial_fval = interpolated.get_feature('labial')
        self.assertIsNotNone(labial_fval)
        self.assertEqual(labial_fval.value, 1.0)


class TestSoundWithFeatureSystems(unittest.TestCase):
    """Test the Sound class with different feature systems."""
    
    def test_sound_creation_with_systems(self):
        """Test creating sounds with different feature systems."""
        # IPA categorical system
        ipa_sound = Sound(grapheme='p', feature_system='ipa_categorical')
        self.assertEqual(ipa_sound.feature_system_name, 'ipa_categorical')
        self.assertEqual(ipa_sound.grapheme(), 'p')
        
        # Unified distinctive system
        unified_sound = Sound(grapheme='p', feature_system='unified_distinctive')
        self.assertEqual(unified_sound.feature_system_name, 'unified_distinctive')
        self.assertEqual(unified_sound.grapheme(), 'p')
        
        # Both should represent the same sound but with different features
        self.assertNotEqual(ipa_sound.features, unified_sound.features)
    
    def test_sound_feature_access(self):
        """Test accessing features from sounds."""
        # IPA categorical
        ipa_sound = Sound(grapheme='p', feature_system='ipa_categorical')
        self.assertTrue(ipa_sound.has_feature('consonant'))
        self.assertTrue(ipa_sound.has_feature('bilabial'))
        
        # Unified distinctive
        unified_sound = Sound(grapheme='p', feature_system='unified_distinctive')
        self.assertTrue(unified_sound.has_feature('labial'))
        self.assertTrue(unified_sound.has_feature('consonantal'))
        
        # Test value access
        labial_val = unified_sound.get_feature_value('labial')
        self.assertIsNotNone(labial_val)
        self.assertEqual(labial_val, 1.0)
    
    def test_sound_arithmetic(self):
        """Test sound arithmetic with different systems."""
        # IPA categorical
        ipa_p = Sound(grapheme='p', feature_system='ipa_categorical')
        ipa_voiced = ipa_p + 'voiced'
        
        # Should become voiced
        self.assertTrue(ipa_voiced.has_feature('voiced'))
        self.assertFalse(ipa_voiced.has_feature('voiceless'))
        
        # Unified distinctive
        unified_p = Sound(grapheme='p', feature_system='unified_distinctive')
        unified_voiced = unified_p + 'voice=1.0'
        
        voice_val = unified_voiced.get_feature_value('voice')
        self.assertIsNotNone(voice_val)
        self.assertEqual(voice_val, 1.0)
    
    def test_sound_distance(self):
        """Test distance calculations between sounds."""
        # Same system
        p1 = Sound(grapheme='p', feature_system='ipa_categorical')
        p2 = Sound(grapheme='p', feature_system='ipa_categorical')
        b = Sound(grapheme='b', feature_system='ipa_categorical')
        
        self.assertEqual(p1.distance_to(p2), 0.0)
        self.assertGreater(p1.distance_to(b), 0.0)
        
        # Different systems (should use conversion)
        p_unified = Sound(grapheme='p', feature_system='unified_distinctive')
        distance = p1.distance_to(p_unified)
        self.assertGreaterEqual(distance, 0.0)
        self.assertLessEqual(distance, 1.0)
    
    def test_sound_conversion(self):
        """Test converting sounds between systems."""
        # Create in IPA system
        ipa_sound = Sound(grapheme='p', feature_system='ipa_categorical')
        
        # Convert to unified system
        unified_sound = ipa_sound.convert_to_system('unified_distinctive')
        
        self.assertEqual(unified_sound.feature_system_name, 'unified_distinctive')
        self.assertEqual(unified_sound.grapheme(), 'p')  # Should still be 'p'
        
        # Convert back
        converted_back = unified_sound.convert_to_system('ipa_categorical')
        self.assertEqual(converted_back.feature_system_name, 'ipa_categorical')
        self.assertEqual(converted_back.grapheme(), 'p')
    
    def test_backward_compatibility(self):
        """Test that old Sound API still works."""
        # Old-style creation
        sound = Sound(grapheme='p')  # Should use default system
        
        # Old-style feature access
        fvalues = sound.fvalues
        self.assertIsInstance(fvalues, frozenset)
        self.assertIn('consonant', fvalues)
        
        # Old-style arithmetic
        voiced_sound = sound + 'voiced'
        self.assertIn('voiced', voiced_sound.fvalues)
        
        # Old-style methods
        self.assertEqual(sound.get_stress_level(), 0)
        self.assertEqual(sound.get_tone_value(), 0)


class TestFeatureSystemRegistry(unittest.TestCase):
    """Test the feature system registry."""
    
    def test_registry_operations(self):
        """Test basic registry operations."""
        # Should have built-in systems
        systems = list_feature_systems()
        self.assertIn('ipa_categorical', systems)
        self.assertIn('unified_distinctive', systems)
        
        # Test getting systems
        ipa_system = get_feature_system('ipa_categorical')
        self.assertEqual(ipa_system.name, 'ipa_categorical')
        
        unified_system = get_feature_system('unified_distinctive')
        self.assertEqual(unified_system.name, 'unified_distinctive')
        
        # Test default system
        default_system = get_default_feature_system()
        self.assertEqual(default_system.name, 'ipa_categorical')
    
    def test_system_switching(self):
        """Test switching default systems."""
        # Remember original default
        original_default = get_default_feature_system().name
        
        try:
            # Switch to unified
            set_default_feature_system('unified_distinctive')
            
            # New sounds should use unified system
            sound = Sound(grapheme='p')
            self.assertEqual(sound.feature_system_name, 'unified_distinctive')
            
        finally:
            # Restore original default
            set_default_feature_system(original_default)
    
    def test_context_manager(self):
        """Test feature system context manager."""
        # Remember original default
        original_default = get_default_feature_system().name
        
        # Use context manager
        with feature_system_context('unified_distinctive'):
            sound = Sound(grapheme='p')
            self.assertEqual(sound.feature_system_name, 'unified_distinctive')
        
        # Should be restored
        restored_default = get_default_feature_system().name
        self.assertEqual(restored_default, original_default)


class TestFeatureSystemConversion(unittest.TestCase):
    """Test feature system conversion utilities."""
    
    def test_basic_conversion(self):
        """Test basic feature system conversion."""
        # Create sound in IPA system
        ipa_sound = Sound(grapheme='p', feature_system='ipa_categorical')
        
        # Convert to unified system
        unified_features = convert_sound_between_systems(
            'ipa_categorical', 
            'unified_distinctive', 
            ipa_sound.features
        )
        
        self.assertIsInstance(unified_features, FeatureBundle)
        self.assertTrue(unified_features.has_feature('labial'))
        self.assertTrue(unified_features.has_feature('consonantal'))
    
    def test_conversion_recommendations(self):
        """Test conversion recommendations."""
        recommendations = get_conversion_recommendations(
            'ipa_categorical', 
            'unified_distinctive'
        )
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Should mention scalar conversion
        rec_text = ' '.join(recommendations)
        self.assertIn('scalar', rec_text.lower())
    
    def test_round_trip_conversion(self):
        """Test round-trip conversion accuracy."""
        # Start with IPA sound
        original_sound = Sound(grapheme='p', feature_system='ipa_categorical')
        
        # Convert to unified and back
        unified_sound = original_sound.convert_to_system('unified_distinctive')
        converted_back = unified_sound.convert_to_system('ipa_categorical')
        
        # Should represent the same sound
        self.assertEqual(original_sound.grapheme(), converted_back.grapheme())
        
        # Distance should be small
        distance = original_sound.distance_to(converted_back)
        self.assertLess(distance, 0.5)  # Allow some conversion loss


if __name__ == '__main__':
    unittest.main()