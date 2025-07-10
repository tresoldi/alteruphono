# Phonological Feature Systems Guide

This comprehensive guide explains AlteruPhono's three feature systems and their applications in historical linguistics and phonological analysis.

## Table of Contents

1. [Overview of Feature Systems](#overview-of-feature-systems)
2. [IPA Categorical System](#ipa-categorical-system)
3. [Unified Distinctive System](#unified-distinctive-system)
4. [Tresoldi Comprehensive System](#tresoldi-comprehensive-system)
5. [Cross-System Conversion](#cross-system-conversion)
6. [Choosing the Right System](#choosing-the-right-system)
7. [Advanced Applications](#advanced-applications)

## Overview of Feature Systems

AlteruPhono provides three distinct feature systems, each designed for different aspects of phonological research:

| Feature System | Sounds | Features | Value Type | Best For |
|----------------|--------|----------|------------|----------|
| **IPA Categorical** | ~200 | ~30 | Binary | Traditional phonology, teaching |
| **Unified Distinctive** | ~200 | ~25 | Scalar | Gradient changes, evolution modeling |
| **Tresoldi Comprehensive** | 1,081 | 43 | Scalar | Cross-linguistic research, typology |

### Theoretical Background

**Distinctive features** are the building blocks of phonological theory, representing the minimal contrastive properties of sounds. AlteruPhono implements three different approaches:

1. **Binary features**: Traditional ±features (e.g., [+voice], [-nasal])
2. **Scalar features**: Continuous values allowing gradient phenomena
3. **Comprehensive coverage**: Extensive cross-linguistic phonological inventories

## IPA Categorical System

### Overview

The IPA categorical system implements traditional binary distinctive features, following classical phonological theory from Chomsky & Halle (1968) through modern feature geometry.

```python
from alteruphono.phonology.feature_systems import get_feature_system
from alteruphono.phonology.sound_v2 import Sound

# Initialize IPA categorical system
ipa_system = get_feature_system('ipa_categorical')
print(f"Sounds supported: {ipa_system.get_sound_count()}")
print(f"Features: {len(ipa_system.get_feature_names())}")
```

### Feature Categories

#### **Major Class Features**
```python
# Test major class features
p_sound = Sound('p', 'ipa_categorical')
a_sound = Sound('a', 'ipa_categorical')

print(f"'p' consonantal: {p_sound.get_feature_value('consonantal')}")  # +1.0 (true)
print(f"'a' syllabic: {a_sound.get_feature_value('syllabic')}")        # +1.0 (true)
print(f"'p' sonorant: {p_sound.get_feature_value('sonorant')}")        # -1.0 (false)
```

#### **Place Features**
```python
# Place of articulation
labials = ['p', 'b', 'm', 'f', 'v']
coronals = ['t', 'd', 'n', 's', 'z']
dorsals = ['k', 'g', 'ŋ', 'x', 'ɣ']

for sound_char in labials:
    sound = Sound(sound_char, 'ipa_categorical')
    print(f"'{sound_char}' labial: {sound.get_feature_value('labial')}")
```

#### **Manner Features**
```python
# Manner of articulation
stops = ['p', 'b', 't', 'd', 'k', 'g']
fricatives = ['f', 'v', 's', 'z', 'x', 'ɣ']

for stop in stops:
    sound = Sound(stop, 'ipa_categorical')
    print(f"'{stop}' continuant: {sound.get_feature_value('continuant')}")  # -1.0

for fricative in fricatives:
    sound = Sound(fricative, 'ipa_categorical')
    print(f"'{fricative}' continuant: {sound.get_feature_value('continuant')}")  # +1.0
```

### Vowel Features

#### **Height and Backness**
```python
# Vowel space organization
vowels = {
    'i': {'high': 1.0, 'low': -1.0, 'back': -1.0, 'round': -1.0},
    'u': {'high': 1.0, 'low': -1.0, 'back': 1.0, 'round': 1.0},
    'a': {'high': -1.0, 'low': 1.0, 'back': 1.0, 'round': -1.0},
    'e': {'high': -1.0, 'low': -1.0, 'back': -1.0, 'round': -1.0}
}

for vowel_char, expected_features in vowels.items():
    vowel = Sound(vowel_char, 'ipa_categorical')
    for feature, expected_value in expected_features.items():
        actual_value = vowel.get_feature_value(feature)
        print(f"'{vowel_char}' {feature}: {actual_value} (expected: {expected_value})")
```

### Applications

#### **Natural Classes**
```python
def find_natural_class(sounds, feature_system='ipa_categorical'):
    """Find common features defining a natural class."""
    if not sounds:
        return {}
    
    # Get feature bundles for all sounds
    sound_objects = [Sound(s, feature_system) for s in sounds]
    
    # Find shared features
    shared_features = {}
    for feature in sound_objects[0].features.get_feature_names():
        values = [s.get_feature_value(feature) for s in sound_objects]
        if all(v == values[0] for v in values):  # All have same value
            shared_features[feature] = values[0]
    
    return shared_features

# Find features defining voiceless stops
voiceless_stops = ['p', 't', 'k']
shared_features = find_natural_class(voiceless_stops)
print(f"Voiceless stops share: {shared_features}")
# Expected: {consonantal: 1.0, voice: -1.0, continuant: -1.0, sonorant: -1.0}
```

#### **Feature-Based Sound Changes**
```python
from alteruphono.phonology.sound_change import FeatureChangeRule
from alteruphono.phonology.sound_change.rules import FeatureChange, ChangeType

# Spirantization: stops become fricatives
spirantization = FeatureChangeRule(
    name="spirantization",
    feature_conditions={
        "consonantal": 1.0,
        "continuant": -1.0,  # Stops
        "sonorant": -1.0     # Non-sonorants
    },
    feature_changes=[
        FeatureChange(
            feature_name="continuant",
            target_value=1.0,  # Become continuant (fricative)
            change_type=ChangeType.CATEGORICAL
        )
    ],
    feature_system_name='ipa_categorical'
)
```

## Unified Distinctive System

### Overview

The unified distinctive system uses scalar feature values (range: -1.0 to +1.0), enabling gradient phonological phenomena and continuous sound change modeling.

```python
# Initialize unified distinctive system
unified_system = get_feature_system('unified_distinctive')
p_sound = Sound('p', 'unified_distinctive')

# Features are scalar, not binary
voice_value = p_sound.get_feature_value('voice')
print(f"'p' voice value: {voice_value}")  # -1.0 (voiceless)
```

### Scalar Feature Arithmetic

#### **Feature Modification**
```python
# Gradual voicing using scalar arithmetic
p_sound = Sound('p', 'unified_distinctive')
original_voice = p_sound.get_feature_value('voice')

# Apply partial voicing
partially_voiced = p_sound + 'voice=0.5'
new_voice = partially_voiced.get_feature_value('voice')

print(f"Original voice: {original_voice}")     # -1.0
print(f"After +0.5: {new_voice}")             # -0.5 (partially voiced)

# Apply more voicing
fully_voiced = partially_voiced + 'voice=1.5'  # Will clamp to 1.0
final_voice = fully_voiced.get_feature_value('voice')
print(f"After +1.5: {final_voice}")           # 1.0 (fully voiced)
```

#### **Continuous Vowel Space**
```python
# Model continuous vowel space
def create_intermediate_vowel(vowel1, vowel2, weight=0.5):
    """Create vowel intermediate between two vowels."""
    v1 = Sound(vowel1, 'unified_distinctive')
    v2 = Sound(vowel2, 'unified_distinctive')
    
    # Calculate intermediate feature values
    features = []
    for feature_name in v1.features.get_feature_names():
        val1 = v1.get_feature_value(feature_name)
        val2 = v2.get_feature_value(feature_name)
        intermediate_val = val1 * (1 - weight) + val2 * weight
        features.append(f"{feature_name}={intermediate_val}")
    
    return v1 + ','.join(features)

# Create vowel between [i] and [a]
intermediate = create_intermediate_vowel('i', 'a', 0.3)
print(f"Intermediate vowel height: {intermediate.get_feature_value('high')}")
```

### Gradient Sound Changes

#### **Progressive Lenition**
```python
from alteruphono.phonology.sound_change import SoundChangeEngine

engine = SoundChangeEngine(feature_system_name='unified_distinctive')

# Model gradual lenition (stop → fricative → approximant)
lenition_stages = [
    FeatureChangeRule(
        name="lenition_stage1",
        feature_conditions={"consonantal": 1.0, "continuant": -1.0},
        feature_changes=[
            FeatureChange(
                feature_name="continuant",
                target_value=0.3,  # Partial continuancy
                change_type=ChangeType.GRADIENT,
                change_strength=0.5
            )
        ]
    ),
    FeatureChangeRule(
        name="lenition_stage2", 
        feature_conditions={"consonantal": 1.0, "continuant": 0.3},
        feature_changes=[
            FeatureChange(
                feature_name="continuant",
                target_value=0.8,  # More continuant
                change_type=ChangeType.GRADIENT,
                change_strength=0.7
            )
        ]
    )
]
```

#### **Vowel Chain Shifts**
```python
# Model Great Vowel Shift-type chain movements
def model_chain_shift(vowels, shift_pattern):
    """Model systematic vowel chain shift."""
    results = {}
    
    for vowel in vowels:
        sound = Sound(vowel, 'unified_distinctive')
        
        # Apply height raising
        if 'raise' in shift_pattern:
            raised = sound + f"high={shift_pattern['raise']}"
            results[vowel] = raised
        
        # Apply fronting/backing
        if 'front' in shift_pattern:
            fronted = sound + f"back={shift_pattern['front']}"
            results[vowel] = fronted
    
    return results

# Great Vowel Shift simulation
gvs_pattern = {'raise': 0.4, 'front': -0.2}
shifted_vowels = model_chain_shift(['e', 'o', 'a'], gvs_pattern)
```

### Distance Calculations

#### **Phonological Distance Metrics**
```python
def calculate_feature_distance(sound1, sound2, feature_system='unified_distinctive'):
    """Calculate Euclidean distance in feature space."""
    s1 = Sound(sound1, feature_system)
    s2 = Sound(sound2, feature_system)
    
    return s1.distance_to(s2)

# Compare distances within manner classes
stop_distances = [
    ('p', 'b'),  # Voicing difference
    ('p', 't'),  # Place difference  
    ('p', 'k'),  # Place difference
    ('p', 'f')   # Manner difference
]

for s1, s2 in stop_distances:
    distance = calculate_feature_distance(s1, s2)
    print(f"Distance {s1}-{s2}: {distance:.3f}")
```

## Tresoldi Comprehensive System

### Overview

The Tresoldi system provides the most comprehensive phonological coverage, with 1,081 sounds and 43 features covering diverse world languages.

```python
# Initialize Tresoldi system
tresoldi_system = get_feature_system('tresoldi_distinctive')
print(f"Total sounds: {tresoldi_system.get_sound_count()}")       # 1,081
print(f"Total features: {len(tresoldi_system.get_feature_names())}")  # 43
```

### Comprehensive Sound Coverage

#### **Complex Segments**
```python
# Test complex segment support
complex_sounds = [
    'kʷ',     # Labialized velar
    'tʃ',     # Affricate
    'ⁿd',     # Prenasalized stop
    'kʷʰ',    # Aspirated labialized velar
    'bd'      # Doubly articulated stop
]

supported_complex = []
for sound in complex_sounds:
    if tresoldi_system.has_grapheme(sound):
        sound_obj = Sound(sound, 'tresoldi_distinctive')
        features = sound_obj.features
        supported_complex.append((sound, len(features.features)))

print("Complex sounds supported:")
for sound, feature_count in supported_complex:
    print(f"  {sound}: {feature_count} features")
```

#### **Click Consonants**
```python
# Analyze click consonant features
click_sounds = ['ǀ', 'ǁ', 'ǃ', 'ǂ', 'ʘ']  # Different click types

for click in click_sounds:
    if tresoldi_system.has_grapheme(click):
        click_sound = Sound(click, 'tresoldi_distinctive')
        
        # Check click-specific features
        click_val = click_sound.get_feature_value('click')
        place_val = click_sound.get_feature_value('coronal')  # Many clicks are coronal
        
        print(f"Click {click}: click={click_val:.1f}, coronal={place_val:.1f}")
```

#### **Rare Phonological Features**
```python
# Explore rare phonological features
rare_features = [
    'ejective',      # Ejective consonants
    'implosive',     # Implosive consonants  
    'creaky',        # Creaky voice
    'breathy',       # Breathy voice
    'prenasal',      # Prenasalized
    'preglottalized' # Preglottalized
]

feature_statistics = {}
for feature in rare_features:
    if feature in tresoldi_system.get_feature_names():
        positive_sounds = tresoldi_system.get_sounds_with_feature(feature, positive=True)
        feature_statistics[feature] = len(positive_sounds)

print("Rare feature distribution:")
for feature, count in feature_statistics.items():
    percentage = (count / 1081) * 100
    print(f"  {feature}: {count} sounds ({percentage:.1f}%)")
```

### Cross-Linguistic Analysis

#### **Phonological Universals**
```python
def test_universal_hierarchies():
    """Test various phonological universal claims."""
    
    # Place hierarchy: labial > coronal > dorsal
    labial_count = len(tresoldi_system.get_sounds_with_feature('labial', positive=True))
    coronal_count = len(tresoldi_system.get_sounds_with_feature('coronal', positive=True))
    dorsal_count = len(tresoldi_system.get_sounds_with_feature('dorsal', positive=True))
    
    place_hierarchy = labial_count >= coronal_count >= dorsal_count
    
    # Voicing hierarchy: voiceless > voiced for obstruents
    voiceless_obs = len([s for s in tresoldi_system.get_all_graphemes()
                        if tresoldi_system.has_grapheme(s) and
                        tresoldi_system.is_negative(tresoldi_system.grapheme_to_features(s), 'voice') and
                        tresoldi_system.is_negative(tresoldi_system.grapheme_to_features(s), 'sonorant')])
    
    voiced_obs = len([s for s in tresoldi_system.get_all_graphemes()
                     if tresoldi_system.has_grapheme(s) and
                     tresoldi_system.is_positive(tresoldi_system.grapheme_to_features(s), 'voice') and
                     tresoldi_system.is_negative(tresoldi_system.grapheme_to_features(s), 'sonorant')])
    
    voicing_hierarchy = voiceless_obs >= voiced_obs
    
    return {
        'place_hierarchy': place_hierarchy,
        'place_counts': (labial_count, coronal_count, dorsal_count),
        'voicing_hierarchy': voicing_hierarchy,
        'voicing_counts': (voiceless_obs, voiced_obs)
    }

universals = test_universal_hierarchies()
print("Universal hierarchy tests:")
for test, result in universals.items():
    print(f"  {test}: {result}")
```

#### **Typological Profiles**
```python
def create_typological_profile(sound_inventory):
    """Create typological profile of a sound inventory."""
    profile = {
        'total_sounds': len(sound_inventory),
        'consonants': 0,
        'vowels': 0,
        'complex_segments': 0,
        'rare_features': {}
    }
    
    for sound_char in sound_inventory:
        if tresoldi_system.has_grapheme(sound_char):
            sound = Sound(sound_char, 'tresoldi_distinctive')
            
            # Count major classes
            if sound.get_feature_value('consonantal') > 0:
                profile['consonants'] += 1
            if sound.get_feature_value('syllabic') > 0:
                profile['vowels'] += 1
            
            # Count complex segments (multi-character)
            if len(sound_char) > 1:
                profile['complex_segments'] += 1
            
            # Count rare features
            for rare_feature in ['click', 'ejective', 'implosive']:
                if rare_feature in tresoldi_system.get_feature_names():
                    if sound.get_feature_value(rare_feature) > 0:
                        profile['rare_features'][rare_feature] = profile['rare_features'].get(rare_feature, 0) + 1
    
    return profile

# Example: Analyze !Kung inventory (hypothetical)
kung_inventory = ['p', 'b', 't', 'd', 'k', 'g', 'ǀ', 'ǁ', 'ǃ', 'ǂ', 'a', 'e', 'i', 'o', 'u']
profile = create_typological_profile(kung_inventory)
print(f"!Kung typological profile: {profile}")
```

### Advanced Feature Statistics

#### **Feature Correlations**
```python
def analyze_feature_correlations():
    """Analyze correlations between phonological features."""
    import numpy as np
    
    # Get all sounds and their feature vectors
    all_sounds = tresoldi_system.get_all_graphemes()[:100]  # Sample for efficiency
    feature_names = tresoldi_system.get_feature_names()
    
    # Build feature matrix
    feature_matrix = []
    for sound_char in all_sounds:
        if tresoldi_system.has_grapheme(sound_char):
            sound = Sound(sound_char, 'tresoldi_distinctive')
            feature_vector = [sound.get_feature_value(f) for f in feature_names]
            feature_matrix.append(feature_vector)
    
    feature_matrix = np.array(feature_matrix)
    
    # Calculate correlation matrix
    correlations = np.corrcoef(feature_matrix.T)
    
    # Find strongest correlations
    strong_correlations = []
    for i, feat1 in enumerate(feature_names):
        for j, feat2 in enumerate(feature_names[i+1:], i+1):
            correlation = correlations[i][j]
            if abs(correlation) > 0.7:  # Strong correlation threshold
                strong_correlations.append((feat1, feat2, correlation))
    
    return sorted(strong_correlations, key=lambda x: abs(x[2]), reverse=True)

correlations = analyze_feature_correlations()
print("Strong feature correlations:")
for feat1, feat2, corr in correlations[:10]:
    print(f"  {feat1} ~ {feat2}: {corr:.3f}")
```

## Cross-System Conversion

### Feature Mapping

```python
from alteruphono.phonology.feature_systems import convert_between_systems

# Convert features between systems
ipa_sound = Sound('p', 'ipa_categorical')
ipa_features = ipa_sound.features

# Convert to Tresoldi system
tresoldi_features = convert_between_systems(
    ipa_features,
    'ipa_categorical',
    'tresoldi_distinctive'
)

print(f"IPA features: {len(ipa_features.features)}")
print(f"Converted Tresoldi features: {len(tresoldi_features.features)}")

# Show feature mapping
for ipa_feat in ipa_features.features:
    for tresoldi_feat in tresoldi_features.features:
        if ipa_feat.feature == tresoldi_feat.feature:
            print(f"  {ipa_feat.feature}: {ipa_feat.value} → {tresoldi_feat.value}")
```

### Cross-System Compatibility

```python
def test_cross_system_compatibility():
    """Test that same sound behaves consistently across systems."""
    test_sounds = ['p', 'a', 't', 'i', 'k']
    systems = ['ipa_categorical', 'unified_distinctive', 'tresoldi_distinctive']
    
    compatibility_results = {}
    
    for sound_char in test_sounds:
        sound_results = {}
        
        for system in systems:
            try:
                sound = Sound(sound_char, system)
                # Test key features
                voice_val = sound.get_feature_value('voice')
                consonantal_val = sound.get_feature_value('consonantal')
                
                sound_results[system] = {
                    'voice': voice_val,
                    'consonantal': consonantal_val
                }
            except Exception as e:
                sound_results[system] = f"Error: {e}"
        
        compatibility_results[sound_char] = sound_results
    
    return compatibility_results

compatibility = test_cross_system_compatibility()
print("Cross-system compatibility:")
for sound, systems in compatibility.items():
    print(f"\n{sound}:")
    for system, features in systems.items():
        if isinstance(features, dict):
            print(f"  {system}: voice={features['voice']:.1f}, cons={features['consonantal']:.1f}")
        else:
            print(f"  {system}: {features}")
```

## Choosing the Right System

### Decision Matrix

| Research Goal | Recommended System | Rationale |
|--------------|-------------------|-----------|
| **Traditional phonological analysis** | IPA Categorical | Binary features match classical theory |
| **Sound change modeling** | Unified Distinctive | Scalar values enable gradient changes |
| **Cross-linguistic typology** | Tresoldi Comprehensive | Massive sound inventory covers world languages |
| **Language evolution simulation** | Unified Distinctive | Gradient changes model realistic evolution |
| **Comparative reconstruction** | Any system | All support bidirectional sound changes |
| **Rare phoneme analysis** | Tresoldi Comprehensive | Includes clicks, ejectives, complex segments |

### Performance Considerations

```python
import time

def benchmark_feature_systems():
    """Benchmark performance across feature systems."""
    systems = ['ipa_categorical', 'unified_distinctive', 'tresoldi_distinctive']
    test_sounds = ['p', 'a', 't', 'i', 'k'] * 20  # 100 sounds
    
    results = {}
    
    for system in systems:
        start_time = time.time()
        
        # Test sound creation
        sounds = [Sound(s, system) for s in test_sounds]
        
        # Test feature access
        for sound in sounds:
            sound.get_feature_value('voice')
            sound.has_feature('consonantal')
        
        # Test distance calculations
        for i in range(0, len(sounds)-1, 10):
            sounds[i].distance_to(sounds[i+1])
        
        end_time = time.time()
        results[system] = end_time - start_time
    
    return results

performance = benchmark_feature_systems()
print("Performance benchmarks:")
for system, time_taken in performance.items():
    print(f"  {system}: {time_taken:.4f}s")
```

## Advanced Applications

### Phonological Process Modeling

#### **Assimilation Rules**
```python
def model_vowel_harmony(word, harmony_feature):
    """Model vowel harmony spreading."""
    sounds = [Sound(s, 'unified_distinctive') for s in word]
    
    # Find trigger (first vowel)
    trigger_value = None
    for sound in sounds:
        if sound.get_feature_value('syllabic') > 0:  # Is vowel
            trigger_value = sound.get_feature_value(harmony_feature)
            break
    
    if trigger_value is None:
        return sounds
    
    # Apply harmony to other vowels
    harmonized = []
    for sound in sounds:
        if sound.get_feature_value('syllabic') > 0:  # Is vowel
            # Apply harmony
            harmonized_sound = sound + f"{harmony_feature}={trigger_value}"
            harmonized.append(harmonized_sound)
        else:
            harmonized.append(sound)
    
    return harmonized

# Example: front/back harmony
word = ['k', 'a', 't', 'a']
harmonized_word = model_vowel_harmony(word, 'back')
```

#### **Phonotactic Constraints**
```python
def check_phonotactic_constraints(sequence, feature_system='tresoldi_distinctive'):
    """Check sequence against universal phonotactic constraints."""
    sounds = [Sound(s, feature_system) for s in sequence]
    violations = []
    
    # Constraint: No labial-coronal clusters  
    for i in range(len(sounds) - 1):
        s1, s2 = sounds[i], sounds[i+1]
        if (s1.get_feature_value('labial') > 0 and s1.get_feature_value('consonantal') > 0 and
            s2.get_feature_value('coronal') > 0 and s2.get_feature_value('consonantal') > 0):
            violations.append(f"Labial-coronal cluster at position {i}")
    
    # Constraint: No vowel-vowel sequences without hiatus
    for i in range(len(sounds) - 1):
        s1, s2 = sounds[i], sounds[i+1]
        if (s1.get_feature_value('syllabic') > 0 and 
            s2.get_feature_value('syllabic') > 0):
            violations.append(f"Vowel hiatus at position {i}")
    
    return violations

# Test phonotactic well-formedness
test_sequences = [
    ['p', 't', 'a'],      # Bad: labial-coronal cluster
    ['k', 'a', 't'],      # Good: well-formed
    ['p', 'a', 'e', 'r']  # Bad: vowel hiatus
]

for seq in test_sequences:
    violations = check_phonotactic_constraints(seq)
    status = "GOOD" if not violations else "BAD"
    print(f"{' '.join(seq)}: {status} {violations}")
```

### Evolutionary Modeling

#### **Chain Shift Simulation**
```python
def simulate_chain_shift(vowel_system, shift_parameters):
    """Simulate complex vowel chain shift."""
    shifted_system = {}
    
    for vowel in vowel_system:
        original = Sound(vowel, 'unified_distinctive')
        
        # Apply height shift
        height_shift = shift_parameters.get('height_shift', 0)
        new_high = original.get_feature_value('high') + height_shift
        new_low = original.get_feature_value('low') - height_shift
        
        # Apply backness shift  
        back_shift = shift_parameters.get('back_shift', 0)
        new_back = original.get_feature_value('back') + back_shift
        
        # Create shifted vowel
        shifted = original + f"high={new_high - original.get_feature_value('high')}"
        shifted = shifted + f"low={new_low - original.get_feature_value('low')}"
        shifted = shifted + f"back={new_back - original.get_feature_value('back')}"
        
        shifted_system[vowel] = shifted
    
    return shifted_system

# Simulate Great Vowel Shift
gvs_parameters = {
    'height_shift': 0.3,  # Vowels raise
    'back_shift': -0.1    # Slight fronting
}

original_system = ['i', 'e', 'a', 'o', 'u']
shifted_system = simulate_chain_shift(original_system, gvs_parameters)

print("Great Vowel Shift simulation:")
for original, shifted in shifted_system.items():
    orig_height = Sound(original, 'unified_distinctive').get_feature_value('high')
    new_height = shifted.get_feature_value('high')
    print(f"  {original}: height {orig_height:.2f} → {new_height:.2f}")
```

This comprehensive guide demonstrates the power and flexibility of AlteruPhono's feature systems for serious phonological research. Each system offers unique advantages for different aspects of historical linguistics and phonological analysis.