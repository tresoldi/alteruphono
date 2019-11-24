# __init__.py
# encoding: utf-8

"""
__init__ module for the `alteruphono` package.
"""

# Version of the alteruphono package
__version__ = "0.2"
__author__ = "Tiago Tresoldi"
__email__ = "tresoldi@shh.mpg.de"

# Build the namespace
from alteruphono.parser import parse_rule
from alteruphono.phonoast import Token
from alteruphono import utils

# from alteruphono import compiler
# from alteruphono import utils
# from alteruphono.grammar import SOUND_CHANGEParser as Parser
# from alteruphono.changer import apply_forward, apply_backward
#
# from alteruphono.graph import GraphAutomata
# from alteruphono.natural import NLAutomata
# from alteruphono.reconstruction import ForwardAutomata, BackwardAutomata
