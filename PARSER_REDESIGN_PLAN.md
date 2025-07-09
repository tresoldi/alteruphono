# Alteruphono Parser Redesign Plan

## Overview

This document outlines a comprehensive plan to replace the current regex-based parser with a robust, extensible recursive descent parser that can handle complex phonological notation and future extensions like suprasegmentals and numeric features.

## Current State Analysis

### Current Parser Limitations

1. **Regex-based approach** - brittle and hard to extend
2. **Simple whitespace tokenization** - can't handle complex multi-character symbols
3. **No formal grammar** - makes extensions difficult
4. **Poor error handling** - minimal context in error messages
5. **Fixed syntax** - hard to add new constructs
6. **No validation** - doesn't check phonological constraints
7. **No extensibility** for:
   - Suprasegmental features (tone, stress, length)
   - Numeric features (F0, duration, formants)
   - Hierarchical feature structures
   - Prosodic units (syllables, feet, words)
   - Autosegmental notation

### Current Syntax Support

```
Rules:       p > b                    (simple substitution)
             p > b / a _ a            (with context)
             S[voiceless] > @1[fricative]  (feature modification)
             
Atoms:       p                       (segment)
             V, C, S                 (sound classes)
             p|t                     (choice)
             {a|e|i}                 (set)
             #                       (boundary)
             _                       (focus)
             :null:                  (deletion/insertion)
             @1, @2[voiced]          (backreferences)
             
Features:    [voiced]                (single feature)
             [voiced,bilabial]       (multiple features)
             [+voiced]               (explicit positive)
             [-voiced]               (explicit negative)
```

## Design Goals

### Primary Goals

1. **Zero Dependencies** - Pure Python implementation
2. **Backward Compatibility** - All current syntax must continue working
3. **Extensibility** - Easy to add new features and constructs
4. **Performance** - Fast parsing for typical academic use cases
5. **Error Handling** - Precise, linguistically meaningful error messages
6. **Maintainability** - Clear, readable code structure

### Future Extension Goals

1. **Suprasegmental Features**
   - Tone: `V[tone=H]`, `V[tone=rising]`
   - Stress: `V[stress=primary]`, `σ[stress=+]`
   - Length: `V[length=long]`, `C[duration=0.15s]`

2. **Numeric Features**
   - F0: `V[F0=120Hz]`, `V[F0>150]`
   - Formants: `V[F1=500,F2=1200]`
   - Duration: `C[dur=50ms]`

3. **Hierarchical Features**
   - Nested: `[place=[labial=[round=+]]]`
   - Feature geometry: `[dorsal=[high=+,back=-]]`

4. **Prosodic Units**
   - Mora: `μ`, syllable: `σ`, foot: `Ft`, word: `ω`
   - Complex contexts: `/ σ[stress=+] C₀ _ C₀ σ[stress=-]`

5. **Advanced Constructs**
   - Variable length: `C₀₋₃` (0-3 consonants)
   - Named rules: `@spirantize`, `@lenition`
   - Conditional rules: `if tone=H then ...`
   - Iterative rules: `repeat until stable`

## Architecture Design

### Overall Architecture

```
Input String
     ↓
┌─────────────┐
│   Lexer     │  → Tokenizes input into meaningful symbols
└─────────────┘
     ↓
┌─────────────┐
│   Parser    │  → Parses tokens into Abstract Syntax Tree
└─────────────┘
     ↓
┌─────────────┐
│  Validator  │  → Validates phonological constraints
└─────────────┘
     ↓
┌─────────────┐
│ AST → Model │  → Converts to current Token-based model
└─────────────┘
```

### Component Design

#### 1. Lexer (Tokenizer)

**Responsibility**: Convert input string into a stream of tokens

