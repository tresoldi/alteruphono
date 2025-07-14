"""
High-level comparative analysis API for historical linguists.

This module provides simple, one-liner functions for common historical linguistics tasks.
Designed to be intuitive for researchers who want powerful results with minimal code.
"""

from collections import defaultdict, Counter
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass

from .phonology.sound_v2 import Sound
from .phonology.feature_systems import get_feature_system


@dataclass
class SoundChangeRule:
    """Simple representation of a sound change rule."""
    source: str
    target: str
    environment: str
    frequency: int
    confidence: float
    examples: List[Tuple[str, str]]


@dataclass
class CorrespondenceSet:
    """Represents a systematic sound correspondence."""
    sounds: Tuple[str, ...]
    languages: Tuple[str, ...]
    frequency: int
    examples: List[str]


class ComparativeAnalysis:
    """
    One-liner comparative analysis for historical linguists.
    
    Usage:
        analysis = ComparativeAnalysis(cognate_data)
        proto = analysis.reconstruct_proto()
        rules = analysis.discover_sound_changes('Spanish')
        tree = analysis.build_phylogeny()
    """
    
    def __init__(self, cognate_sets: Dict[str, Dict[str, List[str]]]):
        """
        Initialize with cognate data.
        
        Args:
            cognate_sets: Dictionary mapping meanings to language forms
                         e.g., {'water': {'Latin': ['a','k','w','a'], 'Spanish': ['a','ɣ','w','a']}}
        """
        self.cognate_sets = cognate_sets
        self.languages = list(next(iter(cognate_sets.values())).keys())
        self.meanings = list(cognate_sets.keys())
        
    def find_correspondences(self, min_frequency: int = 2) -> Counter:
        """
        Find systematic sound correspondences across languages.
        
        Args:
            min_frequency: Minimum frequency for a correspondence to be considered systematic
            
        Returns:
            Counter of correspondence patterns sorted by frequency
        """
        correspondences = defaultdict(list)
        
        for meaning, languages in self.cognate_sets.items():
            # Get maximum length for alignment
            max_len = max(len(word) for word in languages.values())
            
            # Simple position-based alignment
            for pos in range(max_len):
                sounds_at_pos = []
                for lang in self.languages:
                    if lang in languages and pos < len(languages[lang]):
                        sounds_at_pos.append(languages[lang][pos])
                    else:
                        sounds_at_pos.append('∅')  # Empty symbol
                
                if len(sounds_at_pos) == len(self.languages):
                    pattern = tuple(sounds_at_pos)
                    correspondences[pattern].append((meaning, pos))
        
        # Filter by frequency and return sorted
        frequent_correspondences = Counter()
        for pattern, examples in correspondences.items():
            if len(examples) >= min_frequency:
                frequent_correspondences[pattern] = len(examples)
        
        return frequent_correspondences
    
    def reconstruct_proto(self, method: str = 'parsimony') -> Dict[str, List[str]]:
        """
        Reconstruct proto-language forms using the comparative method.
        
        Args:
            method: Reconstruction method ('parsimony', 'majority', 'conservative')
            
        Returns:
            Dictionary mapping meanings to reconstructed proto-forms
        """
        proto_forms = {}
        
        for meaning, languages in self.cognate_sets.items():
            forms = list(languages.values())
            max_len = max(len(form) for form in forms)
            
            proto_form = []
            for pos in range(max_len):
                sounds_at_pos = []
                for form in forms:
                    if pos < len(form):
                        sounds_at_pos.append(form[pos])
                
                if sounds_at_pos:
                    # Simple reconstruction: use most common sound
                    if method == 'majority':
                        proto_sound = Counter(sounds_at_pos).most_common(1)[0][0]
                    elif method == 'conservative':
                        # Prefer voiceless over voiced, stops over fricatives
                        proto_sound = self._conservative_reconstruction(sounds_at_pos)
                    else:  # parsimony
                        proto_sound = self._parsimony_reconstruction(sounds_at_pos)
                    
                    proto_form.append(proto_sound)
            
            proto_forms[meaning] = proto_form
        
        return proto_forms
    
    def _conservative_reconstruction(self, sounds: List[str]) -> str:
        """Apply conservative reconstruction principles."""
        sound_counts = Counter(sounds)
        
        # Prefer voiceless stops
        voiceless_stops = {'p', 't', 'k', 'q'}
        for sound in voiceless_stops:
            if sound in sound_counts:
                return sound
        
        # Fall back to most common
        return sound_counts.most_common(1)[0][0]
    
    def _parsimony_reconstruction(self, sounds: List[str]) -> str:
        """Apply parsimony principle (minimize total changes)."""
        # Simple implementation: return most common sound
        return Counter(sounds).most_common(1)[0][0]
    
    def discover_sound_changes(self, target_language: str, source: str = None) -> List[SoundChangeRule]:
        """
        Discover sound change rules for a specific language.
        
        Args:
            target_language: Language to analyze
            source: Source language (if None, uses reconstructed proto-forms)
            
        Returns:
            List of discovered sound change rules
        """
        if source is None:
            # Use reconstructed proto-forms as source
            source_forms = self.reconstruct_proto()
            source_name = "Proto"
        else:
            # Use specific language as source
            source_forms = {meaning: forms[source] for meaning, forms in self.cognate_sets.items()}
            source_name = source
        
        target_forms = {meaning: forms[target_language] for meaning, forms in self.cognate_sets.items() if target_language in forms}
        
        # Collect sound changes
        changes = defaultdict(list)
        
        for meaning in source_forms.keys():
            if meaning in target_forms:
                source_word = source_forms[meaning]
                target_word = target_forms[meaning]
                
                # Align and find changes
                max_len = max(len(source_word), len(target_word))
                
                for i in range(max_len):
                    source_sound = source_word[i] if i < len(source_word) else '∅'
                    target_sound = target_word[i] if i < len(target_word) else '∅'
                    
                    if source_sound != target_sound and source_sound != '∅' and target_sound != '∅':
                        # Extract context
                        left_context = source_word[i-1] if i > 0 else '#'
                        right_context = source_word[i+1] if i < len(source_word)-1 else '#'
                        
                        change_key = (source_sound, target_sound)
                        context = (left_context, right_context, meaning)
                        changes[change_key].append(context)
        
        # Create rules
        rules = []
        for (source_sound, target_sound), contexts in changes.items():
            if len(contexts) >= 1:  # Include single instances
                # Determine environment
                left_contexts = [ctx[0] for ctx in contexts]
                right_contexts = [ctx[1] for ctx in contexts]
                examples = [(ctx[2], f"{ctx[0]}_{ctx[1]}") for ctx in contexts]
                
                # Find most common context
                if len(contexts) == 1:
                    common_left = left_contexts[0]
                    common_right = right_contexts[0]
                else:
                    common_left = Counter(left_contexts).most_common(1)[0][0]
                    common_right = Counter(right_contexts).most_common(1)[0][0]
                
                # Format environment
                if common_left == '#' and common_right == '#':
                    environment = "everywhere"
                elif common_left == '#':
                    environment = f"word-initially"
                elif common_right == '#':
                    environment = f"word-finally"
                else:
                    environment = f"{common_left}_{common_right}"
                
                confidence = len(contexts) / len(self.meanings)  # Simple confidence measure
                
                rule = SoundChangeRule(
                    source=source_sound,
                    target=target_sound,
                    environment=environment,
                    frequency=len(contexts),
                    confidence=confidence,
                    examples=examples[:3]
                )
                rules.append(rule)
        
        # Sort by frequency
        return sorted(rules, key=lambda x: x.frequency, reverse=True)
    
    def distance_matrix(self, feature_system: str = 'tresoldi_distinctive') -> pd.DataFrame:
        """
        Calculate phonological distance matrix between languages.
        
        Args:
            feature_system: Feature system to use for distance calculation
            
        Returns:
            DataFrame with pairwise distances
        """
        n_langs = len(self.languages)
        distances = np.zeros((n_langs, n_langs))
        
        for i, lang1 in enumerate(self.languages):
            for j, lang2 in enumerate(self.languages):
                if i != j:
                    distance = self._calculate_language_distance(lang1, lang2, feature_system)
                    distances[i][j] = distance
        
        return pd.DataFrame(distances, index=self.languages, columns=self.languages)
    
    def _calculate_language_distance(self, lang1: str, lang2: str, feature_system: str) -> float:
        """Calculate average phonological distance between two languages."""
        total_distance = 0
        word_count = 0
        
        for meaning, forms in self.cognate_sets.items():
            if lang1 in forms and lang2 in forms:
                word1 = forms[lang1]
                word2 = forms[lang2]
                
                # Calculate word distance
                word_distance = self._calculate_word_distance(word1, word2, feature_system)
                total_distance += word_distance
                word_count += 1
        
        return total_distance / word_count if word_count > 0 else 0
    
    def _calculate_word_distance(self, word1: List[str], word2: List[str], feature_system: str) -> float:
        """Calculate phonological distance between two words."""
        try:
            # Convert to Sound objects
            sounds1 = [Sound(grapheme=s, feature_system=feature_system) for s in word1]
            sounds2 = [Sound(grapheme=s, feature_system=feature_system) for s in word2]
            
            # Align words (simple approach)
            max_len = max(len(sounds1), len(sounds2))
            
            total_distance = 0
            for i in range(max_len):
                if i < len(sounds1) and i < len(sounds2):
                    distance = sounds1[i].distance_to(sounds2[i])
                    total_distance += distance
                else:
                    total_distance += 1.0  # Insertion/deletion penalty
            
            return total_distance / max_len
        except Exception:
            # Fallback to simple string distance
            return self._simple_string_distance(word1, word2)
    
    def _simple_string_distance(self, word1: List[str], word2: List[str]) -> float:
        """Simple string-based distance as fallback."""
        max_len = max(len(word1), len(word2))
        differences = 0
        
        for i in range(max_len):
            sound1 = word1[i] if i < len(word1) else '∅'
            sound2 = word2[i] if i < len(word2) else '∅'
            if sound1 != sound2:
                differences += 1
        
        return differences / max_len if max_len > 0 else 0


