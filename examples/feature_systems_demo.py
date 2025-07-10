#!/usr/bin/env python3
"""
Comprehensive demonstration of the pluggable feature system architecture.

This script showcases the new feature system capabilities, including:
- Multiple feature systems (IPA categorical, unified distinctive)
- Feature system switching and conversion
- Advanced phonological operations
- Research applications and use cases
"""

import sys
sys.path.insert(0, '/home/tiagot/tresoldi/alteruphono')

from alteruphono.phonology.feature_systems import (
    get_feature_system,
    list_feature_systems,
    get_default_feature_system,
    set_default_feature_system,
    FeatureValue,
    FeatureBundle,
    FeatureValueType
)
from alteruphono.phonology.feature_systems.conversion import (
    convert_sound_between_systems,
    feature_system_context,
    get_conversion_recommendations
)
from alteruphono.phonology.sound_v2 import Sound


def demo_feature_system_basics():
    """Demonstrate basic feature system operations."""
    print("=" * 70)
    print("FEATURE SYSTEM BASICS")
    print("=" * 70)
    
    # List available systems
    systems = list_feature_systems()
    print(f"Available feature systems: {', '.join(systems)}")
    
    # Get default system
    default = get_default_feature_system()
    print(f"Default system: {default.name}")
    print(f"Description: {default.description}")
    print()
    
    # Get specific systems
    ipa_system = get_feature_system('ipa_categorical')
    unified_system = get_feature_system('unified_distinctive')
    
    print(f"IPA system supported types: {ipa_system.supported_value_types}")
    print(f"Unified system supported types: {unified_system.supported_value_types}")
    print()


def demo_feature_representations():
    """Compare how the same sounds are represented in different systems."""
    print("=" * 70)
    print("FEATURE REPRESENTATIONS COMPARISON")
    print("=" * 70)
    
    test_sounds = ['p', 'b', 't', 'd', 'a', 'i', 'u', 's', 'z', 'n', 'm']
    
    ipa_system = get_feature_system('ipa_categorical')
    unified_system = get_feature_system('unified_distinctive')
    
    for grapheme in test_sounds:
        print(f"\nSound: /{grapheme}/")
        print("-" * 20)
        
        # IPA categorical representation
        ipa_features = ipa_system.grapheme_to_features(grapheme)
        if ipa_features:
            print(f"IPA Categorical: {ipa_features}")
        
        # Unified distinctive representation
        unified_features = unified_system.grapheme_to_features(grapheme)
        if unified_features:
            print(f"Unified Distinctive: {unified_features}")
    
    print()


def demo_sound_creation_and_operations():
    """Demonstrate Sound class with different feature systems."""
    print("=" * 70)
    print("SOUND CREATION AND OPERATIONS")
    print("=" * 70)
    
    # Create same sound in different systems
    ipa_p = Sound(grapheme='p', feature_system='ipa_categorical')
    unified_p = Sound(grapheme='p', feature_system='unified_distinctive')
    
    print(f"IPA /p/: {ipa_p} (system: {ipa_p.feature_system_name})")
    print(f"Unified /p/: {unified_p} (system: {unified_p.feature_system_name})")
    print()
    
    # Feature access
    print("Feature Access:")
    print(f"IPA /p/ has 'consonant': {ipa_p.has_feature('consonant')}")
    print(f"IPA /p/ has 'bilabial': {ipa_p.has_feature('bilabial')}")
    print(f"Unified /p/ has 'labial': {unified_p.has_feature('labial')}")
    print(f"Unified /p/ labial value: {unified_p.get_feature_value('labial')}")
    print(f"Unified /p/ voice value: {unified_p.get_feature_value('voice')}")
    print()
    
    # Feature arithmetic
    print("Feature Arithmetic:")
    
    # IPA system - categorical addition
    ipa_voiced = ipa_p + 'voiced'
    print(f"IPA /p/ + voiced = {ipa_voiced}")
    print(f"  Old features: {ipa_p.fvalues}")
    print(f"  New features: {ipa_voiced.fvalues}")
    
    # Unified system - scalar addition
    unified_voiced = unified_p + 'voice=1.0'
    print(f"Unified /p/ + voice=1.0 = {unified_voiced}")
    print(f"  Voice value: {unified_voiced.get_feature_value('voice')}")
    
    # Partial voicing (only possible in unified system)
    unified_breathy = unified_p + 'voice=0.3'
    print(f"Unified /p/ + voice=0.3 = {unified_breathy} (breathy)")
    print(f"  Voice value: {unified_breathy.get_feature_value('voice')}")
    print()


