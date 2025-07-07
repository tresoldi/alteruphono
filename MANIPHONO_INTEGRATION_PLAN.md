# Comprehensive Plan: Maniphono Integration into Alteruphono

## Executive Summary

**Goal**: Remove maniphono as an external dependency by integrating only the essential components needed by alteruphono, creating a self-contained library ready for 1.0 release.

**Approach**: Implement a minimal but complete phonological system focused on alteruphono's specific needs, avoiding the complexity of the full maniphono framework.

## Phase 1: Architecture and Foundation (4-6 hours)

### 1.1 Create New Internal Module Structure
```
alteruphono/
├── phonology/           # New internal phonology module
│   ├── __init__.py     # Public API exports
│   ├── sound.py        # Sound class implementation
│   ├── segment.py      # Segment classes
│   ├── sequence.py     # SegSequence implementation
│   ├── parsing.py      # Parsing functions
│   └── models.py       # Minimal phonological models
```

### 1.2 Design Principles
- **Minimal Implementation**: Only implement features actually used by alteruphono
- **API Compatibility**: Maintain exact same interface as maniphono for seamless transition
- **Performance Focus**: Optimize for alteruphono's use patterns
- **No External Dependencies**: Completely self-contained

### 1.3 Data Model Design
```python
# Core data structures (simplified from maniphono)
class Sound:
    fvalues: frozenset[str]    # Feature values
    partial: bool              # Partial sound flag
    grapheme: str             # String representation

class SoundSegment:
    sounds: List[Sound]       # Usually single sound

class BoundarySegment:
    pass                      # Just a marker

class SegSequence:
    segments: List[Segment]   # Segment list
    boundaries: bool          # Auto-boundary management
```

## Phase 2: Core Sound System (8-10 hours)

### 2.1 Implement Sound Class (`alteruphono/phonology/sound.py`)
**Priority: HIGH** - Core to all operations

**Essential Methods**:
```python
class Sound:
    def __init__(self, grapheme=None, description=None, partial=False)
    def __add__(self, features: str) -> 'Sound'           # Feature addition
    def __ge__(self, other: 'Sound') -> bool              # Partial matching
    def __eq__(self, other) -> bool                       # Equality
    def __hash__(self) -> int                             # Hashing
    def __str__(self) -> str                              # String representation
    @property
    def partial(self) -> bool                             # Partial flag
```

**Key Features**:
- Store features as `frozenset[str]` for immutability and performance
- Implement feature arithmetic for back-reference modifiers
- Support partial sound matching for pattern matching
- Handle basic grapheme-to-feature mappings

### 2.2 Implement Segment Classes (`alteruphono/phonology/segment.py`)
**Priority: HIGH** - Used extensively

```python
class Segment:
    def add_fvalues(self, fvalues): pass  # Base interface

class SoundSegment(Segment):
    def __init__(self, sounds: Union[str, Sound, List[Sound]])
    def add_fvalues(self, fvalues)        # Modify features
    def __eq__(self, other) -> bool
    def __str__(self) -> str
    @property
    def sounds(self) -> List[Sound]

class BoundarySegment(Segment):
    def __str__(self) -> str: return "#"
```

### 2.3 Feature System Design
**Simplified Approach**:
- Use string-based feature values (e.g., "voiced", "bilabial")
- Hardcode essential phonological features needed by tests
- Support basic feature operations: addition, subtraction, matching
- No complex constraint checking or validation

## Phase 3: Sequence Management (4-6 hours)

### 3.1 Implement SegSequence (`alteruphono/phonology/sequence.py`)
**Priority: MEDIUM** - Used for input/output

```python
class SegSequence:
    def __init__(self, segments: List[Segment], boundaries=True)
    def __len__(self) -> int
    def __getitem__(self, index) -> Segment
    def __iter__(self) -> Iterator[Segment]
    def __str__(self) -> str
    def __eq__(self, other) -> bool
    def _update_boundaries(self)         # Internal boundary management
```