**Token Types**:
```python
@dataclass
class Token:
    type: TokenType
    value: str
    position: int
    line: int
    column: int

class TokenType(Enum):
    # Basic symbols
    GRAPHEME = "grapheme"           # p, a, ɸ, etc.
    SOUND_CLASS = "sound_class"     # V, C, S, N, etc.
    
    # Operators
    ARROW = "arrow"                 # >
    PIPE = "pipe"                   # |
    FOCUS = "focus"                 # _
    BOUNDARY = "boundary"           # #
    
    # Brackets and delimiters
    LBRACKET = "lbracket"          # [
    RBRACKET = "rbracket"          # ]
    LPAREN = "lparen"              # (
    RPAREN = "rparen"              # )
    LBRACE = "lbrace"              # {
    RBRACE = "rbrace"              # }
    
    # Context
    SLASH = "slash"                # /
    
    # Features
    FEATURE = "feature"            # voiced, bilabial
    PLUS = "plus"                  # +
    MINUS = "minus"                # -
    EQUALS = "equals"              # =
    
    # Numbers and units
    NUMBER = "number"              # 120, 0.15
    UNIT = "unit"                  # Hz, ms, s
    
    # Special
    BACKREF = "backref"            # @1, @2
    NULL = "null"                  # :null:
    COMMA = "comma"                # ,
    COLON = "colon"                # :
    
    # Prosodic
    MORA = "mora"                  # μ
    SYLLABLE = "syllable"          # σ
    FOOT = "foot"                  # Ft
    WORD = "word"                  # ω
    PHRASE = "phrase"              # φ
    
    # Control
    EOF = "eof"
    NEWLINE = "newline"
    WHITESPACE = "whitespace"
```

**Features**:
- **Unicode-aware**: Handles IPA symbols, tone marks, etc.
- **Position tracking**: Tracks line/column for error reporting
- **Lookahead**: Can peek at next tokens
- **Error recovery**: Can skip invalid characters and continue

#### 2. Parser (Syntax Analyzer)

**Responsibility**: Parse token stream into Abstract Syntax Tree

**Grammar** (in EBNF-like notation):
```ebnf
rule ::= ante ARROW post (SLASH context)?

ante ::= atom_sequence
post ::= atom_sequence
context ::= atom_sequence

atom_sequence ::= atom+

atom ::= segment
       | sound_class  
       | choice
       | set
       | backref
       | boundary
       | focus
       | null
       | prosodic_unit

segment ::= GRAPHEME feature_spec?
sound_class ::= SOUND_CLASS feature_spec?
choice ::= atom (PIPE atom)+
set ::= LBRACE atom (PIPE atom)+ RBRACE
backref ::= BACKREF feature_spec?
boundary ::= BOUNDARY
focus ::= FOCUS
null ::= NULL
prosodic_unit ::= (MORA | SYLLABLE | FOOT | WORD | PHRASE) feature_spec?

feature_spec ::= LBRACKET feature_list RBRACKET
feature_list ::= feature (COMMA feature)*
feature ::= feature_name
          | PLUS feature_name
          | MINUS feature_name  
          | feature_name EQUALS feature_value

feature_name ::= FEATURE
feature_value ::= FEATURE | NUMBER | NUMBER UNIT | GRAPHEME

# Future extensions
variable_length ::= atom SUBSCRIPT number (MINUS number)?
conditional ::= IF condition THEN atom (ELSE atom)?
iteration ::= REPEAT atom UNTIL condition
```

**AST Node Types**:
```python
@dataclass
class ASTNode:
    position: int

@dataclass
class RuleNode(ASTNode):
    ante: AtomSequenceNode
    post: AtomSequenceNode
    context: Optional[ContextNode] = None

@dataclass
class AtomSequenceNode(ASTNode):
    atoms: List[AtomNode]

@dataclass
class SegmentNode(ASTNode):
    grapheme: str
    features: Optional[FeatureSpecNode] = None

@dataclass
class SoundClassNode(ASTNode):
    class_name: str
    features: Optional[FeatureSpecNode] = None

@dataclass
class ChoiceNode(ASTNode):
    alternatives: List[AtomNode]

@dataclass
class SetNode(ASTNode):
    alternatives: List[AtomNode]

@dataclass
class BackRefNode(ASTNode):
    index: int
    features: Optional[FeatureSpecNode] = None

@dataclass
class FeatureSpecNode(ASTNode):
    features: List[FeatureNode]

@dataclass
class FeatureNode(ASTNode):
    name: str
    polarity: Optional[str] = None  # '+', '-', or None
    value: Optional[FeatureValueNode] = None

@dataclass
class FeatureValueNode(ASTNode):
    value: str
    unit: Optional[str] = None

# Future extensions
@dataclass
class ProsodicUnitNode(ASTNode):
    unit_type: str  # 'mora', 'syllable', etc.
    features: Optional[FeatureSpecNode] = None

@dataclass
class VariableLengthNode(ASTNode):
    atom: AtomNode
    min_length: int
    max_length: Optional[int] = None
```

#### 3. Validator (Semantic Analyzer)

**Responsibility**: Validate phonological and semantic constraints