@dataclass 
class PhylogeneticTree:
    """Simple phylogenetic tree representation."""
    languages: List[str]
    distances: np.ndarray
    
    def show_ascii(self):
        """Display tree in ASCII format."""
        print("Phylogenetic tree (UPGMA clustering):")
        print()
        
        # Simple UPGMA-style clustering display
        # For demo purposes, show a simplified representation
        distances_df = pd.DataFrame(self.distances, index=self.languages, columns=self.languages)
        
        # Find closest pairs iteratively
        remaining_langs = self.languages.copy()
        clusters = {lang: [lang] for lang in self.languages}
        
        print("Language relationships (closest to furthest):")
        while len(remaining_langs) > 1:
            min_dist = float('inf')
            closest_pair = None
            
            for i, lang1 in enumerate(remaining_langs):
                for j, lang2 in enumerate(remaining_langs):
                    if i < j:
                        dist = distances_df.loc[lang1, lang2]
                        if dist < min_dist:
                            min_dist = dist
                            closest_pair = (lang1, lang2)
            
            if closest_pair:
                lang1, lang2 = closest_pair
                print(f"  {lang1} — {lang2} (distance: {min_dist:.3f})")
                
                # Merge clusters (simplified)
                remaining_langs.remove(lang2)
    
    def export_newick(self) -> str:
        """Export tree in Newick format."""
        # Simplified Newick export
        return f"({','.join(self.languages)});"


def quick_analysis(cognate_sets: Dict[str, Dict[str, List[str]]]) -> None:
    """
    Run a complete quick analysis and print results.
    Perfect for Jupyter notebook demonstrations.
    """
    analysis = ComparativeAnalysis(cognate_sets)
    
    print("🔍 COMPARATIVE ANALYSIS RESULTS")
    print("=" * 50)
    
    # Correspondences
    print("\n📋 Sound Correspondences:")
    correspondences = analysis.find_correspondences()
    for pattern, freq in correspondences.most_common(5):
        print(f"  {' — '.join(pattern)} ({freq}×)")
    
    # Proto-reconstruction  
    print("\n🏛️  Proto-Language Reconstruction:")
    proto = analysis.reconstruct_proto()
    for meaning, form in list(proto.items())[:3]:
        print(f"  *{''.join(form)} '{meaning}'")
    
    # Distance matrix
    print("\n📊 Language Distance Matrix:")
    distances = analysis.distance_matrix()
    print(distances.round(3))
    
    print("\n✅ Analysis complete! Use ComparativeAnalysis() for detailed results.")