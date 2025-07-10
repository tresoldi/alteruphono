# Sound Change Rule Engine

This document describes the comprehensive sound change rule engine implemented for alteruphono, which leverages the unified distinctive feature system to enable both traditional categorical and novel gradient sound changes.

## Overview

The sound change engine provides a powerful framework for modeling phonological changes with unprecedented flexibility:

- **Categorical changes**: Traditional A → B sound changes
- **Gradient changes**: Continuous feature modifications using scalar values
- **Environmental conditioning**: Complex contextual patterns
- **Probabilistic application**: Variable rule implementation
- **Rule interactions**: Feeding, bleeding, and ordering effects
- **Historical modeling**: Multi-stage sound change simulation

## Architecture

### Core Components

1. **SoundChangeRule**: Basic rule representation
2. **FeatureChangeRule**: Feature-specific changes
3. **SoundChangeEngine**: Rule application engine
4. **PhonologicalEnvironment**: Environmental condition matching
5. **GradientChange**: Continuous feature modifications
6. **RuleSet**: Collections of ordered rules

### Key Features

- **Unified distinctive system integration**: Leverages scalar features for gradient changes
- **Modular design**: Mix and match different rule types
- **Performance optimized**: Efficient rule application with caching
- **Research-ready**: Built for phonological investigation

## Basic Usage

### Simple Categorical Changes

```python
from alteruphono.phonology.sound_change import SoundChangeRule, SoundChangeEngine
from alteruphono.phonology.sound_v2 import Sound

# Create engine
engine = SoundChangeEngine()

# Create rule: p → f
rule = SoundChangeRule(
    name="p_to_f",
    source_pattern="p",
    target_pattern="f"
)

# Create test sound
sound = Sound(grapheme='p', feature_system='unified_distinctive')

# Apply rule
result = engine.apply_rule(rule, [sound])
print(result.modified_sequence[0].grapheme())  # → 'f'
```

### Environmental Conditioning

```python
from alteruphono.phonology.sound_change.rules import EnvironmentalCondition

# Rule: p → f / V_V (between vowels)
env = EnvironmentalCondition(
    left_context="[sonorant=1.0]",   # After vowel
    right_context="[sonorant=1.0]"   # Before vowel
)

rule = SoundChangeRule(
    name="intervocalic_lenition",
    source_pattern="p",
    target_pattern="f",
    environment=env
)
```

### Gradient Feature Changes

```python
from alteruphono.phonology.sound_change.rules import FeatureChange, ChangeType
from alteruphono.phonology.sound_change import FeatureChangeRule

# Partial voicing: increase voice by 0.3
voicing_change = FeatureChange(
    feature_name="voice",
    target_value=0.3,  # Partial voicing
    change_strength=1.0,
    change_type=ChangeType.GRADIENT
)

rule = FeatureChangeRule(
    name="partial_voicing",
    source_pattern="",
    target_pattern=[voicing_change],
    feature_conditions={"voice": -1.0},  # Only voiceless sounds
    feature_changes=[voicing_change]
)
```

## Advanced Features

### Gradient Rule Builder

```python
from alteruphono.phonology.sound_change.gradients import GradientRuleBuilder

# Fluent interface for complex rules
rule = (GradientRuleBuilder()
        .shift_feature("voice", 1.0, 0.7)         # Increase voicing
        .shift_feature("continuant", 0.5, 0.3)     # Increase continuancy
        .with_condition("consonantal", "+consonantal")
        .with_probability(0.8)                     # 80% application
        .build("complex_lenition"))
```

### Feature Shift Systems

```python
from alteruphono.phonology.sound_change import FeatureShift

# Model vowel chain shifts
shift = FeatureShift()
shift.add_shift("high", -1.0, 1.0, change_rate=0.3)  # Raise vowels
shift.add_shift("tense", -1.0, 1.0, change_rate=0.2)  # Increase tenseness

# Add correlation between features
shift.add_correlation("high", "tense", 0.5)

# Apply to sound
result = shift.apply_to_sound(vowel_sound, strength=1.0)
```

