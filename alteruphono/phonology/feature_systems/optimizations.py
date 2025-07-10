"""
Performance optimizations for the feature system architecture.

This module provides caching, memoization, and other performance improvements
for feature system operations based on benchmarking results.
"""

import functools
from typing import Any, Dict, Optional, FrozenSet, Tuple
from weakref import WeakKeyDictionary, WeakValueDictionary

from .base import FeatureBundle, FeatureValue, FeatureSystem


class FeatureSystemCache:
    """Centralized caching system for feature operations."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.grapheme_cache: Dict[Tuple[str, str], Optional[FeatureBundle]] = {}
        self.features_cache: Dict[Tuple[str, FrozenSet[FeatureValue]], str] = {}
        self.distance_cache: Dict[Tuple[FeatureBundle, FeatureBundle], float] = {}
        self.conversion_cache: Dict[Tuple[str, str, FeatureBundle], FeatureBundle] = {}
        
        # Statistics for cache performance
        self.stats = {
            'grapheme_hits': 0,
            'grapheme_misses': 0,
            'features_hits': 0,
            'features_misses': 0,
            'distance_hits': 0,
            'distance_misses': 0,
            'conversion_hits': 0,
            'conversion_misses': 0,
        }
    
    def _evict_if_needed(self, cache_dict: Dict) -> None:
        """Evict oldest entries if cache is too large."""
        if len(cache_dict) >= self.max_size:
            # Remove oldest 20% of entries (simple FIFO strategy)
            to_remove = list(cache_dict.keys())[:self.max_size // 5]
            for key in to_remove:
                cache_dict.pop(key, None)
    
    def get_grapheme_features(self, system_name: str, grapheme: str) -> Optional[FeatureBundle]:
        """Get cached features for a grapheme."""
        key = (system_name, grapheme)
        if key in self.grapheme_cache:
            self.stats['grapheme_hits'] += 1
            return self.grapheme_cache[key]
        
        self.stats['grapheme_misses'] += 1
        return None
    
    def cache_grapheme_features(self, system_name: str, grapheme: str, 
                               features: Optional[FeatureBundle]) -> None:
        """Cache features for a grapheme."""
        key = (system_name, grapheme)
        self._evict_if_needed(self.grapheme_cache)
        self.grapheme_cache[key] = features
    
    def get_features_grapheme(self, system_name: str, features: FeatureBundle) -> Optional[str]:
        """Get cached grapheme for features."""
        key = (system_name, frozenset(features.features))
        if key in self.features_cache:
            self.stats['features_hits'] += 1
            return self.features_cache[key]
        
        self.stats['features_misses'] += 1
        return None
    
    def cache_features_grapheme(self, system_name: str, features: FeatureBundle, 
                               grapheme: str) -> None:
        """Cache grapheme for features."""
        key = (system_name, frozenset(features.features))
        self._evict_if_needed(self.features_cache)
        self.features_cache[key] = grapheme
    
    def get_distance(self, features1: FeatureBundle, features2: FeatureBundle) -> Optional[float]:
        """Get cached distance between feature bundles."""
        # Ensure consistent ordering for cache key
        key = (features1, features2) if id(features1) < id(features2) else (features2, features1)
        
        if key in self.distance_cache:
            self.stats['distance_hits'] += 1
            return self.distance_cache[key]
        
        self.stats['distance_misses'] += 1
        return None
    
    def cache_distance(self, features1: FeatureBundle, features2: FeatureBundle, 
                      distance: float) -> None:
        """Cache distance between feature bundles."""
        # Ensure consistent ordering for cache key
        key = (features1, features2) if id(features1) < id(features2) else (features2, features1)
        
        self._evict_if_needed(self.distance_cache)
        self.distance_cache[key] = distance
    
    def get_conversion(self, from_system: str, to_system: str, 
                      features: FeatureBundle) -> Optional[FeatureBundle]:
        """Get cached conversion result."""
        key = (from_system, to_system, features)
        if key in self.conversion_cache:
            self.stats['conversion_hits'] += 1
            return self.conversion_cache[key]
        
        self.stats['conversion_misses'] += 1
        return None
    
    def cache_conversion(self, from_system: str, to_system: str, 
                        features: FeatureBundle, result: FeatureBundle) -> None:
        """Cache conversion result."""
        key = (from_system, to_system, features)
        self._evict_if_needed(self.conversion_cache)
        self.conversion_cache[key] = result
    
    def clear(self) -> None:
        """Clear all caches."""
        self.grapheme_cache.clear()
        self.features_cache.clear()
        self.distance_cache.clear()
        self.conversion_cache.clear()
    
    def get_hit_rate(self) -> Dict[str, float]:
        """Get cache hit rates for monitoring."""
        hit_rates = {}
        
        for operation in ['grapheme', 'features', 'distance', 'conversion']:
            hits = self.stats[f'{operation}_hits']
            misses = self.stats[f'{operation}_misses']
            total = hits + misses
            hit_rates[operation] = hits / total if total > 0 else 0.0
        
        return hit_rates


# Global cache instance
_global_cache = FeatureSystemCache()


def get_global_cache() -> FeatureSystemCache:
    """Get the global feature system cache."""
    return _global_cache


def cached_method(cache_key_func):
    """Decorator for caching method results."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            cache = get_global_cache()
            cache_key = cache_key_func(self, *args, **kwargs)
            
            # Try to get from cache
            cached_result = getattr(cache, f'get_{func.__name__}', lambda *a: None)(*cache_key)
            if cached_result is not None:
                return cached_result
            
            # Compute result and cache it
            result = func(self, *args, **kwargs)
            cache_method = getattr(cache, f'cache_{func.__name__}', None)
            if cache_method:
                cache_method(*cache_key, result)
            
            return result
        return wrapper
    return decorator


