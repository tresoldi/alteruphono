"""
Comprehensive exception hierarchy for AlteruPhono.

This module defines a consistent exception hierarchy used throughout the
AlteruPhono library to provide clear, informative error messages and
enable proper error handling and recovery.
"""

from typing import Optional, List, Any, Dict
import traceback


class AlteruPhonoError(Exception):
    """
    Base exception for all AlteruPhono-specific errors.

    This is the root of the exception hierarchy and should be caught
    when you want to handle any AlteruPhono-related error.
    """

    def __init__(
        self,
        message: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        error_code: Optional[str] = None,
    ):
        """
        Initialize base AlteruPhono error.

        Args:
            message: Primary error message
            context: Additional context information (rule, position, etc.)
            suggestions: List of suggested fixes or alternatives
            error_code: Unique error code for documentation/debugging
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.suggestions = suggestions or []
        self.error_code = error_code

    def __str__(self) -> str:
        """Format error message with context and suggestions."""
        parts = [self.message]

        # Add context information
        if self.context:
            context_parts = []
            for key, value in self.context.items():
                context_parts.append(f"{key}: {value}")
            if context_parts:
                parts.append(f"Context: {', '.join(context_parts)}")

        # Add suggestions
        if self.suggestions:
            parts.append("Suggestions:")
            for i, suggestion in enumerate(self.suggestions, 1):
                parts.append(f"  {i}. {suggestion}")

        # Add error code if available
        if self.error_code:
            parts.append(f"Error code: {self.error_code}")

        return "\n".join(parts)


# =============================================================================
# Parsing and Rule-Related Errors
# =============================================================================


class ParseError(AlteruPhonoError):
    """Base class for all parsing-related errors."""

    def __init__(
        self,
        message: str,
        *,
        rule: Optional[str] = None,
        position: Optional[int] = None,
        line: Optional[int] = None,
        column: Optional[int] = None,
        **kwargs,
    ):
        context = kwargs.get("context", {})
        if rule is not None:
            context["rule"] = rule
        if position is not None:
            context["position"] = position
        if line is not None:
            context["line"] = line
        if column is not None:
            context["column"] = column

        super().__init__(message, context=context, **kwargs)


class RuleSyntaxError(ParseError):
    """Error in sound change rule syntax."""

    def __init__(
        self, message: str, rule: str, position: Optional[int] = None, **kwargs
    ):
        suggestions = kwargs.pop("suggestions", [])
        suggestions.extend(
            [
                "Check rule syntax: 'source > target / left_context _ right_context'",
                "Ensure proper spacing around operators (>, /, _)",
                "Verify all brackets and quotes are properly closed",
            ]
        )

        super().__init__(
            message,
            rule=rule,
            position=position,
            suggestions=suggestions,
            error_code="E001",
            **kwargs,
        )


class InvalidRuleError(ParseError):
    """Error in rule semantics or phonological validity."""

    def __init__(self, message: str, rule: str, **kwargs):
        super().__init__(message, rule=rule, error_code="E002", **kwargs)


class SequenceParseError(ParseError):
    """Error parsing sound sequences."""

    def __init__(
        self, message: str, sequence: str, position: Optional[int] = None, **kwargs
    ):
        context = kwargs.get("context", {})
        context["sequence"] = sequence

        super().__init__(
            message, position=position, context=context, error_code="E003", **kwargs
        )


# =============================================================================
# Feature System Errors
# =============================================================================


class FeatureSystemError(AlteruPhonoError):
    """Base class for feature system-related errors."""

    def __init__(self, message: str, feature_system: Optional[str] = None, **kwargs):
        context = kwargs.get("context", {})
        if feature_system:
            context["feature_system"] = feature_system

        super().__init__(message, context=context, **kwargs)


class InvalidFeatureError(FeatureSystemError):
    """Error with feature names or values."""

    def __init__(
        self,
        message: str,
        feature_name: Optional[str] = None,
        feature_value: Optional[Any] = None,
        valid_features: Optional[List[str]] = None,
        **kwargs,
    ):
        context = kwargs.get("context", {})
        if feature_name:
            context["feature_name"] = feature_name
        if feature_value is not None:
            context["feature_value"] = feature_value

        suggestions = kwargs.pop("suggestions", [])
        if valid_features:
            suggestions.append(f"Valid features: {', '.join(valid_features[:5])}")
            if len(valid_features) > 5:
                suggestions.append(f"... and {len(valid_features) - 5} more")

        super().__init__(
            message,
            suggestions=suggestions,
            context=context,
            error_code="E101",
            **kwargs,
        )


class FeatureValueError(FeatureSystemError):
    """Error with feature values (out of range, incompatible type, etc.)."""

    def __init__(
        self,
        message: str,
        feature_name: str,
        provided_value: Any,
        expected_range: Optional[str] = None,
        **kwargs,
    ):
        context = kwargs.get("context", {})
        context.update({"feature_name": feature_name, "provided_value": provided_value})

        suggestions = kwargs.pop("suggestions", [])
        if expected_range:
            suggestions.append(f"Expected value range: {expected_range}")

        super().__init__(
            message,
            suggestions=suggestions,
            context=context,
            error_code="E102",
            **kwargs,
        )


class FeatureConflictError(FeatureSystemError):
    """Error with conflicting or impossible feature combinations."""

    def __init__(self, message: str, conflicting_features: Dict[str, Any], **kwargs):
        context = kwargs.get("context", {})
        context["conflicting_features"] = conflicting_features

        suggestions = kwargs.pop("suggestions", [])
        suggestions.append(
            "Check phonological constraints for valid feature combinations"
        )

        super().__init__(
            message,
            suggestions=suggestions,
            context=context,
            error_code="E103",
            **kwargs,
        )


# =============================================================================
# Sound and Phonology Errors
# =============================================================================


class SoundError(AlteruPhonoError):
    """Base class for sound-related errors."""

    pass


class InvalidSoundError(SoundError):
    """Error with sound creation or manipulation."""

    def __init__(
        self,
        message: str,
        grapheme: Optional[str] = None,
        feature_system: Optional[str] = None,
        **kwargs,
    ):
        context = kwargs.get("context", {})
        if grapheme:
            context["grapheme"] = grapheme
        if feature_system:
            context["feature_system"] = feature_system

        super().__init__(message, context=context, error_code="E201", **kwargs)


class SoundConversionError(SoundError):
    """Error converting sounds between feature systems."""

    def __init__(
        self,
        message: str,
        source_system: str,
        target_system: str,
        grapheme: Optional[str] = None,
        **kwargs,
    ):
        context = kwargs.get("context", {})
        context.update({"source_system": source_system, "target_system": target_system})
        if grapheme:
            context["grapheme"] = grapheme

        super().__init__(message, context=context, error_code="E202", **kwargs)


# =============================================================================
# Sound Change and Rule Application Errors
# =============================================================================


class SoundChangeError(AlteruPhonoError):
    """Base class for sound change application errors."""

    pass


class RuleApplicationError(SoundChangeError):
    """Error applying sound change rules."""

    def __init__(
        self,
        message: str,
        rule_name: Optional[str] = None,
        sequence: Optional[List[str]] = None,
        position: Optional[int] = None,
        **kwargs,
    ):
        context = kwargs.get("context", {})
        if rule_name:
            context["rule_name"] = rule_name
        if sequence:
            context["sequence"] = " ".join(sequence)
        if position is not None:
            context["position"] = position

        super().__init__(message, context=context, error_code="E301", **kwargs)


class EnvironmentMatchError(SoundChangeError):
    """Error with phonological environment matching."""

    def __init__(
        self,
        message: str,
        environment: Optional[str] = None,
        target_sound: Optional[str] = None,
        **kwargs,
    ):
        context = kwargs.get("context", {})
        if environment:
            context["environment"] = environment
        if target_sound:
            context["target_sound"] = target_sound

        super().__init__(message, context=context, error_code="E302", **kwargs)


# =============================================================================
# System and Configuration Errors
# =============================================================================


class ConfigurationError(AlteruPhonoError):
    """Error with system configuration or setup."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="E401", **kwargs)