### Probabilistic Rules

```python
# Variable rule application
rule = SoundChangeRule(
    name="variable_voicing",
    source_pattern="p",
    target_pattern="b",
    probability=0.3  # 30% chance of application
)

# Multiple trials show statistical behavior
for trial in range(100):
    result = engine.apply_rule(rule, test_sequence)
    # Rule applies ~30% of the time
```

### Rule Sets and Ordering

```python
from alteruphono.phonology.sound_change import RuleSet

# Create ordered rule set
rules = RuleSet(name="sound_changes")
rules.add_rule(rule1)  # Applied first
rules.add_rule(rule2)  # Applied second

# Iterative application (for feeding relationships)
rules.iterative = True
rules.max_iterations = 5

# Apply entire rule set
simulation = engine.apply_rule_set(rules, word)
```

## Research Applications

### Historical Sound Change Modeling

```python
# Model Grimm's Law (simplified)
grimm = RuleSet(name="grimms_law")

# p t k → f θ x
grimm.add_rule(SoundChangeRule("p_to_f", "p", "f"))
grimm.add_rule(SoundChangeRule("t_to_th", "t", "θ"))  
grimm.add_rule(SoundChangeRule("k_to_x", "k", "x"))

# Apply to Proto-Indo-European word
pie_word = [Sound(grapheme=g) for g in "pater"]
result = engine.apply_rule_set(grimm, pie_word)
# Result: "faθer" (Proto-Germanic)
```

### Gradual Change Simulation

```python
# Simulate gradual voicing over multiple generations
simulations = engine.simulate_gradual_change(
    rule=voicing_rule,
    sequence=test_word,
    steps=10
)

# Track progression over time
for i, sim in enumerate(simulations):
    voice_val = sim.final_sequence[0].get_feature_value('voice')
    print(f"Generation {i}: voice = {voice_val:.2f}")
```

### Sound Change Diffusion

```python
from alteruphono.phonology.sound_change.gradients import model_sound_change_diffusion

# Model how change spreads through population
diffusion = model_sound_change_diffusion(
    initial_sounds=word,
    rule=innovation_rule,
    generations=100,
    population_size=1000,
    innovation_rate=0.01
)

# Analyze S-curve adoption pattern
print(f"Final adoption rate: {diffusion['final_adoption_rate']:.1%}")
print(f"Generations to completion: {diffusion['generations_to_completion']}")
```

## Predefined Rules

The engine includes several predefined gradient rules for common processes:

```python
from alteruphono.phonology.sound_change.gradients import (
    create_lenition_rule,
    create_vowel_raising_rule,
    create_voicing_assimilation_rule
)

# Predefined lenition process
lenition = create_lenition_rule(strength=0.5)

# Vowel raising for chain shifts  
raising = create_vowel_raising_rule(height_increase=0.3)

# Voicing assimilation
assimilation = create_voicing_assimilation_rule(strength=0.7)
```

## Environmental Conditions

### Pattern Syntax

- **V**: Vowel (sonorant=1.0, consonantal<0)
- **C**: Consonant (consonantal>0)
- **#**: Word boundary
- **[features]**: Feature specification
- **_**: Target position

### Examples

```python
from alteruphono.phonology.sound_change.environments import PhonologicalEnvironment

# Between vowels
env = PhonologicalEnvironment.from_string("V _ V")

# Word-initial
env = PhonologicalEnvironment.from_string("# _")

# Before voiced consonants  
env = PhonologicalEnvironment.from_string("_ [+voice, +consonantal]")

# Complex conditions
env = PhonologicalEnvironment.from_string(
    "V _ V / [+consonantal] // [-voice]"  # Between V, if consonant, unless voiceless
)
```

## Performance and Statistics

### Engine Monitoring