**Key Features**:
- Automatic boundary management when `boundaries=True`
- Support sequence protocol (len, getitem, iter)
- String representation with space-separated segments
- Equality comparison for testing

## Phase 4: Parsing Functions (6-8 hours)

### 4.1 Implement Parsing (`alteruphono/phonology/parsing.py`)
**Priority: HIGH** - Critical for input processing

```python
def parse_segment(segment_str: str) -> Segment:
    """Convert string to SoundSegment or BoundarySegment"""

def parse_sequence(sequence_str: str, boundaries=True) -> SegSequence:
    """Convert space-separated string to SegSequence"""
```

**Key Features**:
- Parse graphemes to Sound objects using lookup tables
- Handle boundaries (`#`) as BoundarySegment
- Support feature specifications in brackets (e.g., `p[voiced]`)
- Error handling for unknown graphemes

### 4.2 Minimal Phonological Model (`alteruphono/phonology/models.py`)
**Simplified Implementation**:
```python
# Basic grapheme-to-features mapping
GRAPHEME_FEATURES = {
    'p': frozenset(['consonant', 'bilabial', 'stop', 'voiceless']),
    'b': frozenset(['consonant', 'bilabial', 'stop', 'voiced']),
    't': frozenset(['consonant', 'alveolar', 'stop', 'voiceless']),
    'd': frozenset(['consonant', 'alveolar', 'stop', 'voiced']),
    'a': frozenset(['vowel', 'low', 'central']),
    'i': frozenset(['vowel', 'high', 'front']),
    # ... add more as needed
}

# Sound class mappings for common notation
CLASS_FEATURES = {
    'V': frozenset(['vowel']),
    'C': frozenset(['consonant']),
    'S': frozenset(['consonant', 'fricative']),
    'N': frozenset(['consonant', 'nasal']),
    # ... add more as needed
}
```

## Phase 5: Integration and Migration (6-8 hours)

### 5.1 Update Alteruphono Imports
**Replace all maniphono imports**:
```python
# OLD (maniphono)
from maniphono import Sound, SoundSegment, BoundarySegment, SegSequence
from maniphono import parse_segment, parse_sequence

# NEW (internal)
from alteruphono.phonology import Sound, SoundSegment, BoundarySegment, SegSequence
from alteruphono.phonology import parse_segment, parse_sequence
```

### 5.2 Update Requirements
- Remove `maniphono>=0.3rc0` from `requirements.txt`
- Update `setup.py` to remove maniphono dependency
- Update version to indicate independence

### 5.3 API Compatibility Layer
Create compatibility layer in `alteruphono/phonology/__init__.py`:
```python
# Maintain exact same API as maniphono for seamless transition
from .sound import Sound
from .segment import Segment, SoundSegment, BoundarySegment
from .sequence import SegSequence
from .parsing import parse_segment, parse_sequence

__all__ = [
    'Sound', 'Segment', 'SoundSegment', 'BoundarySegment',
    'SegSequence', 'parse_segment', 'parse_sequence'
]
```

## Phase 6: Testing and Validation (4-6 hours)

### 6.1 Comprehensive Testing Strategy
- **Unit Tests**: Test each component in isolation
- **Integration Tests**: Verify alteruphono functionality unchanged
- **Regression Tests**: Ensure all 140 existing tests still pass
- **Performance Tests**: Verify no performance degradation

### 6.2 Validation Checklist
- [ ] All existing tests pass without modification
- [ ] No maniphono imports remain in codebase
- [ ] Performance equal or better than before
- [ ] Memory usage optimized
- [ ] Error handling robust

## Phase 7: Documentation and Cleanup (2-4 hours)

### 7.1 Update Documentation
- Update README to reflect independence from maniphono
- Document new internal phonology module
- Add migration notes for any API changes

### 7.2 Code Cleanup
- Remove any unused maniphono compatibility code
- Optimize implementation based on testing results
- Add proper docstrings to all new classes