class ResourceError(AlteruPhonoError):
    """Error loading or accessing required resources."""

    def __init__(
        self,
        message: str,
        resource_name: Optional[str] = None,
        resource_path: Optional[str] = None,
        **kwargs,
    ):
        context = kwargs.get("context", {})
        if resource_name:
            context["resource_name"] = resource_name
        if resource_path:
            context["resource_path"] = resource_path

        super().__init__(message, context=context, error_code="E402", **kwargs)


# =============================================================================
# Validation and Input Errors
# =============================================================================


class ValidationError(AlteruPhonoError):
    """Error in input validation."""

    def __init__(
        self,
        message: str,
        parameter_name: Optional[str] = None,
        provided_value: Optional[Any] = None,
        expected_type: Optional[str] = None,
        **kwargs,
    ):
        context = kwargs.get("context", {})
        if parameter_name:
            context["parameter"] = parameter_name
        if provided_value is not None:
            context["provided_value"] = provided_value
        if expected_type:
            context["expected_type"] = expected_type

        super().__init__(message, context=context, error_code="E501", **kwargs)


class IncompatibilityError(AlteruPhonoError):
    """Error with incompatible operations or data."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="E502", **kwargs)


# =============================================================================
# Utility Functions
# =============================================================================


def format_context_suggestion(
    context_type: str, context_value: str, position: Optional[int] = None
) -> str:
    """Format context information for error messages."""
    if position is not None:
        return f"In {context_type} '{context_value}' at position {position}"
    return f"In {context_type} '{context_value}'"


def suggest_similar_features(
    invalid_feature: str, valid_features: List[str], max_suggestions: int = 3
) -> List[str]:
    """
    Suggest similar feature names for typos.

    Uses simple string distance to find likely intended features.
    """

    def levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate edit distance between two strings."""
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    # Calculate distances and sort
    distances = [
        (feature, levenshtein_distance(invalid_feature.lower(), feature.lower()))
        for feature in valid_features
    ]
    distances.sort(key=lambda x: x[1])

    # Return the closest matches
    suggestions = []
    for feature, distance in distances[:max_suggestions]:
        if distance <= max(2, len(invalid_feature) // 3):  # Reasonable threshold
            suggestions.append(f"Did you mean '{feature}'?")

    return suggestions


def create_error_summary(errors: List[AlteruPhonoError]) -> str:
    """Create a summary of multiple errors."""
    if not errors:
        return "No errors"

    if len(errors) == 1:
        return str(errors[0])

    summary = [f"Multiple errors occurred ({len(errors)} total):"]
    for i, error in enumerate(errors, 1):
        summary.append(f"\n{i}. {type(error).__name__}: {error.message}")
        if error.context:
            context_items = [f"{k}={v}" for k, v in error.context.items()]
            summary.append(f"   Context: {', '.join(context_items)}")

    return "".join(summary)


# =============================================================================
# Error Handler Context Manager
# =============================================================================


class ErrorContext:
    """
    Context manager for collecting and handling multiple errors.

    Useful for validation routines that need to collect all errors
    before reporting them.
    """

    def __init__(self, raise_on_exit: bool = True):
        """
        Initialize error context.

        Args:
            raise_on_exit: Whether to raise collected errors when exiting context
        """
        self.errors: List[AlteruPhonoError] = []
        self.raise_on_exit = raise_on_exit

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.raise_on_exit and self.errors:
            if len(self.errors) == 1:
                raise self.errors[0]
            else:
                # Create summary error for multiple issues
                summary = create_error_summary(self.errors)
                raise AlteruPhonoError(
                    summary,
                    context={"error_count": len(self.errors)},
                    error_code="E999",
                )
        return False  # Don't suppress exceptions

    def add_error(self, error: AlteruPhonoError):
        """Add an error to the collection."""
        self.errors.append(error)

    def add_validation_error(
        self,
        message: str,
        parameter_name: Optional[str] = None,
        provided_value: Optional[Any] = None,
        **kwargs,
    ):
        """Convenience method to add validation errors."""
        error = ValidationError(
            message,
            parameter_name=parameter_name,
            provided_value=provided_value,
            **kwargs,
        )
        self.add_error(error)

    def has_errors(self) -> bool:
        """Check if any errors have been collected."""
        return len(self.errors) > 0

    def clear(self):
        """Clear all collected errors."""
        self.errors.clear()
