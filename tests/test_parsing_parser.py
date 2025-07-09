"""
Tests for the new parsing system - Parser component.
"""

import unittest
from alteruphono.parsing.parser import Parser
from alteruphono.parsing.lexer import Lexer
from alteruphono.parsing.ast_nodes import *
from alteruphono.parsing.errors import ParseError, SyntaxError


class TestParser(unittest.TestCase):
    """Test the parser AST generation."""
    
    def parse_rule(self, rule_string: str) -> RuleNode:
        """Helper to parse a rule string and return AST."""
        lexer = Lexer(rule_string)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        return parser.parse_rule()
    
    def test_simple_rule(self):
        """Test parsing a simple rule."""
        rule = self.parse_rule("p > b")
        
        # Check rule structure
        self.assertIsInstance(rule, RuleNode)
        self.assertIsNone(rule.context)
        
        # Check ante
        self.assertEqual(len(rule.ante.atoms), 1)
        ante_atom = rule.ante.atoms[0]
        self.assertIsInstance(ante_atom, SegmentNode)
        self.assertEqual(ante_atom.grapheme, "p")
        self.assertIsNone(ante_atom.features)
        
        # Check post
        self.assertEqual(len(rule.post.atoms), 1)
        post_atom = rule.post.atoms[0]
        self.assertIsInstance(post_atom, SegmentNode)
        self.assertEqual(post_atom.grapheme, "b")
        self.assertIsNone(post_atom.features)
    
    def test_rule_with_context(self):
        """Test parsing a rule with context."""
        rule = self.parse_rule("p > b / a _ a")
        
        # Check rule structure
        self.assertIsInstance(rule, RuleNode)
        self.assertIsNotNone(rule.context)
        
        # Check ante
        self.assertEqual(len(rule.ante.atoms), 1)
        ante_atom = rule.ante.atoms[0]
        self.assertIsInstance(ante_atom, SegmentNode)
        self.assertEqual(ante_atom.grapheme, "p")
        
        # Check post
        self.assertEqual(len(rule.post.atoms), 1)
        post_atom = rule.post.atoms[0]
        self.assertIsInstance(post_atom, SegmentNode)
        self.assertEqual(post_atom.grapheme, "b")
        
        # Check context
        context = rule.context
        self.assertIsInstance(context, ContextNode)
        
        # Check left context
        self.assertEqual(len(context.left_context.atoms), 1)
        left_atom = context.left_context.atoms[0]
        self.assertIsInstance(left_atom, SegmentNode)
        self.assertEqual(left_atom.grapheme, "a")
        
        # Check right context
        self.assertEqual(len(context.right_context.atoms), 1)
        right_atom = context.right_context.atoms[0]
        self.assertIsInstance(right_atom, SegmentNode)
        self.assertEqual(right_atom.grapheme, "a")
    
    def test_sound_classes(self):
        """Test parsing sound classes."""
        rule = self.parse_rule("V > C")
        
        # Check ante
        ante_atom = rule.ante.atoms[0]
        self.assertIsInstance(ante_atom, SoundClassNode)
        self.assertEqual(ante_atom.class_name, "V")
        
        # Check post
        post_atom = rule.post.atoms[0]
        self.assertIsInstance(post_atom, SoundClassNode)
        self.assertEqual(post_atom.class_name, "C")
    
    def test_features(self):
        """Test parsing features."""
        rule = self.parse_rule("p[voiced] > b")
        
        # Check ante
        ante_atom = rule.ante.atoms[0]
        self.assertIsInstance(ante_atom, SegmentNode)
        self.assertEqual(ante_atom.grapheme, "p")
        self.assertIsNotNone(ante_atom.features)
        
        # Check features
        features = ante_atom.features
        self.assertIsInstance(features, FeatureSpecNode)
        self.assertEqual(len(features.features), 1)
        
        feature = features.features[0]
        self.assertIsInstance(feature, FeatureNode)
        self.assertEqual(feature.name, "voiced")
        self.assertIsNone(feature.polarity)
        self.assertIsNone(feature.value)
    
    def test_feature_polarity(self):
        """Test parsing feature polarity."""
        rule = self.parse_rule("p[+voiced,-nasal] > b")
        
        # Check ante
        ante_atom = rule.ante.atoms[0]
        features = ante_atom.features
        self.assertEqual(len(features.features), 2)
        
        # Check first feature (+voiced)
        feature1 = features.features[0]
        self.assertEqual(feature1.name, "voiced")
        self.assertEqual(feature1.polarity, "+")
        
        # Check second feature (-nasal)
        feature2 = features.features[1]
        self.assertEqual(feature2.name, "nasal")
        self.assertEqual(feature2.polarity, "-")
    
    def test_backreferences(self):
        """Test parsing backreferences."""
        rule = self.parse_rule("p a > @1 @2")
        
        # Check ante
        self.assertEqual(len(rule.ante.atoms), 2)
        
        # Check post
        self.assertEqual(len(rule.post.atoms), 2)
        
        # Check first backreference
        backref1 = rule.post.atoms[0]
        self.assertIsInstance(backref1, BackRefNode)
        self.assertEqual(backref1.index, 0)  # @1 = index 0
        self.assertIsNone(backref1.features)
        
        # Check second backreference
        backref2 = rule.post.atoms[1]
        self.assertIsInstance(backref2, BackRefNode)
        self.assertEqual(backref2.index, 1)  # @2 = index 1
        self.assertIsNone(backref2.features)
    
    def test_backreferences_with_features(self):
        """Test parsing backreferences with features."""
        rule = self.parse_rule("p > @1[voiced]")
        
        # Check post
        backref = rule.post.atoms[0]
        self.assertIsInstance(backref, BackRefNode)
        self.assertEqual(backref.index, 0)
        self.assertIsNotNone(backref.features)
        
        # Check features
        features = backref.features
        self.assertEqual(len(features.features), 1)
        feature = features.features[0]
        self.assertEqual(feature.name, "voiced")
    
    def test_choices(self):
        """Test parsing choices."""
        rule = self.parse_rule("p|t > b")
        
        # Check ante
        ante_atom = rule.ante.atoms[0]
        self.assertIsInstance(ante_atom, ChoiceNode)
        self.assertEqual(len(ante_atom.alternatives), 2)
        
        # Check alternatives
        alt1 = ante_atom.alternatives[0]
        self.assertIsInstance(alt1, SegmentNode)
        self.assertEqual(alt1.grapheme, "p")
        
        alt2 = ante_atom.alternatives[1]
        self.assertIsInstance(alt2, SegmentNode)
        self.assertEqual(alt2.grapheme, "t")
    
    def test_sets(self):
        """Test parsing sets."""
        rule = self.parse_rule("{p|t} > b")
        
        # Check ante
        ante_atom = rule.ante.atoms[0]
        self.assertIsInstance(ante_atom, SetNode)
        self.assertEqual(len(ante_atom.alternatives), 2)
        
        # Check alternatives
        alt1 = ante_atom.alternatives[0]
        self.assertIsInstance(alt1, SegmentNode)
        self.assertEqual(alt1.grapheme, "p")
        
        alt2 = ante_atom.alternatives[1]
        self.assertIsInstance(alt2, SegmentNode)
        self.assertEqual(alt2.grapheme, "t")
    
    def test_boundaries(self):
        """Test parsing boundaries."""
        rule = self.parse_rule("p > b / # _")
        
        # Check context
        context = rule.context
        left_atom = context.left_context.atoms[0]
        self.assertIsInstance(left_atom, BoundaryNode)
        
        # Check that right context is empty
        self.assertEqual(len(context.right_context.atoms), 0)
    
    def test_null_deletion(self):
        """Test parsing null/deletion."""
        rule = self.parse_rule("p > :null:")
        
        # Check post
        post_atom = rule.post.atoms[0]
        self.assertIsInstance(post_atom, NullNode)
    
    def test_complex_rule(self):
        """Test parsing a complex rule with multiple features."""
        rule = self.parse_rule("S[voiceless] a > @1[fricative] a")
        
        # Check ante
        self.assertEqual(len(rule.ante.atoms), 2)
        
        # Check first ante atom (S[voiceless])
        ante1 = rule.ante.atoms[0]
        self.assertIsInstance(ante1, SoundClassNode)
        self.assertEqual(ante1.class_name, "S")
        self.assertIsNotNone(ante1.features)
        
        feature = ante1.features.features[0]
        self.assertEqual(feature.name, "voiceless")
        
        # Check second ante atom (a)
        ante2 = rule.ante.atoms[1]
        self.assertIsInstance(ante2, SegmentNode)
        self.assertEqual(ante2.grapheme, "a")
        
        # Check post
        self.assertEqual(len(rule.post.atoms), 2)
        
        # Check first post atom (@1[fricative])
        post1 = rule.post.atoms[0]
        self.assertIsInstance(post1, BackRefNode)
        self.assertEqual(post1.index, 0)
        self.assertIsNotNone(post1.features)
        
        backref_feature = post1.features.features[0]
        self.assertEqual(backref_feature.name, "fricative")
        
        # Check second post atom (a)
        post2 = rule.post.atoms[1]
        self.assertIsInstance(post2, SegmentNode)
        self.assertEqual(post2.grapheme, "a")
    
    def test_multiple_segments(self):
        """Test parsing rules with multiple segments."""
        rule = self.parse_rule("p t k > b d g")
        
        # Check ante
        self.assertEqual(len(rule.ante.atoms), 3)
        ante_segments = [atom.grapheme for atom in rule.ante.atoms]
        self.assertEqual(ante_segments, ["p", "t", "k"])
        
        # Check post
        self.assertEqual(len(rule.post.atoms), 3)
        post_segments = [atom.grapheme for atom in rule.post.atoms]
        self.assertEqual(post_segments, ["b", "d", "g"])
    
    def test_complex_context(self):
        """Test parsing rules with complex context."""
        rule = self.parse_rule("p > b / V _ V")
        
        # Check context
        context = rule.context
        
        # Check left context
        left_atom = context.left_context.atoms[0]
        self.assertIsInstance(left_atom, SoundClassNode)
        self.assertEqual(left_atom.class_name, "V")
        
        # Check right context
        right_atom = context.right_context.atoms[0]
        self.assertIsInstance(right_atom, SoundClassNode)
        self.assertEqual(right_atom.class_name, "V")
    
    def test_error_handling(self):
        """Test error handling for malformed rules."""
        with self.assertRaises((ParseError, SyntaxError)):
            self.parse_rule("p >")  # Missing post
        
        with self.assertRaises((ParseError, SyntaxError)):
            self.parse_rule("> b")  # Missing ante
        
        with self.assertRaises((ParseError, SyntaxError)):
            self.parse_rule("p b")  # Missing arrow
        
        with self.assertRaises((ParseError, SyntaxError)):
            self.parse_rule("p > b /")  # Missing context
        
        with self.assertRaises((ParseError, SyntaxError)):
            self.parse_rule("p > b / a")  # Missing focus in context
    
    def test_empty_sequences(self):
        """Test handling of empty sequences."""
        # Insertion rule (empty ante)
        rule = self.parse_rule(":null: > p")
        
        # Check ante
        self.assertEqual(len(rule.ante.atoms), 1)
        ante_atom = rule.ante.atoms[0]
        self.assertIsInstance(ante_atom, NullNode)
        
        # Check post
        self.assertEqual(len(rule.post.atoms), 1)
        post_atom = rule.post.atoms[0]
        self.assertIsInstance(post_atom, SegmentNode)
        self.assertEqual(post_atom.grapheme, "p")


