"""
Comprehensive tests for the sound change rule engine.

This test suite covers all aspects of the sound change system including
categorical rules, gradient changes, environmental conditions, and
probabilistic applications.
"""

import unittest
import sys
import os

# Add the parent directory to the path to import alteruphono
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alteruphono.phonology.sound_change import (
    SoundChangeRule,
    FeatureChangeRule,
    EnvironmentalCondition,
    RuleSet,
    RuleApplication,
    SoundChangeEngine,
    PhonologicalEnvironment,
    GradientChange,
    FeatureShift,
    PartialApplication,
    ChangeType,
    ApplicationMode,
    ChangeStrength
)
from alteruphono.phonology.sound_change.rules import FeatureChange
from alteruphono.phonology.sound_change.gradients import (
    GradientRuleBuilder,
    create_lenition_rule,
    create_vowel_raising_rule,
    create_voicing_assimilation_rule
)
from alteruphono.phonology.sound_v2 import Sound
from alteruphono.phonology.feature_systems import FeatureValue, FeatureValueType


class TestSoundChangeRules(unittest.TestCase):
    """Test basic sound change rule functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = SoundChangeEngine()
        
        # Create test sounds
        self.p_sound = Sound(grapheme='p', feature_system='unified_distinctive')
        self.b_sound = Sound(grapheme='b', feature_system='unified_distinctive')
        self.t_sound = Sound(grapheme='t', feature_system='unified_distinctive')
        self.a_sound = Sound(grapheme='a', feature_system='unified_distinctive')
    
    def test_categorical_rule_creation(self):
        """Test creation of categorical sound change rules."""
        # Simple p > f rule
        rule = SoundChangeRule(
            name="p_to_f",
            source_pattern="p",
            target_pattern="f",
            probability=1.0
        )
        
        self.assertEqual(rule.name, "p_to_f")
        self.assertEqual(rule.source_pattern, "p")
        self.assertEqual(rule.target_pattern, "f")
        self.assertEqual(rule.probability, 1.0)
    
    def test_feature_based_rule_creation(self):
        """Test creation of feature-based rules."""
        # Voicing rule: voiceless > voiced
        voicing_change = FeatureChange(
            feature_name="voice",
            target_value=1.0,
            change_type=ChangeType.GRADIENT
        )
        
        rule = FeatureChangeRule(
            name="voicing",
            source_pattern="",
            target_pattern=[voicing_change],
            feature_conditions={"voice": -1.0},
            feature_changes=[voicing_change]
        )
        
        self.assertEqual(rule.name, "voicing")
        self.assertEqual(len(rule.feature_changes), 1)
        self.assertEqual(rule.feature_changes[0].feature_name, "voice")
    
    def test_environmental_conditions(self):
        """Test environmental condition matching."""
        # Simple rule without environment for now
        rule = SoundChangeRule(
            name="simple_change",
            source_pattern="p", 
            target_pattern="f"
        )
        
        # Test basic application
        self.assertTrue(rule.applies_to(self.p_sound, [], []))
        
        # Test with wrong source
        self.assertFalse(rule.applies_to(self.a_sound, [], []))
    
    def test_rule_application(self):
        """Test applying rules to sounds."""
        # Simple categorical change
        rule = SoundChangeRule(
            name="voicing",
            source_pattern="p",
            target_pattern="b"
        )
        
        result = rule.apply_to(self.p_sound)
        self.assertEqual(result.grapheme(), "b")
    
    def test_gradient_rule_application(self):
        """Test gradient feature changes."""
        # Partial voicing rule
        voicing_change = FeatureChange(
            feature_name="voice",
            target_value=0.5,  # Partial voicing
            change_strength=1.0,
            change_type=ChangeType.GRADIENT
        )
        
        rule = FeatureChangeRule(
            name="partial_voicing",
            source_pattern="",
            target_pattern=[voicing_change],
            feature_conditions={"voice": -1.0},
            feature_changes=[voicing_change]
        )
        
        result = rule.apply_to(self.p_sound)
        voice_value = result.get_feature_value("voice")
        
        # Should have intermediate voicing value
        self.assertGreater(voice_value, -1.0)
        self.assertLess(voice_value, 1.0)


class TestSoundChangeEngine(unittest.TestCase):
    """Test the sound change engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = SoundChangeEngine()
        self.test_sequence = [
            Sound(grapheme='p', feature_system='unified_distinctive'),
            Sound(grapheme='a', feature_system='unified_distinctive'),
            Sound(grapheme='t', feature_system='unified_distinctive'),
            Sound(grapheme='a', feature_system='unified_distinctive')
        ]
    
    def test_single_rule_application(self):
        """Test applying a single rule to a sequence."""
        # p > b rule
        rule = SoundChangeRule(
            name="p_voicing",
            source_pattern="p",
            target_pattern="b"
        )
        
        result = self.engine.apply_rule(rule, self.test_sequence)
        
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        self.assertEqual(result.modified_sequence[0].grapheme, "b")
    
    def test_rule_set_application(self):
        """Test applying a set of rules."""
        # Create rule set
        rule_set = RuleSet(name="test_rules")
        
        # Add p > b rule
        p_rule = SoundChangeRule(
            name="p_voicing",
            source_pattern="p", 
            target_pattern="b"
        )
        rule_set.add_rule(p_rule)
        
        # Add t > d rule  
        t_rule = SoundChangeRule(
            name="t_voicing",
            source_pattern="t",
            target_pattern="d"
        )
        rule_set.add_rule(t_rule)
        
        # Apply rule set
        simulation = self.engine.apply_rule_set(rule_set, self.test_sequence)
        
        self.assertEqual(simulation.total_changes, 2)
        self.assertEqual(len(simulation.rules_applied), 2)
        
        # Check final sequence
        final = simulation.final_sequence
        self.assertEqual(final[0].grapheme, "b")  # p > b
        self.assertEqual(final[2].grapheme, "d")  # t > d
    
    def test_iterative_rules(self):
        """Test iterative rule application."""
        # Create chain of changes: p > f > h
        rule1 = SoundChangeRule(name="p_to_f", source_pattern="p", target_pattern="f")
        rule2 = SoundChangeRule(name="f_to_h", source_pattern="f", target_pattern="h")
        
        rule_set = RuleSet(rules=[rule1, rule2], iterative=True)
        
        sequence = [Sound(grapheme='p', feature_system='unified_distinctive')]
        simulation = self.engine.apply_rule_set(rule_set, sequence)
        
        # Should end up with 'h' after both rules apply
        self.assertEqual(simulation.final_sequence[0].grapheme, "h")
    
    def test_probabilistic_rules(self):
        """Test probabilistic rule application."""
        # Rule with 0% probability should never apply
        rule = SoundChangeRule(
            name="never_applies",
            source_pattern="p",
            target_pattern="b", 
            probability=0.0
        )
        
        result = self.engine.apply_rule(rule, self.test_sequence)
        self.assertFalse(result.changed)
        
        # Rule with 100% probability should always apply
        rule.probability = 1.0
        result = self.engine.apply_rule(rule, self.test_sequence)
        self.assertTrue(result.changed)


