#!/usr/bin/env python3
"""
Comprehensive performance benchmarking for the feature system architecture.

This script provides detailed performance analysis of:
- Feature system operations
- Sound creation and manipulation
- Feature arithmetic and conversions
- System comparisons
- Memory usage profiling
"""

import sys
import time
import tracemalloc
import statistics
from typing import List, Dict, Any, Callable
from dataclasses import dataclass
from contextlib import contextmanager

sys.path.insert(0, '/home/tiagot/tresoldi/alteruphono')

from alteruphono.phonology.feature_systems import (
    get_feature_system,
    list_feature_systems,
    FeatureBundle,
    FeatureValue,
    FeatureValueType
)
from alteruphono.phonology.sound_v2 import Sound
from alteruphono.phonology.sound_compat import Sound as CompatSound


@dataclass
class BenchmarkResult:
    """Result of a performance benchmark."""
    name: str
    mean_time: float
    std_time: float
    min_time: float
    max_time: float
    iterations: int
    operations_per_second: float
    memory_peak: float = 0.0
    memory_current: float = 0.0


class PerformanceBenchmarker:
    """Comprehensive performance benchmarking tool."""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.test_graphemes = ['p', 'b', 't', 'd', 'k', 'g', 'a', 'e', 'i', 'o', 'u', 
                              's', 'z', 'f', 'v', 'n', 'm', 'l', 'r', 'w', 'j']
    
    @contextmanager
    def memory_profiling(self):
        """Context manager for memory profiling."""
        tracemalloc.start()
        try:
            yield
        finally:
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            self.current_memory = current / 1024 / 1024  # MB
            self.peak_memory = peak / 1024 / 1024  # MB
    
    def benchmark_function(self, func: Callable, name: str, iterations: int = 1000, 
                         warmup: int = 10) -> BenchmarkResult:
        """Benchmark a function with multiple iterations."""
        
        # Warmup
        for _ in range(warmup):
            func()
        
        times = []
        
        with self.memory_profiling():
            for _ in range(iterations):
                start = time.perf_counter()
                func()
                end = time.perf_counter()
                times.append(end - start)
        
        mean_time = statistics.mean(times)
        std_time = statistics.stdev(times) if len(times) > 1 else 0.0
        min_time = min(times)
        max_time = max(times)
        ops_per_second = 1.0 / mean_time if mean_time > 0 else 0.0
        
        result = BenchmarkResult(
            name=name,
            mean_time=mean_time,
            std_time=std_time,
            min_time=min_time,
            max_time=max_time,
            iterations=iterations,
            operations_per_second=ops_per_second,
            memory_peak=self.peak_memory,
            memory_current=self.current_memory
        )
        
        self.results.append(result)
        return result
    
    def benchmark_sound_creation(self):
        """Benchmark sound creation across different systems."""
        print("=== SOUND CREATION BENCHMARKS ===")
        
        systems = ['ipa_categorical', 'unified_distinctive']
        
        for system_name in systems:
            def create_sounds():
                for grapheme in self.test_graphemes:
                    Sound(grapheme=grapheme, feature_system=system_name)
            
            result = self.benchmark_function(
                create_sounds, 
                f"Sound creation ({system_name})",
                iterations=500
            )
            
            print(f"{result.name}:")
            print(f"  Mean time: {result.mean_time*1000:.3f} ms")
            print(f"  Ops/sec: {result.operations_per_second:.0f}")
            print(f"  Memory peak: {result.memory_peak:.2f} MB")
            print()
    
    def benchmark_feature_access(self):
        """Benchmark feature access operations."""
        print("=== FEATURE ACCESS BENCHMARKS ===")
        
        # Create test sounds
        ipa_sounds = [Sound(grapheme=g, feature_system='ipa_categorical') 
                     for g in self.test_graphemes]
        unified_sounds = [Sound(grapheme=g, feature_system='unified_distinctive') 
                         for g in self.test_graphemes]
        
        def ipa_feature_access():
            for sound in ipa_sounds:
                sound.has_feature('consonant')
                sound.has_feature('voiced')
                if sound.has_feature('bilabial'):
                    sound.get_feature_value('bilabial')
        
        def unified_feature_access():
            for sound in unified_sounds:
                sound.has_feature('consonantal')
                sound.has_feature('voice')
                sound.get_feature_value('voice')
                sound.get_feature_value('sonorant')
        
        result1 = self.benchmark_function(ipa_feature_access, "IPA feature access", 1000)
        result2 = self.benchmark_function(unified_feature_access, "Unified feature access", 1000)
        
        print(f"{result1.name}: {result1.mean_time*1000:.3f} ms")
        print(f"{result2.name}: {result2.mean_time*1000:.3f} ms")
        print(f"Ratio: {result2.mean_time/result1.mean_time:.2f}x")
        print()
    
    def benchmark_feature_arithmetic(self):
        """Benchmark feature arithmetic operations."""
        print("=== FEATURE ARITHMETIC BENCHMARKS ===")
        
        ipa_p = Sound(grapheme='p', feature_system='ipa_categorical')
        unified_p = Sound(grapheme='p', feature_system='unified_distinctive')
        
        def ipa_arithmetic():
            voiced = ipa_p + 'voiced'
            nasal = voiced + 'nasal'
            return nasal
        
        def unified_arithmetic():
            voiced = unified_p + 'voice=1.0'
            nasal = voiced + 'nasal=1.0'
            return nasal
        
        result1 = self.benchmark_function(ipa_arithmetic, "IPA arithmetic", 1000)
        result2 = self.benchmark_function(unified_arithmetic, "Unified arithmetic", 1000)
        
        print(f"{result1.name}: {result1.mean_time*1000:.3f} ms")
        print(f"{result2.name}: {result2.mean_time*1000:.3f} ms")
        print(f"Ratio: {result2.mean_time/result1.mean_time:.2f}x")
        print()
    
    def benchmark_system_conversion(self):
        """Benchmark feature system conversion."""
        print("=== SYSTEM CONVERSION BENCHMARKS ===")
        
        ipa_sounds = [Sound(grapheme=g, feature_system='ipa_categorical') 
                     for g in self.test_graphemes[:10]]  # Smaller set for conversion
        
        def convert_to_unified():
            for sound in ipa_sounds:
                sound.convert_to_system('unified_distinctive')
        
        def convert_back_to_ipa():
            unified_sounds = [s.convert_to_system('unified_distinctive') for s in ipa_sounds]
            for sound in unified_sounds:
                sound.convert_to_system('ipa_categorical')
        
        result1 = self.benchmark_function(convert_to_unified, "IPA → Unified conversion", 200)
        result2 = self.benchmark_function(convert_back_to_ipa, "Round-trip conversion", 100)
        
        print(f"{result1.name}: {result1.mean_time*1000:.3f} ms")
        print(f"{result2.name}: {result2.mean_time*1000:.3f} ms")
        print()
    
    def benchmark_distance_calculations(self):
        """Benchmark distance calculation operations."""
        print("=== DISTANCE CALCULATION BENCHMARKS ===")
        
        ipa_sounds = [Sound(grapheme=g, feature_system='ipa_categorical') 
                     for g in self.test_graphemes[:10]]
        unified_sounds = [Sound(grapheme=g, feature_system='unified_distinctive') 
                         for g in self.test_graphemes[:10]]
        
        def ipa_distances():
            for i, sound1 in enumerate(ipa_sounds):
                for sound2 in ipa_sounds[i+1:]:
                    sound1.distance_to(sound2)
        
        def unified_distances():
            for i, sound1 in enumerate(unified_sounds):
                for sound2 in unified_sounds[i+1:]:
                    sound1.distance_to(sound2)
        
        result1 = self.benchmark_function(ipa_distances, "IPA distance calculations", 100)
        result2 = self.benchmark_function(unified_distances, "Unified distance calculations", 100)
        
        print(f"{result1.name}: {result1.mean_time*1000:.3f} ms")
        print(f"{result2.name}: {result2.mean_time*1000:.3f} ms")
        print(f"Ratio: {result2.mean_time/result1.mean_time:.2f}x")
        print()
    
    def benchmark_advanced_operations(self):
        """Benchmark advanced unified system operations."""
        print("=== ADVANCED OPERATIONS BENCHMARKS ===")
        
        unified_system = get_feature_system('unified_distinctive')
        p_features = unified_system.grapheme_to_features('p')
        b_features = unified_system.grapheme_to_features('b')
        
        def interpolation():
            for ratio in [0.0, 0.25, 0.5, 0.75, 1.0]:
                unified_system.interpolate_sounds(p_features, b_features, ratio)
        
        def vowel_consonant_detection():
            for grapheme in self.test_graphemes:
                features = unified_system.grapheme_to_features(grapheme)
                if features:
                    unified_system.is_vowel_like(features)
                    unified_system.is_consonant_like(features)
        
        result1 = self.benchmark_function(interpolation, "Sound interpolation", 500)
        result2 = self.benchmark_function(vowel_consonant_detection, "Vowel/consonant detection", 500)
        
        print(f"{result1.name}: {result1.mean_time*1000:.3f} ms")
        print(f"{result2.name}: {result2.mean_time*1000:.3f} ms")
        print()
    
    def benchmark_backward_compatibility(self):
        """Benchmark backward compatibility layer."""
        print("=== BACKWARD COMPATIBILITY BENCHMARKS ===")
        
        def old_sound_creation():
            for grapheme in self.test_graphemes:
                CompatSound(grapheme=grapheme)
        
        def new_sound_creation():
            for grapheme in self.test_graphemes:
                Sound(grapheme=grapheme)
        
        result1 = self.benchmark_function(old_sound_creation, "Backward-compatible Sound", 500)
        result2 = self.benchmark_function(new_sound_creation, "Enhanced Sound (default)", 500)
        
        print(f"{result1.name}: {result1.mean_time*1000:.3f} ms")
        print(f"{result2.name}: {result2.mean_time*1000:.3f} ms")
        print(f"Compatibility overhead: {result1.mean_time/result2.mean_time:.2f}x")
        print()
    
    def benchmark_memory_usage(self):
        """Benchmark memory usage of different approaches."""
        print("=== MEMORY USAGE BENCHMARKS ===")
        
        tracemalloc.start()
        
        # Create many sounds with IPA system
        ipa_sounds = []
        snapshot1 = tracemalloc.take_snapshot()
        
        for _ in range(1000):
            for grapheme in self.test_graphemes:
                ipa_sounds.append(Sound(grapheme=grapheme, feature_system='ipa_categorical'))
        
        snapshot2 = tracemalloc.take_snapshot()
        
        # Create many sounds with unified system
        unified_sounds = []
        for _ in range(1000):
            for grapheme in self.test_graphemes:
                unified_sounds.append(Sound(grapheme=grapheme, feature_system='unified_distinctive'))
        
        snapshot3 = tracemalloc.take_snapshot()
        
        # Calculate memory differences
        stats1_2 = snapshot2.compare_to(snapshot1, 'lineno')
        stats2_3 = snapshot3.compare_to(snapshot2, 'lineno')
        
        ipa_memory = sum(stat.size_diff for stat in stats1_2 if stat.size_diff > 0) / 1024 / 1024
        unified_memory = sum(stat.size_diff for stat in stats2_3 if stat.size_diff > 0) / 1024 / 1024
        
        print(f"Memory usage for 21,000 sounds:")
        print(f"  IPA categorical: {ipa_memory:.2f} MB")
        print(f"  Unified distinctive: {unified_memory:.2f} MB")
        print(f"  Ratio: {unified_memory/ipa_memory:.2f}x")
        print()
        
        tracemalloc.stop()
    
    def print_summary(self):
        """Print benchmark summary."""
        print("=== PERFORMANCE SUMMARY ===")
        
        # Group results by category
        categories = {}
        for result in self.results:
            category = result.name.split('(')[0].strip() if '(' in result.name else result.name
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        for category, results in categories.items():
            print(f"\n{category}:")
            for result in results:
                print(f"  {result.name}: {result.mean_time*1000:.3f} ms "
                      f"({result.operations_per_second:.0f} ops/sec)")
        
        # Identify potential bottlenecks
        print("\n=== OPTIMIZATION RECOMMENDATIONS ===")
        
        slow_operations = [r for r in self.results if r.mean_time > 0.001]  # > 1ms
        if slow_operations:
            print("\nOperations that may benefit from optimization:")
            for result in sorted(slow_operations, key=lambda x: x.mean_time, reverse=True):
                print(f"  • {result.name}: {result.mean_time*1000:.3f} ms")
        
        high_memory = [r for r in self.results if r.memory_peak > 10.0]  # > 10MB
        if high_memory:
            print("\nOperations with high memory usage:")
            for result in sorted(high_memory, key=lambda x: x.memory_peak, reverse=True):
                print(f"  • {result.name}: {result.memory_peak:.2f} MB peak")


def main():
    """Run comprehensive performance benchmarks."""
    print("ALTERUPHONO FEATURE SYSTEM PERFORMANCE BENCHMARKS")
    print("=" * 60)
    print("Running comprehensive performance analysis...")
    print()
    
    benchmarker = PerformanceBenchmarker()
    
    # Run all benchmarks
    benchmarker.benchmark_sound_creation()
    benchmarker.benchmark_feature_access()
    benchmarker.benchmark_feature_arithmetic()
    benchmarker.benchmark_system_conversion()
    benchmarker.benchmark_distance_calculations()
    benchmarker.benchmark_advanced_operations()
    benchmarker.benchmark_backward_compatibility()
    benchmarker.benchmark_memory_usage()
    
    # Print summary and recommendations
    benchmarker.print_summary()
    
    print("\n" + "=" * 60)
    print("BENCHMARK COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()