## Implementation Priority and Timeline

### Week 1: Foundation (10-12 hours)
- Phase 1: Architecture and Foundation
- Phase 2: Core Sound System (partial)

### Week 2: Core Implementation (12-14 hours)
- Phase 2: Core Sound System (complete)
- Phase 3: Sequence Management
- Phase 4: Parsing Functions (partial)

### Week 3: Integration (10-12 hours)
- Phase 4: Parsing Functions (complete)
- Phase 5: Integration and Migration
- Phase 6: Testing and Validation (partial)

### Week 4: Finalization (6-8 hours)
- Phase 6: Testing and Validation (complete)
- Phase 7: Documentation and Cleanup

**Total Estimated Effort**: 38-46 hours (4-6 weeks part-time)

## Risk Mitigation

### High-Risk Areas
1. **Feature System Complexity**: Mitigate by implementing minimal viable features first
2. **Partial Sound Matching**: Focus on exact alteruphono usage patterns
3. **Performance Degradation**: Optimize for alteruphono's specific use cases
4. **Test Failures**: Maintain strict API compatibility

### Fallback Plan
- Keep maniphono as optional dependency during transition
- Implement feature flags to switch between implementations
- Gradual migration with comprehensive testing at each step

## Success Metrics

1. **Zero External Dependencies**: No maniphono in requirements.txt
2. **100% Test Compatibility**: All 140 tests pass unchanged
3. **Performance Maintained**: Equal or better performance vs maniphono
4. **API Stability**: No breaking changes to alteruphono public API
5. **Code Quality**: Clean, well-documented internal implementation

This plan provides a systematic approach to achieving independence from maniphono while maintaining all functionality needed for alteruphono's 1.0 release and academic publication readiness.

## Detailed Component Analysis

### Sound Class Requirements

Based on alteruphono usage analysis, the Sound class needs:

1. **Feature Value Storage**: `frozenset[str]` for immutable feature sets
2. **Grapheme Representation**: String representation of the sound
3. **Partial Sound Flag**: Boolean indicating if sound is partial/underspecified
4. **Arithmetic Operations**:
   - `__add__(features)`: Add feature values (used in model.py:182)
   - `__ge__(other)`: Partial matching (used in common.py:74)
5. **Standard Operations**: `__eq__`, `__hash__`, `__str__`

### Segment Class Requirements

1. **SoundSegment**:
   - Contains list of Sound objects (usually one)
   - `add_fvalues()` method for feature modification
   - Equality with Sound and Segment objects
   - String representation for display

2. **BoundarySegment**:
   - Simple marker for word boundaries
   - `__str__()` returns "#"
   - No additional data or methods needed

### SegSequence Requirements

1. **Sequence Protocol**: `__len__`, `__getitem__`, `__iter__`
2. **Boundary Management**: Automatic addition/removal of boundary segments
3. **String Representation**: Space-separated segment strings
4. **Equality and Hashing**: For use in tests and comparisons

### Parsing Requirements

1. **parse_segment()**:
   - Convert string graphemes to SoundSegment objects
   - Handle "#" as BoundarySegment
   - Support feature specifications like "p[voiced]"

2. **parse_sequence()**:
   - Split space-separated strings into segments
   - Create SegSequence with optional boundaries
   - Handle empty strings and edge cases

### Minimal Feature Set

The implementation needs to support these phonological features based on test usage:

**Basic Features**:
- Place of articulation: bilabial, alveolar, velar, etc.
- Manner of articulation: stop, fricative, nasal, etc.
- Voicing: voiced, voiceless
- Vowel features: high, low, front, back, central
- Sound classes: consonant, vowel

**Operations**:
- Feature addition (p + voiced = b)
- Feature subtraction (b - voiced = p)
- Partial matching (V matches any vowel)
- Feature bundling ([consonant, voiced] matches all voiced consonants)

This minimal set covers all the linguistic phenomena tested in the comprehensive test suite while avoiding the complexity of a full phonological framework.