**Validation Rules**:
1. **Feature Compatibility**: Check that features can coexist
2. **Backreference Validity**: Ensure backreferences point to valid positions
3. **Context Well-formedness**: Ensure contexts have proper focus
4. **Sound Class Consistency**: Verify sound classes are used correctly
5. **Numeric Range Validation**: Check that numeric values are reasonable
6. **Prosodic Hierarchy**: Validate prosodic unit relationships

**Example Validations**:
```python
class PhonologicalValidator:
    def validate_feature_compatibility(self, features: List[FeatureNode]) -> List[ValidationError]:
        """Check for contradictory features like [+voiced, -voiced]"""
        
    def validate_backreferences(self, rule: RuleNode) -> List[ValidationError]:
        """Ensure @1, @2, etc. refer to valid positions"""
        
    def validate_numeric_features(self, feature: FeatureNode) -> List[ValidationError]:
        """Check F0, duration, etc. are in reasonable ranges"""
        
    def validate_prosodic_hierarchy(self, units: List[ProsodicUnitNode]) -> List[ValidationError]:
        """Ensure proper prosodic containment (mora ⊆ syllable ⊆ foot ⊆ word)"""
```

#### 4. AST-to-Model Converter

**Responsibility**: Convert AST to current Token-based model for backward compatibility

**Conversion Strategy**:
- Map AST nodes to existing Token classes
- Preserve all current functionality
- Handle new features gracefully (for future)

### Error Handling Strategy

#### Error Types

1. **Lexical Errors**: Invalid characters, malformed tokens
2. **Syntax Errors**: Invalid grammar, unexpected tokens
3. **Semantic Errors**: Invalid feature combinations, bad backreferences
4. **Phonological Errors**: Linguistically invalid constructs

#### Error Reporting

```python
@dataclass
class ParseError:
    type: ErrorType
    message: str
    position: int
    line: int
    column: int
    suggestions: List[str] = field(default_factory=list)

class ErrorType(Enum):
    LEXICAL = "lexical"
    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    PHONOLOGICAL = "phonological"
```

**Error Message Examples**:
```
Lexical Error at line 1, column 5:
  p > [voiced > b
      ^
  Expected ']' to close feature specification

Phonological Error at line 1, column 8:
  p[+voiced,-voiced] > b
    ^
  Contradictory voicing features: cannot be both +voiced and -voiced
  Suggestion: Use either [+voiced] or [-voiced]

Semantic Error at line 1, column 12:
  p > @3 / a _ a
          ^
  Backreference @3 is invalid: only 2 segments available (@1, @2)
```

#### Error Recovery

- **Skip-and-continue**: Skip invalid tokens and attempt to continue parsing
- **Synchronization points**: Reset parsing at major boundaries (rules, contexts)
- **Multiple errors**: Report multiple errors in one pass when possible

## Implementation Plan

### Phase 1: Foundation (Week 1-2)

1. **Design Token Types**
   - Define comprehensive TokenType enum
   - Implement Token dataclass with position tracking
   - Create lexer test cases for all current syntax

2. **Implement Basic Lexer**
   - Character-by-character tokenization
   - Unicode IPA symbol recognition
   - Position tracking (line/column)
   - Basic error handling

3. **Test Lexer**
   - Test with all current rule examples
   - Test with malformed input
   - Verify position tracking accuracy

### Phase 2: Core Parser (Week 3-4)

1. **Define AST Node Hierarchy**
   - Implement all node types for current syntax
   - Add position information to all nodes
   - Create visitor pattern for AST traversal

2. **Implement Recursive Descent Parser**
   - Rule parsing (ante > post / context)
   - Atom parsing (segments, classes, choices, etc.)
   - Feature specification parsing
   - Backref parsing with modifiers

3. **Test Parser**
   - Test with comprehensive rule set
   - Verify AST structure correctness
   - Test error cases and recovery

### Phase 3: Validation & Integration (Week 5-6)

1. **Implement Core Validator**
   - Feature compatibility checking
   - Backreference validation
   - Context well-formedness

2. **Create AST-to-Model Converter**
   - Map AST nodes to current Token classes
   - Ensure 100% backward compatibility
   - Preserve all existing behavior

3. **Integration Testing**
   - Test with entire test suite
   - Performance testing
   - Regression testing

### Phase 4: Advanced Features (Week 7-8)

1. **Extend for Future Features**
   - Add prosodic unit tokens and nodes
   - Implement numeric feature parsing
   - Add hierarchical feature support

2. **Enhanced Error Handling**
   - Improve error messages
   - Add suggestions and corrections
   - Implement error recovery strategies

