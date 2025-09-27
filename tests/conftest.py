"""
Pytest configuration and shared fixtures.
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, MagicMock
from datetime import datetime

# Ensure highlights limit is accessible during tests
from agents.chat.conversation_manager import MAX_STORED_HIGHLIGHTS

# Set test environment variables
os.environ["DATABASE_URL"] = "sqlite:///./test_auth.db"
os.environ["SECRET_KEY"] = "test-secret-key"

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    mock = Mock()
    mock.is_available.return_value = True
    mock.generate_text.return_value = "Test response from LLM"
    mock.generate_subqueries.return_value = ["Test subquery 1", "Test subquery 2"]
    return mock

@pytest.fixture
def mock_retriever():
    """Create a mock document retriever."""
    mock = Mock()
    mock.retrieve.return_value = [
        {
            'title': 'Test Document',
            'full_text': 'This is test content about machine learning.',
            'score': 0.9,
            'filename': 'test.txt',
            'doc_id': 'test-doc-1'
        }
    ]
    mock.get_collection_stats.return_value = {
        'total_documents': 10,
        'unique_files': 5,
        'file_types': {'txt': 3, 'pdf': 2},
        'collection_name': 'test_collection'
    }
    return mock

@pytest.fixture
def sample_conversation():
    """Create a sample conversation for testing."""
    from agents.shared.models import Conversation, ChatMessage
    
    conversation = Conversation(
        id="test-conv-1",
        title="Test Conversation",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        messages=[],
        context={}
    )
    
    # Add some test messages
    conversation.add_message("user", "What is machine learning?")
    conversation.add_message("assistant", "Machine learning is a subset of AI...")
    conversation.add_message("user", "How does it work?")
    
    return conversation

@pytest.fixture
def sample_research_result():
    """Create a sample research result for testing."""
    from agents.shared.models import ResearchResult, SubqueryResult
    
    subquery_results = [
        SubqueryResult(
            subquery="What is machine learning?",
            summary="ML is a subset of AI that enables computers to learn from data.",
            documents=[],
            success=True
        ),
        SubqueryResult(
            subquery="How does machine learning work?",
            summary="ML works by using algorithms to identify patterns in data.",
            documents=[],
            success=True
        )
    ]
    
    return ResearchResult(
        question="What is machine learning and how does it work?",
        answer="Machine learning is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed.",
        subqueries=subquery_results,
        citations=[{"title": "ML Basics", "filename": "ml.txt", "score": 0.9}],
        total_documents=1,
        processing_time=1.5
    )

