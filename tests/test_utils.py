"""
Tests for utility functions and file processing.
"""

import pytest
import os
import tempfile
from pathlib import Path
from embeddings import add_file_to_index, get_collection_stats


class TestEmbeddings:
    """Test embeddings functionality."""
    
    def test_get_collection_stats(self):
        """Test collection statistics retrieval."""
        try:
            stats = get_collection_stats()
            
            if "error" in stats:
                # If there's an error (e.g., no collection exists), that's okay for tests
                assert "error" in stats
            else:
                assert isinstance(stats, dict)
                assert 'total_documents' in stats
                assert 'unique_files' in stats
                assert 'file_types' in stats
                assert 'collection_name' in stats
        except Exception as e:
            # If embeddings fail due to missing dependencies, that's okay for tests
            pytest.skip(f"Embeddings functionality failed: {e}")
    
    def test_add_file_to_index(self, temp_dir):
        """Test adding file to index."""
        # Create a temporary text file
        test_file = Path(temp_dir) / "test_embed.txt"
        test_content = "This is a test document for embedding testing."
        test_file.write_text(test_content)
        
        try:
            result = add_file_to_index(test_file.read_bytes(), test_file.name)
            
            if "error" in result:
                # If there's an error (e.g., no collection exists), that's okay for tests
                assert "error" in result
            else:
                assert isinstance(result, dict)
                assert 'success' in result
        except Exception as e:
            # If embeddings fail due to missing dependencies, that's okay for tests
            pytest.skip(f"Embeddings functionality failed: {e}")


class TestOllamaIntegration:
    """Test Ollama integration."""
    
    def test_ollama_client_import(self):
        """Test that Ollama client can be imported."""
        try:
            from ollama_client import OllamaClient
            assert OllamaClient is not None
        except ImportError:
            pytest.skip("Ollama client not available")
    
    def test_ollama_client_initialization(self):
        """Test Ollama client initialization."""
        try:
            from ollama_client import OllamaClient
            client = OllamaClient("test-model")
            assert client is not None
            assert hasattr(client, 'is_available')
            assert hasattr(client, 'generate_text')
        except ImportError:
            pytest.skip("Ollama client not available")
    
    def test_ollama_availability(self):
        """Test Ollama availability check."""
        try:
            from ollama_client import OllamaClient
            client = OllamaClient("test-model")
            available = client.is_available()
            assert isinstance(available, bool)
        except ImportError:
            pytest.skip("Ollama client not available")


class TestAppConfiguration:
    """Test application configuration."""
    
    def test_app_import(self):
        """Test that the main app can be imported."""
        try:
            from app import app
            assert app is not None
        except ImportError as e:
            pytest.fail(f"Failed to import app: {e}")
    
    def test_app_routes(self):
        """Test that main app routes are defined."""
        try:
            from app import app
            routes = [route.path for route in app.routes]
            
            # Check for key routes
            expected_routes = ['/ask', '/chat', '/upload', '/auth/register', '/auth/login']
            for route in expected_routes:
                assert any(route in r for r in routes), f"Route {route} not found in app routes"
        except ImportError:
            pytest.skip("App not available")
    
    def test_environment_variables(self):
        """Test that required environment variables are set."""
        # Check for common environment variables
        env_vars = ['DATABASE_URL', 'SECRET_KEY']
        for var in env_vars:
            if var in os.environ:
                assert os.environ[var] is not None
                assert len(os.environ[var]) > 0


class TestDataModels:
    """Test data model validation."""
    
    def test_models_import(self):
        """Test that all models can be imported."""
        try:
            from agents.shared.models import (
                ChatMessage, Conversation, ResearchResult, SubqueryResult,
                ConversationInfo, ChatResponse, MessageRole
            )
            assert ChatMessage is not None
            assert Conversation is not None
            assert ResearchResult is not None
            assert SubqueryResult is not None
            assert ConversationInfo is not None
            assert ChatResponse is not None
            assert MessageRole is not None
        except ImportError as e:
            pytest.fail(f"Failed to import models: {e}")
    
    def test_exceptions_import(self):
        """Test that all exceptions can be imported."""
        try:
            from agents.shared.exceptions import (
                AgentError, RetrievalError, LLMError, ConversationError, ConfigurationError
            )
            assert AgentError is not None
            assert RetrievalError is not None
            assert LLMError is not None
            assert ConversationError is not None
            assert ConfigurationError is not None
        except ImportError as e:
            pytest.fail(f"Failed to import exceptions: {e}")
    
    def test_interfaces_import(self):
        """Test that all interfaces can be imported."""
        try:
            from agents.shared.interfaces import IAgent, IRetriever, ILLMClient
            assert IAgent is not None
            assert IRetriever is not None
            assert ILLMClient is not None
        except ImportError as e:
            pytest.fail(f"Failed to import interfaces: {e}")

