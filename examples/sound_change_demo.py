#!/usr/bin/env python3
"""
Comprehensive demonstration of the sound change rule engine.

This script showcases the powerful sound change capabilities enabled by
the unified distinctive feature system, including gradient changes,
probabilistic application, and complex environmental conditions.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alteruphono.phonology.sound_change import (
    SoundChangeRule,
    FeatureChangeRule, 
    SoundChangeEngine,
    RuleSet,
    PhonologicalEnvironment,
    GradientChange,
    FeatureShift,
    PartialApplication
)
from alteruphono.phonology.sound_change.rules import FeatureChange, ChangeType
from alteruphono.phonology.sound_change.gradients import (
    GradientRuleBuilder,
    create_lenition_rule,
    create_vowel_raising_rule,
    create_voicing_assimilation_rule,
    model_sound_change_diffusion
)
from alteruphono.phonology.sound_v2 import Sound


def demo_basic_sound_changes():
    """Demonstrate basic categorical sound changes."""
    print("=" * 70)
    print("BASIC CATEGORICAL SOUND CHANGES")
    print("=" * 70)
    
    engine = SoundChangeEngine()
    
    # Create test word: "pata"
    word = [
        Sound(grapheme='p', feature_system='unified_distinctive'),
        Sound(grapheme='a', feature_system='unified_distinctive'), 
        Sound(grapheme='t', feature_system='unified_distinctive'),
        Sound(grapheme='a', feature_system='unified_distinctive')
    ]
    
    print(f"Original word: {''.join(s.grapheme() for s in word)}")
    
    # Simple categorical changes
    rules = [
        SoundChangeRule(name="p_to_f", source_pattern="p", target_pattern="f"),
        SoundChangeRule(name="t_to_s", source_pattern="t", target_pattern="s")
    ]
    
    current_word = word
    for rule in rules:
        result = engine.apply_rule(rule, current_word)
        if result.changed:
            current_word = result.modified_sequence
            print(f"After {rule.name}: {''.join(s.grapheme() for s in current_word)}")
    
    print()


def demo_environmental_conditions():
    """Demonstrate environmental conditioning."""
    print("=" * 70)
    print("ENVIRONMENTAL CONDITIONS")
    print("=" * 70)
    
    engine = SoundChangeEngine()
    
    # Test words with different environments
    words = [
        # "apa" - p between vowels
        [Sound(grapheme='a'), Sound(grapheme='p'), Sound(grapheme='a')],
        # "spa" - p after consonant
        [Sound(grapheme='s'), Sound(grapheme='p'), Sound(grapheme='a')],
        # "apt" - p before consonant
        [Sound(grapheme='a'), Sound(grapheme='p'), Sound(grapheme='t')]
    ]
    
    # Rule: p > f only between vowels (lenition)
    env = PhonologicalEnvironment(
        left_pattern="[sonorant=1.0]",  # After vowel
        right_pattern="[sonorant=1.0]"   # Before vowel
    )
    
    # Convert to EnvironmentalCondition for the rule
    from alteruphono.phonology.sound_change.rules import EnvironmentalCondition
    env_condition = EnvironmentalCondition(
        left_context="[sonorant=1.0]",
        right_context="[sonorant=1.0]"
    )
    
    rule = SoundChangeRule(
        name="intervocalic_lenition",
        source_pattern="p",
        target_pattern="f",
        environment=env_condition
    )
    
    for i, word in enumerate(words):
        word_str = ''.join(s.grapheme() for s in word)
        print(f"Testing word {i+1}: {word_str}")
        
        result = engine.apply_rule(rule, word)
        final_word = ''.join(s.grapheme() for s in result.modified_sequence)
        
        if result.changed:
            print(f"  → {final_word} (rule applied)")
        else:
            print(f"  → {final_word} (rule blocked)")
    
    print()


def demo_gradient_changes():
    """Demonstrate gradient feature changes."""
    print("=" * 70)
    print("GRADIENT FEATURE CHANGES")
    print("=" * 70)
    
    engine = SoundChangeEngine()
    
    # Create test sound
    p_sound = Sound(grapheme='p', feature_system='unified_distinctive')
    print(f"Original /p/ voice value: {p_sound.get_feature_value('voice'):.2f}")
    
    # Gradient voicing rule
    voicing_change = FeatureChange(
        feature_name="voice",
        target_value=1.0,
        change_strength=0.3,  # Partial change
        change_type=ChangeType.GRADIENT
    )
    
    rule = FeatureChangeRule(
        name="partial_voicing",
        source_pattern="",
        target_pattern=[voicing_change],
        feature_conditions={"voice": -1.0},
        feature_changes=[voicing_change]
    )
    
    # Apply rule multiple times to show gradual change
    current_sound = p_sound
    for step in range(5):
        if rule.applies_to(current_sound, [], []):
            current_sound = rule.apply_to(current_sound)
            voice_val = current_sound.get_feature_value('voice')
            print(f"  Step {step+1}: voice = {voice_val:.2f}")
        else:
            break
    
    print()


def demo_feature_shifts():
    """Demonstrate complex feature shift systems."""
    print("=" * 70)
    print("FEATURE SHIFT SYSTEMS")
    print("=" * 70)
    
    # Create vowel system
    vowels = {
        'i': Sound(grapheme='i', feature_system='unified_distinctive'),
        'e': Sound(grapheme='e', feature_system='unified_distinctive'),
        'a': Sound(grapheme='a', feature_system='unified_distinctive'),
        'o': Sound(grapheme='o', feature_system='unified_distinctive'),
        'u': Sound(grapheme='u', feature_system='unified_distinctive')
    }
    
    print("Original vowel heights:")
    for grapheme, sound in vowels.items():
        high_val = sound.get_feature_value('high')
        print(f"  /{grapheme}/: high = {high_val:.2f}")
    
    # Create vowel raising shift (Great Vowel Shift style)
    shift = FeatureShift()
    shift.add_shift("high", -1.0, 1.0, change_rate=0.3)  # Raise vowels
    shift.add_shift("tense", -1.0, 1.0, change_rate=0.2)  # Increase tenseness
    
    # Add correlation: high and tense changes reinforce each other
    shift.add_correlation("high", "tense", 0.5)
    
    print("\nAfter vowel raising shift:")
    for grapheme, sound in vowels.items():
        shifted = shift.apply_to_sound(sound, strength=1.0)
        high_val = shifted.get_feature_value('high')
        tense_val = shifted.get_feature_value('tense')
        print(f"  /{grapheme}/: high = {high_val:.2f}, tense = {tense_val:.2f}")
    
    print()


def demo_rule_builder():
    """Demonstrate the gradient rule builder interface."""
    print("=" * 70)
    print("GRADIENT RULE BUILDER")
    print("=" * 70)
    
    engine = SoundChangeEngine()
    
    # Build complex gradient rule using fluent interface
    rule = (GradientRuleBuilder()
            .shift_feature("voice", 1.0, 0.7)         # Increase voicing
            .shift_feature("continuant", 0.5, 0.3)     # Increase continuancy (lenition)
            .shift_feature("strident", -0.2, 0.1)      # Reduce stridency
            .with_condition("consonantal", "+consonantal")  # Only consonants
            .with_probability(0.8)                     # 80% application rate
            .with_strength(0.6)                        # 60% strength
            .build("complex_lenition"))
    
    print(f"Created rule: {rule.name}")
    print(f"  Probability: {rule.probability}")
    print(f"  Strength: {rule.change_strength}")
    print(f"  Feature changes: {len(rule.feature_changes)}")
    
    # Test on consonants
    consonants = ['p', 'b', 't', 'd', 'k', 'g', 's', 'z']
    
    for grapheme in consonants:
        sound = Sound(grapheme=grapheme, feature_system='unified_distinctive')
        
        if rule.applies_to(sound, [], []):
            result = rule.apply_to(sound)
            voice_change = result.get_feature_value('voice') - sound.get_feature_value('voice')
            cont_change = result.get_feature_value('continuant') - sound.get_feature_value('continuant')
            
            print(f"  /{grapheme}/: voice Δ{voice_change:+.2f}, continuant Δ{cont_change:+.2f}")
    
    print()


def demo_predefined_rules():
    """Demonstrate predefined gradient rules."""
    print("=" * 70)
    print("PREDEFINED GRADIENT RULES")
    print("=" * 70)
    
    engine = SoundChangeEngine()
    
    # Test word with stops
    word = [
        Sound(grapheme='p', feature_system='unified_distinctive'),
        Sound(grapheme='a', feature_system='unified_distinctive'),
        Sound(grapheme='t', feature_system='unified_distinctive'),
        Sound(grapheme='a', feature_system='unified_distinctive'),
        Sound(grapheme='k', feature_system='unified_distinctive')
    ]
    
    print(f"Original: {''.join(s.grapheme() for s in word)}")
    
    # 1. Lenition rule
    lenition = create_lenition_rule(strength=0.4)
    result = engine.apply_rule(lenition, word)
    
    if result.changed:
        print(f"After lenition: continuant values increased")
        for i, (orig, new) in enumerate(zip(word, result.modified_sequence)):
            orig_cont = orig.get_feature_value('continuant')
            new_cont = new.get_feature_value('continuant')
            if abs(new_cont - orig_cont) > 0.01:
                print(f"  Position {i}: {orig_cont:.2f} → {new_cont:.2f}")
    
    # 2. Voicing assimilation  
    assimilation = create_voicing_assimilation_rule(strength=0.6)
    
    # Create word with voicing context: "adka"
    assim_word = [
        Sound(grapheme='a', feature_system='unified_distinctive'),
        Sound(grapheme='d', feature_system='unified_distinctive'),  # voiced
        Sound(grapheme='k', feature_system='unified_distinctive'),  # voiceless
        Sound(grapheme='a', feature_system='unified_distinctive')
    ]
    
    print(f"\nVoicing assimilation test: {''.join(s.grapheme() for s in assim_word)}")
    result = engine.apply_rule(assimilation, assim_word)
    
    if result.changed:
        print("Voicing values after assimilation:")
        for i, sound in enumerate(result.modified_sequence):
            voice_val = sound.get_feature_value('voice')
            print(f"  Position {i}: voice = {voice_val:.2f}")
    
    print()


def demo_probabilistic_simulation():
    """Demonstrate probabilistic sound change simulation."""
    print("=" * 70)
    print("PROBABILISTIC CHANGE SIMULATION")
    print("=" * 70)
    
    engine = SoundChangeEngine()
    
    # Create probabilistic rule
    rule = SoundChangeRule(
        name="variable_voicing",
        source_pattern="p",
        target_pattern="b",
        probability=0.3  # 30% chance of application
    )
    
    # Test on multiple words
    test_words = [
        [Sound(grapheme='p', feature_system='unified_distinctive'),
         Sound(grapheme='a', feature_system='unified_distinctive')],
        [Sound(grapheme='a', feature_system='unified_distinctive'),
         Sound(grapheme='p', feature_system='unified_distinctive')],
        [Sound(grapheme='p', feature_system='unified_distinctive'),
         Sound(grapheme='i', feature_system='unified_distinctive')]
    ]
    
    # Run multiple trials
    trials = 20
    application_counts = {i: 0 for i in range(len(test_words))}
    
    print(f"Testing probabilistic rule over {trials} trials:")
    
    for trial in range(trials):
        for i, word in enumerate(test_words):
            result = engine.apply_rule(rule, word)
            if result.changed:
                application_counts[i] += 1
    
    for i, count in application_counts.items():
        word_str = ''.join(s.grapheme() for s in test_words[i])
        rate = count / trials
        print(f"  Word '{word_str}': applied {count}/{trials} times ({rate:.1%})")
    
    print()


def demo_historical_sound_change():
    """Demonstrate modeling historical sound changes."""
    print("=" * 70)
    print("HISTORICAL SOUND CHANGE MODELING")
    print("=" * 70)
    
    engine = SoundChangeEngine()
    
    # Model Germanic consonant shift (simplified)
    # Proto-Indo-European → Proto-Germanic
    
    pie_word = [
        Sound(grapheme='p', feature_system='unified_distinctive'),  # PIE *p
        Sound(grapheme='a', feature_system='unified_distinctive'),
        Sound(grapheme='t', feature_system='unified_distinctive'),  # PIE *t
        Sound(grapheme='e', feature_system='unified_distinctive'),
        Sound(grapheme='r', feature_system='unified_distinctive')
    ]
    
    print(f"Proto-Indo-European: {''.join(s.grapheme() for s in pie_word)}")
    
    # Create rule set for Grimm's Law (simplified)
    grimm = RuleSet(name="grimms_law")
    
    # p t k → f θ x (voiceless stops → voiceless fricatives)
    grimm.add_rule(SoundChangeRule(name="p_to_f", source_pattern="p", target_pattern="f"))
    grimm.add_rule(SoundChangeRule(name="t_to_th", source_pattern="t", target_pattern="θ"))  
    grimm.add_rule(SoundChangeRule(name="k_to_x", source_pattern="k", target_pattern="x"))
    
    # Apply Grimm's Law
    simulation = engine.apply_rule_set(grimm, pie_word)
    
    print(f"After Grimm's Law: {''.join(s.grapheme() for s in simulation.final_sequence)}")
    print(f"Rules applied: {', '.join(simulation.rules_applied)}")
    print(f"Total changes: {simulation.total_changes}")
    
    # Show detailed trajectory
    trajectory = simulation.get_change_trajectory()
    print("\nChange trajectory:")
    for i, stage in enumerate(trajectory):
        stage_str = ''.join(s.grapheme() for s in stage)
        print(f"  Stage {i}: {stage_str}")
    
    print()


def demo_complex_rule_interactions():
    """Demonstrate complex rule interactions."""
    print("=" * 70)
    print("COMPLEX RULE INTERACTIONS")
    print("=" * 70)
    
    engine = SoundChangeEngine()
    
    # Test word: "pataka"
    word = [
        Sound(grapheme='p', feature_system='unified_distinctive'),
        Sound(grapheme='a', feature_system='unified_distinctive'),
        Sound(grapheme='t', feature_system='unified_distinctive'),
        Sound(grapheme='a', feature_system='unified_distinctive'),
        Sound(grapheme='k', feature_system='unified_distinctive'),
        Sound(grapheme='a', feature_system='unified_distinctive')
    ]
    
    print(f"Original: {''.join(s.grapheme() for s in word)}")
    
    # Create interacting rules
    rules = RuleSet(name="complex_changes")
    
    # 1. Lenition: stops → fricatives / V_V
    from alteruphono.phonology.sound_change.rules import EnvironmentalCondition
    lenition_env = EnvironmentalCondition(
        left_context="[sonorant=1.0]",
        right_context="[sonorant=1.0]"
    )
    
    rules.add_rule(SoundChangeRule(
        name="lenition_p", source_pattern="p", target_pattern="f", 
        environment=lenition_env
    ))
    rules.add_rule(SoundChangeRule(
        name="lenition_t", source_pattern="t", target_pattern="s",
        environment=lenition_env  
    ))
    rules.add_rule(SoundChangeRule(
        name="lenition_k", source_pattern="k", target_pattern="x",
        environment=lenition_env
    ))
    
    # 2. Fricative voicing: voiceless fricatives → voiced / V_V
    fricative_env = EnvironmentalCondition(
        left_context="[sonorant=1.0]",
        right_context="[sonorant=1.0]"
    )
    
    rules.add_rule(SoundChangeRule(
        name="fricative_voicing_f", source_pattern="f", target_pattern="v",
        environment=fricative_env
    ))
    rules.add_rule(SoundChangeRule(
        name="fricative_voicing_s", source_pattern="s", target_pattern="z", 
        environment=fricative_env
    ))
    
    # Apply with iteration to show feeding relationships
    rules.iterative = True
    rules.max_iterations = 5
    
    simulation = engine.apply_rule_set(rules, word)
    
    print(f"Final result: {''.join(s.grapheme() for s in simulation.final_sequence)}")
    print(f"Total iterations needed: {len([r for r in simulation.rule_applications if r.changed])}")
    
    # Show step-by-step changes
    print("\nStep-by-step changes:")
    current = word
    for i, result in enumerate(simulation.rule_applications):
        if result.changed:
            current = result.modified_sequence
            current_str = ''.join(s.grapheme() for s in current)
            print(f"  {result.rule_name}: {current_str}")
    
    print()


def demo_performance_stats():
    """Demonstrate engine statistics and performance monitoring."""
    print("=" * 70)
    print("ENGINE STATISTICS")
    print("=" * 70)
    
    engine = SoundChangeEngine()
    
    # Run several simulations to generate statistics
    test_words = [
        [Sound(grapheme=g, feature_system='unified_distinctive') for g in word]
        for word in ['pata', 'katu', 'sila', 'mano', 'weru']
    ]
    
    # Create test rule set
    rules = RuleSet(name="test_stats")
    rules.add_rule(SoundChangeRule(name="p_voicing", source_pattern="p", target_pattern="b"))
    rules.add_rule(SoundChangeRule(name="t_spirantization", source_pattern="t", target_pattern="θ"))
    rules.add_rule(SoundChangeRule(name="k_lenition", source_pattern="k", target_pattern="x"))
    
    # Run multiple simulations
    for word in test_words:
        engine.apply_rule_set(rules, word)
    
    # Get statistics
    stats = engine.get_statistics()
    
    print("Engine Performance Statistics:")
    print(f"  Total simulations: {stats['total_simulations']}")
    print(f"  Total changes: {stats['total_changes']}")
    print(f"  Average changes per simulation: {stats['average_changes_per_simulation']:.2f}")
    
    if stats['rule_usage_frequency']:
        print(f"  Most used rule: {stats['most_used_rule']}")
        
        print("\nRule usage frequency:")
        for rule_name, count in stats['rule_usage_frequency'].items():
            print(f"    {rule_name}: {count} times")
    
    print()


def main():
    """Run all demonstrations."""
    print("ALTERUPHONO SOUND CHANGE ENGINE DEMONSTRATION")
    print("=" * 70)
    print("This demo showcases the powerful sound change capabilities enabled")
    print("by the unified distinctive feature system with gradient changes,")
    print("probabilistic application, and complex environmental conditions.")
    print()
    
    # Run all demonstrations
    demo_basic_sound_changes()
    demo_environmental_conditions()
    demo_gradient_changes()
    demo_feature_shifts()
    demo_rule_builder()
    demo_predefined_rules()
    demo_probabilistic_simulation()
    demo_historical_sound_change()
    demo_complex_rule_interactions()
    demo_performance_stats()
    
    print("=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print()
    print("Key capabilities demonstrated:")
    print("✓ Categorical sound changes with environmental conditioning")
    print("✓ Gradient feature changes using scalar values")
    print("✓ Complex feature shift systems with correlations")
    print("✓ Probabilistic and variable rule application")
    print("✓ Rule interactions: feeding, bleeding, and ordering effects")
    print("✓ Historical sound change modeling (Grimm's Law example)")
    print("✓ Performance monitoring and statistics")
    print()
    print("The sound change engine provides unprecedented flexibility for")
    print("modeling both traditional and gradient phonological processes!")


if __name__ == "__main__":
    main()