class OptimizedFeatureBundle(FeatureBundle):
    """Optimized version of FeatureBundle with caching."""
    
    def __init__(self, features: FrozenSet[FeatureValue]):
        super().__init__(features)
        # Pre-compute frequently accessed values
        self._feature_dict = {f.feature: f for f in features}
        self._feature_names = frozenset(f.feature for f in features)
    
    def has_feature(self, feature_name: str) -> bool:
        """Fast feature existence check."""
        return feature_name in self._feature_names
    
    def get_feature(self, feature_name: str) -> Optional[FeatureValue]:
        """Fast feature lookup."""
        return self._feature_dict.get(feature_name)


def memoize_with_size_limit(maxsize: int = 128):
    """Custom memoization decorator with size limit."""
    def decorator(func):
        cache = {}
        cache_order = []
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from hashable arguments
            key = str(args) + str(sorted(kwargs.items()))
            
            if key in cache:
                # Move to end (LRU)
                cache_order.remove(key)
                cache_order.append(key)
                return cache[key]
            
            # Compute result
            result = func(*args, **kwargs)
            
            # Add to cache
            cache[key] = result
            cache_order.append(key)
            
            # Evict if needed
            if len(cache) > maxsize:
                oldest = cache_order.pop(0)
                del cache[oldest]
            
            return result
        
        wrapper.cache_clear = lambda: cache.clear() or cache_order.clear()
        wrapper.cache_info = lambda: {'size': len(cache), 'maxsize': maxsize}
        return wrapper
    return decorator


class FastFeatureOperations:
    """Fast implementations of common feature operations."""
    
    @staticmethod
    @memoize_with_size_limit(256)
    def fast_feature_distance(features1: FrozenSet[FeatureValue], 
                             features2: FrozenSet[FeatureValue]) -> float:
        """Optimized feature distance calculation."""
        # Convert to dictionaries for fast lookup
        dict1 = {f.feature: f.value for f in features1}
        dict2 = {f.feature: f.value for f in features2}
        
        all_features = set(dict1.keys()) | set(dict2.keys())
        
        if not all_features:
            return 0.0
        
        total_diff = 0.0
        
        for feature in all_features:
            val1 = dict1.get(feature, 0.0)
            val2 = dict2.get(feature, 0.0)
            
            # Convert values to comparable form
            if isinstance(val1, bool):
                val1 = 1.0 if val1 else -1.0
            elif isinstance(val1, str):
                val1 = hash(val1) % 1000 / 1000.0  # Simple string hashing
            
            if isinstance(val2, bool):
                val2 = 1.0 if val2 else -1.0
            elif isinstance(val2, str):
                val2 = hash(val2) % 1000 / 1000.0
            
            total_diff += abs(float(val1) - float(val2)) ** 2
        
        return (total_diff / len(all_features)) ** 0.5
    
    @staticmethod
    @memoize_with_size_limit(512)
    def fast_feature_interpolation(features1: FrozenSet[FeatureValue],
                                  features2: FrozenSet[FeatureValue],
                                  ratio: float) -> FrozenSet[FeatureValue]:
        """Optimized feature interpolation."""
        dict1 = {f.feature: f for f in features1}
        dict2 = {f.feature: f for f in features2}
        
        all_features = set(dict1.keys()) | set(dict2.keys())
        result_features = set()
        
        for feature in all_features:
            f1 = dict1.get(feature)
            f2 = dict2.get(feature)
            
            if f1 and f2 and f1.value_type == f2.value_type:
                if f1.value_type.value == "scalar":
                    # Interpolate scalar values
                    new_value = f1.value * (1 - ratio) + f2.value * ratio
                    result_features.add(FeatureValue(feature, new_value, f1.value_type))
                else:
                    # Use f2's value if ratio > 0.5, else f1's value
                    chosen_feature = f2 if ratio > 0.5 else f1
                    result_features.add(chosen_feature)
            elif f1:
                result_features.add(f1)
            elif f2:
                result_features.add(f2)
        
        return frozenset(result_features)


def optimize_feature_system(feature_system: FeatureSystem) -> FeatureSystem:
    """Apply optimizations to a feature system."""
    
    # Patch methods with cached versions
    original_grapheme_to_features = feature_system.grapheme_to_features
    original_features_to_grapheme = feature_system.features_to_grapheme
    
    def cached_grapheme_to_features(grapheme: str) -> Optional[FeatureBundle]:
        cache = get_global_cache()
        cached = cache.get_grapheme_features(feature_system.name, grapheme)
        if cached is not None:
            return cached
        
        result = original_grapheme_to_features(grapheme)
        cache.cache_grapheme_features(feature_system.name, grapheme, result)
        return result
    
    def cached_features_to_grapheme(features: FeatureBundle) -> str:
        cache = get_global_cache()
        cached = cache.get_features_grapheme(feature_system.name, features)
        if cached is not None:
            return cached
        
        result = original_features_to_grapheme(features)
        cache.cache_features_grapheme(feature_system.name, features, result)
        return result
    
    # Replace methods
    feature_system.grapheme_to_features = cached_grapheme_to_features
    feature_system.features_to_grapheme = cached_features_to_grapheme
    
    return feature_system