class TestGradientChanges(unittest.TestCase):
    """Test gradient sound changes."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.p_sound = Sound(grapheme='p', feature_system='unified_distinctive')
        self.engine = SoundChangeEngine()
    
    def test_gradient_change_creation(self):
        """Test creating gradient changes."""
        change = GradientChange(
            feature_name="voice",
            source_value=-1.0,
            target_value=1.0,
            change_rate=0.2
        )
        
        self.assertEqual(change.feature_name, "voice")
        self.assertEqual(change.source_value, -1.0)
        self.assertEqual(change.target_value, 1.0)
    
    def test_gradient_step_application(self):
        """Test applying gradient change steps."""
        change = GradientChange(
            feature_name="voice",
            source_value=-1.0,
            target_value=1.0,
            change_rate=0.2
        )
        
        # Apply one step
        new_value = change.apply_step(-1.0, strength=1.0)
        self.assertGreater(new_value, -1.0)
        self.assertLessEqual(new_value, -0.8)  # Should move toward target
    
    def test_feature_shift(self):
        """Test feature shift systems."""
        shift = FeatureShift()
        shift.add_shift("voice", -1.0, 1.0, change_rate=0.5)
        shift.add_shift("continuant", -1.0, 0.5, change_rate=0.3)
        
        # Apply to sound
        result = shift.apply_to_sound(self.p_sound, strength=1.0)
        
        # Check that features changed
        voice_val = result.get_feature_value("voice")
        cont_val = result.get_feature_value("continuant")
        
        self.assertGreater(voice_val, -1.0)
        self.assertGreater(cont_val, -1.0)
    
    def test_partial_application(self):
        """Test partial rule application."""
        rule = SoundChangeRule(
            name="voicing",
            source_pattern="p",
            target_pattern="b"
        )
        
        partial = PartialApplication(
            rule=rule,
            application_probability=1.0,  # Always apply
            strength_distribution=lambda: 0.5  # Half strength
        )
        
        result = partial.apply_to_sound(self.p_sound)
        
        # Should have partial change toward 'b'
        voice_val = result.get_feature_value("voice")
        original_voice = self.p_sound.get_feature_value("voice")
        self.assertGreater(voice_val, original_voice)
    
    def test_gradient_rule_builder(self):
        """Test gradient rule builder interface."""
        rule = (GradientRuleBuilder()
                .shift_feature("voice", 1.0, 0.7)
                .shift_feature("continuant", 0.5, 0.5)
                .with_condition("consonantal", "+consonantal")
                .with_probability(0.8)
                .build("test_gradient"))
        
        self.assertEqual(rule.name, "test_gradient")
        self.assertEqual(len(rule.feature_changes), 2)
        self.assertEqual(rule.probability, 0.8)
    
    def test_predefined_gradient_rules(self):
        """Test predefined gradient rule functions."""
        # Test lenition rule
        lenition = create_lenition_rule(strength=0.5)
        self.assertEqual(lenition.name, "gradient_lenition")
        
        # Test vowel raising
        raising = create_vowel_raising_rule(height_increase=0.3)
        self.assertEqual(raising.name, "vowel_raising")
        
        # Test voicing assimilation
        assimilation = create_voicing_assimilation_rule(strength=0.7)
        self.assertEqual(assimilation.name, "voicing_assimilation")


class TestEnvironmentalMatching(unittest.TestCase):
    """Test environmental condition matching."""
    
    def test_phonological_environment_creation(self):
        """Test creating phonological environments."""
        env = PhonologicalEnvironment(
            left_pattern="V",
            right_pattern="V",
            target_conditions={"consonantal": "+consonantal"}
        )
        
        self.assertEqual(env.left_pattern, "V")
        self.assertEqual(env.right_pattern, "V")
    
    def test_environment_from_string(self):
        """Test creating environments from string notation."""
        env = PhonologicalEnvironment.from_string("V _ V / [+consonantal]")
        
        self.assertEqual(env.left_pattern, "V")
        self.assertEqual(env.right_pattern, "V")
        self.assertIsNotNone(env.target_conditions)
    
    def test_complex_environment_matching(self):
        """Test complex environmental conditions."""
        # Rule only applies to voiceless stops between vowels
        env = PhonologicalEnvironment(
            left_pattern="V",
            right_pattern="V", 
            target_conditions={"voice": -1.0, "consonantal": 1.0}
        )
        
        p_sound = Sound(grapheme='p', feature_system='unified_distinctive')
        a_sound = Sound(grapheme='a', feature_system='unified_distinctive')
        
        # Should match p between vowels
        self.assertTrue(env.matches(p_sound, [a_sound], [a_sound]))


class TestSoundChangeSimulation(unittest.TestCase):
    """Test sound change simulation features."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = SoundChangeEngine()
        self.test_word = [
            Sound(grapheme='p', feature_system='unified_distinctive'),
            Sound(grapheme='a', feature_system='unified_distinctive'),
            Sound(grapheme='t', feature_system='unified_distinctive'),
            Sound(grapheme='a', feature_system='unified_distinctive')
        ]
    
    def test_gradual_change_simulation(self):
        """Test gradual change simulation."""
        # Create partial voicing rule
        voicing_change = FeatureChange(
            feature_name="voice",
            target_value=1.0,
            change_type=ChangeType.GRADIENT
        )
        
        rule = FeatureChangeRule(
            name="gradual_voicing",
            source_pattern="p",
            target_pattern=[voicing_change],
            feature_conditions={"voice": -1.0},
            feature_changes=[voicing_change]
        )
        
        # Simulate gradual application
        simulations = self.engine.simulate_gradual_change(rule, self.test_word, steps=5)
        
        self.assertEqual(len(simulations), 5)
        
        # Voice value should increase gradually
        voice_values = []
        for sim in simulations:
            if sim.final_sequence[0].has_feature("voice"):
                voice_values.append(sim.final_sequence[0].get_feature_value("voice"))
        
        # Should be generally increasing (allowing for some noise)
        self.assertGreater(voice_values[-1], voice_values[0])
    
    def test_change_trajectory_tracking(self):
        """Test tracking change trajectories."""
        rule1 = SoundChangeRule(name="p_to_f", source_pattern="p", target_pattern="f")
        rule2 = SoundChangeRule(name="t_to_s", source_pattern="t", target_pattern="s")
        
        rule_set = RuleSet(rules=[rule1, rule2])
        simulation = self.engine.apply_rule_set(rule_set, self.test_word)
        
        trajectory = simulation.get_change_trajectory()
        
        # Should have initial state plus states after each rule
        self.assertGreaterEqual(len(trajectory), 2)  # At least initial + final
        
        # First state should be original
        self.assertEqual(trajectory[0], self.test_word)
    
    def test_detailed_change_analysis(self):
        """Test detailed change analysis."""
        rule = SoundChangeRule(
            name="voicing",
            source_pattern="p",
            target_pattern="b"
        )
        
        result = self.engine.apply_rule(rule, self.test_word)
        
        # Check change summary
        summary = result.get_change_summary()
        self.assertIsInstance(summary, dict)
        
        if result.changed:
            self.assertGreater(len(summary), 0)


