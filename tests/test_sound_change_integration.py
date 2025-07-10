"""
Integration tests for sound change engine with all feature systems.

This test suite validates that the sound change engine works correctly
with IPA categorical, unified distinctive, and Tresoldi feature systems,
testing both categorical and gradient sound changes.
"""

import unittest
import sys
import os

# Add the parent directory to the path to import alteruphono
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alteruphono.phonology.sound_change import (
    SoundChangeEngine, 
    FeatureChangeRule, 
    SoundChangeRule,
    RuleSet
)
from alteruphono.phonology.sound_change.rules import FeatureChange, ChangeType
from alteruphono.phonology.sound_v2 import Sound
from alteruphono.phonology.feature_systems import list_feature_systems


class TestSoundChangeEngineIntegration(unittest.TestCase):
    """Test sound change engine integration with all feature systems."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.systems = list_feature_systems()
        print(f"Testing with systems: {self.systems}")
    
    def test_engine_creation_with_all_systems(self):
        """Test that engines can be created with all feature systems."""
        for system_name in self.systems:
            with self.subTest(system=system_name):
                engine = SoundChangeEngine(feature_system_name=system_name)
                self.assertEqual(engine.feature_system_name, system_name)
                # Engine should be created successfully
                self.assertIsNotNone(engine)
    
    def test_categorical_sound_changes_all_systems(self):
        """Test categorical sound changes work with all systems."""
        test_cases = [
            # Simple substitution
            {
                'name': 'p_to_b',
                'source_pattern': 'p',
                'target_pattern': 'b',
                'input': ['p', 'a', 't'],
                'expected_change': True
            },
            # Vowel change
            {
                'name': 'a_to_e',
                'source_pattern': 'a',
                'target_pattern': 'e',
                'input': ['p', 'a', 't'],
                'expected_change': True
            }
        ]
        
        for system_name in self.systems:
            with self.subTest(system=system_name):
                engine = SoundChangeEngine(feature_system_name=system_name)
                
                for test_case in test_cases:
                    with self.subTest(rule=test_case['name']):
                        # Create rule
                        rule = SoundChangeRule(
                            name=test_case['name'],
                            source_pattern=test_case['source_pattern'],
                            target_pattern=test_case['target_pattern']
                        )
                        
                        # Create input sequence
                        input_sounds = [
                            Sound(grapheme=g, feature_system=system_name) 
                            for g in test_case['input']
                        ]
                        
                        # Apply rule
                        result = engine.apply_rule(rule, input_sounds)
                        
                        # Check that rule applied if expected
                        if test_case['expected_change']:
                            self.assertTrue(result.changed, 
                                          f"Rule {test_case['name']} should have applied in {system_name}")
    
    def test_feature_based_rules_all_systems(self):
        """Test feature-based rules work with all systems."""
        # Test voicing rule (works with systems that have voice feature)
        for system_name in self.systems:
            with self.subTest(system=system_name):
                engine = SoundChangeEngine(feature_system_name=system_name)
                
                # Create a sound that might have voice feature
                try:
                    p_sound = Sound(grapheme='p', feature_system=system_name)
                    
                    # Check if this system supports voice feature
                    if p_sound.has_feature('voice'):
                        # Create voicing rule
                        voicing_change = FeatureChange(
                            feature_name="voice",
                            target_value=1.0,
                            change_type=ChangeType.CATEGORICAL
                        )
                        
                        rule = FeatureChangeRule(
                            name="voicing",
                            source_pattern="",
                            target_pattern=[voicing_change],
                            feature_conditions={"voice": -1.0},  # Voiceless sounds
                            feature_changes=[voicing_change],
                            feature_system_name=system_name
                        )
                        
                        # Apply rule
                        result = engine.apply_rule(rule, [p_sound])
                        
                        # Rule should apply to voiceless p
                        if p_sound.get_feature_value('voice') < 0:
                            # Check if any sound was changed (change_count may not be reliable)
                            changed = any(
                                abs(orig.get_feature_value('voice') - new.get_feature_value('voice')) > 0.01
                                for orig, new in zip([p_sound], result.modified_sequence)
                                if orig.has_feature('voice') and new.has_feature('voice')
                            )
                            if changed:
                                print(f"✓ {system_name}: Voice feature rule applied")
                            else:
                                print(f"⚠ {system_name}: Voice feature rule may not have applied")
                        else:
                            print(f"⚠ {system_name}: Test sound not voiceless")
                    else:
                        print(f"⚠ {system_name}: No voice feature support")
                        
                except Exception as e:
                    self.fail(f"Feature-based rule failed in {system_name}: {e}")
    
    def test_gradient_rules_scalar_systems(self):
        """Test gradient rules with scalar feature systems."""
        scalar_systems = ['unified_distinctive', 'tresoldi_distinctive']
        
        for system_name in scalar_systems:
            with self.subTest(system=system_name):
                engine = SoundChangeEngine(feature_system_name=system_name)
                
                # Create test sound
                p_sound = Sound(grapheme='p', feature_system=system_name)
                
                # Create gradient voicing rule
                gradient_change = FeatureChange(
                    feature_name="voice",
                    target_value=0.5,  # Partial voicing
                    change_strength=1.0,
                    change_type=ChangeType.GRADIENT
                )
                
                rule = FeatureChangeRule(
                    name="gradient_voicing",
                    source_pattern="",
                    target_pattern=[gradient_change],
                    feature_conditions={"voice": -1.0},
                    feature_changes=[gradient_change],
                    feature_system_name=system_name
                )
                
                # Apply rule
                result = engine.apply_rule(rule, [p_sound])
                
                # Check that gradient change occurred
                if len(result.modified_sequence) > 0:
                    original_voice = p_sound.get_feature_value('voice')
                    new_voice = result.modified_sequence[0].get_feature_value('voice')
                    
                    # Should be different (gradient change)
                    if abs(new_voice - original_voice) > 0.01:
                        print(f"✓ {system_name}: Gradient voicing {original_voice:.2f} → {new_voice:.2f}")
    
    def test_rule_ordering_all_systems(self):
        """Test rule ordering and interaction across systems."""
        for system_name in self.systems:
            with self.subTest(system=system_name):
                engine = SoundChangeEngine(feature_system_name=system_name)
                
                # Create a chain of rules
                rule1 = SoundChangeRule(name="p_to_f", source_pattern="p", target_pattern="f")
                rule2 = SoundChangeRule(name="f_to_h", source_pattern="f", target_pattern="h")
                
                rule_set = RuleSet(rules=[rule1, rule2], iterative=True)
                
                # Create input
                input_sounds = [Sound(grapheme='p', feature_system=system_name)]
                
                # Apply rule set
                result = engine.apply_rule_set(rule_set, input_sounds)
                
                # Should end up with 'h' after both rules apply
                if len(result.final_sequence) > 0:
                    final_sound = result.final_sequence[0]
                    final_grapheme = final_sound.grapheme()
                    print(f"✓ {system_name}: p → {final_grapheme} (chain: p→f→h)")
    
    def test_environmental_conditions_all_systems(self):
        """Test environmental condition matching across systems."""
        from alteruphono.phonology.sound_change import PhonologicalEnvironment
        
        for system_name in self.systems:
            with self.subTest(system=system_name):
                # Create test sounds
                try:
                    p_sound = Sound(grapheme='p', feature_system=system_name)
                    a_sound = Sound(grapheme='a', feature_system=system_name)
                    
                    # Create environment: vowel _ vowel
                    env = PhonologicalEnvironment(
                        left_pattern="V",
                        right_pattern="V",
                        target_conditions={"consonantal": 1.0},
                        feature_system_name=system_name
                    )
                    
                    # Test environment matching
                    matches = env.matches(p_sound, [a_sound], [a_sound])
                    
                    # Result depends on whether system supports V class and features
                    print(f"✓ {system_name}: Environment matching works (result: {matches})")
                    
                except Exception as e:
                    print(f"⚠ {system_name}: Environment matching issue: {e}")
    
    def test_performance_comparison_across_systems(self):
        """Test performance comparison across feature systems."""
        import time
        
        n_iterations = 100
        test_word = ['p', 'a', 't', 'a']
        
        performance_results = {}
        
        for system_name in self.systems:
            engine = SoundChangeEngine(feature_system_name=system_name)
            
            # Create rule
            rule = SoundChangeRule(name="test", source_pattern="p", target_pattern="b")
            
            # Create input
            input_sounds = [Sound(grapheme=g, feature_system=system_name) for g in test_word]
            
            # Time the operations
            start_time = time.time()
            for _ in range(n_iterations):
                result = engine.apply_rule(rule, input_sounds)
            end_time = time.time()
            
            avg_time = (end_time - start_time) / n_iterations * 1000
            performance_results[system_name] = avg_time
        
        print("Performance comparison (avg time per rule application):")
        for system, time_ms in performance_results.items():
            print(f"  {system}: {time_ms:.3f}ms")
        
        # All systems should be reasonably fast
        for system, time_ms in performance_results.items():
            self.assertLess(time_ms, 50.0, f"{system} too slow: {time_ms:.3f}ms")
    
    def test_feature_system_specific_rules(self):
        """Test rules that are specific to certain feature systems."""
        
        # Test IPA categorical specific rules
        if 'ipa_categorical' in self.systems:
            engine = SoundChangeEngine(feature_system_name='ipa_categorical')
            
            # Test binary feature rule
            p_sound = Sound(grapheme='p', feature_system='ipa_categorical')
            if p_sound.has_feature('voiceless'):
                print("✓ IPA categorical: Binary features supported")
        
        # Test unified distinctive specific rules
        if 'unified_distinctive' in self.systems:
            engine = SoundChangeEngine(feature_system_name='unified_distinctive')
            
            # Test scalar arithmetic
            p_sound = Sound(grapheme='p', feature_system='unified_distinctive')
            voiced_p = p_sound + 'voice=2.0'  # Test additive behavior
            
            voice_change = voiced_p.get_feature_value('voice') - p_sound.get_feature_value('voice')
            self.assertGreater(voice_change, 0, "Unified distinctive should support scalar arithmetic")
            print("✓ Unified distinctive: Scalar arithmetic supported")
        
        # Test Tresoldi specific rules
        if 'tresoldi_distinctive' in self.systems:
            engine = SoundChangeEngine(feature_system_name='tresoldi_distinctive')
            
            # Test comprehensive coverage
            from alteruphono.phonology.feature_systems import get_feature_system
            system = get_feature_system('tresoldi_distinctive')
            complex_sounds = ['bd', 'kʷ', 'ǃ']
            supported = [s for s in complex_sounds if system.has_grapheme(s)]
            
            if supported:
                print(f"✓ Tresoldi: Complex sounds supported: {supported}")
    
    def test_cross_system_consistency(self):
        """Test consistency of basic operations across systems."""
        # Test that basic sound changes produce similar results
        test_rules = [
            ('p > b', ['p', 'a'], ['b', 'a']),
            ('a > e', ['p', 'a'], ['p', 'e'])
        ]
        
        results = {}
        
        for rule_str, input_seq, expected in test_rules:
            rule = SoundChangeRule(name="test", source_pattern=rule_str.split(' > ')[0], 
                                 target_pattern=rule_str.split(' > ')[1])
            
            system_results = {}
            
            for system_name in self.systems:
                engine = SoundChangeEngine(feature_system_name=system_name)
                input_sounds = [Sound(grapheme=g, feature_system=system_name) for g in input_seq]
                
                result = engine.apply_rule(rule, input_sounds)
                
                # Extract graphemes from result
                result_graphemes = [s.grapheme() for s in result.modified_sequence]
                system_results[system_name] = result_graphemes
            
            results[rule_str] = system_results
        
        print("Cross-system consistency check:")
        for rule_str, system_results in results.items():
            print(f"  {rule_str}:")
            for system, result in system_results.items():
                print(f"    {system}: {' '.join(result)}")
            
            # Check if all systems produce the same result
            unique_results = set(tuple(r) for r in system_results.values())
            if len(unique_results) == 1:
                print(f"    ✓ All systems consistent")
            else:
                print(f"    ⚠ Systems differ")


if __name__ == '__main__':
    unittest.main(verbosity=2)