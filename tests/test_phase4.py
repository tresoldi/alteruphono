"""
Tests for Phase 4 features: suprasegmental and numeric features.
"""

import unittest
from alteruphono.phonology.sound import Sound
from alteruphono.phonology.models import (
    is_suprasegmental_feature,
    is_numeric_feature,
    get_numeric_value,
    increment_numeric_feature,
    decrement_numeric_feature
)
from alteruphono.phonology.prosody import (
    ProsodicBoundary,
    BoundaryType,
    Syllable,
    ProsodicWord,
    syllabify_sounds,
    parse_prosodic_string
)
from alteruphono.model import ProsodicBoundaryToken, SegmentToken
from alteruphono.parser import parse_atom


class TestSuprasegmentalFeatures(unittest.TestCase):
    """Test suprasegmental feature handling."""
    
    def test_stress_features(self):
        """Test stress feature operations."""
        # Create a vowel and add stress
        vowel = Sound(grapheme='a')
        stressed = vowel + 'stress1'
        
        assert stressed.has_stress()
        assert stressed.get_stress_level() == 1
        assert 'stress1' in stressed.fvalues
        
        # Test secondary stress
        secondary = vowel + 'stress2'
        assert secondary.get_stress_level() == 2
        assert 'stress2' in secondary.fvalues
        
        # Test unstressed
        unstressed = stressed + 'unstressed'
        assert not unstressed.has_stress()
        assert 'unstressed' in unstressed.fvalues
        assert 'stress1' not in unstressed.fvalues
    
    def test_tone_features(self):
        """Test tone feature operations."""
        vowel = Sound(grapheme='a')
        
        # Test basic tone levels
        high_tone = vowel + 'tone1'
        assert high_tone.has_tone()
        assert high_tone.get_tone_value() == 1
        assert 'tone1' in high_tone.fvalues
        
        mid_tone = vowel + 'tone2'
        assert mid_tone.get_tone_value() == 2
        
        low_tone = vowel + 'tone3'
        assert low_tone.get_tone_value() == 3
        
        # Test tone contours
        rising = vowel + 'rising'
        assert rising.has_tone()
        assert 'rising' in rising.fvalues
        
        falling = vowel + 'falling'
        assert 'falling' in falling.fvalues
        assert 'rising' not in falling.fvalues  # Should replace rising
    
    def test_feature_identification(self):
        """Test suprasegmental feature identification."""
        assert is_suprasegmental_feature('stress1')
        assert is_suprasegmental_feature('stress2')
        assert is_suprasegmental_feature('unstressed')
        assert is_suprasegmental_feature('tone1')
        assert is_suprasegmental_feature('rising')
        assert is_suprasegmental_feature('falling')
        assert is_suprasegmental_feature('f0_3')
        assert is_suprasegmental_feature('duration_2')
        
        assert not is_suprasegmental_feature('voiced')
        assert not is_suprasegmental_feature('consonant')
        assert not is_suprasegmental_feature('bilabial')


class TestNumericFeatures(unittest.TestCase):
    """Test numeric feature handling."""
    
    def test_numeric_feature_identification(self):
        """Test identification of numeric features."""
        assert is_numeric_feature('f0_3')
        assert is_numeric_feature('duration_2')
        assert is_numeric_feature('tone1')
        assert is_numeric_feature('tone5')
        
        assert not is_numeric_feature('voiced')
        assert not is_numeric_feature('stress1')  # Not purely numeric
    
    def test_numeric_value_extraction(self):
        """Test extraction of numeric values."""
        assert get_numeric_value('f0_3') == 3
        assert get_numeric_value('duration_2') == 2
        assert get_numeric_value('tone1') == 1
        assert get_numeric_value('tone5') == 5
        assert get_numeric_value('voiced') == 0  # Non-numeric
    
    def test_numeric_feature_arithmetic(self):
        """Test incrementing and decrementing numeric features."""
        # Test increment
        assert increment_numeric_feature('f0_3', 1) == 'f0_4'
        assert increment_numeric_feature('f0_3', 2) == 'f0_5'
        assert increment_numeric_feature('tone1', 1) == 'tone2'
        assert increment_numeric_feature('duration_2', 1) == 'duration_3'
        
        # Test decrement
        assert decrement_numeric_feature('f0_3', 1) == 'f0_2'
        assert decrement_numeric_feature('tone3', 1) == 'tone2'
        assert decrement_numeric_feature('f0_2', 1) == 'f0_1'
        assert decrement_numeric_feature('f0_1', 1) == 'f0_1'  # Minimum is 1
        
        # Test non-numeric features pass through unchanged
        assert increment_numeric_feature('voiced', 1) == 'voiced'
        assert decrement_numeric_feature('voiced', 1) == 'voiced'
    
    def test_sound_numeric_operations(self):
        """Test numeric operations on Sound objects."""
        sound = Sound(grapheme='a') + 'f0_2'
        
        # Test increment
        incremented = sound.increment_feature('f0', 1)
        assert 'f0_3' in incremented.fvalues
        assert 'f0_2' not in incremented.fvalues
        
        # Test decrement
        decremented = sound.decrement_feature('f0', 1)
        assert 'f0_1' in decremented.fvalues
        assert 'f0_2' not in decremented.fvalues
        
        # Test adding new numeric feature
        with_tone = sound.increment_feature('tone', 2)
        assert 'tone_2' in with_tone.fvalues