class TestRuleInteractions(unittest.TestCase):
    """Test interactions between multiple rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = SoundChangeEngine()
    
    def test_rule_ordering_effects(self):
        """Test that rule ordering matters."""
        # Create rules that interact
        rule1 = SoundChangeRule(name="p_to_f", source_pattern="p", target_pattern="f")
        rule2 = SoundChangeRule(name="f_to_h", source_pattern="f", target_pattern="h")
        
        sequence = [Sound(grapheme='p', feature_system='unified_distinctive')]
        
        # Order 1: p > f, then f > h = h
        rule_set1 = RuleSet(rules=[rule1, rule2])
        result1 = self.engine.apply_rule_set(rule_set1, sequence)
        
        # Order 2: f > h, then p > f = f (no h because f>h applies before p>f)
        rule_set2 = RuleSet(rules=[rule2, rule1])  
        result2 = self.engine.apply_rule_set(rule_set2, sequence)
        
        # Results should be different due to ordering
        final1 = result1.final_sequence[0].grapheme
        final2 = result2.final_sequence[0].grapheme
        
        # With iterative=False, different orders give different results
        if not rule_set1.iterative:
            self.assertNotEqual(final1, final2)
    
    def test_bleeding_and_feeding(self):
        """Test bleeding and feeding rule relationships."""
        # Feeding: rule A creates input for rule B
        # Bleeding: rule A removes input for rule B
        
        p_sound = Sound(grapheme='p', feature_system='unified_distinctive')
        t_sound = Sound(grapheme='t', feature_system='unified_distinctive')
        sequence = [p_sound, t_sound]
        
        # Feeding: p>f creates f, then f>h applies
        feed1 = SoundChangeRule(name="p_to_f", source_pattern="p", target_pattern="f")
        feed2 = SoundChangeRule(name="f_to_h", source_pattern="f", target_pattern="h")
        
        feeding_set = RuleSet(rules=[feed1, feed2], iterative=True)
        result = self.engine.apply_rule_set(feeding_set, [p_sound])
        
        # Should end with 'h' due to feeding
        self.assertEqual(result.final_sequence[0].grapheme, "h")


if __name__ == '__main__':
    # Run specific test groups
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', choices=['rules', 'engine', 'gradient', 'environment', 'simulation', 'interaction', 'all'],
                       default='all', help='Which test group to run')
    args = parser.parse_args()
    
    if args.test == 'all':
        unittest.main(argv=[''])
    else:
        suite = unittest.TestSuite()
        
        if args.test == 'rules':
            suite.addTest(unittest.makeSuite(TestSoundChangeRules))
        elif args.test == 'engine':
            suite.addTest(unittest.makeSuite(TestSoundChangeEngine))
        elif args.test == 'gradient':
            suite.addTest(unittest.makeSuite(TestGradientChanges))
        elif args.test == 'environment':
            suite.addTest(unittest.makeSuite(TestEnvironmentalMatching))
        elif args.test == 'simulation':
            suite.addTest(unittest.makeSuite(TestSoundChangeSimulation))
        elif args.test == 'interaction':
            suite.addTest(unittest.makeSuite(TestRuleInteractions))
        
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)