# Phase 4: Suprasegmental and Numeric Features

This document describes the Phase 4 implementation of alteruphono, which adds comprehensive support for suprasegmental features, numeric feature values, and prosodic hierarchy representation.

## Overview

Phase 4 extends alteruphono's phonological system with:

1. **Suprasegmental Features**: Stress, tone, length, and other features that span beyond individual segments
2. **Numeric Features**: Gradual feature values with arithmetic operations
3. **Prosodic Hierarchy**: Syllables, feet, prosodic words, and boundary markers
4. **Enhanced Parser**: Support for prosodic boundary tokens in rules

## New Features

### Suprasegmental Features

#### Stress Features
- `stress1`: Primary stress
- `stress2`: Secondary stress  
- `unstressed`: Explicitly unstressed
- `+stress` / `-stress`: Shorthand for stress assignment

#### Tone Features
- `tone1` through `tone5`: Level tones (1=high, 5=extra low)
- `high`, `mid`, `low`: Common tone level aliases
- `rising`, `falling`, `level`: Tone contours

#### Length Features
- `long` / `+long`: Long segments
- `short` / `-long`: Short segments

### Numeric Features

Numeric features allow gradual distinctions and arithmetic operations:

- `f0_N`: Fundamental frequency levels (N = 1-5)
- `duration_N`: Duration levels (N = 1-3) 
- `tone_N`: Numeric tone values

Arithmetic operations:
```python
sound = Sound(grapheme='a') + 'f0_2'
higher = sound.increment_feature('f0', 1)  # f0_2 -> f0_3
lower = sound.decrement_feature('f0', 1)   # f0_2 -> f0_1
```

### Prosodic Hierarchy

#### Boundary Types
- `σ`: Syllable boundary
- `Ft`: Foot boundary
- `#`: Word boundary (with optional strength: `#2`, `#3`)
- `φ`: Phonological phrase boundary
- `U`: Utterance boundary

#### Syllable Structure
```python
from alteruphono.phonology import Syllable, Sound

p = Sound(grapheme='p')
a = Sound(grapheme='a') 
t = Sound(grapheme='t')

# Create syllable with stress and tone
syll = Syllable(
    onset=[p],
    nucleus=[a], 
    coda=[t],
    stress=1,     # Primary stress
    tone='tone2'  # Mid tone
)

print(syll)  # Output: pˈa̅t
```

#### Prosodic Words
```python
from alteruphono.phonology import ProsodicWord

word = ProsodicWord([syll1, syll2])
word.assign_stress("10")  # Trochaic pattern
stress_pos = word.get_main_stress_position()
```

#### Automatic Syllabification
```python
from alteruphono.phonology import syllabify_sounds

sounds = [Sound(grapheme=c) for c in 'pata']
syllables = syllabify_sounds(sounds)  # [pa.ta]
```

## Usage Examples

### Basic Suprasegmental Operations
```python
from alteruphono.phonology import Sound

# Create vowel with stress and tone
vowel = Sound(grapheme='a')
complex_vowel = vowel + 'stress1,tone2,f0_3'

print(complex_vowel.has_stress())      # True
print(complex_vowel.get_stress_level()) # 1
print(complex_vowel.has_tone())        # True  
print(complex_vowel.get_tone_value())  # 2
```

### Feature Separation
```python
# Separate segmental and suprasegmental features
segmental = sound.get_segmental_features()      # {vowel, low, front, ...}
suprasegmental = sound.get_suprasegmental_features()  # {stress1, tone2, f0_3}
```

### Prosodic Rules
Rules can now reference prosodic boundaries:
```python
from alteruphono.parser import parse_rule

# Stress assignment at word boundaries
rule = parse_rule("V > V[+stress] / # _ σ")

# Tone spreading within prosodic words  
rule = parse_rule("V[tone1] V > V[tone1] V[tone1] / _ #")
```

### Parser Integration
```python
from alteruphono.parser import parse_atom

# Parse prosodic boundaries
syll_token = parse_atom("σ")     # Syllable boundary
foot_token = parse_atom("Ft")    # Foot boundary
word_token = parse_atom("#")     # Word boundary
phrase_token = parse_atom("φ")   # Phrase boundary
```

## API Reference

### Sound Class Extensions
- `has_stress() -> bool`: Check for stress
- `has_tone() -> bool`: Check for tone
- `get_stress_level() -> int`: Get stress level (0-2)
- `get_tone_value() -> int`: Get tone value (1-5)
- `increment_feature(feature_type, amount=1) -> Sound`: Increment numeric feature
- `decrement_feature(feature_type, amount=1) -> Sound`: Decrement numeric feature
- `get_suprasegmental_features() -> FrozenSet[str]`: Get suprasegmental features only
- `get_segmental_features() -> FrozenSet[str]`: Get segmental features only

### Utility Functions
- `is_suprasegmental_feature(feature: str) -> bool`: Check if feature is suprasegmental
- `is_numeric_feature(feature: str) -> bool`: Check if feature is numeric
- `get_numeric_value(feature: str) -> int`: Extract numeric value
- `increment_numeric_feature(feature: str, amount: int) -> str`: Increment feature value
- `decrement_numeric_feature(feature: str, amount: int) -> str`: Decrement feature value

### Prosodic Classes
- `ProsodicBoundary(boundary_type, strength=1)`: Prosodic boundary marker
- `Syllable(onset, nucleus, coda, stress=0, tone=None)`: Syllable structure
- `ProsodicWord(syllables)`: Prosodic word with feet
- `syllabify_sounds(sounds) -> List[Syllable]`: Automatic syllabification
- `parse_prosodic_string(text) -> List[Union[Sound, ProsodicBoundary]]`: Parse prosodic markup

## Testing

Run the Phase 4 test suite:
```bash
python -m unittest tests.test_phase4
```

Run the interactive demo:
```bash
PYTHONPATH=. python examples/phase4_demo.py
```

## Compatibility

Phase 4 maintains full backward compatibility with earlier phases. All existing functionality continues to work unchanged, with new features available as optional extensions.

## Version

Phase 4 features are available in alteruphono v0.7.0 and later.