```python
# Get performance statistics
stats = engine.get_statistics()
print(f"Total simulations: {stats['total_simulations']}")
print(f"Average changes per simulation: {stats['average_changes_per_simulation']:.2f}")
print(f"Most used rule: {stats['most_used_rule']}")

# Rule usage frequency
for rule_name, count in stats['rule_usage_frequency'].items():
    print(f"  {rule_name}: {count} applications")
```

### Rule Interaction Analysis

```python
# Analyze rule interactions
analysis = engine.analyze_rule_interactions(rule_set, test_sequences)

# Check for ordering effects
for rule1, interactions in analysis['interaction_matrix'].items():
    for rule2, data in interactions.items():
        if data['order_sensitive']:
            print(f"{rule1} and {rule2} have ordering effects")
```

## Advanced Topics

### Custom Feature Systems

The sound change engine works with any feature system:

```python
# Use different feature system
rule = SoundChangeRule(
    name="custom_change",
    source_pattern="p",
    target_pattern="f",
    feature_system_name="my_custom_system"
)
```

### Rule Debugging

```python
# Detailed change tracking
result = engine.apply_rule(rule, sequence)

for application in result.applications:
    if application.changed:
        changes = application.get_feature_changes()
        for feature, (old, new) in changes.items():
            print(f"{feature}: {old} → {new}")
```

### Performance Optimization

```python
# Batch processing
sequences = [word1, word2, word3, ...]
for sequence in sequences:
    result = engine.apply_rule_set(rules, sequence)
    # Engine caches feature lookups automatically
```

## Integration with Feature Systems

### Unified Distinctive Features

The engine is optimized for the unified distinctive system:

```python
# Scalar feature modifications
rule = (GradientRuleBuilder()
        .shift_feature("voice", 0.8)      # 80% voicing
        .shift_feature("continuant", 0.3)  # 30% more continuant
        .build("gradient_change"))

# Natural for gradient processes
lenition_strength = 0.4  # 40% lenition
rule.change_strength = lenition_strength
```

### Cross-System Compatibility

```python
# Convert between systems during rule application
ipa_sound = Sound(grapheme='p', feature_system='ipa_categorical')
unified_result = rule.apply_to(ipa_sound)  # Auto-converts to unified system
```

## Best Practices

### Rule Design

1. **Start simple**: Begin with categorical rules, add gradient features as needed
2. **Test environments**: Verify environmental conditions with multiple contexts
3. **Monitor statistics**: Use engine statistics to optimize rule sets
4. **Document patterns**: Keep clear descriptions of linguistic motivations

### Performance

1. **Cache frequently used rules**: Engine caches automatically
2. **Batch similar operations**: Process multiple sequences together
3. **Profile complex rule sets**: Use interaction analysis for optimization
4. **Limit iterations**: Set reasonable max_iterations for iterative rule sets

### Research Workflow

1. **Define hypothesis**: Clear statement of expected changes
2. **Model incrementally**: Build rule sets step by step
3. **Validate with data**: Test against known historical changes
4. **Analyze interactions**: Check for unexpected rule relationships

## Examples and Demonstrations

See `examples/sound_change_demo.py` for comprehensive demonstrations including:

- Basic categorical changes
- Environmental conditioning  
- Gradient feature modifications
- Complex rule interactions
- Historical sound change modeling
- Performance monitoring

## Conclusion

The sound change engine represents a major advancement in computational phonology, enabling researchers to model both traditional and gradient sound changes within a unified framework. The integration with the unified distinctive feature system provides unprecedented flexibility for investigating phonological processes across languages and time periods.

Key advantages:

- **Theoretical flexibility**: Supports multiple approaches to phonological change
- **Empirical grounding**: Gradient features enable data-driven modeling
- **Research applications**: Tools for historical linguistics and phonological theory
- **Performance**: Optimized for large-scale analysis
- **Extensibility**: Pluggable architecture for custom feature systems

This engine opens new possibilities for phonological research, from fine-grained acoustic analysis to broad typological studies.