class TestParserRealWorldExamples(unittest.TestCase):
    """Test parser with real-world phonological rules."""
    
    def parse_rule(self, rule_string: str) -> RuleNode:
        """Helper to parse a rule string and return AST."""
        lexer = Lexer(rule_string)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        return parser.parse_rule()
    
    def test_germanic_rules(self):
        """Test with Germanic sound change rules."""
        rules = [
            "p t k > b d g / V _ V",  # Lenition
            "s > z / V _ V",          # Voicing
            "ai > e / _ #",           # Monophthongization
            "kw > p / _ V",           # Labialization
            "θ > d / V _ V",          # Spirant law
        ]
        
        for rule_str in rules:
            rule = self.parse_rule(rule_str)
            self.assertIsInstance(rule, RuleNode)
            # Just check that parsing succeeds
    
    def test_romance_rules(self):
        """Test with Romance sound change rules."""
        rules = [
            "kt > tt",                # Simplification
            "V > V[+stress] / _ C #", # Final stress
            "s C > C / _ #",          # Cluster reduction
            "p t k > b d g / V _ V",  # Lenition
            "f > h / V _ V",          # Weakening
        ]
        
        for rule_str in rules:
            rule = self.parse_rule(rule_str)
            self.assertIsInstance(rule, RuleNode)
    
    def test_complex_features(self):
        """Test with complex feature specifications."""
        rules = [
            "C[+voice,-nasal] > C[-voice]",
            "V[high,front] > V[+tense]",
            "S[voiceless] a > @1[fricative] a",
            "p[+aspirated] > p[-aspirated] / _ t",
            "V[+stress] > V[-stress] / V[+stress] C _",
        ]
        
        for rule_str in rules:
            rule = self.parse_rule(rule_str)
            self.assertIsInstance(rule, RuleNode)
    
    def test_deletion_insertion(self):
        """Test deletion and insertion rules."""
        rules = [
            "h > :null: / V _ V",     # Deletion
            ":null: > ə / C _ C",     # Insertion
            "ə > :null: / _ #",       # Final deletion
            "V > :null: / _ C C",     # Syncope
        ]
        
        for rule_str in rules:
            rule = self.parse_rule(rule_str)
            self.assertIsInstance(rule, RuleNode)
    
    def test_metathesis_rules(self):
        """Test metathesis rules using backreferences."""
        rules = [
            "r V > @2 @1",           # Simple metathesis
            "C l > l @1",            # Liquid metathesis
            "s k > k s",             # Consonant metathesis
        ]
        
        for rule_str in rules:
            rule = self.parse_rule(rule_str)
            self.assertIsInstance(rule, RuleNode)
    
    def test_assimilation_rules(self):
        """Test assimilation rules."""
        rules = [
            "n > m / _ p",            # Place assimilation
            "t > d / _ V[+voice]",    # Voice assimilation
            "s > ʃ / _ i",            # Palatalization
        ]
        
        for rule_str in rules:
            rule = self.parse_rule(rule_str)
            self.assertIsInstance(rule, RuleNode)


if __name__ == "__main__":
    unittest.main()