class TestProsodicHierarchy(unittest.TestCase):
    """Test prosodic hierarchy support."""
    
    def test_prosodic_boundary_creation(self):
        """Test creation of prosodic boundaries."""
        syll_boundary = ProsodicBoundary(BoundaryType.SYLLABLE)
        assert str(syll_boundary) == 'σ'
        
        foot_boundary = ProsodicBoundary(BoundaryType.FOOT)
        assert str(foot_boundary) == 'Ft'
        
        word_boundary = ProsodicBoundary(BoundaryType.WORD)
        assert str(word_boundary) == '#'
        
        # Test with strength
        strong_boundary = ProsodicBoundary(BoundaryType.WORD, strength=3)
        assert str(strong_boundary) == '#3'
    
    def test_syllable_creation(self):
        """Test syllable creation and properties."""
        # Create sounds
        p = Sound(grapheme='p')
        a = Sound(grapheme='a')
        t = Sound(grapheme='t')
        
        # Create syllable
        syllable = Syllable(onset=[p], nucleus=[a], coda=[t])
        
        assert len(syllable.onset) == 1
        assert len(syllable.nucleus) == 1
        assert len(syllable.coda) == 1
        assert not syllable.is_stressed()
        assert syllable.is_heavy()  # Has coda
        
        # Test with stress
        stressed_syll = Syllable(onset=[p], nucleus=[a], coda=[t], stress=1)
        assert stressed_syll.is_stressed()
        assert stressed_syll.get_stress_level() == 1
        
        # Test syllable without coda
        light_syll = Syllable(onset=[p], nucleus=[a])
        assert not light_syll.is_heavy()  # No coda, short vowel
    
    def test_prosodic_word(self):
        """Test prosodic word creation and stress patterns."""
        # Create syllables
        p = Sound(grapheme='p')
        a = Sound(grapheme='a')
        t = Sound(grapheme='t')
        i = Sound(grapheme='i')
        
        syll1 = Syllable(onset=[p], nucleus=[a], stress=1)  # Stressed
        syll2 = Syllable(onset=[t], nucleus=[i], stress=0)  # Unstressed
        
        word = ProsodicWord([syll1, syll2])
        
        assert len(word.syllables) == 2
        assert word.get_stress_pattern() == [1, 0]
        assert word.get_main_stress_position() == 0
        
        # Test stress assignment
        word.assign_stress("01")  # Change to iambic
        assert word.get_stress_pattern() == [0, 1]
        assert word.get_main_stress_position() == 1
    
    def test_syllabification(self):
        """Test automatic syllabification."""
        # Create sequence: pa.ta
        p = Sound(grapheme='p')
        a = Sound(grapheme='a')
        t = Sound(grapheme='t')
        
        sounds = [p, a, t, a]
        syllables = syllabify_sounds(sounds)
        
        assert len(syllables) == 2
        
        # First syllable: pa
        assert len(syllables[0].onset) == 1
        assert len(syllables[0].nucleus) == 1
        assert len(syllables[0].coda) == 0
        
        # Second syllable: ta
        assert len(syllables[1].onset) == 1
        assert len(syllables[1].nucleus) == 1
        assert len(syllables[1].coda) == 0
    
    def test_prosodic_string_parsing(self):
        """Test parsing of prosodic markup."""
        # Test basic parsing
        result = parse_prosodic_string("p a σ t a")
        
        assert len(result) == 5
        assert isinstance(result[0], Sound)
        assert isinstance(result[1], Sound)
        assert isinstance(result[2], ProsodicBoundary)
        assert result[2].boundary_type == BoundaryType.SYLLABLE
        
        # Test multiple boundary types
        result = parse_prosodic_string("# p a σ t a #")
        assert isinstance(result[0], ProsodicBoundary)
        assert result[0].boundary_type == BoundaryType.WORD
        assert isinstance(result[-1], ProsodicBoundary)
        assert result[-1].boundary_type == BoundaryType.WORD


