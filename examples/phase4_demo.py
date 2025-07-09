#!/usr/bin/env python3
"""
Demo script for Phase 4 features: suprasegmental and numeric features.

This script demonstrates the new capabilities added in Phase 4:
- Suprasegmental features (stress, tone, length)
- Numeric feature values and arithmetic
- Prosodic hierarchy support (syllables, feet, words)
- Prosodic boundary markers in rules
"""

from alteruphono.phonology import (
    Sound, 
    ProsodicBoundary, 
    BoundaryType,
    Syllable, 
    ProsodicWord,
    syllabify_sounds,
    parse_prosodic_string,
    is_suprasegmental_feature,
    is_numeric_feature,
    get_numeric_value
)
from alteruphono.parser import parse_atom, Rule


def demo_suprasegmental_features():
    """Demonstrate suprasegmental feature operations."""
    print("=" * 60)
    print("SUPRASEGMENTAL FEATURES DEMO")
    print("=" * 60)
    
    # Basic vowel
    vowel = Sound(grapheme='a')
    print(f"Base vowel: {vowel}")
    print(f"Features: {sorted(vowel.fvalues)}")
    print()
    
    # Add stress
    stressed = vowel + 'stress1'
    print(f"Primary stress: {stressed}")
    print(f"Has stress: {stressed.has_stress()}")
    print(f"Stress level: {stressed.get_stress_level()}")
    print()
    
    # Add tone
    toned = vowel + 'tone2'
    print(f"Mid tone: {toned}")
    print(f"Has tone: {toned.has_tone()}")
    print(f"Tone value: {toned.get_tone_value()}")
    print()
    
    # Complex suprasegmental features
    complex_vowel = vowel + 'stress1,tone3,f0_4,duration_2'
    print(f"Complex vowel: {complex_vowel}")
    print(f"All features: {sorted(complex_vowel.fvalues)}")
    print(f"Suprasegmental features: {sorted(complex_vowel.get_suprasegmental_features())}")
    print(f"Segmental features: {sorted(complex_vowel.get_segmental_features())}")
    print()


def demo_numeric_features():
    """Demonstrate numeric feature operations."""
    print("=" * 60)
    print("NUMERIC FEATURES DEMO")
    print("=" * 60)
    
    # Create sound with numeric features
    sound = Sound(grapheme='a') + 'f0_2,duration_1'
    print(f"Sound with numeric features: {sound}")
    print(f"f0 level: {get_numeric_value('f0_2')}")
    print(f"Duration level: {get_numeric_value('duration_1')}")
    print()
    
    # Increment features
    higher_pitch = sound.increment_feature('f0', 2)
    print(f"Higher pitch (+2): {higher_pitch}")
    print(f"Features: {sorted(higher_pitch.fvalues)}")
    print()
    
    # Decrement features
    lower_pitch = sound.decrement_feature('f0', 1)
    print(f"Lower pitch (-1): {lower_pitch}")
    print(f"Features: {sorted(lower_pitch.fvalues)}")
    print()
    
    # Feature identification
    print(f"'f0_3' is numeric: {is_numeric_feature('f0_3')}")
    print(f"'tone2' is numeric: {is_numeric_feature('tone2')}")
    print(f"'voiced' is numeric: {is_numeric_feature('voiced')}")
    print()
    
    print(f"'stress1' is suprasegmental: {is_suprasegmental_feature('stress1')}")
    print(f"'f0_3' is suprasegmental: {is_suprasegmental_feature('f0_3')}")
    print(f"'voiced' is suprasegmental: {is_suprasegmental_feature('voiced')}")
    print()


def demo_prosodic_hierarchy():
    """Demonstrate prosodic hierarchy operations."""
    print("=" * 60)
    print("PROSODIC HIERARCHY DEMO")
    print("=" * 60)
    
    # Create prosodic boundaries
    syll_boundary = ProsodicBoundary(BoundaryType.SYLLABLE)
    foot_boundary = ProsodicBoundary(BoundaryType.FOOT)
    word_boundary = ProsodicBoundary(BoundaryType.WORD)
    
    print(f"Syllable boundary: {syll_boundary}")
    print(f"Foot boundary: {foot_boundary}")
    print(f"Word boundary: {word_boundary}")
    print()
    
    # Create syllables
    p = Sound(grapheme='p')
    a = Sound(grapheme='a')
    t = Sound(grapheme='t')
    i = Sound(grapheme='i')
    
    # First syllable: "pa" (stressed)
    syll1 = Syllable(onset=[p], nucleus=[a], stress=1)
    print(f"Syllable 1: {syll1}")
    print(f"  - Is stressed: {syll1.is_stressed()}")
    print(f"  - Is heavy: {syll1.is_heavy()}")
    print()
    
    # Second syllable: "ti" (unstressed)  
    syll2 = Syllable(onset=[t], nucleus=[i], stress=0)
    print(f"Syllable 2: {syll2}")
    print(f"  - Is stressed: {syll2.is_stressed()}")
    print(f"  - Is heavy: {syll2.is_heavy()}")
    print()
    
    # Create prosodic word
    word = ProsodicWord([syll1, syll2])
    print(f"Prosodic word: {word}")
    print(f"Stress pattern: {word.get_stress_pattern()}")
    print(f"Main stress position: {word.get_main_stress_position()}")
    print()
    
    # Change stress pattern
    word.assign_stress("01")  # Iambic pattern
    print(f"After iambic assignment: {word}")
    print(f"New stress pattern: {word.get_stress_pattern()}")
    print(f"New main stress position: {word.get_main_stress_position()}")
    print()


