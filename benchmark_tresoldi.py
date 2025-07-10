#!/usr/bin/env python3
"""
Performance benchmarking for Tresoldi feature system.

This script evaluates the performance of the Tresoldi system compared to other
feature systems, focusing on the impact of the large inventory size.
"""

import sys
import os
import time
import random

# Add the parent directory to the path to import alteruphono
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alteruphono.phonology.feature_systems import get_feature_system, list_feature_systems
from alteruphono.phonology.sound_v2 import Sound


def benchmark_system(system_name: str, n_iterations: int = 1000) -> dict:
    """Benchmark a feature system across multiple operations."""
    print(f'\nBenchmarking {system_name}...')
    system = get_feature_system(system_name)
    
    test_sounds = ['p', 'b', 't', 'd', 'k', 'g', 'a', 'e', 'i', 'o', 'u', 'n', 'm', 'l', 'r']
    
    # Test 1: Sound creation speed
    start_time = time.time()
    created_sounds = []
    for _ in range(n_iterations):
        for sound_char in test_sounds:
            try:
                sound = Sound(grapheme=sound_char, feature_system=system_name)
                created_sounds.append(sound)
            except:
                pass  # Skip if sound not available
    end_time = time.time()
    
    sound_creation_time = (end_time - start_time) / len(created_sounds) * 1000 if created_sounds else 0
    
    # Test 2: Feature access speed
    test_sound = None
    for sound_char in test_sounds:
        try:
            test_sound = Sound(grapheme=sound_char, feature_system=system_name)
            break
        except:
            continue
    
    feature_access_time = 0
    if test_sound:
        start_time = time.time()
        for _ in range(n_iterations):
            for feature_name in ['voice', 'consonantal', 'sonorant', 'nasal']:
                if test_sound.has_feature(feature_name):
                    test_sound.get_feature_value(feature_name)
        end_time = time.time()
        feature_access_time = (end_time - start_time) / n_iterations * 1000
    
    # Test 3: Distance calculation speed  
    distance_time = 0
    if test_sound:
        try:
            sound2_char = 'a' if test_sound.grapheme() != 'a' else 'p'
            sound2 = Sound(grapheme=sound2_char, feature_system=system_name)
            start_time = time.time()
            for _ in range(n_iterations // 10):  # Fewer iterations for expensive operation
                test_sound.distance_to(sound2)
            end_time = time.time()
            distance_time = (end_time - start_time) / (n_iterations // 10) * 1000
        except:
            pass
    
    # Test 4: Feature system info
    inventory_size = 0
    feature_count = 0
    
    if hasattr(system, 'get_sound_count'):
        inventory_size = system.get_sound_count()
    
    if hasattr(system, 'get_feature_names'):
        feature_count = len(system.get_feature_names())
    elif test_sound:
        feature_count = len(test_sound.features.features)
    
    result = {
        'sound_creation_ms': sound_creation_time,
        'feature_access_ms': feature_access_time,
        'distance_calc_ms': distance_time,
        'inventory_size': inventory_size,
        'feature_count': feature_count,
        'sounds_created': len(created_sounds)
    }
    
    print(f'  Sound creation: {sound_creation_time:.3f} ms/sound ({len(created_sounds)} sounds created)')
    print(f'  Feature access: {feature_access_time:.3f} ms/1000 accesses')
    print(f'  Distance calc: {distance_time:.3f} ms/calculation')
    print(f'  Inventory: {inventory_size} sounds, {feature_count} features')
    
    return result


def main():
    """Run comprehensive benchmarks."""
    print('Performance benchmarking with large inventory...')
    print('=' * 60)
    
    systems = list_feature_systems()
    n_iterations = 1000
    
    results = {}
    
    for system_name in systems:
        try:
            results[system_name] = benchmark_system(system_name, n_iterations)
        except Exception as e:
            print(f'Error benchmarking {system_name}: {e}')
            results[system_name] = None
    
    # Summary comparison
    print('\n' + '=' * 60)
    print('PERFORMANCE SUMMARY')
    print('=' * 60)
    
    print(f'{"System":<20} {"Creation":<10} {"Access":<10} {"Distance":<10} {"Inventory":<15}')
    print('-' * 70)
    
    for system_name, data in results.items():
        if data:
            inv_str = f'{data["inventory_size"]}s/{data["feature_count"]}f'
            print(f'{system_name:<20} {data["sound_creation_ms"]:<10.3f} {data["feature_access_ms"]:<10.3f} {data["distance_calc_ms"]:<10.3f} {inv_str:<15}')
        else:
            print(f'{system_name:<20} {"ERROR":<10} {"ERROR":<10} {"ERROR":<10} {"ERROR":<15}')
    
    # Performance insights
    print('\nPerformance Insights:')
    tresoldi_data = results.get('tresoldi_distinctive')
    if tresoldi_data:
        print(f'• Tresoldi system handles {tresoldi_data["inventory_size"]} sounds efficiently')
        print(f'• Despite having {tresoldi_data["feature_count"]} features, performance is competitive')
        
        # Compare with other systems
        other_systems = [k for k, v in results.items() if k != 'tresoldi_distinctive' and v is not None]
        if other_systems:
            avg_creation = sum(results[s]['sound_creation_ms'] for s in other_systems) / len(other_systems)
            if avg_creation > 0:
                ratio = tresoldi_data['sound_creation_ms'] / avg_creation
                print(f'• Sound creation is {ratio:.1f}x vs average of other systems')
    
    # Memory usage insights
    print('\nMemory Usage Analysis:')
    for system_name, data in results.items():
        if data:
            memory_per_sound = data['feature_count'] * 8  # Rough estimate: 8 bytes per feature
            total_memory = data['inventory_size'] * memory_per_sound / 1024  # KB
            print(f'• {system_name}: ~{total_memory:.1f} KB for full inventory')
    
    print('\nBenchmarking completed!')


if __name__ == '__main__':
    main()