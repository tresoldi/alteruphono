"""
Global registry functions for feature systems.

This module provides the public API for working with the feature system registry.
"""

from typing import List
from .base import FeatureSystem, get_registry


def register_feature_system(system: FeatureSystem) -> None:
    """
    Register a new feature system globally.
    
    Args:
        system: The feature system to register
        
    Raises:
        ValueError: If a system with the same name is already registered
    """
    get_registry().register(system)


def get_feature_system(name: str) -> FeatureSystem:
    """
    Get a registered feature system by name.
    
    Args:
        name: Name of the feature system
        
    Returns:
        The requested feature system
        
    Raises:
        ValueError: If the system is not registered
    """
    return get_registry().get(name)


def list_feature_systems() -> List[str]:
    """
    Get a list of all registered feature system names.
    
    Returns:
        List of system names
    """
    return get_registry().list_systems()


def get_default_feature_system() -> FeatureSystem:
    """
    Get the default feature system.
    
    Returns:
        The default feature system
        
    Raises:
        ValueError: If no default system is set
    """
    return get_registry().get_default()


def set_default_feature_system(name: str) -> None:
    """
    Set the default feature system.
    
    Args:
        name: Name of the system to set as default
        
    Raises:
        ValueError: If the system is not registered
    """
    get_registry().set_default(name)