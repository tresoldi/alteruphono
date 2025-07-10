# Pluggable Feature System Architecture

This document describes the new pluggable feature system architecture in alteruphono, which allows for multiple phonological feature systems to coexist and be used interchangeably.

## Overview

The traditional approach to phonological features in computational systems has been to use a single, fixed feature system (typically IPA-based categorical features). This new architecture allows researchers to:

1. **Use different feature theories** - Switch between IPA categorical, unified distinctive, or custom systems
2. **Compare approaches** - Analyze the same data with different feature representations
3. **Develop new systems** - Implement custom feature systems for specific research needs
4. **Maintain compatibility** - Keep existing code working while enabling new capabilities

## Architecture Components

### 1. Feature Values (`FeatureValue`)

The atomic unit of the feature system, representing a single feature-value pair:

```python
from alteruphono.phonology.feature_systems import FeatureValue, FeatureValueType

# Binary feature (traditional +/-)
voiced = FeatureValue('voiced', True, FeatureValueType.BINARY)

# Categorical feature (named categories)
place = FeatureValue('place', 'bilabial', FeatureValueType.CATEGORICAL)

# Scalar feature (continuous values)
voice_strength = FeatureValue('voice', 0.8, FeatureValueType.SCALAR)

# Ordinal feature (ordered discrete values)
tone_level = FeatureValue('tone', 3, FeatureValueType.ORDINAL)
```

### 2. Feature Bundles (`FeatureBundle`)

Collections of feature values representing complete phonological descriptions:

```python
from alteruphono.phonology.feature_systems import FeatureBundle

# Create a feature bundle
features = {
    FeatureValue('voiced', True, FeatureValueType.BINARY),
    FeatureValue('place', 'bilabial', FeatureValueType.CATEGORICAL),
    FeatureValue('manner', 'stop', FeatureValueType.CATEGORICAL)
}

bundle = FeatureBundle(frozenset(features))

# Operations
bundle.has_feature('voiced')  # True
bundle.get_feature('place')   # FeatureValue('place', 'bilabial', ...)
bundle.add_feature(new_feature)
bundle.remove_feature('voiced')
```

### 3. Feature Systems (`FeatureSystem`)

Abstract base class defining the interface for all feature systems:

```python
from alteruphono.phonology.feature_systems import FeatureSystem

class MyFeatureSystem(FeatureSystem):
    @property
    def name(self) -> str:
        return "my_system"
    
    @property 
    def description(self) -> str:
        return "My custom feature system"
    
    def grapheme_to_features(self, grapheme: str) -> Optional[FeatureBundle]:
        # Convert grapheme to features
        pass
    
    def features_to_grapheme(self, features: FeatureBundle) -> str:
        # Convert features back to grapheme
        pass
    
    # ... other required methods
```

### 4. Feature System Registry

Central registry for managing multiple feature systems:

```python
from alteruphono.phonology.feature_systems import (
    register_feature_system,
    get_feature_system,
    list_feature_systems,
    set_default_feature_system
)

# Register a new system
register_feature_system(MyFeatureSystem())

# List available systems
systems = list_feature_systems()  # ['ipa_categorical', 'unified_distinctive', 'my_system']

# Get a specific system
system = get_feature_system('unified_distinctive')

# Set default system
set_default_feature_system('unified_distinctive')
```

## Built-in Feature Systems

### 1. IPA Categorical System (`ipa_categorical`)

Traditional IPA-based categorical feature system with binary and categorical features:

```python
from alteruphono.phonology.feature_systems import get_feature_system

ipa_system = get_feature_system('ipa_categorical')

# Features for /p/
p_features = ipa_system.grapheme_to_features('p')
# Result: [consonant=consonant, bilabial=bilabial, stop=stop, voiceless=voiceless]

# Feature specification parsing
features = ipa_system.parse_feature_specification('[+voiced, bilabial, stop]')
```

**Supported features:**
- **Major class**: consonant, vowel, sonorant
- **Place**: bilabial, alveolar, velar, etc.
- **Manner**: stop, fricative, nasal, etc.
- **Voicing**: voiced, voiceless (+/- notation)
- **Vowel**: high, low, front, back, round
- **Suprasegmental**: stress1, stress2, tone1-5, etc.

### 2. Unified Distinctive System (`unified_distinctive`)

Modern unified feature system with scalar values from -1.0 to +1.0:

```python
unified_system = get_feature_system('unified_distinctive')

# Features for /p/
p_features = unified_system.grapheme_to_features('p')
# Result: [sonorant=-0.90, consonantal=1.00, continuant=-1.00, labial=1.00, voice=-1.00, nasal=-1.00]

# Scalar feature specifications
features = unified_system.parse_feature_specification('[voice=0.8, high=-0.3, labial=1.0]')
```