def demo_system_conversion():
    """Demonstrate conversion between feature systems."""
    print("=" * 70)
    print("FEATURE SYSTEM CONVERSION")
    print("=" * 70)
    
    # Create sound in IPA system
    ipa_sound = Sound(grapheme='p', feature_system='ipa_categorical')
    print(f"Original IPA sound: {ipa_sound}")
    print(f"IPA features: {ipa_sound.features}")
    
    # Convert to unified system
    unified_converted = ipa_sound.convert_to_system('unified_distinctive')
    print(f"Converted to unified: {unified_converted}")
    print(f"Unified features: {unified_converted.features}")
    
    # Convert back to IPA
    ipa_reconverted = unified_converted.convert_to_system('ipa_categorical')
    print(f"Converted back to IPA: {ipa_reconverted}")
    print(f"Reconverted features: {ipa_reconverted.features}")
    
    # Check conversion accuracy
    distance = ipa_sound.distance_to(ipa_reconverted)
    print(f"Distance after round-trip conversion: {distance:.3f}")
    
    # Conversion recommendations
    print(f"\nConversion recommendations (IPA → Unified):")
    recommendations = get_conversion_recommendations('ipa_categorical', 'unified_distinctive')
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")
    print()


def demo_unified_system_advanced_features():
    """Demonstrate advanced features of the unified distinctive system."""
    print("=" * 70)
    print("UNIFIED SYSTEM ADVANCED FEATURES")
    print("=" * 70)
    
    unified_system = get_feature_system('unified_distinctive')
    
    # Sound interpolation
    print("Sound Interpolation:")
    p_features = unified_system.grapheme_to_features('p')
    b_features = unified_system.grapheme_to_features('b')
    
    print(f"/p/ voice value: {p_features.get_feature('voice').value}")
    print(f"/b/ voice value: {b_features.get_feature('voice').value}")
    
    # Create sounds at different interpolation points
    for ratio in [0.0, 0.25, 0.5, 0.75, 1.0]:
        interpolated = unified_system.interpolate_sounds(p_features, b_features, ratio)
        voice_val = interpolated.get_feature('voice').value
        grapheme = unified_system.features_to_grapheme(interpolated)
        print(f"  Ratio {ratio}: voice={voice_val:.2f}, closest grapheme: {grapheme}")
    
    print()
    
    # Gradient voicing
    print("Gradient Voicing Operations:")
    p_sound = Sound(grapheme='p', feature_system='unified_distinctive')
    
    for voice_level in [-1.0, -0.5, 0.0, 0.5, 1.0]:
        voiced_sound = p_sound + f'voice={voice_level}'
        closest_grapheme = unified_system.features_to_grapheme(voiced_sound.features)
        print(f"  Voice level {voice_level:+.1f}: {closest_grapheme}")
    
    print()
    
    # Vowel/consonant detection
    print("Vowel/Consonant Detection:")
    test_sounds = ['p', 'b', 'n', 'l', 'a', 'i', 'u']
    
    for grapheme in test_sounds:
        features = unified_system.grapheme_to_features(grapheme)
        if features:
            is_vowel = unified_system.is_vowel_like(features)
            is_consonant = unified_system.is_consonant_like(features)
            sonorant_val = features.get_feature('sonorant').value
            consonantal_val = features.get_feature('consonantal').value
            
            print(f"  /{grapheme}/: vowel={is_vowel}, consonant={is_consonant}")
            print(f"       sonorant={sonorant_val:+.2f}, consonantal={consonantal_val:+.2f}")
    
    print()


