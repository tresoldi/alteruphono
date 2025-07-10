"""
Sound change rule application engine.

This module provides the core engine for applying sound change rules to 
phonological sequences, with support for gradient changes, probabilistic
application, and comprehensive change tracking.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Iterator
from enum import Enum
import time
import uuid
from collections import defaultdict

from .rules import SoundChangeRule, RuleSet, RuleApplication, FeatureChange
from ..sound_v2 import Sound
from ..feature_systems import get_feature_system


class SimulationMode(Enum):
    """Modes for sound change simulation."""
    SYNCHRONIC = "synchronic"      # All rules apply simultaneously
    DIACHRONIC = "diachronic"     # Rules apply in historical order
    PROBABILISTIC = "probabilistic"  # Rules apply probabilistically over time
    GRADIENT = "gradient"         # Rules apply gradually with variable strength


@dataclass
class RuleApplicationResult:
    """Result of applying a rule to a sequence."""
    original_sequence: List[Sound]
    modified_sequence: List[Sound]
    applications: List[RuleApplication] = field(default_factory=list)
    rule_name: str = ""
    execution_time: float = 0.0
    
    @property
    def changed(self) -> bool:
        """Whether any changes occurred."""
        return len(self.applications) > 0 and any(app.changed for app in self.applications)
    
    @property 
    def change_count(self) -> int:
        """Number of sounds that were actually changed."""
        return sum(1 for app in self.applications if app.changed)
    
    def get_change_summary(self) -> Dict[str, int]:
        """Get summary of changes by type."""
        summary = defaultdict(int)
        
        for app in self.applications:
            if app.changed:
                feature_changes = app.get_feature_changes()
                for feature, (old_val, new_val) in feature_changes.items():
                    change_key = f"{feature}: {old_val} → {new_val}"
                    summary[change_key] += 1
        
        return dict(summary)


@dataclass
class ChangeSimulation:
    """Results of a complete sound change simulation."""
    initial_sequence: List[Sound]
    final_sequence: List[Sound]
    rule_applications: List[RuleApplicationResult] = field(default_factory=list)
    simulation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    simulation_mode: SimulationMode = SimulationMode.DIACHRONIC
    total_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_changes(self) -> int:
        """Total number of sound changes across all rules."""
        return sum(result.change_count for result in self.rule_applications)
    
    @property
    def rules_applied(self) -> List[str]:
        """List of rule names that were actually applied."""
        return [result.rule_name for result in self.rule_applications if result.changed]
    
    def get_change_trajectory(self) -> List[List[Sound]]:
        """Get sequence states after each rule application."""
        trajectory = [self.initial_sequence]
        
        current = self.initial_sequence
        for result in self.rule_applications:
            if result.changed:
                current = result.modified_sequence
                trajectory.append(current.copy())
        
        return trajectory
    
    def get_detailed_changes(self) -> Dict[str, List[RuleApplication]]:
        """Get detailed changes organized by rule."""
        changes_by_rule = defaultdict(list)
        
        for result in self.rule_applications:
            for app in result.applications:
                if app.changed:
                    changes_by_rule[result.rule_name].append(app)
        
        return dict(changes_by_rule)


class SoundChangeEngine:
    """
    Main engine for applying sound change rules.
    
    This engine handles the application of both traditional categorical
    sound changes and gradient changes using the unified distinctive
    feature system.
    """
    
    def __init__(self, feature_system_name: str = "unified_distinctive"):
        self.feature_system_name = feature_system_name
        self.feature_system = get_feature_system(feature_system_name)
        self.rule_sets: Dict[str, RuleSet] = {}
        self.application_history: List[ChangeSimulation] = []
    
    def add_rule_set(self, rule_set: RuleSet) -> None:
        """Add a rule set to the engine."""
        self.rule_sets[rule_set.name] = rule_set
    
    def remove_rule_set(self, name: str) -> None:
        """Remove a rule set from the engine."""
        if name in self.rule_sets:
            del self.rule_sets[name]
    
    def get_rule_set(self, name: str) -> Optional[RuleSet]:
        """Get a rule set by name."""
        return self.rule_sets.get(name)
    
    def apply_rule(self, rule: SoundChangeRule, sequence: List[Sound]) -> RuleApplicationResult:
        """Apply a single rule to a sequence of sounds."""
        start_time = time.perf_counter()
        
        applications = []
        modified_sequence = []
        
        for i, sound in enumerate(sequence):
            # Get context windows
            left_context = sequence[max(0, i-2):i] if i > 0 else []
            right_context = sequence[i+1:i+3] if i < len(sequence)-1 else []
            
            # Check if rule applies
            if rule.applies_to(sound, left_context, right_context):
                # Apply the rule
                modified_sound = rule.apply_to(sound)
                
                # Record the application
                application = RuleApplication(
                    rule_name=rule.name,
                    original_sound=sound,
                    modified_sound=modified_sound,
                    context_left=left_context,
                    context_right=right_context,
                    application_strength=rule.change_strength,
                    timestamp=str(time.time())
                )
                applications.append(application)
                modified_sequence.append(modified_sound)
            else:
                modified_sequence.append(sound)
        
        end_time = time.perf_counter()
        
        return RuleApplicationResult(
            original_sequence=sequence,
            modified_sequence=modified_sequence,
            applications=applications,
            rule_name=rule.name,
            execution_time=end_time - start_time
        )
    
    def apply_rule_set(self, rule_set: RuleSet, sequence: List[Sound]) -> ChangeSimulation:
        """Apply a complete rule set to a sequence."""
        start_time = time.perf_counter()
        
        simulation = ChangeSimulation(
            initial_sequence=sequence.copy(),
            final_sequence=sequence.copy(),
            simulation_mode=SimulationMode.DIACHRONIC
        )
        
        current_sequence = sequence.copy()
        
        if rule_set.iterative:
            # Iterative application until convergence
            for iteration in range(rule_set.max_iterations):
                iteration_changed = False
                
                for rule in rule_set.rules:
                    result = self.apply_rule(rule, current_sequence)
                    simulation.rule_applications.append(result)
                    
                    if result.changed:
                        iteration_changed = True
                        current_sequence = result.modified_sequence
                
                if not iteration_changed:
                    break
        else:
            # Single pass through rules
            for rule in rule_set.rules:
                result = self.apply_rule(rule, current_sequence)
                simulation.rule_applications.append(result)
                
                if result.changed:
                    current_sequence = result.modified_sequence
        
        simulation.final_sequence = current_sequence
        simulation.total_time = time.perf_counter() - start_time
        
        # Store in history
        self.application_history.append(simulation)
        
        return simulation
    
    def simulate_gradual_change(self, rule: SoundChangeRule, sequence: List[Sound],
                               steps: int = 10) -> List[ChangeSimulation]:
        """
        Simulate gradual application of a rule over multiple steps.
        
        This is particularly useful for gradient changes in the unified
        distinctive system where features change gradually.
        """
        simulations = []
        current_sequence = sequence.copy()
        
        original_strength = rule.change_strength
        
        for step in range(1, steps + 1):
            # Gradually increase rule strength
            rule.change_strength = original_strength * (step / steps)
            
            # Apply rule with current strength
            result = self.apply_rule(rule, current_sequence)
            
            simulation = ChangeSimulation(
                initial_sequence=current_sequence.copy(),
                final_sequence=result.modified_sequence,
                rule_applications=[result],
                simulation_mode=SimulationMode.GRADIENT,
                metadata={'step': step, 'total_steps': steps, 'strength': rule.change_strength}
            )
            
            simulations.append(simulation)
            current_sequence = result.modified_sequence
        
        # Restore original strength
        rule.change_strength = original_strength
        
        return simulations
    
    def simulate_probabilistic_change(self, rule: SoundChangeRule, sequence: List[Sound],
                                    generations: int = 100, population_size: int = 1000) -> ChangeSimulation:
        """
        Simulate probabilistic sound change over multiple generations.
        
        This models how a sound change might spread through a population
        over time with probabilistic application.
        """
        start_time = time.perf_counter()
        
        # Track changes across generations
        generation_results = []
        current_frequency = {}  # Track frequency of each variant
        
        # Initialize with original sequence
        original_key = tuple(str(s) for s in sequence)
        current_frequency[original_key] = population_size
        
        for generation in range(generations):
            new_frequency = defaultdict(int)
            
            # Apply rule probabilistically to each individual
            for variant, count in current_frequency.items():
                variant_sounds = [Sound(grapheme=s) for s in variant if s != 'None']
                
                for _ in range(count):
                    result = self.apply_rule(rule, variant_sounds)
                    result_key = tuple(str(s) for s in result.modified_sequence)
                    new_frequency[result_key] += 1
            
            current_frequency = dict(new_frequency)
            generation_results.append(dict(current_frequency))
        
        # Find most common final variant
        final_variant = max(current_frequency.items(), key=lambda x: x[1])
        final_sequence = [Sound(grapheme=s) for s in final_variant[0] if s != 'None']
        
        simulation = ChangeSimulation(
            initial_sequence=sequence,
            final_sequence=final_sequence,
            simulation_mode=SimulationMode.PROBABILISTIC,
            total_time=time.perf_counter() - start_time,
            metadata={
                'generations': generations,
                'population_size': population_size,
                'final_frequency': final_variant[1],
                'generation_results': generation_results
            }
        )
        
        return simulation
    
    def analyze_rule_interactions(self, rule_set: RuleSet, 
                                 test_sequences: List[List[Sound]]) -> Dict[str, Any]:
        """
        Analyze how rules in a set interact with each other.
        
        Tests rule ordering effects, bleeding/feeding relationships, etc.
        """
        analysis = {
            'rule_effects': {},
            'ordering_effects': {},
            'interaction_matrix': defaultdict(dict)
        }
        
        # Test individual rule effects
        for rule in rule_set.rules:
            rule_effects = []
            single_rule_set = RuleSet(rules=[rule], name=f"test_{rule.name}")
            
            for test_seq in test_sequences:
                result = self.apply_rule_set(single_rule_set, test_seq)
                rule_effects.append({
                    'input': test_seq,
                    'output': result.final_sequence,
                    'changes': result.total_changes
                })
            
            analysis['rule_effects'][rule.name] = rule_effects
        
        # Test pairwise rule interactions
        for i, rule1 in enumerate(rule_set.rules):
            for j, rule2 in enumerate(rule_set.rules):
                if i != j:
                    # Test rule1 → rule2 order
                    forward_effects = []
                    reverse_effects = []
                    
                    for test_seq in test_sequences[:5]:  # Limit for performance
                        # Forward order
                        temp_set = RuleSet(rules=[rule1, rule2], name="temp_forward")
                        forward_result = self.apply_rule_set(temp_set, test_seq)
                        
                        # Reverse order  
                        temp_set = RuleSet(rules=[rule2, rule1], name="temp_reverse")
                        reverse_result = self.apply_rule_set(temp_set, test_seq)
                        
                        forward_effects.append(forward_result.total_changes)
                        reverse_effects.append(reverse_result.total_changes)
                    
                    analysis['interaction_matrix'][rule1.name][rule2.name] = {
                        'forward_changes': sum(forward_effects),
                        'reverse_changes': sum(reverse_effects),
                        'order_sensitive': forward_effects != reverse_effects
                    }
        
        return analysis
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about rule applications."""
        if not self.application_history:
            return {}
        
        total_simulations = len(self.application_history)
        total_changes = sum(sim.total_changes for sim in self.application_history)
        avg_changes = total_changes / total_simulations if total_simulations > 0 else 0
        
        rule_usage = defaultdict(int)
        for sim in self.application_history:
            for rule_name in sim.rules_applied:
                rule_usage[rule_name] += 1
        
        return {
            'total_simulations': total_simulations,
            'total_changes': total_changes,
            'average_changes_per_simulation': avg_changes,
            'rule_usage_frequency': dict(rule_usage),
            'most_used_rule': max(rule_usage.items(), key=lambda x: x[1])[0] if rule_usage else None
        }
    
    def clear_history(self) -> None:
        """Clear the application history."""
        self.application_history.clear()