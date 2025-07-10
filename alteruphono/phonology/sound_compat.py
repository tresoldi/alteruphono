"""
Backward compatibility layer for the Sound class.

This module provides the original Sound class interface while internally
using the new feature system architecture. This ensures that existing
code continues to work without modification.
"""

from typing import FrozenSet, Optional, Union
from .sound_v2 import Sound as EnhancedSound


class Sound(EnhancedSound):
    """
    Backward-compatible Sound class.
    
    This class maintains the exact same API as the original Sound class
    while internally using the new feature system architecture. All
    existing code should work without modification.
    """
    
    def __init__(
        self,
        grapheme: Optional[str] = None,
        description: Optional[str] = None,
        partial: Optional[bool] = None
    ) -> None:
        """
        Initialize a Sound object (backward-compatible API).
        
        Args:
            grapheme: A grapheme like 'p', 'a', 'V' (sound class)
            description: Feature specification like 'voiced,bilabial'
            partial: Whether this is a partial/underspecified sound
        """
        # Always use the default feature system for backward compatibility
        super().__init__(
            grapheme=grapheme,
            description=description,
            partial=partial,
            feature_system=None  # Use default system
        )
    
    # All other methods are inherited from EnhancedSound
    # The enhanced class maintains full backward compatibility


# For even better compatibility, provide aliases
SoundLegacy = Sound