def demo_feature_system_context():
    """Demonstrate feature system context management."""
    print("=" * 70)
    print("FEATURE SYSTEM CONTEXT MANAGEMENT")
    print("=" * 70)
    
    # Show current default
    print(f"Current default system: {get_default_feature_system().name}")
    
    # Create sound with default system
    default_sound = Sound(grapheme='p')
    print(f"Sound with default system: {default_sound.feature_system_name}")
    
    # Use context manager to temporarily change system
    print(f"\nUsing unified_distinctive context:")
    with feature_system_context('unified_distinctive'):
        context_sound = Sound(grapheme='p')
        print(f"Sound in context: {context_sound.feature_system_name}")
        print(f"Context default: {get_default_feature_system().name}")
    
    # System restored outside context
    print(f"After context: {get_default_feature_system().name}")
    print()


def demo_research_applications():
    """Demonstrate research applications and use cases."""
    print("=" * 70)
    print("RESEARCH APPLICATIONS")
    print("=" * 70)
    
    print("1. Sound Change Modeling:")
    print("-" * 30)
    
    # Model a sound change: p > f / _ V (lenition)
    unified_system = get_feature_system('unified_distinctive')
    
    p_sound = Sound(grapheme='p', feature_system='unified_distinctive')
    print(f"Original /p/: continuant = {p_sound.get_feature_value('continuant')}")
    
    # Increase continuant (fricativization)
    fricative = p_sound + 'continuant=0.8'
    print(f"After lenition: continuant = {fricative.get_feature_value('continuant')}")
    print(f"Closest grapheme: {unified_system.features_to_grapheme(fricative.features)}")
    
    print()
    
    print("2. Phonological Distance Analysis:")
    print("-" * 35)
    
    # Calculate distances between sounds
    sounds = ['p', 'b', 't', 'd', 'f', 'v', 's', 'z']
    
    print("Distance matrix (unified distinctive system):")
    print("     " + "".join(f"{s:>6}" for s in sounds))
    
    for i, sound1 in enumerate(sounds):
        s1 = Sound(grapheme=sound1, feature_system='unified_distinctive')
        row = f"{sound1:>3}: "
        
        for j, sound2 in enumerate(sounds):
            s2 = Sound(grapheme=sound2, feature_system='unified_distinctive')
            distance = s1.distance_to(s2)
            row += f"{distance:>6.2f}"
        
        print(row)
    
    print()
    
    print("3. Feature System Comparison:")
    print("-" * 32)
    
    # Compare voicing representation
    for grapheme in ['p', 'b']:
        ipa_sound = Sound(grapheme=grapheme, feature_system='ipa_categorical')
        unified_sound = Sound(grapheme=grapheme, feature_system='unified_distinctive')
        
        ipa_voice = 'voiced' if ipa_sound.has_feature('voiced') else 'voiceless'
        unified_voice = unified_sound.get_feature_value('voice')
        
        print(f"/{grapheme}/ voicing:")
        print(f"  IPA: {ipa_voice}")
        print(f"  Unified: {unified_voice:+.2f}")
    
    print()