**Key features:**
- **Major class**: sonorant, consonantal, continuant (all scalar)
- **Place**: labial, coronal, dorsal, pharyngeal, laryngeal
- **Coronal**: anterior, distributed
- **Dorsal**: high, low, back, tense
- **Manner**: nasal, lateral, strident  
- **Laryngeal**: voice, spread_glottis, constricted_glottis
- **Vocalic**: round, atr
- **Suprasegmental**: stress, tone, length
- **Acoustic**: f0, f1, f2, f3, intensity

**Advantages:**
- **Unified representation**: No categorical vowel/consonant distinction
- **Gradient phenomena**: Supports continuous variation
- **Interpolation**: Can create intermediate sounds
- **Distance metrics**: Quantitative similarity measures

## Using Feature Systems

### Basic Usage

```python
from alteruphono.phonology.sound_v2 import Sound

# Create sounds with different systems
ipa_sound = Sound(grapheme='p', feature_system='ipa_categorical')
unified_sound = Sound(grapheme='p', feature_system='unified_distinctive')

# Both represent /p/ but with different feature representations
print(ipa_sound.features)      # Categorical features
print(unified_sound.features)  # Scalar features
```

### Feature System Context

```python
from alteruphono.phonology.feature_systems.conversion import feature_system_context

# Temporarily change default system
with feature_system_context('unified_distinctive'):
    sound = Sound(grapheme='p')  # Uses unified system
    print(sound.feature_system_name)  # 'unified_distinctive'

# Default system restored outside context
```

### Feature Arithmetic

```python
# IPA categorical system
ipa_p = Sound(grapheme='p', feature_system='ipa_categorical')
ipa_voiced = ipa_p + 'voiced'  # Results in /b/

# Unified distinctive system  
unified_p = Sound(grapheme='p', feature_system='unified_distinctive')
unified_voiced = unified_p + 'voice=1.0'  # Adds full voicing

# Scalar arithmetic
slightly_voiced = unified_p + 'voice=0.3'  # Partial voicing
```

### System Conversion

```python
# Convert between systems
ipa_sound = Sound(grapheme='p', feature_system='ipa_categorical')
unified_sound = ipa_sound.convert_to_system('unified_distinctive')

# Distance calculations (cross-system)
distance = ipa_sound.distance_to(unified_sound)  # Should be small for /p/
```

## Advanced Features

### Unified Distinctive System Capabilities

#### Sound Interpolation
```python
unified_system = get_feature_system('unified_distinctive')

p_features = unified_system.grapheme_to_features('p')
b_features = unified_system.grapheme_to_features('b')

# Create sound halfway between /p/ and /b/
intermediate = unified_system.interpolate_sounds(p_features, b_features, 0.5)
print(f"Voice value: {intermediate.get_feature('voice').value}")  # 0.0
```

#### Gradient Feature Operations
```python
# Create sound with intermediate voicing
sound = Sound(description='[voice=0.3, labial=1.0]', feature_system='unified_distinctive')

# Increment voicing
more_voiced = sound.increment_feature('voice', 0.2)  # voice: 0.3 -> 0.5
```

#### Vowel/Consonant Detection
```python
unified_system = get_feature_system('unified_distinctive')

a_features = unified_system.grapheme_to_features('a')
p_features = unified_system.grapheme_to_features('p')

print(unified_system.is_vowel_like(a_features))     # True
print(unified_system.is_consonant_like(p_features)) # True
```

### Feature System Conversion

#### Automatic Conversion
```python
from alteruphono.phonology.feature_systems.conversion import convert_sound_between_systems

# Convert IPA features to unified
ipa_features = ipa_system.grapheme_to_features('p')
unified_features = convert_sound_between_systems(
    'ipa_categorical', 'unified_distinctive', ipa_features
)
```

#### Conversion Recommendations
```python
from alteruphono.phonology.feature_systems.conversion import get_conversion_recommendations

recommendations = get_conversion_recommendations('ipa_categorical', 'unified_distinctive')
for rec in recommendations:
    print(f"- {rec}")
```

## Implementation Guide

### Creating a Custom Feature System

1. **Inherit from FeatureSystem**:
```python
from alteruphono.phonology.feature_systems import FeatureSystem

class MyFeatureSystem(FeatureSystem):
    @property
    def name(self) -> str:
        return "my_system"
    
    @property
    def description(self) -> str:
        return "My custom phonological feature system"
    
    @property
    def supported_value_types(self) -> Set[FeatureValueType]:
        return {FeatureValueType.SCALAR, FeatureValueType.CATEGORICAL}
```

