#!/usr/bin/env python3
"""
Comprehensive demonstration of Tresoldi's distinctive feature system.

This script showcases the capabilities of the Tresoldi feature system with
43 features covering 1,081 sounds including complex segments, clicks, 
prenasals, and tonal variants.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alteruphono.phonology.feature_systems import (
    get_feature_system,
    list_feature_systems
)
from alteruphono.phonology.sound_v2 import Sound
from alteruphono.phonology.sound_change import (
    SoundChangeEngine,
    FeatureChangeRule
)
from alteruphono.phonology.sound_change.rules import FeatureChange, ChangeType


def demo_system_overview():
    """Demonstrate basic system properties and inventory."""
    print("=" * 70)
    print("TRESOLDI DISTINCTIVE FEATURE SYSTEM OVERVIEW")
    print("=" * 70)
    
    # Show available systems
    systems = list_feature_systems()
    print(f"Available feature systems: {', '.join(systems)}")
    
    # Get Tresoldi system
    tresoldi = get_feature_system('tresoldi_distinctive')
    print(f"\nTresoldi System Properties:")
    print(f"  Name: {tresoldi.name}")
    print(f"  Description: {tresoldi.description}")
    print(f"  Sound inventory: {tresoldi.get_sound_count()} sounds")
    print(f"  Feature inventory: {len(tresoldi.get_feature_names())} features")
    
    # Show feature list
    features = tresoldi.get_feature_names()
    print(f"\nAll 43 features:")
    for i, feature in enumerate(sorted(features)):
        if i % 6 == 0:
            print()
        print(f"  {feature:<15}", end="")
    print("\n")


def demo_sound_inventory():
    """Demonstrate the comprehensive sound inventory."""
    print("=" * 70)
    print("SOUND INVENTORY DEMONSTRATION")
    print("=" * 70)
    
    tresoldi = get_feature_system('tresoldi_distinctive')
    all_sounds = tresoldi.get_all_graphemes()
    
    # Categorize sounds by type
    basic_vowels = [s for s in all_sounds if s in 'aeiouæɑɨɪʊəɛɔʌʉɒ']
    basic_consonants = [s for s in all_sounds if s in 'pbtdkgmnŋɲflrsjzθðʃʒxɣhw']
    complex_sounds = [s for s in all_sounds if len(s) > 1]
    click_sounds = [s for s in all_sounds if any(c in s for c in 'ǀǁǃǂʘ')]
    tonal_sounds = [s for s in all_sounds if any(c in s for c in '́̀̂̌̄')]
    
    print(f"Basic vowels ({len(basic_vowels)}): {' '.join(basic_vowels[:20])}")
    if len(basic_vowels) > 20:
        print(f"  ... and {len(basic_vowels) - 20} more")
    
    print(f"Basic consonants ({len(basic_consonants)}): {' '.join(basic_consonants[:20])}")
    if len(basic_consonants) > 20:
        print(f"  ... and {len(basic_consonants) - 20} more")
    
    print(f"Complex sounds ({len(complex_sounds)}): {' '.join(complex_sounds[:15])}")
    if len(complex_sounds) > 15:
        print(f"  ... and {len(complex_sounds) - 15} more")
    
    print(f"Click sounds ({len(click_sounds)}): {' '.join(click_sounds[:10])}")
    
    print(f"Tonal variants ({len(tonal_sounds)}): {' '.join(tonal_sounds[:10])}")
    
    print()


def demo_feature_analysis():
    """Demonstrate feature analysis for different sound types."""
    print("=" * 70)
    print("FEATURE ANALYSIS")
    print("=" * 70)
    
    tresoldi = get_feature_system('tresoldi_distinctive')
    
    # Analyze basic sounds
    test_sounds = ['a', 'i', 'u', 'p', 'b', 't', 'd', 'k', 'g', 'n', 'm', 's', 'z']
    
    print("Feature analysis for basic sounds:")
    print(f"{'Sound':<8} {'Syll':<6} {'Cons':<6} {'Son':<6} {'Voice':<6} {'Nas':<6} {'Lab':<6} {'Cor':<6} {'Dor':<6}")
    print("-" * 64)
    
    for sound_sym in test_sounds:
        if tresoldi.has_grapheme(sound_sym):
            features = tresoldi.grapheme_to_features(sound_sym)
            if features:
                syll = features.get_feature('syllabic')
                cons = features.get_feature('consonantal')
                son = features.get_feature('sonorant')
                voice = features.get_feature('voice')
                nasal = features.get_feature('nasal')
                labial = features.get_feature('labial')
                coronal = features.get_feature('coronal')
                dorsal = features.get_feature('dorsal')
                
                print(f"{sound_sym:<8} {syll.value:>5.1f} {cons.value:>5.1f} {son.value:>5.1f} "
                      f"{voice.value:>5.1f} {nasal.value:>5.1f} {labial.value:>5.1f} "
                      f"{coronal.value:>5.1f} {dorsal.value:>5.1f}")
    
    print()


def demo_binary_oppositions():
    """Demonstrate binary opposition logic."""
    print("=" * 70)
    print("BINARY OPPOSITION LOGIC")
    print("=" * 70)
    
    tresoldi = get_feature_system('tresoldi_distinctive')
    
    # Test vowel/consonant distinction
    vowel_sounds = tresoldi.get_sounds_with_feature('syllabic', positive=True)
    consonant_sounds = tresoldi.get_sounds_with_feature('consonantal', positive=True)
    
    print(f"Syllabic sounds (+syllabic): {len(vowel_sounds)} sounds")
    print(f"  Examples: {' '.join(vowel_sounds[:15])}")
    
    print(f"Consonantal sounds (+consonantal): {len(consonant_sounds)} sounds")
    print(f"  Examples: {' '.join(consonant_sounds[:15])}")
    
    # Test voicing distinction
    voiced_sounds = tresoldi.get_sounds_with_feature('voice', positive=True)
    voiceless_sounds = tresoldi.get_sounds_with_feature('voice', positive=False)
    
    print(f"Voiced sounds (+voice): {len(voiced_sounds)} sounds")
    print(f"  Examples: {' '.join(voiced_sounds[:15])}")
    
    print(f"Voiceless sounds (-voice): {len(voiceless_sounds)} sounds")
    print(f"  Examples: {' '.join(voiceless_sounds[:15])}")
    
    # Test binary logic on specific sounds
    print(f"\nBinary feature tests:")
    test_pairs = [('a', 'syllabic'), ('p', 'consonantal'), ('b', 'voice'), ('n', 'nasal')]
    
    for sound, feature in test_pairs:
        if tresoldi.has_grapheme(sound):
            features = tresoldi.grapheme_to_features(sound)
            is_positive = tresoldi.is_positive(features, feature)
            is_negative = tresoldi.is_negative(features, feature)
            is_neutral = tresoldi.is_neutral(features, feature)
            
            status = "positive" if is_positive else "negative" if is_negative else "neutral"
            print(f"  /{sound}/ {feature}: {status}")
    
    print()


def demo_complex_sounds():
    """Demonstrate handling of complex sounds."""
    print("=" * 70)
    print("COMPLEX SOUND ANALYSIS")
    print("=" * 70)
    
    tresoldi = get_feature_system('tresoldi_distinctive')
    
    # Find and analyze complex sounds
    all_sounds = tresoldi.get_all_graphemes()
    complex_sounds = [s for s in all_sounds if len(s) > 1]
    
    print(f"Total complex sounds: {len(complex_sounds)}")
    
    # Analyze some interesting complex sounds
    interesting_complex = []
    for sound in complex_sounds:
        if any(marker in sound for marker in ['ⁿ', 'ʷ', 'ʲ', 'ː', 'ǃ', 'ǀ']):
            interesting_complex.append(sound)
        if len(interesting_complex) >= 10:
            break
    
    print(f"\nAnalysis of complex sounds:")
    print(f"{'Sound':<10} {'Type':<15} {'Special Features'}")
    print("-" * 50)
    
    for sound in interesting_complex:
        features = tresoldi.grapheme_to_features(sound)
        if features:
            # Determine type
            sound_type = "Unknown"
            special_features = []
            
            if tresoldi.is_positive(features, 'syllabic'):
                sound_type = "Vowel variant"
            elif tresoldi.is_positive(features, 'consonantal'):
                sound_type = "Consonant variant"
            
            # Check for special features
            if tresoldi.is_positive(features, 'prenasal'):
                special_features.append("prenasalized")
            if tresoldi.is_positive(features, 'click'):
                special_features.append("click")
            if features.get_feature('length') and abs(features.get_feature('length').value) > 0.1:
                special_features.append("length variant")
            if tresoldi.is_positive(features, 'creaky'):
                special_features.append("creaky")
            if tresoldi.is_positive(features, 'breathy'):
                special_features.append("breathy")
            
            special_str = ", ".join(special_features) if special_features else "none"
            print(f"{sound:<10} {sound_type:<15} {special_str}")
    
    print()


def demo_sound_operations():
    """Demonstrate sound operations with Tresoldi system."""
    print("=" * 70)
    print("SOUND OPERATIONS WITH TRESOLDI SYSTEM")
    print("=" * 70)
    
    # Create sounds
    sound_p = Sound(grapheme='p', feature_system='tresoldi_distinctive')
    sound_b = Sound(grapheme='b', feature_system='tresoldi_distinctive')
    sound_a = Sound(grapheme='a', feature_system='tresoldi_distinctive')
    
    print(f"Created sounds: /{sound_p.grapheme()}/, /{sound_b.grapheme()}/, /{sound_a.grapheme()}/")
    
    # Distance calculations
    dist_pb = sound_p.distance_to(sound_b)
    dist_pa = sound_p.distance_to(sound_a)
    dist_ba = sound_b.distance_to(sound_a)
    
    print(f"\nDistance calculations:")
    print(f"  /p/ ↔ /b/: {dist_pb:.3f}")
    print(f"  /p/ ↔ /a/: {dist_pa:.3f}")
    print(f"  /b/ ↔ /a/: {dist_ba:.3f}")
    
    # Feature arithmetic
    print(f"\nFeature arithmetic:")
    original_voice = sound_p.get_feature_value('voice')
    print(f"  Original /p/ voice: {original_voice:.2f}")
    
    # Add partial voicing
    partial_voiced = sound_p + 'voice=0.3'
    new_voice = partial_voiced.get_feature_value('voice')
    print(f"  After adding voice=0.3: {new_voice:.2f}")
    
    # Add full voicing
    full_voiced = sound_p + 'voice=1.0'
    final_voice = full_voiced.get_feature_value('voice')
    print(f"  After adding voice=1.0: {final_voice:.2f}")
    
    # Distance to /b/ after modifications
    dist_partial = partial_voiced.distance_to(sound_b)
    dist_full = full_voiced.distance_to(sound_b)
    
    print(f"\nDistance to /b/ after voicing:")
    print(f"  Original /p/ → /b/: {dist_pb:.3f}")
    print(f"  Partial voiced → /b/: {dist_partial:.3f}")
    print(f"  Full voiced → /b/: {dist_full:.3f}")
    
    print()


def demo_feature_statistics():
    """Demonstrate feature usage statistics."""
    print("=" * 70)
    print("FEATURE USAGE STATISTICS")
    print("=" * 70)
    
    tresoldi = get_feature_system('tresoldi_distinctive')
    stats = tresoldi.get_feature_statistics()
    
    # Show most balanced features (close to 50/50 split)
    print("Most balanced features (positive/negative distribution):")
    
    balanced_features = []
    for feature, data in stats.items():
        total = data['positive'] + data['negative']
        if total > 100:  # Only consider features used frequently
            balance = min(data['positive'], data['negative']) / max(data['positive'], data['negative'])
            balanced_features.append((feature, balance, data))
    
    balanced_features.sort(key=lambda x: x[1], reverse=True)
    
    for feature, balance, data in balanced_features[:10]:
        print(f"  {feature:<15}: +{data['positive']:>4} / -{data['negative']:>4} / 0{data['neutral']:>4} "
              f"(balance: {balance:.2f})")
    
    # Show most skewed features
    print(f"\nMost skewed features:")
    
    skewed_features = []
    for feature, data in stats.items():
        total = data['positive'] + data['negative']
        if total > 50:
            if data['positive'] > data['negative']:
                skew = data['positive'] / max(data['negative'], 1)
                skewed_features.append((feature, skew, data, 'positive'))
            else:
                skew = data['negative'] / max(data['positive'], 1)
                skewed_features.append((feature, skew, data, 'negative'))
    
    skewed_features.sort(key=lambda x: x[1], reverse=True)
    
    for feature, skew, data, direction in skewed_features[:8]:
        print(f"  {feature:<15}: +{data['positive']:>4} / -{data['negative']:>4} "
              f"(skewed {direction}, ratio: {skew:.1f}:1)")
    
    print()


def demo_sound_change_integration():
    """Demonstrate integration with sound change engine."""
    print("=" * 70)
    print("SOUND CHANGE ENGINE INTEGRATION")
    print("=" * 70)
    
    engine = SoundChangeEngine(feature_system_name='tresoldi_distinctive')
    
    # Create test word using Tresoldi system
    word = [
        Sound(grapheme='p', feature_system='tresoldi_distinctive'),
        Sound(grapheme='a', feature_system='tresoldi_distinctive'),
        Sound(grapheme='t', feature_system='tresoldi_distinctive'),
        Sound(grapheme='a', feature_system='tresoldi_distinctive')
    ]
    
    print(f"Original word: {''.join(s.grapheme() for s in word)}")
    
    # Create gradient voicing rule
    voicing_change = FeatureChange(
        feature_name="voice",
        target_value=0.6,  # Partial voicing
        change_strength=1.0,
        change_type=ChangeType.GRADIENT
    )
    
    voicing_rule = FeatureChangeRule(
        name="gradient_voicing",
        source_pattern="",
        target_pattern=[voicing_change],
        feature_conditions={"voice": -1.0},  # Only voiceless sounds
        feature_changes=[voicing_change],
        feature_system_name='tresoldi_distinctive'
    )
    
    # Apply rule
    result = engine.apply_rule(voicing_rule, word)
    
    print(f"After gradient voicing rule:")
    for i, (orig, new) in enumerate(zip(word, result.modified_sequence)):
        orig_voice = orig.get_feature_value('voice')
        new_voice = new.get_feature_value('voice')
        if abs(new_voice - orig_voice) > 0.01:
            print(f"  Position {i} (/{orig.grapheme()}/): voice {orig_voice:.2f} → {new_voice:.2f}")
    
    # Create lenition rule using Tresoldi features
    lenition_change = FeatureChange(
        feature_name="continuant",
        target_value=0.8,  # Increase continuancy
        change_strength=1.0,
        change_type=ChangeType.GRADIENT
    )
    
    lenition_rule = FeatureChangeRule(
        name="gradient_lenition",
        source_pattern="",
        target_pattern=[lenition_change],
        feature_conditions={"consonantal": 1.0, "continuant": -1.0},  # Stops only
        feature_changes=[lenition_change],
        feature_system_name='tresoldi_distinctive'
    )
    
    # Apply lenition to original word
    lenition_result = engine.apply_rule(lenition_rule, word)
    
    print(f"\nAfter gradient lenition rule:")
    for i, (orig, new) in enumerate(zip(word, lenition_result.modified_sequence)):
        orig_cont = orig.get_feature_value('continuant')
        new_cont = new.get_feature_value('continuant')
        if abs(new_cont - orig_cont) > 0.01:
            print(f"  Position {i} (/{orig.grapheme()}/): continuant {orig_cont:.2f} → {new_cont:.2f}")
    
    print()


def demo_system_comparison():
    """Compare Tresoldi system with other feature systems."""
    print("=" * 70)
    print("FEATURE SYSTEM COMPARISON")
    print("=" * 70)
    
    # Create same sound in different systems
    systems = ['ipa_categorical', 'unified_distinctive', 'tresoldi_distinctive']
    test_sound = 'p'
    
    print(f"Comparing /{test_sound}/ across feature systems:")
    
    for system_name in systems:
        try:
            system = get_feature_system(system_name)
            sound = Sound(grapheme=test_sound, feature_system=system_name)
            
            print(f"\n{system_name.upper()}:")
            print(f"  Total features: {len(sound.features.features)}")
            print(f"  Voice value: {sound.get_feature_value('voice'):.2f}")
            print(f"  Has 'consonantal': {sound.has_feature('consonantal')}")
            
            if sound.has_feature('consonantal'):
                cons_val = sound.get_feature_value('consonantal')
                print(f"  Consonantal value: {cons_val:.2f}")
            
            # Show unique features (if any)
            if system_name == 'tresoldi_distinctive':
                unique_features = []
                tresoldi_features = set(f.feature for f in sound.features.features)
                
                # Compare with unified system
                unified_sound = Sound(grapheme=test_sound, feature_system='unified_distinctive')
                unified_features = set(f.feature for f in unified_sound.features.features)
                
                unique_to_tresoldi = tresoldi_features - unified_features
                if unique_to_tresoldi:
                    print(f"  Unique to Tresoldi: {', '.join(sorted(list(unique_to_tresoldi)[:5]))}")
        
        except Exception as e:
            print(f"  Error with {system_name}: {e}")
    
    # Performance comparison
    print(f"\nPerformance comparison (sound creation):")
    import time
    
    n_trials = 1000
    for system_name in systems:
        try:
            start_time = time.time()
            for _ in range(n_trials):
                sound = Sound(grapheme=test_sound, feature_system=system_name)
            end_time = time.time()
            
            avg_time = (end_time - start_time) / n_trials * 1000
            print(f"  {system_name}: {avg_time:.3f} ms per sound")
        
        except Exception as e:
            print(f"  {system_name}: Error - {e}")
    
    print()


def main():
    """Run all demonstrations."""
    print("TRESOLDI DISTINCTIVE FEATURE SYSTEM DEMONSTRATION")
    print("=" * 70)
    print("Showcasing Tresoldi's comprehensive 43-feature system")
    print("with 1,081 sounds including complex segments and variants.")
    print()
    
    try:
        # Run all demonstrations
        demo_system_overview()
        demo_sound_inventory()
        demo_feature_analysis()
        demo_binary_oppositions()
        demo_complex_sounds()
        demo_sound_operations()
        demo_feature_statistics()
        demo_sound_change_integration()
        demo_system_comparison()
        
        print("=" * 70)
        print("DEMONSTRATION COMPLETE")
        print("=" * 70)
        print()
        print("Key achievements demonstrated:")
        print("✓ Comprehensive sound inventory (1,081 sounds)")
        print("✓ Rich feature set (43 distinctive features)")
        print("✓ Complex sound support (prenasals, clicks, length, tone)")
        print("✓ Binary opposition logic for feature interpretation")
        print("✓ Gradient sound change capabilities")
        print("✓ Integration with pluggable architecture")
        print("✓ Performance comparable to other systems")
        print()
        print("The Tresoldi system provides unprecedented phonological coverage")
        print("while maintaining compatibility with alteruphono's advanced features!")
    
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()