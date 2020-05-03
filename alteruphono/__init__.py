# __init__.py

"""
__init__ module for the `alteruphono` package.
"""

# Version of the alteruphono package
__version__ = "0.3"
__author__ = "Tiago Tresoldi"
__email__ = "tresoldi@shh.mpg.de"

# Build the namespace
from alteruphono import utils
from alteruphono.parser import parse_rule
from alteruphono.model import Model
from alteruphono.sequence import Sequence
