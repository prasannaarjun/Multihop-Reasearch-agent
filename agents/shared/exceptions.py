"""
Custom exceptions for the multi-hop research agent system.
"""


class AgentError(Exception):
    """Base exception for agent-related errors."""
    pass


class RetrievalError(AgentError):
    """Exception raised when document retrieval fails."""
    pass


class LLMError(AgentError):
    """Exception raised when LLM operations fail."""
    pass


class ConversationError(AgentError):
    """Exception raised when conversation operations fail."""
    pass


class ConfigurationError(AgentError):
    """Exception raised when configuration is invalid."""
    pass
