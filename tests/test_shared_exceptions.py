"""
Tests for shared exceptions.
"""

import pytest
from agents.shared.exceptions import (
    AgentError, RetrievalError, LLMError, ConversationError, ConfigurationError
)


class TestExceptions:
    """Test custom exceptions."""
    
    def test_agent_error(self):
        """Test AgentError exception."""
        error = AgentError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_retrieval_error(self):
        """Test RetrievalError exception."""
        error = RetrievalError("Retrieval failed")
        assert str(error) == "Retrieval failed"
        assert isinstance(error, AgentError)
    
    def test_llm_error(self):
        """Test LLMError exception."""
        error = LLMError("LLM failed")
        assert str(error) == "LLM failed"
        assert isinstance(error, AgentError)
    
    def test_conversation_error(self):
        """Test ConversationError exception."""
        error = ConversationError("Conversation failed")
        assert str(error) == "Conversation failed"
        assert isinstance(error, AgentError)
    
    def test_configuration_error(self):
        """Test ConfigurationError exception."""
        error = ConfigurationError("Configuration failed")
        assert str(error) == "Configuration failed"
        assert isinstance(error, AgentError)
    
    def test_exception_inheritance(self):
        """Test exception inheritance hierarchy."""
        retrieval_error = RetrievalError("Test")
        llm_error = LLMError("Test")
        conversation_error = ConversationError("Test")
        configuration_error = ConfigurationError("Test")
        
        # All should inherit from AgentError
        assert isinstance(retrieval_error, AgentError)
        assert isinstance(llm_error, AgentError)
        assert isinstance(conversation_error, AgentError)
        assert isinstance(configuration_error, AgentError)
        
        # All should inherit from Exception
        assert isinstance(retrieval_error, Exception)
        assert isinstance(llm_error, Exception)
        assert isinstance(conversation_error, Exception)
        assert isinstance(configuration_error, Exception)
    
    def test_exception_basic(self):
        """Test basic exception creation."""
        error = AgentError("Main error")
        assert str(error) == "Main error"
        assert isinstance(error, Exception)
    
    def test_exception_chaining(self):
        """Test exception chaining."""
        original_error = ValueError("Original error")
        try:
            raise AgentError("Agent failed") from original_error
        except AgentError as agent_error:
            assert str(agent_error) == "Agent failed"
            assert agent_error.__cause__ == original_error
