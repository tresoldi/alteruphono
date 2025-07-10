# Sound Change Modeling Tutorial

This tutorial provides a comprehensive guide to modeling phonological sound changes using AlteruPhono, from basic categorical rules to advanced gradient processes and complex rule interactions.

## Table of Contents

1. [Introduction to Sound Change](#introduction-to-sound-change)
2. [Basic Rule Syntax](#basic-rule-syntax)
3. [Categorical Sound Changes](#categorical-sound-changes)
4. [Feature-Based Rules](#feature-based-rules)
5. [Environmental Conditioning](#environmental-conditioning)
6. [Gradient Sound Changes](#gradient-sound-changes)
7. [Rule Ordering and Interaction](#rule-ordering-and-interaction)
8. [Historical Case Studies](#historical-case-studies)
9. [Advanced Techniques](#advanced-techniques)
10. [Best Practices](#best-practices)

## Introduction to Sound Change

Sound change is the fundamental mechanism of language evolution. AlteruPhono models sound changes as **rules** that transform phonological representations, supporting both:

- **Categorical changes**: Traditional discrete sound substitutions
- **Gradient changes**: Continuous phonological processes with partial application

### Types of Sound Change

```python
from alteruphono.phonology.sound_change import (
    SoundChangeEngine, 
    SoundChangeRule, 
    FeatureChangeRule,
    RuleSet
)
from alteruphono.phonology.sound_change.rules import FeatureChange, ChangeType
from alteruphono.phonology.sound_v2 import Sound

# Initialize engine
engine = SoundChangeEngine(feature_system_name='unified_distinctive')
```

#### **1. Segment Substitution**
```python
# p > f / # _ (word-initial p becomes f)
p_to_f = SoundChangeRule(
    name="initial_p_fricativization",
    source_pattern="p",
    target_pattern="f",
    environment="# _"
)

word = [Sound('#', 'unified_distinctive'), Sound('p', 'unified_distinctive'), 
        Sound('a', 'unified_distinctive'), Sound('t', 'unified_distinctive')]
result = engine.apply_rule(p_to_f, word)
print("Before:", [s.grapheme() for s in word])
print("After:", [s.grapheme() for s in result.modified_sequence])
```

#### **2. Feature-Based Changes**
```python
# Voicing assimilation: voiceless obstruents become voiced
voicing_assimilation = FeatureChangeRule(
    name="voicing_assimilation",
    feature_conditions={"voice": -1.0, "sonorant": -1.0},  # Voiceless obstruents
    feature_changes=[
        FeatureChange(feature_name="voice", target_value=1.0, change_type=ChangeType.CATEGORICAL)
    ]
)
```

#### **3. Gradient Processes**
```python
# Progressive lenition with partial application
lenition = FeatureChangeRule(
    name="progressive_lenition",
    feature_conditions={"consonantal": 1.0, "continuant": -1.0},
    feature_changes=[
        FeatureChange(
            feature_name="continuant",
            target_value=0.6,  # Partial continuancy
            change_type=ChangeType.GRADIENT,
            change_strength=0.4  # Gradual application
        )
    ]
)
```

## Basic Rule Syntax

### Traditional Notation

AlteruPhono supports the standard linguistic notation for sound changes:

```
A > B / C _ D
```

Where:
- **A**: Source (what changes)
- **B**: Target (what it becomes)  
- **C**: Left context (preceding environment)
- **D**: Right context (following environment)
- **_**: Focus position (where the change occurs)

### Implementation Examples

```python
import alteruphono

# Simple substitution
result1 = alteruphono.forward("# p a t e r #", "p > b")
print("p > b:", result1)  # ['#', 'b', 'a', 't', 'e', 'r', '#']

# Context-dependent change  
result2 = alteruphono.forward("# p a t a p #", "p > b / _ a")
print("p > b / _ a:", result2)  # ['#', 'b', 'a', 't', 'a', 'b', '#']

# Word boundary conditioning
result3 = alteruphono.forward("# a p t o s #", "p > f / # _")  
print("p > f / # _:", result3)  # No change (p not word-initial)
```

### Advanced Syntax Features

#### **Sound Classes**
```python
# Use natural sound classes
result = alteruphono.forward("# p a t i k a #", "C > Ø / _ V")  # Delete consonants before vowels
print("C deletion:", result)

# Vowel changes
result = alteruphono.forward("# p a t a #", "V > V[+high] / _ #")  # Raise final vowels
print("Final raising:", result)
```

#### **Feature Bundles**
```python
# Feature-based patterns
result = alteruphono.forward("# k a t a #", "[+dorsal] > [+coronal] / _ V")
print("Dorsals to coronals:", result)
```

## Categorical Sound Changes

### Simple Substitutions

#### **Unconditioned Changes**
```python
def test_unconditioned_change():
    """Test sound change without environmental conditioning."""
    
    # Rhotacism: all /s/ become /r/
    rhotacism = SoundChangeRule(
        name="rhotacism", 
        source_pattern="s",
        target_pattern="r"
    )
    
    test_words = [
        ['m', 'a', 's', 'a'],      # masa > mara
        ['s', 'a', 'l', 's', 'a'], # salsa > ralra  
        ['k', 'a', 's', 't', 'o']  # kasto > karto
    ]
    
    for word in test_words:
        sounds = [Sound(s, 'unified_distinctive') for s in word]
        result = engine.apply_rule(rhotacism, sounds)
        
        original = ' '.join([s.grapheme() for s in sounds])
        changed = ' '.join([s.grapheme() for s in result.modified_sequence])
        print(f"Rhotacism: {original} > {changed}")

test_unconditioned_change()
```

#### **Multiple Segment Changes**
```python
def test_cluster_simplification():
    """Test consonant cluster simplification."""
    
    # Cluster reduction: pt > t
    cluster_reduction = SoundChangeRule(
        name="pt_cluster_reduction",
        source_pattern="p t",
        target_pattern="t"
    )
    
    test_cases = [
        ['a', 'p', 't', 'o'],      # apto > ato
        ['k', 'a', 'p', 't', 'a'], # kapta > kata
        ['p', 't', 'a', 'k', 'a']  # ptaka > taka
    ]
    
    for word in test_cases:
        sounds = [Sound(s, 'unified_distinctive') for s in word]
        result = engine.apply_rule(cluster_reduction, sounds)
        
        original = ' '.join([s.grapheme() for s in sounds])
        changed = ' '.join([s.grapheme() for s in result.modified_sequence])
        print(f"Cluster reduction: {original} > {changed}")

test_cluster_simplification()
```

### Conditioned Changes

#### **Positional Conditioning**
```python
def test_positional_changes():
    """Test position-dependent sound changes."""
    
    # Final devoicing: voiced obstruents devoice word-finally
    final_devoicing = SoundChangeRule(
        name="final_devoicing",
        source_pattern="[+voice,-sonorant]",
        target_pattern="[-voice]",
        environment="_ #"
    )
    
    # Initial strengthening: fricatives become stops initially
    initial_strengthening = SoundChangeRule(
        name="initial_strengthening", 
        source_pattern="[+continuant,-sonorant]",
        target_pattern="[-continuant]",
        environment="# _"
    )
    
    test_words = [
        ['h', 'u', 'n', 'd'],      # Final /d/ devoices
        ['f', 'a', 't', 'a'],      # Initial /f/ strengthens
        ['z', 'a', 'g', 'a']       # Both rules apply
    ]
    
    for word in test_words:
        sounds = [Sound(s, 'unified_distinctive') for s in word]
        
        # Apply final devoicing
        result1 = engine.apply_rule(final_devoicing, sounds)
        # Apply initial strengthening  
        result2 = engine.apply_rule(initial_strengthening, result1.modified_sequence)
        
        original = ' '.join([s.grapheme() for s in sounds])
        final = ' '.join([s.grapheme() for s in result2.modified_sequence])
        print(f"Positional changes: {original} > {final}")

test_positional_changes()
```

#### **Vocalic Conditioning**
```python
def test_vocalic_conditioning():
    """Test vowel-conditioned consonant changes."""
    
    # Palatalization before front vowels
    palatalization = SoundChangeRule(
        name="palatalization",
        source_pattern="[+coronal,-continuant]",  # t, d
        target_pattern="[+coronal,+continuant]",  # s, z
        environment="_ [+syllabic,-back]"         # Before front vowels
    )
    
    test_words = [
        ['k', 'a', 't', 'i'],      # kati > kasi (t before i)
        ['d', 'e', 'n', 't', 'e'], # dente > dense (t before e)
        ['t', 'a', 't', 'a']       # tata > tata (no change before a)
    ]
    
    for word in test_words:
        sounds = [Sound(s, 'unified_distinctive') for s in word]
        result = engine.apply_rule(palatalization, sounds)
        
        original = ' '.join([s.grapheme() for s in sounds])
        changed = ' '.join([s.grapheme() for s in result.modified_sequence])
        print(f"Palatalization: {original} > {changed}")

test_vocalic_conditioning()
```

## Feature-Based Rules

### Natural Class Targeting

#### **Obstruent Voicing**
```python
def model_intervocalic_voicing():
    """Model voicing of obstruents between vowels."""
    
    voicing_rule = FeatureChangeRule(
        name="intervocalic_voicing",
        feature_conditions={
            "consonantal": 1.0,
            "voice": -1.0,      # Voiceless  
            "sonorant": -1.0    # Obstruent
        },
        feature_changes=[
            FeatureChange(
                feature_name="voice",
                target_value=1.0,  # Become voiced
                change_type=ChangeType.CATEGORICAL
            )
        ],
        environment=PhonologicalEnvironment(
            left_pattern="V",   # Vowel before
            right_pattern="V"   # Vowel after
        )
    )
    
    test_words = [
        ['a', 'p', 'a'],      # apa > aba
        ['o', 't', 'o'],      # oto > odo  
        ['i', 'k', 'a'],      # ika > iga
        ['p', 'a', 't'],      # pat > pat (no change, not intervocalic)
    ]
    
    from alteruphono.phonology.sound_change.environments import PhonologicalEnvironment
    
    for word in test_words:
        sounds = [Sound(s, 'unified_distinctive') for s in word]
        result = engine.apply_rule(voicing_rule, sounds)
        
        original = ' '.join([s.grapheme() for s in sounds])
        changed = ' '.join([s.grapheme() for s in result.modified_sequence])
        changed_any = result.changed
        print(f"Intervocalic voicing: {original} > {changed} ({'changed' if changed_any else 'no change'})")

model_intervocalic_voicing()
```

#### **Vowel Harmony**
```python
def model_vowel_harmony():
    """Model vowel harmony based on backness features."""
    
    # Back harmony: unspecified vowels become [+back] after [+back] vowels
    back_harmony = FeatureChangeRule(
        name="back_harmony",
        feature_conditions={
            "syllabic": 1.0,     # Vowels only
            "back": 0.0          # Unspecified backness
        },
        feature_changes=[
            FeatureChange(
                feature_name="back",
                target_value=1.0,   # Become [+back]
                change_type=ChangeType.CATEGORICAL
            )
        ]
        # Note: Full harmony implementation requires iterative application
    )
    
    # Example words showing harmony potential
    harmony_words = [
        ['k', 'a', 'l', 'ə'],  # kalə > kalo (ə harmonizes with a)
        ['t', 'u', 'k', 'ə'],  # tukə > tuku (ə harmonizes with u)
        ['p', 'i', 't', 'ə']   # pitə > pitə (ə doesn't harmonize with front i)
    ]
    
    for word in harmony_words:
        sounds = [Sound(s, 'unified_distinctive') for s in word]
        result = engine.apply_rule(back_harmony, sounds)
        
        original = ' '.join([s.grapheme() for s in sounds])
        changed = ' '.join([s.grapheme() for s in result.modified_sequence])
        print(f"Back harmony: {original} > {changed}")

model_vowel_harmony()
```

### Complex Feature Interactions

#### **Chain Shifts**
```python
def model_chain_shift():
    """Model complex vowel chain shift."""
    
    # Great Vowel Shift-like chain
    # Step 1: [+high] vowels diphthongize
    high_diphthongization = FeatureChangeRule(
        name="high_diphthongization",
        feature_conditions={
            "syllabic": 1.0,
            "high": 1.0
        },
        feature_changes=[
            FeatureChange(feature_name="diphthong", target_value=1.0, change_type=ChangeType.CATEGORICAL)
        ]
    )
    
    # Step 2: [+mid] vowels raise to [+high]  
    mid_raising = FeatureChangeRule(
        name="mid_raising",
        feature_conditions={
            "syllabic": 1.0,
            "high": -1.0,
            "low": -1.0    # Mid vowels
        },
        feature_changes=[
            FeatureChange(feature_name="high", target_value=1.0, change_type=ChangeType.CATEGORICAL),
            FeatureChange(feature_name="low", target_value=-1.0, change_type=ChangeType.CATEGORICAL)
        ]
    )
    
    # Step 3: [+low] vowels raise to [-low]
    low_raising = FeatureChangeRule(
        name="low_raising", 
        feature_conditions={
            "syllabic": 1.0,
            "low": 1.0
        },
        feature_changes=[
            FeatureChange(feature_name="low", target_value=-1.0, change_type=ChangeType.CATEGORICAL),
            FeatureChange(feature_name="high", target_value=-1.0, change_type=ChangeType.CATEGORICAL)
        ]
    )
    
    # Create rule set for ordered application
    chain_shift = RuleSet(
        rules=[high_diphthongization, mid_raising, low_raising],
        iterative=False  # Apply each rule once in order
    )
    
    vowel_words = [
        ['b', 'i', 't'],      # bit: i diphthongizes
        ['b', 'e', 't'],      # bet: e raises to i
        ['b', 'a', 't']       # bat: a raises to e
    ]
    
    for word in vowel_words:
        sounds = [Sound(s, 'unified_distinctive') for s in word]
        result = engine.apply_rule_set(chain_shift, sounds)
        
        original = ' '.join([s.grapheme() for s in sounds])
        final = ' '.join([s.grapheme() for s in result.final_sequence])
        print(f"Chain shift: {original} > {final}")

model_chain_shift()
```

## Environmental Conditioning

### Phonological Environments

#### **Syllable Structure Conditioning**
```python
from alteruphono.phonology.sound_change.environments import PhonologicalEnvironment

def test_syllable_conditioning():
    """Test syllable position-dependent changes."""
    
    # Coda devoicing: voiced obstruents devoice in syllable codas
    coda_devoicing = FeatureChangeRule(
        name="coda_devoicing",
        feature_conditions={"voice": 1.0, "sonorant": -1.0},  # Voiced obstruents
        feature_changes=[
            FeatureChange(feature_name="voice", target_value=-1.0, change_type=ChangeType.CATEGORICAL)
        ],
        environment=PhonologicalEnvironment(
            right_pattern=["#", "C"],  # Word boundary or consonant (coda position)
            position="coda"
        )
    )
    
    # Onset strengthening: fricatives become stops in onsets
    onset_strengthening = FeatureChangeRule(
        name="onset_strengthening",
        feature_conditions={"continuant": 1.0, "sonorant": -1.0},  # Fricatives
        feature_changes=[
            FeatureChange(feature_name="continuant", target_value=-1.0, change_type=ChangeType.CATEGORICAL)
        ],
        environment=PhonologicalEnvironment(
            position="onset"
        )
    )
    
    syllable_words = [
        ['s', 'a', 'g', 'a'],      # saga: s strengthens, g unchanged (intervocalic)
        ['a', 'g', '#'],           # ag#: g devoices in coda
        ['f', 'a', 't', 'a']       # fata: f strengthens in onset
    ]
    
    for word in syllable_words:
        sounds = [Sound(s, 'unified_distinctive') for s in word if s != '#']
        
        # Apply coda devoicing
        result1 = engine.apply_rule(coda_devoicing, sounds)
        # Apply onset strengthening
        result2 = engine.apply_rule(onset_strengthening, result1.modified_sequence)
        
        original = ' '.join([s.grapheme() for s in sounds])
        final = ' '.join([s.grapheme() for s in result2.modified_sequence])
        print(f"Syllable conditioning: {original} > {final}")

test_syllable_conditioning()
```

#### **Stress Conditioning**
```python
def test_stress_conditioning():
    """Test stress-dependent vowel changes."""
    
    # Vowel reduction in unstressed syllables
    vowel_reduction = FeatureChangeRule(
        name="vowel_reduction",
        feature_conditions={"syllabic": 1.0},  # All vowels
        feature_changes=[
            FeatureChange(feature_name="high", target_value=0.0, change_type=ChangeType.CATEGORICAL),
            FeatureChange(feature_name="low", target_value=0.0, change_type=ChangeType.CATEGORICAL),
            FeatureChange(feature_name="back", target_value=0.0, change_type=ChangeType.CATEGORICAL)
        ],
        environment=PhonologicalEnvironment(
            stress_pattern="unstressed"
        )
    )
    
    # Note: This is a simplified example. Full stress conditioning 
    # requires prosodic structure implementation
    
    stress_words = [
        ['ˈk', 'a', 't', 'ə'],     # Primary stress on first syllable
        ['k', 'əˈt', 'a', 'r']     # Primary stress on second syllable
    ]
    
    for word in stress_words:
        # This would need proper stress marking implementation
        print(f"Stress conditioning example: {' '.join(word)}")

test_stress_conditioning()
```

### Complex Environmental Patterns

#### **Multiple Trigger Environments**
```python
def test_multiple_triggers():
    """Test changes triggered by multiple environments."""
    
    # Lenition in multiple weak positions
    lenition_environments = [
        PhonologicalEnvironment(left_pattern="V", right_pattern="V"),  # Intervocalic
        PhonologicalEnvironment(right_pattern="#"),                   # Word-final
        PhonologicalEnvironment(left_pattern="V", right_pattern="L")  # Before liquids
    ]
    
    # Note: This would require enhanced environment handling
    # For now, demonstrate the concept with simpler rules
    
    intervocalic_lenition = FeatureChangeRule(
        name="intervocalic_lenition",
        feature_conditions={"consonantal": 1.0, "continuant": -1.0},
        feature_changes=[
            FeatureChange(feature_name="continuant", target_value=1.0, change_type=ChangeType.CATEGORICAL)
        ],
        environment=PhonologicalEnvironment(left_pattern="V", right_pattern="V")
    )
    
    test_words = [
        ['a', 'p', 'a'],      # apa > afa (intervocalic)
        ['a', 'p', 'r', 'a'], # apra > afra (before liquid)
        ['a', 'p']            # ap > ap (no change, not in weak position)
    ]
    
    for word in test_words:
        sounds = [Sound(s, 'unified_distinctive') for s in word]
        result = engine.apply_rule(intervocalic_lenition, sounds)
        
        original = ' '.join([s.grapheme() for s in sounds])
        changed = ' '.join([s.grapheme() for s in result.modified_sequence])
        print(f"Lenition: {original} > {changed}")

test_multiple_triggers()
```

## Gradient Sound Changes

### Continuous Feature Values

#### **Progressive Palatalization**
```python
def model_gradient_palatalization():
    """Model gradual palatalization as a continuous process."""
    
    # Stage 1: Initial palatalization (20% progress)
    initial_palatalization = FeatureChangeRule(
        name="palatalization_stage1",
        feature_conditions={"coronal": 1.0, "continuant": -1.0},  # Coronal stops
        feature_changes=[
            FeatureChange(
                feature_name="coronal",
                target_value=0.8,  # Slightly more coronal
                change_type=ChangeType.GRADIENT,
                change_strength=0.2
            )
        ],
        environment=PhonologicalEnvironment(right_pattern="[+syllabic,-back]")  # Before front vowels
    )
    
    # Stage 2: Advanced palatalization (50% progress)
    advanced_palatalization = FeatureChangeRule(
        name="palatalization_stage2", 
        feature_conditions={"coronal": 0.8},  # Previously palatalized sounds
        feature_changes=[
            FeatureChange(
                feature_name="coronal",
                target_value=1.0,
                change_type=ChangeType.GRADIENT,
                change_strength=0.5
            ),
            FeatureChange(
                feature_name="continuant",
                target_value=0.3,  # Partial frication
                change_type=ChangeType.GRADIENT,
                change_strength=0.3
            )
        ]
    )
    
    # Stage 3: Complete palatalization (affrication)
    complete_palatalization = FeatureChangeRule(
        name="palatalization_stage3",
        feature_conditions={"coronal": 1.0, "continuant": 0.3},
        feature_changes=[
            FeatureChange(
                feature_name="continuant", 
                target_value=1.0,  # Complete frication
                change_type=ChangeType.GRADIENT,
                change_strength=0.7
            )
        ]
    )
    
    palatalization_chain = RuleSet(
        rules=[initial_palatalization, advanced_palatalization, complete_palatalization],
        iterative=True  # Allow multiple applications
    )
    
    test_words = [
        ['t', 'i'],           # ti undergoes palatalization
        ['t', 'a'],           # ta does not (not before front vowel)
        ['d', 'e']            # de undergoes palatalization
    ]
    
    for word in test_words:
        sounds = [Sound(s, 'unified_distinctive') for s in word]
        result = engine.apply_rule_set(palatalization_chain, sounds)
        
        original = ' '.join([s.grapheme() for s in sounds])
        final = ' '.join([s.grapheme() for s in result.final_sequence])
        
        # Show gradient values
        if len(result.final_sequence) > 0:
            first_consonant = result.final_sequence[0]
            coronal_val = first_consonant.get_feature_value('coronal')
            continuant_val = first_consonant.get_feature_value('continuant')
            print(f"Palatalization: {original} > {final} (coronal={coronal_val:.2f}, cont={continuant_val:.2f})")

model_gradient_palatalization()
```

#### **Vowel Lowering**
```python
def model_gradient_lowering():
    """Model gradual vowel lowering over time."""
    
    gradual_lowering = FeatureChangeRule(
        name="gradual_lowering",
        feature_conditions={"syllabic": 1.0, "high": 1.0},  # High vowels
        feature_changes=[
            FeatureChange(
                feature_name="high",
                target_value=0.6,  # Partial lowering
                change_type=ChangeType.GRADIENT,
                change_strength=0.4
            ),
            FeatureChange(
                feature_name="low",
                target_value=0.2,  # Slight opening
                change_type=ChangeType.GRADIENT,
                change_strength=0.3
            )
        ]
    )
    
    vowel_words = [
        ['p', 'i', 't'],      # pit: i lowers partially
        ['p', 'u', 't'],      # put: u lowers partially
        ['p', 'a', 't']       # pat: a unchanged (not high)
    ]
    
    for word in vowel_words:
        sounds = [Sound(s, 'unified_distinctive') for s in word]
        result = engine.apply_rule(gradual_lowering, sounds)
        
        original = ' '.join([s.grapheme() for s in sounds])
        changed = ' '.join([s.grapheme() for s in result.modified_sequence])
        
        # Show vowel height values
        vowel_index = 1  # Second sound is vowel
        if len(result.modified_sequence) > vowel_index:
            vowel = result.modified_sequence[vowel_index]
            high_val = vowel.get_feature_value('high')
            low_val = vowel.get_feature_value('low')
            print(f"Lowering: {original} > {changed} (high={high_val:.2f}, low={low_val:.2f})")

model_gradient_lowering()
```

### Variable Rule Application

#### **Probabilistic Changes**
```python
def model_variable_application():
    """Model variable rule application with different strengths."""
    
    # Weak lenition (30% application strength)
    weak_lenition = FeatureChangeRule(
        name="weak_lenition",
        feature_conditions={"consonantal": 1.0, "continuant": -1.0},
        feature_changes=[
            FeatureChange(
                feature_name="continuant",
                target_value=0.4,  # Partial continuancy
                change_type=ChangeType.GRADIENT,
                change_strength=0.3  # Low application rate
            )
        ]
    )
    
    # Strong lenition (80% application strength)
    strong_lenition = FeatureChangeRule(
        name="strong_lenition",
        feature_conditions={"consonantal": 1.0, "continuant": -1.0},
        feature_changes=[
            FeatureChange(
                feature_name="continuant",
                target_value=0.8,  # More continuant
                change_type=ChangeType.GRADIENT,
                change_strength=0.8  # High application rate
            )
        ]
    )
    
    test_words = [
        ['p', 'a', 't', 'a'],
        ['k', 'a', 's', 'a']
    ]
    
    for word in test_words:
        sounds = [Sound(s, 'unified_distinctive') for s in word]
        
        # Apply weak lenition
        weak_result = engine.apply_rule(weak_lenition, sounds)
        # Apply strong lenition  
        strong_result = engine.apply_rule(strong_lenition, sounds)
        
        original = ' '.join([s.grapheme() for s in sounds])
        weak_final = ' '.join([s.grapheme() for s in weak_result.modified_sequence])
        strong_final = ' '.join([s.grapheme() for s in strong_result.modified_sequence])
        
        print(f"Variable lenition:")
        print(f"  Original: {original}")
        print(f"  Weak: {weak_final}")
        print(f"  Strong: {strong_final}")

model_variable_application()
```

## Rule Ordering and Interaction

### Rule Feeding and Bleeding

#### **Feeding Order**
```python
def test_feeding_order():
    """Test feeding relationship between rules."""
    
    # Rule A: t > s / _ i (palatalization)
    palatalization = SoundChangeRule(
        name="palatalization",
        source_pattern="t",
        target_pattern="s",
        environment="_ i"
    )
    
    # Rule B: s > h / V _ V (intervocalic weakening)
    intervocalic_weakening = SoundChangeRule(
        name="intervocalic_weakening",
        source_pattern="s", 
        target_pattern="h",
        environment="V _ V"
    )
    
    # Feeding order: A feeds B (t > s > h in VtiV)
    feeding_rules = RuleSet(
        rules=[palatalization, intervocalic_weakening],
        iterative=False
    )
    
    test_word = ['a', 't', 'i', 'a']  # atia > asia > ahia
    sounds = [Sound(s, 'unified_distinctive') for s in test_word]
    
    result = engine.apply_rule_set(feeding_rules, sounds)
    
    original = ' '.join([s.grapheme() for s in sounds])
    final = ' '.join([s.grapheme() for s in result.final_sequence])
    print(f"Feeding order: {original} > {final}")
    
    # Show intermediate steps
    step1 = engine.apply_rule(palatalization, sounds)
    intermediate = ' '.join([s.grapheme() for s in step1.modified_sequence])
    print(f"  Step 1 (palatalization): {original} > {intermediate}")
    print(f"  Step 2 (weakening): {intermediate} > {final}")

test_feeding_order()
```

#### **Bleeding Order**
```python
def test_bleeding_order():
    """Test bleeding relationship between rules."""
    
    # Rule A: t > Ø / V _ V (intervocalic deletion)
    intervocalic_deletion = SoundChangeRule(
        name="intervocalic_deletion",
        source_pattern="t",
        target_pattern="",  # Deletion
        environment="V _ V"
    )
    
    # Rule B: t > s / _ i (palatalization)  
    palatalization = SoundChangeRule(
        name="palatalization",
        source_pattern="t",
        target_pattern="s",
        environment="_ i"
    )
    
    # Bleeding order: A bleeds B (no /t/ left for palatalization)
    bleeding_rules = RuleSet(
        rules=[intervocalic_deletion, palatalization],
        iterative=False
    )
    
    test_word = ['a', 't', 'i']  # ati > ai (deletion bleeds palatalization)
    sounds = [Sound(s, 'unified_distinctive') for s in test_word]
    
    result = engine.apply_rule_set(bleeding_rules, sounds)
    
    original = ' '.join([s.grapheme() for s in sounds])
    final = ' '.join([s.grapheme() for s in result.final_sequence])
    print(f"Bleeding order: {original} > {final}")

test_bleeding_order()
```

### Cyclic Rule Application

#### **Iterative Processes**
```python
def test_iterative_rules():
    """Test rules that apply cyclically until no more changes occur."""
    
    # Vowel deletion in open syllables (iterative)
    vowel_syncope = SoundChangeRule(
        name="vowel_syncope",
        source_pattern="V",  # Any vowel
        target_pattern="",   # Delete
        environment="C _ C V"  # In CVCV sequences
    )
    
    iterative_syncope = RuleSet(
        rules=[vowel_syncope],
        iterative=True,  # Apply until no more changes
        max_iterations=10
    )
    
    test_words = [
        ['k', 'a', 't', 'a', 'r', 'a'],  # katara > katra > ktra
        ['p', 'a', 'l', 'a', 'p', 'a']   # palapa > plapa > plpa
    ]
    
    for word in test_words:
        sounds = [Sound(s, 'unified_distinctive') for s in word]
        result = engine.apply_rule_set(iterative_syncope, sounds)
        
        original = ' '.join([s.grapheme() for s in sounds])
        final = ' '.join([s.grapheme() for s in result.final_sequence])
        iterations = len(result.rule_applications)
        print(f"Iterative syncope: {original} > {final} ({iterations} cycles)")

test_iterative_rules()
```

## Historical Case Studies

### Indo-European Sound Changes

#### **Grimm's Law**
```python
def model_grimms_law():
    """Model the Germanic consonant shift (Grimm's Law)."""
    
    # Phase 1: Voiceless stops > fricatives
    # p t k > f θ x
    phase1_rules = [
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
    
    # Phase 2: Voiced stops > voiceless stops  
    # b d g > p t k
    phase2_rules = [
        FeatureChangeRule(
            name="grimm_b_p",
            feature_conditions={"consonantal": 1.0, "voice": 1.0, "continuant": -1.0},
            feature_changes=[FeatureChange(feature_name="voice", target_value=-1.0, change_type=ChangeType.CATEGORICAL)]
        )
    ]
    
    # Phase 3: Voiced aspirates > voiced stops
    # bʰ dʰ gʰ > b d g  
    phase3_rules = [
        FeatureChangeRule(
            name="grimm_bh_b",
            feature_conditions={"consonantal": 1.0, "voice": 1.0, "spread": 1.0},  # Voiced aspirates
            feature_changes=[FeatureChange(feature_name="spread", target_value=-1.0, change_type=ChangeType.CATEGORICAL)]
        )
    ]
    
    grimms_law = RuleSet(
        rules=phase1_rules + phase2_rules + phase3_rules,
        iterative=False
    )
    
    pie_words = [
        ['p', 'a', 't', 'e', 'r'],    # *pater > fater (father)
        ['b', 'r', 'a', 't', 'e', 'r'], # *brater > prater (brother)  
        ['g', 'e', 'n', 'o', 's']     # *genos > kenos (kin)
    ]
    
    for word in pie_words:
        sounds = [Sound(s, 'unified_distinctive') for s in word]
        result = engine.apply_rule_set(grimms_law, sounds)
        
        pie_form = ' '.join([s.grapheme() for s in sounds])
        germanic_form = ' '.join([s.grapheme() for s in result.final_sequence])
        print(f"Grimm's Law: *{pie_form} > {germanic_form}")

model_grimms_law()
```

#### **Great Vowel Shift**
```python
def model_great_vowel_shift():
    """Model the English Great Vowel Shift."""
    
    # Stage 1: High vowels diphthongize
    high_diphthongization = FeatureChangeRule(
        name="gvs_high_diphthongization",
        feature_conditions={"syllabic": 1.0, "high": 1.0, "tense": 1.0},
        feature_changes=[
            FeatureChange(feature_name="diphthong", target_value=1.0, change_type=ChangeType.CATEGORICAL)
        ]
    )
    
    # Stage 2: Mid vowels raise
    mid_raising = FeatureChangeRule(
        name="gvs_mid_raising",
        feature_conditions={"syllabic": 1.0, "high": -1.0, "low": -1.0, "tense": 1.0},
        feature_changes=[
            FeatureChange(feature_name="high", target_value=1.0, change_type=ChangeType.CATEGORICAL)
        ]
    )
    
    # Stage 3: Low-mid vowels raise to mid
    low_mid_raising = FeatureChangeRule(
        name="gvs_low_mid_raising",
        feature_conditions={"syllabic": 1.0, "low": 1.0, "tense": 1.0},
        feature_changes=[
            FeatureChange(feature_name="low", target_value=-1.0, change_type=ChangeType.CATEGORICAL)
        ]
    )
    
    gvs_rules = RuleSet(
        rules=[high_diphthongization, mid_raising, low_mid_raising],
        iterative=False
    )
    
    middle_english_words = [
        ['b', 'i', 't'],      # bite [i:] > [aɪ]
        ['b', 'e', 't'],      # beet [e:] > [i:]  
        ['b', 'a', 't']       # bate [a:] > [e:]
    ]
    
    for word in middle_english_words:
        sounds = [Sound(s, 'unified_distinctive') for s in word]
        result = engine.apply_rule_set(gvs_rules, sounds)
        
        me_form = ' '.join([s.grapheme() for s in sounds])
        modern_form = ' '.join([s.grapheme() for s in result.final_sequence])
        print(f"Great Vowel Shift: ME {me_form} > ModE {modern_form}")

model_great_vowel_shift()
```

### Romance Language Evolution

#### **Latin to Spanish**
```python
def model_latin_to_spanish():
    """Model key sound changes from Latin to Spanish."""
    
    # Lenition of intervocalic voiceless stops
    intervocalic_lenition = FeatureChangeRule(
        name="latin_intervocalic_lenition",
        feature_conditions={"consonantal": 1.0, "voice": -1.0, "continuant": -1.0},
        feature_changes=[
            FeatureChange(feature_name="voice", target_value=1.0, change_type=ChangeType.CATEGORICAL)
        ],
        environment=PhonologicalEnvironment(left_pattern="V", right_pattern="V")
    )
    
    # Loss of final consonants except /s/
    final_consonant_loss = FeatureChangeRule(
        name="latin_final_loss",
        feature_conditions={"consonantal": 1.0},
        feature_changes=[
            # This would need deletion implementation
        ],
        environment=PhonologicalEnvironment(right_pattern="#")
    )
    
    # Vowel merger (classical 10-vowel > 7-vowel system)
    vowel_merger = FeatureChangeRule(
        name="latin_vowel_merger",
        feature_conditions={"syllabic": 1.0, "length": 1.0},  # Long vowels
        feature_changes=[
            FeatureChange(feature_name="length", target_value=-1.0, change_type=ChangeType.CATEGORICAL)
        ]
    )
    
    latin_spanish_rules = RuleSet(
        rules=[intervocalic_lenition, vowel_merger],
        iterative=False
    )
    
    latin_words = [
        ['v', 'i', 't', 'a'],        # vita > vida (life)
        ['a', 'k', 'w', 'a'],        # aqua > agua (water)
        ['r', 'o', 't', 'a']         # rota > rueda (wheel)
    ]
    
    for word in latin_words:
        sounds = [Sound(s, 'unified_distinctive') for s in word]
        result = engine.apply_rule_set(latin_spanish_rules, sounds)
        
        latin_form = ' '.join([s.grapheme() for s in sounds])
        spanish_form = ' '.join([s.grapheme() for s in result.final_sequence])
        print(f"Latin > Spanish: {latin_form} > {spanish_form}")

model_latin_to_spanish()
```

## Advanced Techniques

### Optimality Theory Integration

#### **Constraint-Based Rules**
```python
def model_ot_interaction():
    """Model Optimality Theory constraint interaction."""
    
    # This is a conceptual example of how OT constraints could be modeled
    class PhonologicalConstraint:
        def __init__(self, name, violation_function, weight=1.0):
            self.name = name
            self.violation_function = violation_function
            self.weight = weight
        
        def evaluate(self, candidate):
            """Return number of violations for this candidate."""
            return self.violation_function(candidate) * self.weight
    
    # Example constraints
    def no_coda_violations(word):
        """Count coda consonants (simplified)."""
        violations = 0
        for i, sound in enumerate(word):
            if (sound.get_feature_value('consonantal') > 0 and 
                i == len(word) - 1):  # Final consonant
                violations += 1
        return violations
    
    def max_onset_violations(word):
        """Prefer complex onsets."""
        violations = 0
        # Simplified: count missed opportunities for complex onsets
        return violations
    
    # Define constraint ranking
    constraints = [
        PhonologicalConstraint("NoCoda", no_coda_violations, weight=3.0),
        PhonologicalConstraint("MaxOnset", max_onset_violations, weight=1.0)
    ]
    
    def evaluate_candidate(candidate):
        """Evaluate total constraint violations."""
        total_violations = sum(constraint.evaluate(candidate) for constraint in constraints)
        return total_violations
    
    # This would integrate with the sound change system
    print("OT constraint modeling framework defined")

model_ot_interaction()
```

### Stochastic Sound Change

#### **Variable Rules with Probabilities**
```python
import random

def model_stochastic_change():
    """Model probabilistic sound change application."""
    
    class StochasticRule:
        def __init__(self, rule, probability):
            self.rule = rule
            self.probability = probability
        
        def apply(self, engine, sounds):
            """Apply rule with given probability."""
            if random.random() < self.probability:
                return engine.apply_rule(self.rule, sounds)
            else:
                # Return unchanged
                from alteruphono.phonology.sound_change.engine import RuleApplicationResult
                return RuleApplicationResult(
                    modified_sequence=sounds,
                    changed=False,
                    rule_name=self.rule.name,
                    change_count=0
                )
    
    # Example: Variable voicing (70% probability)
    voicing_rule = FeatureChangeRule(
        name="variable_voicing",
        feature_conditions={"voice": -1.0, "sonorant": -1.0},
        feature_changes=[
            FeatureChange(feature_name="voice", target_value=1.0, change_type=ChangeType.CATEGORICAL)
        ]
    )
    
    stochastic_voicing = StochasticRule(voicing_rule, probability=0.7)
    
    # Test on multiple instances
    test_word = [Sound('p', 'unified_distinctive'), Sound('a', 'unified_distinctive')]
    applications = 0
    
    for trial in range(10):
        result = stochastic_voicing.apply(engine, test_word)
        if result.changed:
            applications += 1
    
    print(f"Stochastic rule applied in {applications}/10 trials (expected ~7)")

model_stochastic_change()
```

### Phonological Learning

#### **Constraint Induction**
```python
def model_constraint_learning():
    """Model learning of phonological constraints from data."""
    
    def extract_patterns(word_list):
        """Extract phonological patterns from word list."""
        patterns = {
            'initial_clusters': [],
            'final_clusters': [],
            'vowel_sequences': []
        }
        
        for word in word_list:
            sounds = [Sound(s, 'unified_distinctive') for s in word]
            
            # Extract initial clusters
            initial_consonants = []
            for sound in sounds:
                if sound.get_feature_value('consonantal') > 0:
                    initial_consonants.append(sound.grapheme())
                else:
                    break
            
            if len(initial_consonants) > 1:
                patterns['initial_clusters'].append(''.join(initial_consonants))
            
            # Extract vowel sequences
            vowel_sequence = []
            for sound in sounds:
                if sound.get_feature_value('syllabic') > 0:
                    vowel_sequence.append(sound.grapheme())
                elif vowel_sequence:
                    if len(vowel_sequence) > 1:
                        patterns['vowel_sequences'].append(''.join(vowel_sequence))
                    vowel_sequence = []
        
        return patterns
    
    # Example word list
    word_list = [
        ['s', 'p', 'a'],      # spa (sp- cluster)
        ['s', 't', 'a'],      # sta (st- cluster)  
        ['p', 'a'],           # pa (no cluster)
        ['a', 'e'],           # ae (vowel sequence)
        ['t', 'a']            # ta (no cluster)
    ]
    
    patterns = extract_patterns(word_list)
    print("Learned patterns:")
    for pattern_type, instances in patterns.items():
        print(f"  {pattern_type}: {instances}")

model_constraint_learning()
```

## Best Practices

### Rule Design Guidelines

1. **Use Natural Classes**: Define rules using phonological features rather than lists of segments
2. **Specify Environments Clearly**: Be explicit about conditioning environments
3. **Order Rules Carefully**: Consider feeding/bleeding relationships
4. **Test Thoroughly**: Validate rules with diverse test cases
5. **Document Motivations**: Explain the linguistic basis for each rule

### Performance Optimization

```python
def optimize_rule_application():
    """Best practices for efficient rule application."""
    
    # 1. Batch rule application when possible
    efficient_rules = RuleSet(
        rules=[rule1, rule2, rule3],
        iterative=False  # More efficient than individual applications
    )
    
    # 2. Use appropriate feature systems
    # - IPA categorical for simple binary operations
    # - Unified distinctive for gradient changes
    # - Tresoldi for cross-linguistic coverage
    
    # 3. Cache sound objects when processing large datasets
    sound_cache = {}
    def get_cached_sound(grapheme, system):
        key = (grapheme, system)
        if key not in sound_cache:
            sound_cache[key] = Sound(grapheme, system)
        return sound_cache[key]
    
    # 4. Profile rule performance
    import time
    start_time = time.time()
    # Apply rules
    end_time = time.time()
    print(f"Rule application time: {end_time - start_time:.3f}s")

optimize_rule_application()
```

### Testing Strategies

```python
def test_rule_validation():
    """Comprehensive testing strategies for sound change rules."""
    
    def test_rule_correctness(rule, test_cases):
        """Test rule against known input-output pairs."""
        for input_word, expected_output in test_cases:
            sounds = [Sound(s, 'unified_distinctive') for s in input_word]
            result = engine.apply_rule(rule, sounds)
            actual_output = [s.grapheme() for s in result.modified_sequence]
            
            if actual_output != expected_output:
                print(f"FAIL: {' '.join(input_word)} > {' '.join(actual_output)} (expected {' '.join(expected_output)})")
            else:
                print(f"PASS: {' '.join(input_word)} > {' '.join(actual_output)}")
    
    def test_rule_generalization(rule, minimal_pairs):
        """Test that rule applies to natural classes correctly."""
        for pair in minimal_pairs:
            sound1, sound2 = pair
            # Test that rule treats natural class members similarly
            result1 = engine.apply_rule(rule, [Sound(sound1, 'unified_distinctive')])
            result2 = engine.apply_rule(rule, [Sound(sound2, 'unified_distinctive')])
            
            # Both should change or both should not change
            if result1.changed != result2.changed:
                print(f"WARNING: Inconsistent application on {sound1} vs {sound2}")
    
    def test_rule_ordering(rule_sequence, test_words):
        """Test that rule ordering produces expected results."""
        for word in test_words:
            sounds = [Sound(s, 'unified_distinctive') for s in word]
            
            # Apply rules in sequence
            current = sounds
            for rule in rule_sequence:
                result = engine.apply_rule(rule, current)
                current = result.modified_sequence
            
            original = ' '.join([s.grapheme() for s in sounds])
            final = ' '.join([s.grapheme() for s in current])
            print(f"Rule sequence: {original} > {final}")
    
    # Example usage
    print("Rule validation framework defined")

test_rule_validation()
```

This tutorial provides a comprehensive foundation for modeling sound changes in AlteruPhono, from basic categorical rules to sophisticated gradient processes and complex rule interactions. The examples demonstrate both the theoretical linguistics concepts and their practical implementation in the system.