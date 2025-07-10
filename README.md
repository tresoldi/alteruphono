# AlteruPhono: Advanced Phonological Evolution Modeling

[![PyPI](https://img.shields.io/pypi/v/alteruphono.svg)](https://pypi.org/project/alteruphono)
![Python package](https://github.com/tresoldi/alteruphono/workflows/Python%20package/badge.svg)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/1c6218b0741d453c96c72e9504acd757)](https://app.codacy.com/manual/tresoldi/alteruphono?utm_source=github.com&utm_medium=referral&utm_content=tresoldi/alteruphono&utm_campaign=Badge_Grade_Dashboard)

**AlteruPhono** is a comprehensive Python library for modeling phonological evolution and sound change in historical linguistics. It provides sophisticated tools for simulating, analyzing, and reconstructing the phonological development of languages over time, with support for gradient sound changes, feature-based modeling, and comparative reconstruction.

## Table of Contents

- [Key Features](#key-features)
- [Historical Linguistics Applications](#historical-linguistics-applications)
- [Phonological Modeling Capabilities](#phonological-modeling-capabilities)
- [Quick Start](#quick-start)
- [Feature Systems](#feature-systems)
- [Sound Change Engine](#sound-change-engine)
- [Documentation](#documentation)
- [Installation](#installation)
- [Citation](#citation)

## Key Features

### 🔬 **Advanced Phonological Modeling**
- **Three comprehensive feature systems**: IPA categorical, unified distinctive features, and Tresoldi comprehensive system (1,081 sounds, 43 features)
- **Gradient sound changes**: Model continuous phonological processes with scalar feature values
- **Feature-based rules**: Define sound changes using phonological features rather than just segments
- **Cross-system compatibility**: Convert between different feature representations seamlessly

### ⚡ **High-Performance Sound Change Engine**
- **Bidirectional application**: Apply sound changes forward (evolution) and backward (reconstruction)
- **Environmental conditioning**: Complex phonological environments with feature-based matching
- **Rule ordering and interaction**: Model feeding, bleeding, and other rule interactions
- **Efficient processing**: Optimized for large-scale linguistic datasets

### 🌍 **Comprehensive Phonological Coverage**
- **Cross-linguistic support**: Handle diverse phonological inventories from world languages
- **Complex segments**: Support for affricates, prenasalized stops, clicks, and other complex sounds
- **Suprasegmental features**: Model tone, length, stress, and other prosodic features
- **Rare phonological phenomena**: Specialized support for clicks, ejectives, implosives, and more

## Historical Linguistics Applications

### 📚 **Language Evolution Simulation**

AlteruPhono excels in modeling realistic language change scenarios:

```python
import alteruphono
from alteruphono.phonology.sound_change import SoundChangeEngine, FeatureChangeRule
from alteruphono.phonology.sound_v2 import Sound

# Model Proto-Indo-European to Germanic sound shift (Grimm's Law)
engine = SoundChangeEngine(feature_system_name='unified_distinctive')

# Define Grimm's Law: voiceless stops become fricatives
grimms_law = FeatureChangeRule(
    name="grimms_law_p_f",
    feature_conditions={"consonantal": 1.0, "voice": -1.0, "continuant": -1.0},
    feature_changes=[
        FeatureChange(feature_name="continuant", target_value=1.0)
    ]
)

# Apply to Proto-Germanic words
pie_word = [Sound(g, 'unified_distinctive') for g in ['p', 'a', 't', 'e', 'r']]
germanic_result = engine.apply_rule(grimms_law, pie_word)
```

### 🔍 **Comparative Reconstruction**

Reconstruct proto-languages from descendant forms:

```python
# Reverse-engineer sound changes to find proto-forms
proto_candidates = alteruphono.backward("# f a ð e r #", "p > f / # _")
# Returns multiple possible reconstructions: [['# p a ð e r #'], ['# f a ð e r #']]
```

### 📊 **Phonological Distance Analysis**

Measure phonological similarity for:
- **Language classification**: Calculate distances between phonological systems
- **Contact linguistics**: Detect borrowing patterns and areal features
- **Evolutionary modeling**: Track phonological change over time

```python
# Compare phonological distance between related sounds
p_sound = Sound('p', 'tresoldi_distinctive')
b_sound = Sound('b', 'tresoldi_distinctive')
f_sound = Sound('f', 'tresoldi_distinctive')

voicing_distance = p_sound.distance_to(b_sound)    # Small distance (voicing only)
manner_distance = p_sound.distance_to(f_sound)     # Larger distance (manner change)
```

## Phonological Modeling Capabilities

### 🎯 **Feature-Based Sound Changes**

Model natural phonological processes using distinctive features:

```python
# Intervocalic voicing: voiceless stops become voiced between vowels
intervocalic_voicing = FeatureChangeRule(
    name="intervocalic_voicing",
    feature_conditions={"consonantal": 1.0, "voice": -1.0, "sonorant": -1.0},
    feature_changes=[FeatureChange(feature_name="voice", target_value=1.0)],
    environment=PhonologicalEnvironment(
        left_pattern="V",      # Vowel before
        right_pattern="V"      # Vowel after
    )
)
```

### 📈 **Gradient Phonological Changes**

Model continuous sound change with scalar features:

```python
# Gradual lenition: progressive weakening of consonants
lenition = FeatureChangeRule(
    name="lenition",
    feature_changes=[
        FeatureChange(
            feature_name="continuant",
            target_value=0.8,           # Partial continuancy
            change_type=ChangeType.GRADIENT,
            change_strength=0.3         # Gradual application
        )
    ]
)
```

### 🌐 **Cross-Linguistic Phonological Patterns**

Study universal tendencies and language-specific patterns:

```python
# Test universal implicational hierarchies
def test_implicational_hierarchy(inventory):
    """Test if inventory follows place hierarchy: labial > coronal > dorsal"""
    labial_count = len([s for s in inventory if s.has_feature('labial')])
    coronal_count = len([s for s in inventory if s.has_feature('coronal')])
    dorsal_count = len([s for s in inventory if s.has_feature('dorsal')])
    
    return labial_count >= coronal_count >= dorsal_count
```

## Quick Start

### Basic Sound Change Application

```python
import alteruphono

# Simple sound change: p becomes f word-initially
result = alteruphono.forward("# p a t e r #", "p > f / # _")
print(' '.join(result))  # "# f a t e r #"

# Reverse reconstruction
proto_forms = alteruphono.backward("# f a t e r #", "p > f / # _")
print(proto_forms)  # [['#', 'p', 'a', 't', 'e', 'r', '#'], ['#', 'f', 'a', 't', 'e', 'r', '#']]
```

### Advanced Feature-Based Modeling

```python
from alteruphono.phonology.sound_change import SoundChangeEngine
from alteruphono.phonology.sound_v2 import Sound

# Create sounds with rich feature representations
engine = SoundChangeEngine(feature_system_name='tresoldi_distinctive')

# Model complex sound inventory (1,081 sounds across world languages)
word = [
    Sound('kʷʰ', 'tresoldi_distinctive'),  # Aspirated labialized velar
    Sound('a', 'tresoldi_distinctive'),
    Sound('ⁿd', 'tresoldi_distinctive')    # Prenasalized stop
]

# Apply sophisticated phonological rules
result = engine.apply_rule_set(complex_ruleset, word)
```

## Feature Systems

AlteruPhono provides three sophisticated feature systems for different research needs:

### 1. **IPA Categorical System**
- Traditional binary distinctive features
- Optimized for basic phonological operations
- Compatible with standard linguistic notation

### 2. **Unified Distinctive System**
- Scalar feature values enabling gradient modeling
- Support for continuous phonological spaces
- Advanced arithmetic operations on features

### 3. **Tresoldi Comprehensive System**
- **1,081 sounds** from world languages
- **43 distinctive features** covering all major phonological categories
- Comprehensive coverage including:
  - Click consonants (ǀ, ǁ, ǃ, ǂ, ʘ)
  - Prenasalized stops (ⁿd, ⁿg, ⁿk)
  - Complex affricates and clusters
  - Rare phonological features

```python
# Compare feature system capabilities
from alteruphono.phonology.feature_systems import get_feature_system

ipa_system = get_feature_system('ipa_categorical')
tresoldi_system = get_feature_system('tresoldi_distinctive')

print(f"IPA sounds: {ipa_system.get_sound_count()}")
print(f"Tresoldi sounds: {tresoldi_system.get_sound_count()}")  # 1,081 sounds
print(f"Tresoldi features: {len(tresoldi_system.get_feature_names())}")  # 43 features
```

## Sound Change Engine

### Rule Types and Applications

#### **Categorical Rules**
Traditional sound changes with discrete outcomes:
```python
# Rhotacism: /s/ becomes /r/ between vowels
rhotacism = SoundChangeRule(
    name="rhotacism",
    source_pattern="s",
    target_pattern="r",
    environment="V _ V"
)
```

#### **Gradient Rules**
Continuous sound changes with partial application:
```python
# Progressive palatalization
palatalization = FeatureChangeRule(
    name="palatalization",
    feature_changes=[
        FeatureChange(
            feature_name="coronal",
            target_value=0.7,
            change_type=ChangeType.GRADIENT
        )
    ]
)
```

#### **Environmental Conditioning**
Complex phonological environments:
```python
# Devoicing in syllable codas
coda_devoicing = FeatureChangeRule(
    name="coda_devoicing",
    feature_conditions={"voice": 1.0, "sonorant": -1.0},
    feature_changes=[FeatureChange(feature_name="voice", target_value=-1.0)],
    environment=PhonologicalEnvironment(
        right_pattern=["#", "C"],  # Word boundary or consonant
        position="coda"
    )
)
```

### Performance Characteristics

AlteruPhono is optimized for large-scale linguistic analysis:

- **Sound creation**: < 1ms per sound (even with 1,081-sound inventory)
- **Feature access**: < 0.1ms per operation
- **Rule application**: < 50ms per complex rule on typical words
- **Distance calculation**: < 10ms between sounds with 43 features

## Documentation

### 📖 **User Guides**
- [Phonological Feature Systems Guide](docs/feature_systems.md)
- [Sound Change Modeling Tutorial](docs/sound_change_tutorial.md)
- [Historical Linguistics Workflows](docs/historical_linguistics.md)

### 💻 **Example Notebooks**
- [Comparative Reconstruction Examples](examples/comparative_reconstruction.ipynb)
- [Language Evolution Simulation](examples/evolution_modeling.ipynb)
- [Cross-Linguistic Phonological Analysis](examples/cross_linguistic_analysis.ipynb)

### 🔍 **API Reference**
- [Core API Documentation](docs/api_reference.md)
- [Feature Systems API](docs/feature_systems_api.md)
- [Sound Change Engine API](docs/sound_change_api.md)

## Installation

### Standard Installation
```bash
pip install alteruphono
```

### Development Installation
```bash
git clone https://github.com/tresoldi/alteruphono.git
cd alteruphono
pip install -e .
```

### Requirements
- Python 3.7+
- NumPy (for numerical operations)
- Pandas (for data handling)

## Research Applications

AlteruPhono has been designed for serious historical linguistics research:

### **Comparative Method**
- Automate systematic correspondences detection
- Generate proto-language reconstructions
- Validate reconstruction hypotheses

### **Language Classification**
- Calculate phonological distances for family trees
- Test competing classification hypotheses
- Detect contact-induced changes

### **Diachronic Phonology**
- Model realistic sound change pathways
- Test theories of phonological change
- Simulate language evolution scenarios

### **Typological Studies**
- Test universal phonological tendencies
- Study cross-linguistic patterns
- Analyze rare phonological phenomena

## Citation

If you use AlteruPhono in your research, please cite:

```bibtex
@software{tresoldi2024alteruphono,
  author = {Tresoldi, Tiago},
  title = {AlteruPhono: Advanced Phonological Evolution Modeling},
  version = {2.0},
  year = {2024},
  url = {https://github.com/tresoldi/alteruphono},
  note = {Python library for historical linguistics and phonological analysis}
}
```

## Contributing

We welcome contributions from the linguistics and computational community:

- **Bug reports**: Use GitHub issues for bug reports
- **Feature requests**: Suggest new phonological modeling capabilities
- **Documentation**: Help improve examples and tutorials
- **Code contributions**: Submit pull requests for new features

## License

AlteruPhono is released under the MIT License. See [LICENSE](LICENSE) for details.

## Support

- **Documentation**: [docs/](docs/)
- **Examples**: [examples/](examples/)
- **Issues**: [GitHub Issues](https://github.com/tresoldi/alteruphono/issues)
- **Discussions**: [GitHub Discussions](https://github.com/tresoldi/alteruphono/discussions)

---

**AlteruPhono** - *Empowering historical linguistics through computational phonology*