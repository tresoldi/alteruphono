# __init__.py

"""
__init__ module for the `alteruphono` package.
"""

# Version of the alteruphono package  
__version__ = "0.7.0"  # Phase 4: Suprasegmental and numeric features
__author__ = "Tiago Tresoldi"
__email__ = "tiago.tresoldi@lingfil.uu.se"

# Build the namespace
from alteruphono.model import (
    BoundaryToken,
    ProsodicBoundaryToken,  # Phase 4: Prosodic boundaries
    FocusToken,
    EmptyToken,
    BackRefToken,
    ChoiceToken,
    SetToken,
    SegmentToken,
)
from alteruphono.parser import Rule, parse_rule, parse_seq_as_rule
from alteruphono.common import check_match
from alteruphono.forward import forward
from alteruphono.backward import backward