def demo_syllabification():
    """Demonstrate automatic syllabification."""
    print("=" * 60)
    print("SYLLABIFICATION DEMO")
    print("=" * 60)
    
    # Create sound sequence: "pata"
    sounds = [
        Sound(grapheme='p'),
        Sound(grapheme='a'),
        Sound(grapheme='t'),
        Sound(grapheme='a')
    ]
    
    print(f"Input sounds: {[str(s) for s in sounds]}")
    
    # Syllabify
    syllables = syllabify_sounds(sounds)
    print(f"Number of syllables: {len(syllables)}")
    
    for i, syll in enumerate(syllables):
        print(f"  Syllable {i+1}: {syll}")
        print(f"    - Onset: {[str(s) for s in syll.onset]}")
        print(f"    - Nucleus: {[str(s) for s in syll.nucleus]}")
        print(f"    - Coda: {[str(s) for s in syll.coda]}")
    print()


def demo_prosodic_parsing():
    """Demonstrate prosodic string parsing."""
    print("=" * 60)
    print("PROSODIC PARSING DEMO")
    print("=" * 60)
    
    # Parse prosodic string
    prosodic_string = "# p a σ t a σ k o #"
    print(f"Input: {prosodic_string}")
    
    result = parse_prosodic_string(prosodic_string)
    print(f"Parsed elements:")
    
    for i, element in enumerate(result):
        element_type = type(element).__name__
        print(f"  {i}: {element} ({element_type})")
    print()


def demo_parser_integration():
    """Demonstrate integration with the rule parser."""
    print("=" * 60)
    print("PARSER INTEGRATION DEMO")
    print("=" * 60)
    
    # Test prosodic boundary parsing
    tokens = ['σ', 'Ft', 'φ', 'U', '#']
    
    for token_str in tokens:
        token = parse_atom(token_str)
        print(f"'{token_str}' -> {token} ({type(token).__name__})")
    print()
    
    # Example rule with prosodic context
    rule_str = "V > V[+stress] / # _ σ"
    print(f"Example rule: {rule_str}")
    print("This rule would add stress to vowels at word-initial position before syllable boundary")
    print()


def demo_feature_arithmetic():
    """Demonstrate feature arithmetic with suprasegmental features."""
    print("=" * 60)
    print("FEATURE ARITHMETIC DEMO")
    print("=" * 60)
    
    # Start with consonant
    consonant = Sound(grapheme='p')
    print(f"Base consonant: {consonant}")
    print(f"Features: {sorted(consonant.fvalues)}")
    print()
    
    # Voice it
    voiced = consonant + 'voiced'
    print(f"After voicing: {voiced}")
    print(f"Features: {sorted(voiced.fvalues)}")
    print()
    
    # Make it fricative
    fricative = voiced + 'fricative'
    print(f"After making fricative: {fricative}")
    print(f"Features: {sorted(fricative.fvalues)}")
    print()
    
    # Add suprasegmental features (unusual but possible)
    with_prosody = fricative + 'f0_3,duration_2'
    print(f"With prosodic features: {with_prosody}")
    print(f"All features: {sorted(with_prosody.fvalues)}")
    print(f"Segmental only: {sorted(with_prosody.get_segmental_features())}")
    print(f"Suprasegmental only: {sorted(with_prosody.get_suprasegmental_features())}")
    print()


def main():
    """Run all demos."""
    print("ALTERUPHONO PHASE 4 FEATURE DEMONSTRATION")
    print("Suprasegmental Features, Numeric Values, and Prosodic Hierarchy")
    print()
    
    demo_suprasegmental_features()
    demo_numeric_features()
    demo_prosodic_hierarchy()
    demo_syllabification()
    demo_prosodic_parsing()
    demo_parser_integration()
    demo_feature_arithmetic()
    
    print("=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("Phase 4 features successfully implemented!")
    print()
    print("Key new capabilities:")
    print("- Stress levels (stress1, stress2, unstressed)")
    print("- Tone values (tone1-5, rising, falling, level)")
    print("- Numeric features (f0_N, duration_N)")
    print("- Prosodic boundaries (σ, Ft, φ, U, #)")
    print("- Syllable structure (onset, nucleus, coda)")
    print("- Prosodic words and feet")
    print("- Automatic syllabification")
    print("- Feature arithmetic for all feature types")


if __name__ == "__main__":
    main()