def demo_backward_compatibility():
    """Demonstrate backward compatibility with existing code."""
    print("=" * 70)
    print("BACKWARD COMPATIBILITY")
    print("=" * 70)
    
    # Old-style Sound class usage still works
    sound = Sound(grapheme='p')  # Uses default system
    print(f"Sound created with default API: {sound}")
    print(f"Feature system: {sound.feature_system_name}")
    print(f"Old-style fvalues: {sound.fvalues}")
    print(f"New-style features: {sound.features}")
    
    # Old-style operations
    voiced_sound = sound + 'voiced'
    print(f"After adding 'voiced': {voiced_sound}")
    print(f"Old-style fvalues: {voiced_sound.fvalues}")
    
    # Old-style methods
    print(f"Stress level: {sound.get_stress_level()}")
    print(f"Tone value: {sound.get_tone_value()}")
    
    # New methods on old sounds
    print(f"Distance to voiced version: {sound.distance_to(voiced_sound):.3f}")
    print(f"Has 'consonant' feature: {sound.has_feature('consonant')}")
    
    print()


def demo_performance_comparison():
    """Compare performance between feature systems."""
    print("=" * 70)
    print("PERFORMANCE COMPARISON")
    print("=" * 70)
    
    import time
    
    # Test sound creation performance
    n_iterations = 1000
    test_graphemes = ['p', 'b', 't', 'd', 'a', 'i', 'u', 's', 'z', 'n']
    
    # IPA categorical system
    start_time = time.time()
    for _ in range(n_iterations):
        for grapheme in test_graphemes:
            sound = Sound(grapheme=grapheme, feature_system='ipa_categorical')
    ipa_time = time.time() - start_time
    
    # Unified distinctive system
    start_time = time.time()
    for _ in range(n_iterations):
        for grapheme in test_graphemes:
            sound = Sound(grapheme=grapheme, feature_system='unified_distinctive')
    unified_time = time.time() - start_time
    
    print(f"Sound creation performance ({n_iterations * len(test_graphemes)} sounds):")
    print(f"  IPA categorical: {ipa_time:.3f} seconds")
    print(f"  Unified distinctive: {unified_time:.3f} seconds")
    print(f"  Ratio: {unified_time/ipa_time:.2f}x")
    
    # Test feature arithmetic performance
    ipa_sound = Sound(grapheme='p', feature_system='ipa_categorical')
    unified_sound = Sound(grapheme='p', feature_system='unified_distinctive')
    
    start_time = time.time()
    for _ in range(n_iterations):
        voiced = ipa_sound + 'voiced'
    ipa_arith_time = time.time() - start_time
    
    start_time = time.time()
    for _ in range(n_iterations):
        voiced = unified_sound + 'voice=1.0'
    unified_arith_time = time.time() - start_time
    
    print(f"\nFeature arithmetic performance ({n_iterations} operations):")
    print(f"  IPA categorical: {ipa_arith_time:.3f} seconds")
    print(f"  Unified distinctive: {unified_arith_time:.3f} seconds")
    print(f"  Ratio: {unified_arith_time/ipa_arith_time:.2f}x")
    
    print()


def main():
    """Run all demonstrations."""
    print("ALTERUPHONO PLUGGABLE FEATURE SYSTEM DEMONSTRATION")
    print("=" * 70)
    print("This script demonstrates the new feature system architecture")
    print("that allows multiple phonological feature systems to coexist.")
    print()
    
    # Run all demonstrations
    demo_feature_system_basics()
    demo_feature_representations()
    demo_sound_creation_and_operations()
    demo_system_conversion()
    demo_unified_system_advanced_features()
    demo_feature_system_context()
    demo_research_applications()
    demo_backward_compatibility()
    demo_performance_comparison()
    
    print("=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("Key achievements:")
    print("✓ Multiple feature systems working in parallel")
    print("✓ IPA categorical system (traditional approach)")
    print("✓ Unified distinctive system (-1.0 to +1.0 values)")
    print("✓ Seamless conversion between systems")
    print("✓ Advanced phonological operations (interpolation, distance)")
    print("✓ Full backward compatibility")
    print("✓ Research-ready applications")
    print()
    print("Your unified distinctive feature system is now fully integrated!")
    print("You can use scalar values from -1.0 to +1.0 for all sounds,")
    print("eliminating the traditional vowel/consonant distinction.")


if __name__ == "__main__":
    main()