# Historical Linguistics Workflows with AlteruPhono

This guide demonstrates complete workflows for historical linguistics research using AlteruPhono's advanced phonological modeling capabilities.

## Table of Contents

1. [Comparative Method Workflow](#comparative-method-workflow)
2. [Language Evolution Simulation](#language-evolution-simulation)
3. [Phonological Classification](#phonological-classification)
4. [Sound Change Discovery](#sound-change-discovery)
5. [Typological Analysis](#typological-analysis)
6. [Reconstruction Validation](#reconstruction-validation)

## Comparative Method Workflow

### Step 1: Data Collection and Preparation

```python
import alteruphono
from alteruphono.phonology.sound_change import SoundChangeEngine
from alteruphono.phonology.sound_v2 import Sound
import pandas as pd

# Organize cognate sets
cognate_data = {
    'meaning': ['water', 'fire', 'stone', 'tree', 'eye'],
    'language_a': [
        ['w', 'a', 't', 'a'],
        ['f', 'i', 'r', 'a'], 
        ['s', 't', 'o', 'n'],
        ['t', 'r', 'e'],
        ['a', 'j']
    ],
    'language_b': [
        ['b', 'a', 'd', 'a'],
        ['p', 'i', 'r', 'a'],
        ['s', 't', 'o', 'n'], 
        ['t', 'r', 'e'],
        ['a', 'j']
    ],
    'language_c': [
        ['v', 'a', 't', 'a'],
        ['f', 'i', 'r', 'a'],
        ['ʃ', 't', 'o', 'n'],
        ['t', 'r', 'e'], 
        ['a', 'j']
    ]
}

# Convert to structured format
cognate_sets = {}
for i, meaning in enumerate(cognate_data['meaning']):
    cognate_sets[meaning] = {
        'Language_A': cognate_data['language_a'][i],
        'Language_B': cognate_data['language_b'][i], 
        'Language_C': cognate_data['language_c'][i]
    }
```

### Step 2: Extract Sound Correspondences

```python
from collections import defaultdict

def extract_correspondences(cognate_sets):
    """Extract systematic sound correspondences."""
    correspondences = defaultdict(list)
    
    for meaning, languages in cognate_sets.items():
        # Align cognates by position
        max_len = max(len(word) for word in languages.values())
        
        for pos in range(max_len):
            correspondence = []
            for lang_name in sorted(languages.keys()):
                word = languages[lang_name]
                if pos < len(word):
                    correspondence.append(word[pos])
                else:
                    correspondence.append('∅')  # Empty slot
            
            if len(set(correspondence)) > 1:  # Only non-identical correspondences
                corr_tuple = tuple(correspondence)
                correspondences[corr_tuple].append((meaning, pos))
    
    return correspondences

correspondences = extract_correspondences(cognate_sets)

print("Sound Correspondences:")
for corr, contexts in correspondences.items():
    if len(contexts) > 1:  # Recurrent correspondences
        lang_a, lang_b, lang_c = corr
        print(f"A:{lang_a} ~ B:{lang_b} ~ C:{lang_c} (appears {len(contexts)} times)")
```

### Step 3: Reconstruct Proto-Language

```python
def reconstruct_proto_language(cognate_sets):
    """Apply comparative method principles for reconstruction."""
    proto_forms = {}
    
    for meaning, languages in cognate_sets.items():
        proto_form = []
        max_len = max(len(word) for word in languages.values())
        
        for pos in range(max_len):
            sounds_at_pos = []
            for word in languages.values():
                if pos < len(word):
                    sounds_at_pos.append(word[pos])
            
            if sounds_at_pos:
                # Apply reconstruction principles
                proto_sound = apply_reconstruction_principles(sounds_at_pos)
                proto_form.append(proto_sound)
        
        proto_forms[meaning] = proto_form
    
    return proto_forms

def apply_reconstruction_principles(sound_list):
    """Apply standard reconstruction heuristics."""
    from collections import Counter
    
    # Remove duplicates and count
    sound_counts = Counter(sound_list)
    
    # Principle 1: If all agree, reconstruct the common sound
    if len(sound_counts) == 1:
        return list(sound_counts.keys())[0]
    
    # Principle 2: Voiceless stops often more conservative
    conservative_sounds = {'p', 't', 'k', 'q'}
    for sound in sound_counts:
        if sound in conservative_sounds:
            return sound
    
    # Principle 3: Take majority
    return sound_counts.most_common(1)[0][0]

proto_forms = reconstruct_proto_language(cognate_sets)

print("\nReconstructed Proto-Language:")
for meaning, proto_form in proto_forms.items():
    proto_str = ' '.join(proto_form)
    print(f"*{proto_str} '{meaning}'")
```

### Step 4: Validate Reconstruction

```python
def validate_reconstruction(proto_forms, daughter_languages):
    """Validate reconstruction by checking regularity."""
    
    # Extract all sound changes
    changes_by_language = {}
    
    for lang_name in daughter_languages:
        changes = defaultdict(int)
        
        for meaning in proto_forms:
            if meaning in cognate_sets:
                proto_word = proto_forms[meaning]
                daughter_word = cognate_sets[meaning][lang_name]
                
                # Find changes
                for i, (proto_sound, daughter_sound) in enumerate(zip(proto_word, daughter_word)):
                    if proto_sound != daughter_sound:
                        change_key = f"{proto_sound} > {daughter_sound}"
                        changes[change_key] += 1
        
        changes_by_language[lang_name] = changes
    
    return changes_by_language

validation_results = validate_reconstruction(proto_forms, ['Language_A', 'Language_B', 'Language_C'])

print("\nSound Change Regularity Check:")
for lang, changes in validation_results.items():
    print(f"\n{lang}:")
    for change, frequency in sorted(changes.items(), key=lambda x: x[1], reverse=True):
        print(f"  {change}: {frequency} instances")
```

## Language Evolution Simulation

### Modeling Realistic Sound Change

```python
from alteruphono.phonology.sound_change import SoundChangeEngine, FeatureChangeRule, RuleSet
from alteruphono.phonology.sound_change.rules import FeatureChange, ChangeType

def simulate_language_evolution(proto_forms, sound_changes, target_language):
    """Simulate evolution from proto-language to target language."""
    
    engine = SoundChangeEngine(feature_system_name='unified_distinctive')
    
    results = {}
    for meaning, proto_form in proto_forms.items():
        # Convert to Sound objects
        sounds = [Sound(s, 'unified_distinctive') for s in proto_form]
        
        # Apply sound changes
        evolved_result = engine.apply_rule_set(sound_changes, sounds)
        
        # Extract evolved form
        evolved_form = [s.grapheme() for s in evolved_result.final_sequence]
        results[meaning] = evolved_form
    
    return results

# Define sound change rules for specific language
spanish_evolution = RuleSet([
    # Intervocalic voicing: voiceless stops → voiced between vowels
    FeatureChangeRule(
        name="intervocalic_voicing",
        feature_conditions={"voice": -1.0, "consonantal": 1.0, "continuant": -1.0},
        feature_changes=[
            FeatureChange(feature_name="voice", target_value=1.0, change_type=ChangeType.CATEGORICAL)
        ],
        environment=PhonologicalEnvironment(left_pattern="V", right_pattern="V")
    ),
    
    # Final consonant loss
    FeatureChangeRule(
        name="final_consonant_loss",
        feature_conditions={"consonantal": 1.0},
        feature_changes=[],  # Deletion - would need special implementation
        environment=PhonologicalEnvironment(right_pattern="#")
    )
], iterative=False)

# Simulate evolution
evolved_spanish = simulate_language_evolution(proto_forms, spanish_evolution, "Spanish")

print("Language Evolution Simulation:")
for meaning in proto_forms:
    proto_str = ' '.join(proto_forms[meaning])
    evolved_str = ' '.join(evolved_spanish[meaning])
    print(f"*{proto_str} → {evolved_str} '{meaning}'")
```

### Gradient Sound Change Modeling

```python
def model_gradual_change(time_points, change_strength_function):
    """Model gradual sound change over time."""
    
    # Example: Progressive lenition
    lenition_stages = []
    
    for t in time_points:
        strength = change_strength_function(t)
        
        stage = FeatureChangeRule(
            name=f"lenition_t{t}",
            feature_conditions={"consonantal": 1.0, "continuant": -1.0},
            feature_changes=[
                FeatureChange(
                    feature_name="continuant",
                    target_value=strength,  # Gradual increase
                    change_type=ChangeType.GRADIENT,
                    change_strength=0.1  # Small incremental change
                )
            ]
        )
        lenition_stages.append(stage)
    
    return lenition_stages

# Define change function (sigmoid-like)
import numpy as np

def lenition_strength(t):
    """Sigmoid function for gradual lenition."""
    return 1.0 / (1.0 + np.exp(-(t - 50) / 10))

# Model 100 time points
time_points = range(0, 101, 10)
gradual_lenition = model_gradual_change(time_points, lenition_strength)

print(f"\nGradual lenition modeled over {len(time_points)} time points")
```

## Phonological Classification

### Distance-Based Classification

```python
def calculate_phonological_distances(language_inventories, feature_system='tresoldi_distinctive'):
    """Calculate pairwise distances between language inventories."""
    
    languages = list(language_inventories.keys())
    n_langs = len(languages)
    distance_matrix = np.zeros((n_langs, n_langs))
    
    for i, lang1 in enumerate(languages):
        for j, lang2 in enumerate(languages):
            if i != j:
                distance = calculate_inventory_distance(
                    language_inventories[lang1],
                    language_inventories[lang2],
                    feature_system
                )
                distance_matrix[i][j] = distance
    
    return distance_matrix, languages

def calculate_inventory_distance(inv1, inv2, feature_system):
    """Calculate distance between two phonological inventories."""
    
    # Method 1: Jaccard distance
    set1, set2 = set(inv1), set(inv2)
    jaccard = 1 - len(set1 & set2) / len(set1 | set2)
    
    # Method 2: Feature-based distance
    system = get_feature_system(feature_system)
    feature_distances = []
    
    # Compare sounds that exist in both inventories
    common_sounds = set1 & set2
    unique_to_1 = set1 - set2
    unique_to_2 = set2 - set1
    
    # Distance from unique sounds (max penalty)
    unique_penalty = (len(unique_to_1) + len(unique_to_2)) / max(len(set1 | set2), 1)
    
    return jaccard + unique_penalty

# Example language inventories
inventories = {
    'English': ['p', 'b', 't', 'd', 'k', 'g', 'f', 'v', 'θ', 'ð', 's', 'z'],
    'Spanish': ['p', 'b', 't', 'd', 'k', 'g', 'f', 'β', 's', 'x', 'θ'],
    'French': ['p', 'b', 't', 'd', 'k', 'g', 'f', 'v', 's', 'z', 'ʃ', 'ʒ'],
    'German': ['p', 'b', 't', 'd', 'k', 'g', 'f', 'v', 's', 'z', 'ʃ', 'x']
}

distance_matrix, language_names = calculate_phonological_distances(inventories)

print("Phonological Distance Matrix:")
print(pd.DataFrame(distance_matrix, index=language_names, columns=language_names).round(3))
```

### Phylogenetic Tree Construction

```python
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import squareform
import matplotlib.pyplot as plt

def build_phylogenetic_tree(distance_matrix, language_names):
    """Build phylogenetic tree from distance matrix."""
    
    # Convert to condensed format for scipy
    condensed_distances = squareform(distance_matrix)
    
    # Perform hierarchical clustering
    linkage_matrix = linkage(condensed_distances, method='average')
    
    # Plot dendrogram
    plt.figure(figsize=(10, 6))
    dendrogram(linkage_matrix, labels=language_names, leaf_rotation=45)
    plt.title('Phonological Distance-Based Language Tree')
    plt.xlabel('Languages')
    plt.ylabel('Distance')
    plt.tight_layout()
    plt.show()
    
    return linkage_matrix

# Build and display tree
tree = build_phylogenetic_tree(distance_matrix, language_names)
print("Phylogenetic tree constructed based on phonological distances")
```

## Sound Change Discovery

### Automatic Rule Extraction

```python
def discover_sound_change_rules(comparative_data):
    """Automatically discover sound change rules from comparative data."""
    
    discovered_rules = []
    
    # Collect all changes
    changes = defaultdict(list)
    
    for proto_lang, daughter_langs in comparative_data.items():
        for daughter_name, daughter_words in daughter_langs.items():
            
            for meaning, (proto_word, daughter_word) in daughter_words.items():
                # Find position-by-position changes
                for i, (p_sound, d_sound) in enumerate(zip(proto_word, daughter_word)):
                    if p_sound != d_sound:
                        # Extract context
                        left_ctx = proto_word[i-1] if i > 0 else '#'
                        right_ctx = proto_word[i+1] if i < len(proto_word)-1 else '#'
                        
                        change_signature = (p_sound, d_sound, left_ctx, right_ctx)
                        changes[change_signature].append((meaning, daughter_name))
    
    # Find regular patterns
    for (source, target, left, right), instances in changes.items():
        if len(instances) >= 2:  # Require multiple instances
            
            # Determine environment
            if left == '#' and right == '#':
                environment = "word boundaries"
            elif left == '#':
                environment = f"word-initially before {right}"
            elif right == '#':
                environment = f"word-finally after {left}"
            else:
                environment = f"between {left} and {right}"
            
            rule = {
                'change': f"{source} > {target}",
                'environment': environment,
                'frequency': len(instances),
                'examples': instances[:3]
            }
            discovered_rules.append(rule)
    
    return discovered_rules

# Example comparative data
comparative_data = {
    'Proto-Language': {
        'Daughter_A': {
            'water': (['w', 'a', 't', 'a'], ['w', 'a', 'd', 'a']),
            'fire': (['p', 'i', 't', 'a'], ['p', 'i', 'd', 'a'])
        },
        'Daughter_B': {
            'water': (['w', 'a', 't', 'a'], ['w', 'a', 't', 'a']),
            'fire': (['p', 'i', 't', 'a'], ['p', 'i', 't', 'a'])
        }
    }
}

rules = discover_sound_change_rules(comparative_data)

print("Discovered Sound Change Rules:")
for rule in rules:
    print(f"{rule['change']} / {rule['environment']} ({rule['frequency']} instances)")
```

## Typological Analysis

### Universal Tendency Testing

```python
def test_phonological_universals(language_sample):
    """Test various phonological universals against language sample."""
    
    from alteruphono.phonology.feature_systems import get_feature_system
    tresoldi_system = get_feature_system('tresoldi_distinctive')
    
    test_results = {}
    
    # Universal 1: If /g/ then /k/
    def test_voicing_implication():
        violations = 0
        total = 0
        
        for lang_name, inventory in language_sample.items():
            has_g = 'g' in inventory
            has_k = 'k' in inventory
            
            if has_g and not has_k:
                violations += 1
            total += 1
        
        return {'violations': violations, 'total': total, 'support': 1 - violations/total}
    
    # Universal 2: Coronals more frequent than labials
    def test_place_frequency():
        coronal_totals = []
        labial_totals = []
        
        for lang_name, inventory in language_sample.items():
            coronal_count = 0
            labial_count = 0
            
            for sound in inventory:
                if tresoldi_system.has_grapheme(sound):
                    sound_obj = Sound(sound, 'tresoldi_distinctive')
                    if sound_obj.get_feature_value('coronal') > 0:
                        coronal_count += 1
                    if sound_obj.get_feature_value('labial') > 0:
                        labial_count += 1
            
            coronal_totals.append(coronal_count)
            labial_totals.append(labial_count)
        
        # Test if coronals generally more frequent
        coronal_higher = sum(1 for c, l in zip(coronal_totals, labial_totals) if c >= l)
        support = coronal_higher / len(language_sample)
        
        return {'coronal_higher': coronal_higher, 'total': len(language_sample), 'support': support}
    
    # Run tests
    test_results['voicing_implication'] = test_voicing_implication()
    test_results['place_frequency'] = test_place_frequency()
    
    return test_results

# Test with sample
language_sample = {
    'English': ['p', 'b', 't', 'd', 'k', 'g', 's', 'z', 'n', 'm'],
    'Spanish': ['p', 'b', 't', 'd', 'k', 'g', 's', 'n', 'm'],
    'French': ['p', 'b', 't', 'd', 'k', 'g', 's', 'z', 'n', 'm'],
    'NoG_Lang': ['p', 'b', 't', 'd', 'k', 's', 'n', 'm']  # Hypothetical language without /g/
}

universal_results = test_phonological_universals(language_sample)

print("Phonological Universals Test Results:")
for test_name, results in universal_results.items():
    print(f"{test_name}: {results}")
```

## Reconstruction Validation

### Cross-Validation Methods

```python
def validate_reconstruction_cross_linguistically(proto_forms, known_changes, test_languages):
    """Validate reconstruction using known sound changes."""
    
    validation_scores = {}
    
    for lang_name, sound_changes in known_changes.items():
        if lang_name in test_languages:
            
            # Predict what proto-forms should become
            predicted_forms = {}
            for meaning, proto_form in proto_forms.items():
                predicted = apply_sound_changes(proto_form, sound_changes)
                predicted_forms[meaning] = predicted
            
            # Compare with actual attested forms
            actual_forms = test_languages[lang_name]
            
            # Calculate accuracy
            matches = 0
            total = 0
            
            for meaning in predicted_forms:
                if meaning in actual_forms:
                    predicted = predicted_forms[meaning]
                    actual = actual_forms[meaning]
                    
                    if predicted == actual:
                        matches += 1
                    total += 1
            
            accuracy = matches / total if total > 0 else 0
            validation_scores[lang_name] = {
                'matches': matches,
                'total': total,
                'accuracy': accuracy
            }
    
    return validation_scores

def apply_sound_changes(word, sound_changes):
    """Apply list of sound changes to word."""
    result = word[:]
    
    for change in sound_changes:
        # Simple string replacement for demonstration
        source, target = change
        result = [target if sound == source else sound for sound in result]
    
    return result

# Example validation
known_changes = {
    'Language_A': [('t', 'd'), ('p', 'b')],  # Known historical changes
    'Language_B': [('k', 'g')]
}

test_languages = {
    'Language_A': {
        'water': ['w', 'a', 'd', 'a'],  # From *wata
        'path': ['p', 'a', 'd']         # From *pat
    },
    'Language_B': {
        'water': ['w', 'a', 't', 'a'],  # Conservative
        'path': ['p', 'a', 't']
    }
}

# Validate reconstructions
validation_results = validate_reconstruction_cross_linguistically(
    {'water': ['w', 'a', 't', 'a'], 'path': ['p', 'a', 't']},
    known_changes,
    test_languages
)

print("Reconstruction Validation Results:")
for lang, results in validation_results.items():
    accuracy = results['accuracy'] * 100
    print(f"{lang}: {results['matches']}/{results['total']} correct ({accuracy:.1f}%)")
```

### Statistical Validation

```python
def statistical_validation(cognate_sets, n_bootstrap=1000):
    """Bootstrap validation of sound correspondences."""
    
    import random
    
    # Extract all correspondences
    all_correspondences = []
    for meaning, languages in cognate_sets.items():
        # Create correspondence tuples
        lang_names = sorted(languages.keys())
        max_len = max(len(languages[lang]) for lang in lang_names)
        
        for pos in range(max_len):
            correspondence = []
            for lang in lang_names:
                word = languages[lang]
                sound = word[pos] if pos < len(word) else '∅'
                correspondence.append(sound)
            all_correspondences.append(tuple(correspondence))
    
    # Bootstrap sampling
    bootstrap_results = []
    
    for _ in range(n_bootstrap):
        # Sample with replacement
        bootstrap_sample = random.choices(all_correspondences, k=len(all_correspondences))
        
        # Count unique correspondences
        unique_correspondences = len(set(bootstrap_sample))
        bootstrap_results.append(unique_correspondences)
    
    # Calculate confidence interval
    bootstrap_results.sort()
    ci_lower = bootstrap_results[int(0.025 * n_bootstrap)]
    ci_upper = bootstrap_results[int(0.975 * n_bootstrap)]
    mean_unique = np.mean(bootstrap_results)
    
    return {
        'mean_unique_correspondences': mean_unique,
        'confidence_interval': (ci_lower, ci_upper),
        'original_unique': len(set(all_correspondences))
    }

# Run statistical validation
stats = statistical_validation(cognate_sets)
print(f"Statistical Validation:")
print(f"Original unique correspondences: {stats['original_unique']}")
print(f"Bootstrap mean: {stats['mean_unique_correspondences']:.1f}")
print(f"95% CI: {stats['confidence_interval']}")
```

This comprehensive guide demonstrates how AlteruPhono can be used for complete historical linguistics workflows, from initial data collection through final validation of reconstructions. Each workflow can be adapted for specific research questions and language families.