3. **Documentation and Examples**
   - Document new syntax capabilities
   - Create migration guide
   - Add comprehensive examples

### Phase 5: Optimization & Polish (Week 9-10)

1. **Performance Optimization**
   - Profile parsing performance
   - Optimize hot paths
   - Add parsing benchmarks

2. **Code Quality**
   - Comprehensive test coverage
   - Code review and refactoring
   - Documentation completion

## File Structure

```
alteruphono/
├── parsing/
│   ├── __init__.py
│   ├── lexer.py           # Tokenizer implementation
│   ├── parser.py          # Recursive descent parser  
│   ├── ast_nodes.py       # AST node definitions
│   ├── validator.py       # Semantic validation
│   ├── converter.py       # AST → Token model conversion
│   ├── errors.py          # Error types and handling
│   └── grammar.py         # Grammar documentation and utilities
├── tests/
│   ├── test_lexer.py
│   ├── test_parser.py
│   ├── test_validator.py
│   ├── test_converter.py
│   └── test_integration.py
└── examples/
    ├── basic_rules.py
    ├── advanced_features.py
    └── migration_guide.py
```

## Backward Compatibility Strategy

### Current API Preservation

1. **Rule Class**: Keep existing interface unchanged
2. **parse_rule Function**: Maintain current signature and behavior
3. **Token Classes**: Keep all existing token types and methods
4. **Error Behavior**: Preserve existing error types and messages (where reasonable)

### Migration Path

1. **Phase 1**: New parser available alongside old parser
2. **Phase 2**: New parser becomes default with fallback
3. **Phase 3**: Old parser deprecated but available
4. **Phase 4**: Old parser removed (major version bump)

### Testing Strategy

1. **Comprehensive Regression Tests**: All existing tests must pass
2. **Performance Benchmarks**: New parser must not be significantly slower
3. **Error Message Compatibility**: Important error cases should have similar messages
4. **Rule Parsing Equivalence**: AST → Token conversion must produce identical results

## Future Extension Examples

Once the new parser is implemented, adding new features becomes straightforward:

### Example 1: Tone Features
```python
# Add to lexer
class TokenType(Enum):
    TONE_H = "tone_h"      # H
    TONE_L = "tone_l"      # L
    TONE_M = "tone_m"      # M

# Add to parser grammar
tone_feature ::= TONE_H | TONE_L | TONE_M

# Usage in rules
"a[tone=H] > a[tone=L] / _ L"  # High tone becomes low before low tone
```

### Example 2: Syllable Structure
```python
# Add prosodic units
"CV > V / σ[stress=-] _"       # Delete C in unstressed syllables
"V[+high] > V[-high] / _ C] σ" # Lower vowels at syllable end
```

### Example 3: Numeric Features
```python
"V[F0>200] > V[F0=150] / _ #"  # Lower F0 phrase-finally
"C[dur<50ms] > :null:"         # Delete very short consonants
```

## Risk Assessment

### Technical Risks

1. **Performance Regression**: New parser might be slower
   - **Mitigation**: Extensive benchmarking and optimization
   
2. **Backward Compatibility**: Breaking changes to existing API
   - **Mitigation**: Comprehensive test suite and gradual migration
   
3. **Complexity**: Over-engineering for current needs
   - **Mitigation**: Implement incrementally, test thoroughly

### Implementation Risks

1. **Time Overrun**: Complex implementation taking longer than expected
   - **Mitigation**: Phased approach with working intermediate versions
   
2. **Testing Coverage**: Missing edge cases in new parser
   - **Mitigation**: Reuse existing comprehensive test suite
   
3. **User Adoption**: Resistance to syntax changes
   - **Mitigation**: Maintain full backward compatibility

## Success Metrics

1. **Functionality**: 100% backward compatibility with existing rules
2. **Performance**: Parsing time within 150% of current parser
3. **Extensibility**: New features can be added with <50 lines of code
4. **Error Quality**: Error messages are more helpful than current parser
5. **Test Coverage**: >95% code coverage for new parser components
6. **Documentation**: Complete API documentation and migration guide

## Conclusion

This redesign will provide alteruphono with a robust, extensible parser that can handle current needs while enabling future expansion into advanced phonological notation. The recursive descent approach offers the best balance of simplicity, performance, and extensibility for our use case, while maintaining zero dependencies and full backward compatibility.

The phased implementation approach ensures we can deliver value incrementally while minimizing risk to the existing stable codebase. The new architecture will position alteruphono as a leading tool for computational phonology research.