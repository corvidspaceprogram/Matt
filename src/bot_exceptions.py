"""
Custom exception classes for Mastodon LLM bot.

These exceptions help classify different types of errors for better
error handling and admin notification clarity.
"""


class MastodonBotError(Exception):
    """Base exception for Mastodon bot errors."""
    pass


class NetworkError(MastodonBotError):
    """Network-related errors (API calls, timeouts, connection issues)."""
    pass


class FileOperationError(MastodonBotError):
    """File operation errors (reading, writing, JSON parsing, file not found)."""
    pass


class ConfigurationError(MastodonBotError):
    """Configuration and environment variable errors."""
    pass


class APIResponseError(MastodonBotError):
    """Invalid API responses or data format errors."""
    pass


class LLMError(MastodonBotError):
    """LLM service specific errors."""
    pass