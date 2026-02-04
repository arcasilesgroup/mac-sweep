"""Exception hierarchy for mac-sweep."""


class SweepError(Exception):
    """Base exception for all mac-sweep errors."""


class SafetyError(SweepError):
    """Base for safety-related errors."""


class ProtectedAppError(SafetyError):
    """Raised when attempting to remove a protected Apple system app."""


class DependencyError(SafetyError):
    """Raised when attempting to remove a brew dependency."""


class RunningProcessError(SafetyError):
    """Raised when attempting to remove a currently running process."""


class ProtectedPathError(SafetyError):
    """Raised when attempting to delete a protected filesystem path."""


class RemovalError(SweepError):
    """Raised when a removal operation fails."""


class ValidationError(SweepError):
    """Raised when input validation fails."""


class ConfigError(SweepError):
    """Raised for configuration-related errors."""


class LLMError(SweepError):
    """Raised for LLM API errors."""


class AuditError(SweepError):
    """Raised for audit processing errors."""