class TestParserIntegration(unittest.TestCase):
    """Test integration with the parser system."""
    
    def test_prosodic_boundary_tokens(self):
        """Test parsing of prosodic boundary tokens."""
        # Test syllable boundary
        token = parse_atom("σ")
        assert isinstance(token, ProsodicBoundaryToken)
        assert token.boundary.boundary_type == BoundaryType.SYLLABLE
        
        # Test foot boundary
        token = parse_atom("Ft")
        assert isinstance(token, ProsodicBoundaryToken)
        assert token.boundary.boundary_type == BoundaryType.FOOT
        
        # Test phrase boundary
        token = parse_atom("φ")
        assert isinstance(token, ProsodicBoundaryToken)
        assert token.boundary.boundary_type == BoundaryType.PHRASE
        
        # Test utterance boundary
        token = parse_atom("U")
        assert isinstance(token, ProsodicBoundaryToken)
        assert token.boundary.boundary_type == BoundaryType.UTTERANCE
    
    def test_segment_token_suprasegmental_features(self):
        """Test segment tokens with suprasegmental features."""
        # Create a segment token
        token = SegmentToken('a')
        
        # Test basic properties
        assert not token.has_suprasegmental_features()
        assert token.get_stress_level() == 0
        assert token.get_tone_value() == 0
        
        # Add suprasegmental features
        token.add_modifier('stress1,tone2')
        
        # Test after modification
        assert token.has_suprasegmental_features()
        assert token.get_stress_level() == 1
        assert token.get_tone_value() == 2


class TestFeatureIntegration(unittest.TestCase):
    """Test integration of all Phase 4 features."""
    
    def test_complex_feature_operations(self):
        """Test complex combinations of features."""
        # Start with a basic vowel
        vowel = Sound(grapheme='a')
        
        # Add multiple suprasegmental features
        complex_sound = vowel + 'stress1,tone2,f0_3,duration_2'
        
        assert complex_sound.has_stress()
        assert complex_sound.has_tone()
        assert complex_sound.get_stress_level() == 1
        assert complex_sound.get_tone_value() == 2
        assert 'f0_3' in complex_sound.fvalues
        assert 'duration_2' in complex_sound.fvalues
        
        # Test feature replacement
        modified = complex_sound + 'tone4'  # Should replace tone2
        assert 'tone4' in modified.fvalues
        assert 'tone2' not in modified.fvalues
        assert modified.get_tone_value() == 4
        
        # Test feature separation
        supraseg = complex_sound.get_suprasegmental_features()
        segmental = complex_sound.get_segmental_features()
        
        assert 'stress1' in supraseg
        assert 'tone2' in supraseg
        assert 'f0_3' in supraseg
        assert 'duration_2' in supraseg
        
        assert 'vowel' in segmental
        assert 'stress1' not in segmental
    
    def test_prosodic_rule_context(self):
        """Test prosodic contexts in phonological rules."""
        # This would test rules like: V > V[+stress] / # _ σ
        # (Vowels get stress at word-initial position before syllable boundary)
        
        # For now, just test that the tokens can be created
        boundary_token = parse_atom("#")
        syll_token = parse_atom("σ")
        vowel_token = parse_atom("V")
        
        assert str(boundary_token) == "#"
        assert str(syll_token) == "σ"
        assert str(vowel_token) == "V"


if __name__ == "__main__":
    unittest.main()