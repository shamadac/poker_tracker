"""
Custom exceptions for the hand parsing system.
"""


class HandParsingError(Exception):
    """Exception raised when hand parsing fails."""
    pass


class UnsupportedPlatformError(HandParsingError):
    """Exception raised when platform is not supported."""
    pass


class ValidationError(HandParsingError):
    """Exception raised when hand validation fails."""
    pass


class DuplicateHandError(HandParsingError):
    """Exception raised when duplicate hands are detected."""
    pass


class FileMonitoringError(Exception):
    """Exception raised when file monitoring operations fail."""
    pass


class NotFoundError(Exception):
    """Exception raised when a requested resource is not found."""
    pass