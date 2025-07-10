# AlteruPhono API Reference

This comprehensive API reference covers all major classes, functions, and modules in AlteruPhono for phonological modeling and sound change analysis.

## Table of Contents

1. [Core API](#core-api)
2. [Sound Representation](#sound-representation)
3. [Feature Systems](#feature-systems)
4. [Sound Change Engine](#sound-change-engine)
5. [Phonological Environments](#phonological-environments)
6. [Utilities and Helpers](#utilities-and-helpers)

## Core API

### Main Module Functions

#### `alteruphono.forward(sequence, rule_string)`

Apply sound change rule in forward direction (evolution).

**Parameters:**
- `sequence` (str): Space-separated sound sequence (e.g., "# p a t e r #")
- `rule_string` (str): Sound change rule in standard notation (e.g., "p > f / # _")

**Returns:**
- `list[str]`: Modified sound sequence

**Example:**
```python
import alteruphono
result = alteruphono.forward("# p a t e r #", "p > f / # _")
print(result)  # ['#', 'f', 'a', 't', 'e', 'r', '#']
```

#### `alteruphono.backward(sequence, rule_string)`

Apply sound change rule in backward direction (reconstruction).

**Parameters:**
- `sequence` (str): Space-separated sound sequence
- `rule_string` (str): Sound change rule in standard notation

**Returns:**
- `list[list[str]]`: List of possible proto-forms

**Example:**
```python
proto_forms = alteruphono.backward("# f a t e r #", "p > f / # _")
print(proto_forms)  # [['#', 'p', 'a', 't', 'e', 'r', '#'], ['#', 'f', 'a', 't', 'e', 'r', '#']]
```

## Sound Representation

### `Sound` Class

Primary class for representing individual sounds with phonological features.

#### Constructor

```python
Sound(grapheme, feature_system='ipa_categorical')
```

**Parameters:**
- `grapheme` (str): Graphemic representation of the sound
- `feature_system` (str): Feature system to use ('ipa_categorical', 'unified_distinctive', 'tresoldi_distinctive')

#### Methods

##### `grapheme()`

Get the graphemic representation of the sound.

**Returns:**
- `str`: Grapheme string

**Example:**
```python
from alteruphono.phonology.sound_v2 import Sound
sound = Sound('p', 'unified_distinctive')
print(sound.grapheme())  # 'p'
```

##### `get_feature_value(feature_name)`

Get the value of a specific feature.

**Parameters:**
- `feature_name` (str): Name of the feature

**Returns:**
- `float`: Feature value (-1.0 to 1.0 for scalar systems, -1.0/1.0 for binary)

**Example:**
```python
sound = Sound('p', 'unified_distinctive')
voice_value = sound.get_feature_value('voice')
print(voice_value)  # -1.0 (voiceless)
```

##### `has_feature(feature_name)`

Check if sound has a specific feature.

**Parameters:**
- `feature_name` (str): Name of the feature

**Returns:**
- `bool`: True if feature exists

##### `distance_to(other_sound)`

Calculate phonological distance to another sound.

**Parameters:**
- `other_sound` (Sound): Target sound for distance calculation

**Returns:**
- `float`: Euclidean distance in feature space

**Example:**
```python
p_sound = Sound('p', 'tresoldi_distinctive')
b_sound = Sound('b', 'tresoldi_distinctive')
distance = p_sound.distance_to(b_sound)
print(f"Distance: {distance:.3f}")
```

##### `__add__(feature_specification)`

Add feature modifications using arithmetic syntax.

**Parameters:**
- `feature_specification` (str): Comma-separated feature modifications (e.g., "voice=1.0,continuant=0.5")

**Returns:**
- `Sound`: New sound with modified features

**Example:**
```python
p_sound = Sound('p', 'unified_distinctive')
voiced_p = p_sound + 'voice=2.0'  # Add voicing
print(voiced_p.get_feature_value('voice'))  # 1.0 (clamped)
```

### `FeatureBundle` Class

Container for phonological features with values.

#### Constructor

```python
FeatureBundle(features)
```

**Parameters:**
- `features` (frozenset[FeatureValue]): Set of feature-value pairs

#### Methods

##### `get_feature(feature_name)`

Get specific feature from bundle.

**Parameters:**
- `feature_name` (str): Name of feature to retrieve

**Returns:**
- `FeatureValue | None`: Feature value object or None if not found

##### `get_feature_names()`

Get list of all feature names in bundle.

**Returns:**
- `list[str]`: List of feature names

### `FeatureValue` Class

Individual feature-value pair.

#### Constructor

```python
FeatureValue(feature, value, value_type)
```

**Parameters:**
- `feature` (str): Feature name
- `value` (float): Feature value
- `value_type` (FeatureValueType): Type of value (BINARY or SCALAR)

#### Properties

- `feature` (str): Feature name
- `value` (float): Feature value
- `value_type` (FeatureValueType): Value type

## Feature Systems

### Feature System Functions

#### `get_feature_system(system_name)`

Get a feature system instance.

**Parameters:**
- `system_name` (str): Name of feature system ('ipa_categorical', 'unified_distinctive', 'tresoldi_distinctive')

**Returns:**
- `FeatureSystem`: Feature system instance

**Example:**
```python
from alteruphono.phonology.feature_systems import get_feature_system
system = get_feature_system('tresoldi_distinctive')
print(f"Sounds: {system.get_sound_count()}")  # 1081
```

#### `list_feature_systems()`

Get list of available feature systems.

**Returns:**
- `list[str]`: List of system names

#### `convert_between_systems(features, source_system, target_system)`

Convert features between different feature systems.

**Parameters:**
- `features` (FeatureBundle): Features to convert
- `source_system` (str): Source system name
- `target_system` (str): Target system name

**Returns:**
- `FeatureBundle`: Converted features

**Example:**
```python
from alteruphono.phonology.feature_systems import convert_between_systems
ipa_sound = Sound('p', 'ipa_categorical')
tresoldi_features = convert_between_systems(
    ipa_sound.features, 'ipa_categorical', 'tresoldi_distinctive'
)
```

### `FeatureSystem` Base Class

Abstract base class for all feature systems.

#### Abstract Methods

##### `grapheme_to_features(grapheme)`

Convert grapheme to feature bundle.

**Parameters:**
- `grapheme` (str): Graphemic representation

**Returns:**
- `FeatureBundle | None`: Feature bundle or None if not found

##### `has_grapheme(grapheme)`

Check if grapheme is supported.

**Parameters:**
- `grapheme` (str): Graphemic representation

**Returns:**
- `bool`: True if supported

##### `get_sound_count()`

Get total number of sounds in system.

**Returns:**
- `int`: Number of sounds

##### `get_feature_names()`

Get list of all feature names.

**Returns:**
- `list[str]`: Feature names

#### Common Methods

##### `is_positive(features, feature_name)`

Check if feature has positive value.

**Parameters:**
- `features` (FeatureBundle): Feature bundle
- `feature_name` (str): Feature name

**Returns:**
- `bool`: True if positive

##### `is_negative(features, feature_name)`

Check if feature has negative value.

**Parameters:**
- `features` (FeatureBundle): Feature bundle
- `feature_name` (str): Feature name

**Returns:**
- `bool`: True if negative

##### `get_sounds_with_feature(feature_name, positive=True)`

Get sounds with specific feature value.

**Parameters:**
- `feature_name` (str): Feature name
- `positive` (bool): Whether to find positive or negative values

**Returns:**
- `list[str]`: List of graphemes

## Sound Change Engine

### `SoundChangeEngine` Class

Main engine for applying sound change rules.

#### Constructor

```python
SoundChangeEngine(feature_system_name='unified_distinctive')
```

**Parameters:**
- `feature_system_name` (str): Feature system to use

#### Methods

##### `apply_rule(rule, sounds)`

Apply single sound change rule to sequence.

**Parameters:**
- `rule` (SoundChangeRule | FeatureChangeRule): Rule to apply
- `sounds` (list[Sound]): Input sound sequence

**Returns:**
- `RuleApplicationResult`: Result with modified sequence and metadata

**Example:**
```python
from alteruphono.phonology.sound_change import SoundChangeEngine, SoundChangeRule
engine = SoundChangeEngine(feature_system_name='unified_distinctive')

rule = SoundChangeRule(name="test", source_pattern="p", target_pattern="f")
sounds = [Sound('p', 'unified_distinctive'), Sound('a', 'unified_distinctive')]
result = engine.apply_rule(rule, sounds)

print([s.grapheme() for s in result.modified_sequence])  # ['f', 'a']
```

##### `apply_rule_set(rule_set, sounds)`

Apply set of rules to sequence.

**Parameters:**
- `rule_set` (RuleSet): Set of rules to apply
- `sounds` (list[Sound]): Input sound sequence

**Returns:**
- `RuleSetApplicationResult`: Result with final sequence and application history

### Rule Classes

#### `SoundChangeRule` Class

Basic sound change rule for segment substitution.

```python
SoundChangeRule(name, source_pattern, target_pattern, environment=None)
```

**Parameters:**
- `name` (str): Rule name
- `source_pattern` (str): Pattern to match
- `target_pattern` (str): Replacement pattern
- `environment` (str, optional): Environmental conditioning

**Example:**
```python
from alteruphono.phonology.sound_change import SoundChangeRule
rule = SoundChangeRule(
    name="initial_fricativization",
    source_pattern="p",
    target_pattern="f", 
    environment="# _"
)
```

#### `FeatureChangeRule` Class

Advanced rule using feature-based matching and changes.

```python
FeatureChangeRule(
    name, 
    source_pattern="",
    target_pattern=None,
    feature_conditions=None,
    feature_changes=None,
    environment=None,
    feature_system_name='unified_distinctive'
)
```

**Parameters:**
- `name` (str): Rule name
- `source_pattern` (str): Source pattern (can be empty for feature-only rules)
- `target_pattern` (list[FeatureChange], optional): Target modifications
- `feature_conditions` (dict[str, float], optional): Feature constraints for rule application
- `feature_changes` (list[FeatureChange], optional): Feature modifications to apply
- `environment` (PhonologicalEnvironment, optional): Environmental conditioning
- `feature_system_name` (str): Feature system to use

**Example:**
```python
from alteruphono.phonology.sound_change import FeatureChangeRule
from alteruphono.phonology.sound_change.rules import FeatureChange, ChangeType

voicing_rule = FeatureChangeRule(
    name="intervocalic_voicing",
    feature_conditions={"voice": -1.0, "sonorant": -1.0},  # Voiceless obstruents
    feature_changes=[
        FeatureChange(
            feature_name="voice",
            target_value=1.0,
            change_type=ChangeType.CATEGORICAL
        )
    ]
)
```

#### `FeatureChange` Class

Specification of feature modification.

```python
FeatureChange(
    feature_name,
    target_value,
    change_type=ChangeType.CATEGORICAL,
    change_strength=1.0
)
```

**Parameters:**
- `feature_name` (str): Name of feature to modify
- `target_value` (float): Target value for feature
- `change_type` (ChangeType): CATEGORICAL or GRADIENT
- `change_strength` (float): Strength of application (0.0-1.0)

#### `RuleSet` Class

Container for multiple rules with application control.

```python
RuleSet(rules, iterative=False, max_iterations=10)
```

**Parameters:**
- `rules` (list[SoundChangeRule | FeatureChangeRule]): Rules to apply
- `iterative` (bool): Whether to apply rules cyclically until no changes
- `max_iterations` (int): Maximum number of iterations

### Result Classes

#### `RuleApplicationResult`

Result of applying single rule.

**Attributes:**
- `modified_sequence` (list[Sound]): Resulting sound sequence
- `changed` (bool): Whether any changes occurred
- `rule_name` (str): Name of applied rule
- `change_count` (int): Number of changes made

#### `RuleSetApplicationResult`

Result of applying rule set.

**Attributes:**
- `final_sequence` (list[Sound]): Final sound sequence
- `rule_applications` (list[RuleApplicationResult]): Individual rule applications
- `total_changes` (int): Total number of changes

## Phonological Environments

### `PhonologicalEnvironment` Class

Specification of phonological context for sound changes.

#### Constructor

```python
PhonologicalEnvironment(
    left_pattern=None,
    right_pattern=None,
    target_conditions=None,
    feature_system_name='unified_distinctive',
    position=None,
    stress_pattern=None
)
```

**Parameters:**
- `left_pattern` (str | list[str], optional): Pattern before target
- `right_pattern` (str | list[str], optional): Pattern after target
- `target_conditions` (dict[str, float], optional): Feature conditions for target
- `feature_system_name` (str): Feature system to use
- `position` (str, optional): Syllable position ('onset', 'coda')
- `stress_pattern` (str, optional): Stress context

#### Methods

##### `matches(target_sound, left_context, right_context)`

Check if environment matches given context.

**Parameters:**
- `target_sound` (Sound): Sound at target position
- `left_context` (list[Sound]): Sounds before target
- `right_context` (list[Sound]): Sounds after target

**Returns:**
- `bool`: True if environment matches

**Example:**
```python
from alteruphono.phonology.sound_change.environments import PhonologicalEnvironment

# Intervocalic environment
env = PhonologicalEnvironment(
    left_pattern="V",
    right_pattern="V"
)

target = Sound('p', 'unified_distinctive')
left = [Sound('a', 'unified_distinctive')]
right = [Sound('a', 'unified_distinctive')]

matches = env.matches(target, left, right)
print(matches)  # True
```

## Utilities and Helpers

### Parsing Functions

#### `parse_rule_string(rule_string)`

Parse traditional sound change notation into rule object.

**Parameters:**
- `rule_string` (str): Rule in "A > B / C _ D" format

**Returns:**
- `SoundChangeRule`: Parsed rule object

### Validation Functions

#### `validate_features(feature_bundle)`

Validate feature bundle for phonological constraints.

**Parameters:**
- `feature_bundle` (FeatureBundle): Features to validate

**Returns:**
- `list[str]`: List of constraint violations

### Analysis Functions

#### `calculate_feature_statistics(feature_system)`

Calculate usage statistics for features in system.

**Parameters:**
- `feature_system` (FeatureSystem): System to analyze

**Returns:**
- `dict[str, dict[str, int]]`: Statistics per feature

**Example:**
```python
from alteruphono.phonology.feature_systems import get_feature_system

system = get_feature_system('tresoldi_distinctive')
stats = system.get_feature_statistics()

for feature, data in stats.items():
    total = data['positive'] + data['negative'] + data['neutral']
    print(f"{feature}: {data['positive']} positive, {data['negative']} negative")
```

### Sound Class Utilities

#### `get_sound_class_features(sound_class)`

Get feature specification for sound class.

**Parameters:**
- `sound_class` (str): Sound class symbol ('V', 'C', 'L', etc.)

**Returns:**
- `dict[str, float]`: Feature specifications

**Example:**
```python
system = get_feature_system('unified_distinctive')
vowel_features = system.get_sound_class_features('V')
print(vowel_features)  # {'syllabic': 1.0, 'consonantal': -1.0}
```

## Error Handling

### Exception Classes

#### `FeatureSystemError`

Raised when feature system operations fail.

#### `SoundChangeError`

Raised when sound change application fails.

#### `ParseError`

Raised when rule parsing fails.

### Error Handling Example

```python
try:
    sound = Sound('invalid_grapheme', 'ipa_categorical')
except FeatureSystemError as e:
    print(f"Feature system error: {e}")

try:
    rule = SoundChangeRule("bad_rule", "", "")
    result = engine.apply_rule(rule, sounds)
except SoundChangeError as e:
    print(f"Sound change error: {e}")
```

## Performance Considerations

### Best Practices

1. **Batch Operations**: Use `RuleSet` for multiple rules rather than individual applications
2. **Feature System Choice**: 
   - Use `ipa_categorical` for simple binary operations
   - Use `unified_distinctive` for gradient changes
   - Use `tresoldi_distinctive` for comprehensive coverage
3. **Caching**: Sound objects are cached automatically for repeated use
4. **Large Datasets**: Consider using generators for processing large word lists

### Performance Metrics

Typical performance characteristics:

- **Sound creation**: < 1ms per sound
- **Feature access**: < 0.1ms per operation  
- **Rule application**: < 50ms per rule on typical words
- **Distance calculation**: < 10ms between sounds with 43 features

### Memory Usage

- **IPA system**: ~5MB memory footprint
- **Unified system**: ~8MB memory footprint
- **Tresoldi system**: ~25MB memory footprint (1,081 sounds × 43 features)

This API reference provides comprehensive coverage of AlteruPhono's functionality for phonological modeling and historical linguistics research.