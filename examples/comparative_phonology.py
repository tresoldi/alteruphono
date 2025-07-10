#!/usr/bin/env python3
"""
Comparative Phonology Examples using AlteruPhono

This module demonstrates advanced comparative phonology techniques including:
- Indo-European sound law modeling
- Romance language evolution
- Germanic consonant shifts  
- Austronesian comparative reconstruction
- Sino-Tibetan tone development
- Cross-linguistic typological analysis

For use in historical linguistics research and teaching.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alteruphono.phonology.sound_change import (
    SoundChangeEngine, 
    SoundChangeRule, 
    FeatureChangeRule,
    RuleSet
)
from alteruphono.phonology.sound_change.rules import FeatureChange, ChangeType
from alteruphono.phonology.sound_change.environments import PhonologicalEnvironment
from alteruphono.phonology.sound_v2 import Sound
from alteruphono.phonology.feature_systems import get_feature_system, convert_between_systems

from collections import defaultdict
import pandas as pd
import numpy as np

def demo_indo_european_sound_laws():
    """
    Demonstrate major Indo-European sound laws including:
    - Grimm's Law (Germanic)
    - Grassmann's Law (Greek/Sanskrit)
    - Bartholomae's Law (Indo-Iranian)
    - Verner's Law (Germanic)
    """
    print("=" * 60)
    print("INDO-EUROPEAN SOUND LAW DEMONSTRATIONS")
    print("=" * 60)
    
    engine = SoundChangeEngine(feature_system_name='unified_distinctive')
    
    # 1. GRIMM'S LAW (Germanic Consonant Shift)
    print("\n1. GRIMM'S LAW (Proto-Indo-European → Proto-Germanic)")
    print("-" * 55)
    
    # Phase I: PIE voiceless stops → Germanic fricatives
    grimm_phase1 = [
        FeatureChangeRule(
            name="grimm_p_f",
            feature_conditions={"consonantal": 1.0, "voice": -1.0, "continuant": -1.0, "labial": 1.0},
            feature_changes=[FeatureChange(feature_name="continuant", target_value=1.0, change_type=ChangeType.CATEGORICAL)]
        ),
        FeatureChangeRule(
            name="grimm_t_th", 
            feature_conditions={"consonantal": 1.0, "voice": -1.0, "continuant": -1.0, "coronal": 1.0},
            feature_changes=[FeatureChange(feature_name="continuant", target_value=1.0, change_type=ChangeType.CATEGORICAL)]
        ),
        FeatureChangeRule(
            name="grimm_k_x",
            feature_conditions={"consonantal": 1.0, "voice": -1.0, "continuant": -1.0, "dorsal": 1.0},
            feature_changes=[FeatureChange(feature_name="continuant", target_value=1.0, change_type=ChangeType.CATEGORICAL)]
        )
    ]
    
    # Phase II: PIE voiced stops → Germanic voiceless stops
    grimm_phase2 = [
        FeatureChangeRule(
            name="grimm_voiced_devoicing",
            feature_conditions={"consonantal": 1.0, "voice": 1.0, "continuant": -1.0, "sonorant": -1.0},
            feature_changes=[FeatureChange(feature_name="voice", target_value=-1.0, change_type=ChangeType.CATEGORICAL)]
        )
    ]
    
    # Phase III: PIE voiced aspirates → Germanic voiced stops
    grimm_phase3 = [
        FeatureChangeRule(
            name="grimm_aspirate_deaspiration",
            feature_conditions={"consonantal": 1.0, "voice": 1.0, "spread": 1.0},
            feature_changes=[FeatureChange(feature_name="spread", target_value=-1.0, change_type=ChangeType.CATEGORICAL)]
        )
    ]
    
    grimms_law = RuleSet(rules=grimm_phase1 + grimm_phase2 + grimm_phase3, iterative=False)
    
    pie_words = [
        (['p', 'a', 't', 'e', 'r'], '*pater', 'father'),
        (['t', 'r', 'e', 'j', 'e', 's'], '*trejes', 'three'),
        (['k', 'o', 'r', 'd'], '*kord', 'heart'),
        (['b', 'r', 'a', 't', 'e', 'r'], '*bhráter', 'brother'),
        (['d', 'e', 'k', 'm'], '*dekm', 'ten'),
        (['g', 'e', 'n', 'o', 's'], '*génos', 'kin')
    ]
    
    for word_sounds, pie_form, meaning in pie_words:
        sounds = [Sound(s, 'unified_distinctive') for s in word_sounds]
        result = engine.apply_rule_set(grimms_law, sounds)
        
        pie_str = ' '.join(word_sounds)
        germanic_str = ' '.join([s.grapheme() for s in result.final_sequence])
        print(f"  {pie_form:12} → {germanic_str:12} '{meaning}'")
    
    # 2. GRASSMANN'S LAW (Deaspiration)
    print("\n2. GRASSMANN'S LAW (Greek/Sanskrit Deaspiration)")
    print("-" * 50)
    
    grassmann = FeatureChangeRule(
        name="grassmann_deaspiration",
        feature_conditions={"consonantal": 1.0, "spread": 1.0},  # Aspirated consonants
        feature_changes=[FeatureChange(feature_name="spread", target_value=-1.0, change_type=ChangeType.CATEGORICAL)],
        environment=PhonologicalEnvironment(
            # Simplified: deaspiration when another aspirate follows
            right_pattern="C[+spread]"  # This would need more sophisticated pattern matching
        )
    )
    
    print("  Grassmann's Law: First of two aspirates loses aspiration")
    print("  Example: *bheubh- → *bheub- (not fully implemented due to pattern complexity)")
    
    # 3. VERNER'S LAW (Germanic)
    print("\n3. VERNER'S LAW (Post-Grimm Germanic)")
    print("-" * 40)
    
    # Simplified Verner's Law: voiceless fricatives → voiced in specific environments
    verners_law = FeatureChangeRule(
        name="verners_voicing",
        feature_conditions={"consonantal": 1.0, "voice": -1.0, "continuant": 1.0},  # Voiceless fricatives
        feature_changes=[FeatureChange(feature_name="voice", target_value=1.0, change_type=ChangeType.CATEGORICAL)],
        # Note: Real Verner's Law depends on accent position, simplified here
    )
    
    verner_examples = [
        (['f', 'a', 'θ', 'e', 'r'], 'unaccented position'),
        (['b', 'r', 'o', 'θ', 'e', 'r'], 'unaccented position')
    ]
    
    for word_sounds, context in verner_examples:
        sounds = [Sound(s, 'unified_distinctive') for s in word_sounds]
        result = engine.apply_rule(verners_law, sounds)
        
        original = ' '.join(word_sounds)
        modified = ' '.join([s.grapheme() for s in result.modified_sequence])
        print(f"  {original:12} → {modified:12} ({context})")

def demo_romance_evolution():
    """
    Demonstrate Romance language evolution from Latin including:
    - Consonant lenition
    - Vowel changes
    - Palatalization
    - Loss of final consonants
    """
    print("\n\n" + "=" * 60)
    print("ROMANCE LANGUAGE EVOLUTION FROM LATIN")
    print("=" * 60)
    
    engine = SoundChangeEngine(feature_system_name='unified_distinctive')
    
    # LATIN TO SPANISH EVOLUTION
    print("\n1. LATIN → SPANISH SOUND CHANGES")
    print("-" * 40)
    
    # Spanish sound changes
    spanish_changes = [
        # Intervocalic voicing
        FeatureChangeRule(
            name="spanish_intervocalic_voicing",
            feature_conditions={"consonantal": 1.0, "voice": -1.0, "continuant": -1.0, "sonorant": -1.0},
            feature_changes=[FeatureChange(feature_name="voice", target_value=1.0, change_type=ChangeType.CATEGORICAL)],
            environment=PhonologicalEnvironment(left_pattern="V", right_pattern="V")
        ),
        
        # /f/ → /h/ (debuccalization)
        SoundChangeRule(
            name="spanish_f_to_h",
            source_pattern="f",
            target_pattern="h",
            environment="# _"  # Word-initial
        ),
        
        # Palatalization of /kt/ → /tʃ/
        SoundChangeRule(
            name="spanish_kt_palatalization", 
            source_pattern="k t",
            target_pattern="tʃ"
        ),
        
        # Loss of final consonants except /s/
        FeatureChangeRule(
            name="spanish_final_consonant_loss",
            feature_conditions={"consonantal": 1.0},
            feature_changes=[],  # Deletion would need special handling
            environment=PhonologicalEnvironment(right_pattern="#")
        )
    ]
    
    # LATIN TO FRENCH EVOLUTION  
    print("\n2. LATIN → FRENCH SOUND CHANGES")
    print("-" * 40)
    
    french_changes = [
        # Lenition: /p t k/ → /b d g/ → /β ð ɣ/ → loss
        FeatureChangeRule(
            name="french_lenition_stage1",
            feature_conditions={"consonantal": 1.0, "voice": -1.0, "continuant": -1.0},
            feature_changes=[FeatureChange(feature_name="voice", target_value=1.0, change_type=ChangeType.CATEGORICAL)],
            environment=PhonologicalEnvironment(left_pattern="V", right_pattern="V")
        ),
        
        FeatureChangeRule(
            name="french_lenition_stage2", 
            feature_conditions={"consonantal": 1.0, "voice": 1.0, "continuant": -1.0},
            feature_changes=[FeatureChange(feature_name="continuant", target_value=1.0, change_type=ChangeType.CATEGORICAL)],
            environment=PhonologicalEnvironment(left_pattern="V", right_pattern="V")
        ),
        
        # Palatalization before front vowels
        FeatureChangeRule(
            name="french_palatalization",
            feature_conditions={"consonantal": 1.0, "coronal": 1.0},
            feature_changes=[
                FeatureChange(feature_name="coronal", target_value=1.0, change_type=ChangeType.CATEGORICAL),
                FeatureChange(feature_name="continuant", target_value=0.5, change_type=ChangeType.GRADIENT)
            ],
            environment=PhonologicalEnvironment(right_pattern="[+syllabic,-back]")
        )
    ]
    
    # LATIN TO ITALIAN EVOLUTION
    print("\n3. LATIN → ITALIAN SOUND CHANGES")  
    print("-" * 40)
    
    italian_changes = [
        # Gemination preservation
        FeatureChangeRule(
            name="italian_gemination_preservation",
            feature_conditions={"consonantal": 1.0},
            feature_changes=[FeatureChange(feature_name="length", target_value=1.0, change_type=ChangeType.CATEGORICAL)]
            # This would need gemination detection
        ),
        
        # Intervocalic lenition (weaker than French)
        FeatureChangeRule(
            name="italian_mild_lenition",
            feature_conditions={"consonantal": 1.0, "voice": -1.0, "continuant": -1.0},
            feature_changes=[FeatureChange(feature_name="voice", target_value=0.5, change_type=ChangeType.GRADIENT)],
            environment=PhonologicalEnvironment(left_pattern="V", right_pattern="V")
        )
    ]
    
    # Test words
    latin_words = [
        (['v', 'i', 't', 'a'], 'VITA', 'life'),
        (['a', 'k', 'w', 'a'], 'AQUA', 'water'),  
        (['f', 'o', 'k', 'u', 's'], 'FOCUS', 'fire'),
        (['n', 'o', 'k', 't', 'e'], 'NOCTE', 'night'),
        (['l', 'a', 'k', 't', 'e'], 'LACTE', 'milk')
    ]
    
    for word_sounds, latin_form, meaning in latin_words:
        sounds = [Sound(s, 'unified_distinctive') for s in word_sounds]
        
        # Apply Spanish changes
        spanish_result = engine.apply_rule_set(RuleSet(spanish_changes[:2], iterative=False), sounds)
        spanish_form = ' '.join([s.grapheme() for s in spanish_result.final_sequence])
        
        # Apply French changes  
        french_result = engine.apply_rule_set(RuleSet(french_changes[:2], iterative=False), sounds)
        french_form = ' '.join([s.grapheme() for s in french_result.final_sequence])
        
        # Apply Italian changes
        italian_result = engine.apply_rule_set(RuleSet(italian_changes[:1], iterative=False), sounds)
        italian_form = ' '.join([s.grapheme() for s in italian_result.final_sequence])
        
        print(f"  {latin_form:8} → Sp: {spanish_form:12} Fr: {french_form:12} It: {italian_form:12} '{meaning}'")

def demo_germanic_consonant_shift():
    """
    Demonstrate the High German Consonant Shift (Second Germanic Consonant Shift).
    """
    print("\n\n" + "=" * 60)
    print("HIGH GERMAN CONSONANT SHIFT")
    print("=" * 60)
    
    engine = SoundChangeEngine(feature_system_name='unified_distinctive')
    
    print("\nProto-Germanic → Old High German")
    print("-" * 40)
    
    # High German Consonant Shift
    hgcs_rules = [
        # /p/ → /pf/ (geminate), /ff/ (intervocalic)
        FeatureChangeRule(
            name="hgcs_p_to_pf",
            feature_conditions={"consonantal": 1.0, "voice": -1.0, "continuant": -1.0, "labial": 1.0},
            feature_changes=[
                FeatureChange(feature_name="continuant", target_value=0.5, change_type=ChangeType.GRADIENT),  # Affrication
                FeatureChange(feature_name="strident", target_value=1.0, change_type=ChangeType.CATEGORICAL)
            ]
        ),
        
        # /t/ → /ts/ (geminate), /ss/ (intervocalic)  
        FeatureChangeRule(
            name="hgcs_t_to_ts",
            feature_conditions={"consonantal": 1.0, "voice": -1.0, "continuant": -1.0, "coronal": 1.0},
            feature_changes=[
                FeatureChange(feature_name="continuant", target_value=0.5, change_type=ChangeType.GRADIENT),
                FeatureChange(feature_name="strident", target_value=1.0, change_type=ChangeType.CATEGORICAL)
            ]
        ),
        
        # /k/ → /kx/ (geminate), /xx/ (intervocalic)
        FeatureChangeRule(
            name="hgcs_k_to_kx", 
            feature_conditions={"consonantal": 1.0, "voice": -1.0, "continuant": -1.0, "dorsal": 1.0},
            feature_changes=[
                FeatureChange(feature_name="continuant", target_value=0.8, change_type=ChangeType.GRADIENT)  # Fricativization
            ]
        ),
        
        # /d/ → /t/ (final devoicing already occurred)
        # /b/ → /p/ 
        # /g/ → /k/
        FeatureChangeRule(
            name="hgcs_voiced_to_voiceless",
            feature_conditions={"consonantal": 1.0, "voice": 1.0, "continuant": -1.0, "sonorant": -1.0},
            feature_changes=[FeatureChange(feature_name="voice", target_value=-1.0, change_type=ChangeType.CATEGORICAL)]
        )
    ]
    
    hgcs = RuleSet(rules=hgcs_rules, iterative=False)
    
    # Test words
    proto_germanic_words = [
        (['s', 'l', 'a', 'p', 'a', 'n'], '*slapan', 'sleep'),
        (['w', 'a', 't', 'e', 'r'], '*water', 'water'),
        (['m', 'a', 'k', 'o', 'n'], '*makon', 'make'),
        (['h', 'e', 'r', 't', 'o'], '*herto', 'heart'),
        (['a', 'p', 'u', 'l'], '*apul', 'apple')
    ]
    
    for word_sounds, pg_form, meaning in proto_germanic_words:
        sounds = [Sound(s, 'unified_distinctive') for s in word_sounds]
        result = engine.apply_rule_set(hgcs, sounds)
        
        pg_str = ' '.join(word_sounds)
        ohg_str = ' '.join([s.grapheme() for s in result.final_sequence])
        print(f"  {pg_form:12} → {ohg_str:12} '{meaning}'")
    
    print("\nNote: This shows phonetic tendencies. Actual OHG forms:")
    print("  *slapan → slafan, *water → wazzar, *makon → mahhon")

def demo_austronesian_reconstruction():
    """
    Demonstrate Austronesian comparative reconstruction techniques.
    """
    print("\n\n" + "=" * 60)
    print("AUSTRONESIAN COMPARATIVE RECONSTRUCTION")
    print("=" * 60)
    
    # Proto-Austronesian to daughter language correspondences
    print("\n1. SOUND CORRESPONDENCES")
    print("-" * 30)
    
    correspondences = {
        'Proto-AN': ['*p', '*t', '*k', '*q', '*s', '*h', '*l', '*r', '*m', '*n'],
        'Tagalog':  ['p',  't',  'k',  'ʔ',  's',  'h',  'l',  'r',  'm',  'n'],
        'Malay':    ['p',  't',  'k',  'k',  's',  'h',  'l',  'r',  'm',  'n'],  
        'Javanese': ['p',  't',  'k',  'k',  's',  'h',  'l',  'r',  'm',  'n'],
        'Hawaiian': ['p',  'k',  'ʔ',  'ʔ',  'h',  'h',  'l',  'l',  'm',  'n']
    }
    
    corr_df = pd.DataFrame(correspondences)
    print(corr_df.to_string(index=False))
    
    # Demonstrate sound changes
    engine = SoundChangeEngine(feature_system_name='unified_distinctive')
    
    print("\n2. SOUND CHANGE RULES")
    print("-" * 25)
    
    # Hawaiian changes from Proto-Austronesian
    hawaiian_changes = [
        # *t → k 
        SoundChangeRule(name="hawaiian_t_to_k", source_pattern="t", target_pattern="k"),
        
        # *k → ʔ
        SoundChangeRule(name="hawaiian_k_to_glottal", source_pattern="k", target_pattern="ʔ"),
        
        # *q → ʔ  
        SoundChangeRule(name="hawaiian_q_to_glottal", source_pattern="q", target_pattern="ʔ"),
        
        # *s → h
        SoundChangeRule(name="hawaiian_s_to_h", source_pattern="s", target_pattern="h"),
        
        # *r → l
        SoundChangeRule(name="hawaiian_r_to_l", source_pattern="r", target_pattern="l")
    ]
    
    hawaiian_evolution = RuleSet(rules=hawaiian_changes, iterative=False)
    
    # Test reconstructions
    pan_words = [
        (['t', 'a', 'l', 'u'], '*talu', 'three'),
        (['k', 'a', 'h', 'u'], '*kahu', 'wood'),  
        (['q', 'u', 't', 'a'], '*quta', 'we (incl)'),
        (['s', 'a', 'k', 'i'], '*saki', 'climb'),
        (['r', 'a', 'n', 'u', 'm'], '*ranum', 'water')
    ]
    
    print("\nProto-Austronesian → Hawaiian Evolution:")
    for word_sounds, pan_form, meaning in pan_words:
        sounds = [Sound(s, 'unified_distinctive') for s in word_sounds]
        result = engine.apply_rule_set(hawaiian_evolution, sounds)
        
        pan_str = ' '.join(word_sounds)
        hawaiian_str = ' '.join([s.grapheme() for s in result.final_sequence])
        print(f"  {pan_form:10} → {hawaiian_str:10} '{meaning}'")

def demo_tone_development():
    """
    Demonstrate tone development in Sino-Tibetan languages.
    """
    print("\n\n" + "=" * 60)  
    print("SINO-TIBETAN TONE DEVELOPMENT")
    print("=" * 60)
    
    print("\n1. CONSONANT-INDUCED TONOGENESIS")
    print("-" * 40)
    
    # Simplified model of tonogenesis
    # In reality, this involves complex prosodic features
    
    print("Proto-Sino-Tibetan → Chinese tone development:")
    print("  Voiced initials → low tone")
    print("  Voiceless initials → high tone")  
    print("  Aspirated initials → mid-rising tone")
    print("  Final glottal stop → falling tone")
    
    tonogenesis_examples = [
        ('*ba', 'bá', 'low tone', 'eight'),
        ('*pa', 'pā', 'high tone', 'eight'),
        ('*pʰa', 'pá', 'rising tone', 'fear'),
        ('*bakʔ', 'bàk', 'falling tone', 'white')
    ]
    
    print("\nExamples (simplified):")
    for pst, chinese, tone, meaning in tonogenesis_examples:
        print(f"  {pst:8} → {chinese:6} ({tone:12}) '{meaning}'")
    
    print("\n2. TONE SPLITTING AND MERGING")
    print("-" * 35)
    
    print("Historical tone changes often involve:")
    print("  - Tone splitting by vowel length")
    print("  - Tone merging in unstressed syllables") 
    print("  - Tone sandhi rules")
    print("  - Tonal minimal pairs creation")

def analyze_cross_linguistic_patterns():
    """
    Analyze cross-linguistic phonological patterns using the Tresoldi system.
    """
    print("\n\n" + "=" * 60)
    print("CROSS-LINGUISTIC PHONOLOGICAL ANALYSIS")
    print("=" * 60)
    
    tresoldi_system = get_feature_system('tresoldi_distinctive')
    
    print(f"\nTresoldi System Coverage:")
    print(f"  Total sounds: {tresoldi_system.get_sound_count()}")
    print(f"  Total features: {len(tresoldi_system.get_feature_names())}")
    
    # 1. ANALYZE PLACE OF ARTICULATION PATTERNS
    print("\n1. PLACE OF ARTICULATION UNIVERSALS")
    print("-" * 40)
    
    place_features = ['labial', 'coronal', 'dorsal', 'glottal']
    place_counts = {}
    
    for place in place_features:
        if place in tresoldi_system.get_feature_names():
            sounds_with_place = tresoldi_system.get_sounds_with_feature(place, positive=True)
            place_counts[place] = len(sounds_with_place)
    
    print("Place of articulation frequency:")
    for place, count in sorted(place_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / tresoldi_system.get_sound_count()) * 100
        print(f"  {place:10}: {count:4} sounds ({percentage:5.1f}%)")
    
    # Test universal: coronal > labial > dorsal > glottal
    hierarchy_holds = (place_counts.get('coronal', 0) >= place_counts.get('labial', 0) >= 
                      place_counts.get('dorsal', 0) >= place_counts.get('glottal', 0))
    print(f"\nPlace hierarchy (C>L>D>G): {'✓ Confirmed' if hierarchy_holds else '✗ Violated'}")
    
    # 2. ANALYZE RARE FEATURE DISTRIBUTIONS  
    print("\n2. RARE FEATURE ANALYSIS")
    print("-" * 30)
    
    rare_features = ['click', 'ejective', 'implosive', 'creaky', 'breathy', 'prenasal']
    rare_stats = {}
    
    for rare_feat in rare_features:
        if rare_feat in tresoldi_system.get_feature_names():
            rare_sounds = tresoldi_system.get_sounds_with_feature(rare_feat, positive=True)
            rare_stats[rare_feat] = len(rare_sounds)
    
    print("Rare feature distribution:")
    for feature, count in sorted(rare_stats.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            percentage = (count / tresoldi_system.get_sound_count()) * 100
            print(f"  {feature:12}: {count:3} sounds ({percentage:4.1f}%)")
    
    # 3. VOWEL SYSTEM ANALYSIS
    print("\n3. VOWEL SYSTEM PATTERNS")
    print("-" * 30)
    
    vowel_sounds = tresoldi_system.get_sounds_with_feature('syllabic', positive=True)
    print(f"Total vowels: {len(vowel_sounds)}")
    
    # Analyze vowel height distribution
    height_features = ['high', 'low']
    vowel_heights = defaultdict(int)
    
    for vowel_char in vowel_sounds[:50]:  # Sample first 50 vowels
        if tresoldi_system.has_grapheme(vowel_char):
            vowel = Sound(vowel_char, 'tresoldi_distinctive')
            high_val = vowel.get_feature_value('high')
            low_val = vowel.get_feature_value('low')
            
            if high_val > 0.5:
                vowel_heights['high'] += 1
            elif low_val > 0.5:
                vowel_heights['low'] += 1
            else:
                vowel_heights['mid'] += 1
    
    print("Vowel height distribution (sample):")
    for height, count in vowel_heights.items():
        print(f"  {height:6}: {count:3} vowels")

def demo_phonological_distance_metrics():
    """
    Demonstrate phonological distance calculations for linguistic classification.
    """
    print("\n\n" + "=" * 60)
    print("PHONOLOGICAL DISTANCE METRICS")
    print("=" * 60)
    
    # Define sample language inventories
    language_inventories = {
        'English': ['p', 'b', 't', 'd', 'k', 'g', 'f', 'v', 'θ', 'ð', 's', 'z', 'ʃ', 'ʒ', 'h', 'm', 'n', 'ŋ', 'l', 'r', 'w', 'j'],
        'Spanish': ['p', 'b', 't', 'd', 'k', 'g', 'f', 'β', 's', 'x', 'θ', 'm', 'n', 'ɲ', 'ŋ', 'l', 'ʎ', 'r', 'ɾ', 'w', 'j'],
        'French': ['p', 'b', 't', 'd', 'k', 'g', 'f', 'v', 's', 'z', 'ʃ', 'ʒ', 'ʁ', 'm', 'n', 'ɲ', 'ŋ', 'l', 'w', 'j'],
        'German': ['p', 'b', 't', 'd', 'k', 'g', 'f', 'v', 's', 'z', 'ʃ', 'ʒ', 'x', 'h', 'm', 'n', 'ŋ', 'l', 'ʁ', 'w', 'j'],
        'Mandarin': ['p', 'pʰ', 't', 'tʰ', 'k', 'kʰ', 'f', 's', 'ʂ', 'x', 'm', 'n', 'ŋ', 'l', 'w', 'j'],
        'Japanese': ['p', 'b', 't', 'd', 'k', 'g', 'f', 's', 'z', 'ʃ', 'ʒ', 'h', 'm', 'n', 'ɲ', 'ŋ', 'l', 'r', 'w', 'j']
    }
    
    print("\n1. INVENTORY-BASED DISTANCES")
    print("-" * 35)
    
    def calculate_inventory_distance(inv1, inv2, feature_system='tresoldi_distinctive'):
        """Calculate distance between two phonological inventories."""
        # Convert to sets for set operations
        set1 = set(inv1)
        set2 = set(inv2)
        
        # Jaccard distance: 1 - (intersection / union)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        jaccard_distance = 1 - (intersection / union) if union > 0 else 1
        
        # Feature-based distance for shared sounds
        feature_distance = 0
        shared_sounds = set1 & set2
        
        if shared_sounds:
            system = get_feature_system(feature_system)
            distances = []
            
            for sound_char in shared_sounds:
                if system.has_grapheme(sound_char):
                    sound1 = Sound(sound_char, feature_system)
                    sound2 = Sound(sound_char, feature_system)
                    distances.append(sound1.distance_to(sound2))  # Should be 0 for identical sounds
        
        return jaccard_distance
    
    # Calculate distance matrix
    languages = list(language_inventories.keys())
    n_langs = len(languages)
    distance_matrix = np.zeros((n_langs, n_langs))
    
    for i, lang1 in enumerate(languages):
        for j, lang2 in enumerate(languages):
            if i != j:
                distance = calculate_inventory_distance(
                    language_inventories[lang1],
                    language_inventories[lang2]
                )
                distance_matrix[i][j] = distance
    
    # Display distance matrix
    distance_df = pd.DataFrame(
        distance_matrix,
        index=languages,
        columns=languages
    )
    
    print("Phonological distance matrix (Jaccard distance):")
    print(distance_df.round(3))
    
    # Find most similar languages
    min_distance = float('inf')
    most_similar = None
    
    for i in range(n_langs):
        for j in range(i+1, n_langs):
            if distance_matrix[i][j] < min_distance:
                min_distance = distance_matrix[i][j]
                most_similar = (languages[i], languages[j])
    
    print(f"\nMost similar languages: {most_similar[0]} - {most_similar[1]} (distance: {min_distance:.3f})")
    
    # 2. FEATURE-BASED ANALYSIS
    print("\n2. FEATURE-BASED CLASSIFICATION")
    print("-" * 35)
    
    def analyze_inventory_features(inventory, feature_system='tresoldi_distinctive'):
        """Analyze feature distribution in inventory."""
        system = get_feature_system(feature_system)
        feature_stats = defaultdict(int)
        
        for sound_char in inventory:
            if system.has_grapheme(sound_char):
                sound = Sound(sound_char, feature_system)
                for feature_name in system.get_feature_names():
                    if sound.has_feature(feature_name):
                        feature_val = sound.get_feature_value(feature_name)
                        if abs(feature_val) > 0.5:  # Significant feature value
                            feature_stats[f"{feature_name}_{'+' if feature_val > 0 else '-'}"] += 1
        
        return feature_stats
    
    print("Feature analysis (Tresoldi system):")
    for lang, inventory in language_inventories.items():
        stats = analyze_inventory_features(inventory)
        # Show top 5 most common features
        top_features = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:5]
        feature_str = ', '.join([f"{feat}({count})" for feat, count in top_features])
        print(f"  {lang:10}: {feature_str}")

def main():
    """Run all comparative phonology demonstrations."""
    print("ALTERUPHONO COMPARATIVE PHONOLOGY DEMONSTRATIONS")
    print("=" * 65)
    print("Comprehensive examples for historical linguistics research")
    
    try:
        demo_indo_european_sound_laws()
        demo_romance_evolution()
        demo_germanic_consonant_shift()
        demo_austronesian_reconstruction()
        demo_tone_development()
        analyze_cross_linguistic_patterns()
        demo_phonological_distance_metrics()
        
        print("\n\n" + "=" * 65)
        print("DEMONSTRATIONS COMPLETED SUCCESSFULLY")
        print("=" * 65)
        print("\nThese examples demonstrate AlteruPhono's capabilities for:")
        print("• Historical sound law modeling")
        print("• Comparative reconstruction")
        print("• Language family classification")
        print("• Cross-linguistic phonological analysis")
        print("• Typological pattern detection")
        print("\nFor more advanced usage, see the full documentation.")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        print("Some features may require the full AlteruPhono installation.")

if __name__ == "__main__":
    main()