2. **Implement required methods**:
```python
def grapheme_to_features(self, grapheme: str) -> Optional[FeatureBundle]:
    """Convert grapheme to feature bundle."""
    if grapheme == 'p':
        return FeatureBundle(frozenset([
            FeatureValue('stop', 1.0, FeatureValueType.SCALAR),
            FeatureValue('labial', 1.0, FeatureValueType.SCALAR),
            FeatureValue('voiced', -1.0, FeatureValueType.SCALAR)
        ]))
    # ... handle other graphemes
    return None

def features_to_grapheme(self, features: FeatureBundle) -> str:
    """Convert features back to grapheme."""
    # Find best matching grapheme
    # ... implementation
    return '?'  # Default for unknown

def parse_feature_specification(self, spec: str) -> FeatureBundle:
    """Parse feature specification string."""
    # ... implementation
    pass

def add_features(self, base: FeatureBundle, additional: FeatureBundle) -> FeatureBundle:
    """Add features with system-specific logic."""
    # ... implementation
    pass

def validate_features(self, features: FeatureBundle) -> List[str]:
    """Validate feature bundle."""
    # ... return list of error messages
    return []
```

3. **Register the system**:
```python
from alteruphono.phonology.feature_systems import register_feature_system

register_feature_system(MyFeatureSystem())
```

### Best Practices

1. **Feature Naming**: Use consistent, descriptive feature names
2. **Value Ranges**: Document expected value ranges for scalar features
3. **Validation**: Implement thorough validation for feature combinations
4. **Documentation**: Provide clear descriptions of feature meanings
5. **Testing**: Create comprehensive test suites for custom systems

## Backward Compatibility

The new architecture maintains full backward compatibility:

```python
# Old API still works
from alteruphono.phonology.sound import Sound  # Uses default system

sound = Sound(grapheme='p')
print(sound.fvalues)  # Returns frozenset of strings (old format)

# New API provides additional capabilities
from alteruphono.phonology.sound_v2 import Sound  # New enhanced version

sound = Sound(grapheme='p')
print(sound.features)  # Returns FeatureBundle (new format)
print(sound.fvalues)   # Still works (converted format)
```

## Migration Guide

### For Existing Code

1. **No changes required** - existing code continues to work
2. **Optional enhancement** - use `sound_v2.Sound` for new features
3. **Gradual adoption** - mix old and new APIs as needed

### For New Projects

1. **Start with enhanced Sound class**:
```python
from alteruphono.phonology.sound_v2 import Sound
```

2. **Choose appropriate feature system**:
```python
# For traditional phonology
sound = Sound(grapheme='p', feature_system='ipa_categorical')

# For gradient/quantitative work
sound = Sound(grapheme='p', feature_system='unified_distinctive')
```

3. **Leverage new capabilities**:
```python
# Distance calculations
distance = sound1.distance_to(sound2)

# Feature access
value = sound.get_feature_value('voice')

# System conversion
converted = sound.convert_to_system('unified_distinctive')
```

## Research Applications

### Phonological Analysis
- Compare categorical vs. gradient approaches
- Analyze sound change patterns with different feature systems
- Study cross-linguistic phonological typology

### Computational Modeling
- Use scalar features for neural network training
- Implement gradient phonological processes
- Model acoustic-phonetic interfaces

### Historical Linguistics
- Track feature evolution across time
- Model sound change probability
- Compare reconstruction methods

## Future Directions

### Planned Enhancements
1. **More built-in systems** - Additional feature theories
2. **Conversion improvement** - Better cross-system mapping
3. **Performance optimization** - Faster feature operations
4. **Visualization tools** - Feature space plotting
5. **Integration APIs** - Export to other frameworks

### Research Opportunities
1. **Custom systems** - Implement specialized feature theories
2. **Hybrid approaches** - Combine multiple systems
3. **Machine learning** - Train feature systems from data
4. **Acoustic integration** - Connect to speech processing

## Conclusion

The pluggable feature system architecture provides alteruphono with unprecedented flexibility for phonological research. By supporting multiple feature theories within a unified framework, researchers can:

- Explore different theoretical approaches
- Compare results across systems
- Develop new phonological models
- Maintain compatibility with existing work

This architecture positions alteruphono as a leading platform for computational phonology research, capable of supporting both traditional categorical approaches and modern gradient/quantitative methods.

The unified distinctive feature system, in particular, represents a significant advancement in computational phonology, providing a mathematically principled approach to sound representation that eliminates artificial categorical boundaries while maintaining linguistic interpretability.