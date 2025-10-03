"""
Tests for Postgres + pgvector embedding storage functionality.
"""

import pytest
import numpy as np
from sqlalchemy.orm import Session
from unittest.mock import Mock
from agents.shared.exceptions import AgentError
from embedding_storage import (
    store_embedding,
    retrieve_similar_embeddings,
    get_embedding_stats,
    delete_embeddings_by_message,
    delete_embeddings_by_user
)


class TestEmbeddingStorage:
    """Test cases for embedding storage functions."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_vector(self):
        """Sample embedding vector."""
        return [0.1] * 1536  # Default embedding dimension
    
    @pytest.fixture
    def sample_metadata(self):
        """Sample metadata."""
        return {
            "text": "Sample text content",
            "chunk_index": 0,
            "filename": "test.txt",
            "file_type": ".txt",
            "title": "Test Document"
        }
    
    def test_store_embedding_success(self, mock_db_session, sample_vector, sample_metadata):
        """Test successful embedding storage."""
        # Mock the embedding object
        mock_embedding = Mock()
        mock_embedding.id = "test-id-123"
        
        # Mock database operations
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        
        # Mock the EmbeddingDB constructor
        with pytest.Mock.patch('embedding_storage.EmbeddingDB') as mock_embedding_db:
            mock_embedding_db.return_value = mock_embedding
            
            result = store_embedding(
                db_session=mock_db_session,
                user_id=1,
                message_id="msg-123",
                vector=sample_vector,
                metadata=sample_metadata
            )
            
            assert result == "test-id-123"
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
    
    def test_store_embedding_invalid_dimension(self, mock_db_session, sample_metadata):
        """Test embedding storage with invalid vector dimension."""
        invalid_vector = [0.1] * 100  # Wrong dimension
        
        with pytest.raises(AgentError) as exc_info:
            store_embedding(
                db_session=mock_db_session,
                user_id=1,
                message_id="msg-123",
                vector=invalid_vector,
                metadata=sample_metadata
            )
        
        assert "Vector dimension mismatch" in str(exc_info.value)
    
    def test_store_embedding_non_numeric_values(self, mock_db_session, sample_metadata):
        """Test embedding storage with non-numeric values."""
        invalid_vector = ["not", "numeric", "values"] + [0.1] * 1533
        
        with pytest.raises(AgentError) as exc_info:
            store_embedding(
                db_session=mock_db_session,
                user_id=1,
                message_id="msg-123",
                vector=invalid_vector,
                metadata=sample_metadata
            )
        
        assert "Vector must contain only numeric values" in str(exc_info.value)
    
    def test_store_embedding_nan_values(self, mock_db_session, sample_metadata):
        """Test embedding storage with NaN values."""
        invalid_vector = [float('nan')] + [0.1] * 1535
        
        with pytest.raises(AgentError) as exc_info:
            store_embedding(
                db_session=mock_db_session,
                user_id=1,
                message_id="msg-123",
                vector=invalid_vector,
                metadata=sample_metadata
            )
        
        assert "Vector contains NaN or infinite values" in str(exc_info.value)
    
    def test_store_embedding_database_error(self, mock_db_session, sample_vector, sample_metadata):
        """Test embedding storage with database error."""
        # Mock database error
        mock_db_session.add.side_effect = Exception("Database error")
        mock_db_session.rollback.return_value = None
        
        with pytest.raises(AgentError) as exc_info:
            store_embedding(
                db_session=mock_db_session,
                user_id=1,
                message_id="msg-123",
                vector=sample_vector,
                metadata=sample_metadata
            )
        
        assert "Failed to store embedding" in str(exc_info.value)
        mock_db_session.rollback.assert_called_once()
    
    def test_retrieve_similar_embeddings_success(self, mock_db_session, sample_vector):
        """Test successful embedding retrieval."""
        # Mock query result
        mock_result = Mock()
        mock_result.id = "emb-123"
        mock_result.message_id = "msg-123"
        mock_result.user_id = 1
        mock_result.metadata = {"text": "Sample text"}
        mock_result.created_at = "2023-01-01T00:00:00"
        mock_result.similarity_score = 0.95
        
        mock_db_session.execute.return_value = [mock_result]
        
        results = retrieve_similar_embeddings(
            db_session=mock_db_session,
            user_id=1,
            query_vector=sample_vector,
            k=3
        )
        
        assert len(results) == 1
        assert results[0]["id"] == "emb-123"
        assert results[0]["similarity_score"] == 0.95
        mock_db_session.execute.assert_called_once()
    
    def test_retrieve_similar_embeddings_invalid_query(self, mock_db_session):
        """Test embedding retrieval with invalid query vector."""
        invalid_vector = [0.1] * 100  # Wrong dimension
        
        with pytest.raises(AgentError) as exc_info:
            retrieve_similar_embeddings(
                db_session=mock_db_session,
                user_id=1,
                query_vector=invalid_vector,
                k=3
            )
        
        assert "Query vector dimension mismatch" in str(exc_info.value)
    
    def test_retrieve_similar_embeddings_database_error(self, mock_db_session, sample_vector):
        """Test embedding retrieval with database error."""
        mock_db_session.execute.side_effect = Exception("Database error")
        
        with pytest.raises(AgentError) as exc_info:
            retrieve_similar_embeddings(
                db_session=mock_db_session,
                user_id=1,
                query_vector=sample_vector,
                k=3
            )
        
        assert "Failed to retrieve similar embeddings" in str(exc_info.value)
    
    def test_get_embedding_stats_success(self, mock_db_session):
        """Test successful embedding statistics retrieval."""
        # Mock count query result
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 100
        
        # Mock messages query result
        mock_messages_result = Mock()
        mock_messages_result.scalar.return_value = 50
        
        # Mock users query result
        mock_users_result = Mock()
        mock_users_result.scalar.return_value = 10
        
        # Mock execute calls
        mock_db_session.execute.side_effect = [
            mock_count_result,  # First call for total embeddings
            mock_messages_result,  # Second call for unique messages
            mock_users_result  # Third call for unique users
        ]
        
        stats = get_embedding_stats(mock_db_session, user_id=None)
        
        assert stats["total_embeddings"] == 100
        assert stats["unique_messages"] == 50
        assert stats["unique_users"] == 10
        assert stats["embedding_dimension"] == 1536
    
    def test_get_embedding_stats_user_specific(self, mock_db_session):
        """Test embedding statistics for specific user."""
        # Mock count query result
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 25
        
        # Mock messages query result
        mock_messages_result = Mock()
        mock_messages_result.scalar.return_value = 15
        
        # Mock execute calls
        mock_db_session.execute.side_effect = [
            mock_count_result,  # First call for total embeddings
            mock_messages_result  # Second call for unique messages
        ]
        
        stats = get_embedding_stats(mock_db_session, user_id=1)
        
        assert stats["total_embeddings"] == 25
        assert stats["unique_messages"] == 15
        assert "unique_users" not in stats  # Not included for user-specific stats
        assert stats["embedding_dimension"] == 1536
    
    def test_get_embedding_stats_error(self, mock_db_session):
        """Test embedding statistics with database error."""
        mock_db_session.execute.side_effect = Exception("Database error")
        
        stats = get_embedding_stats(mock_db_session, user_id=1)
        
        assert "error" in stats
        assert stats["total_embeddings"] == 0
        assert stats["unique_messages"] == 0
        assert stats["embedding_dimension"] == 1536
    
    def test_delete_embeddings_by_message_success(self, mock_db_session):
        """Test successful deletion of embeddings by message."""
        # Mock count query result
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 5
        
        # Mock delete query result
        mock_delete_result = Mock()
        mock_delete_result.rowcount = 5
        
        # Mock execute calls
        mock_db_session.execute.side_effect = [
            mock_count_result,  # Count query
            mock_delete_result  # Delete query
        ]
        
        deleted_count = delete_embeddings_by_message(mock_db_session, "msg-123")
        
        assert deleted_count == 5
        mock_db_session.commit.assert_called_once()
    
    def test_delete_embeddings_by_message_error(self, mock_db_session):
        """Test deletion of embeddings by message with database error."""
        mock_db_session.execute.side_effect = Exception("Database error")
        mock_db_session.rollback.return_value = None
        
        with pytest.raises(AgentError) as exc_info:
            delete_embeddings_by_message(mock_db_session, "msg-123")
        
        assert "Failed to delete embeddings" in str(exc_info.value)
        mock_db_session.rollback.assert_called_once()
    
    def test_delete_embeddings_by_user_success(self, mock_db_session):
        """Test successful deletion of embeddings by user."""
        # Mock count query result
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 20
        
        # Mock delete query result
        mock_delete_result = Mock()
        mock_delete_result.rowcount = 20
        
        # Mock execute calls
        mock_db_session.execute.side_effect = [
            mock_count_result,  # Count query
            mock_delete_result  # Delete query
        ]
        
        deleted_count = delete_embeddings_by_user(mock_db_session, 1)
        
        assert deleted_count == 20
        mock_db_session.commit.assert_called_once()
    
    def test_delete_embeddings_by_user_error(self, mock_db_session):
        """Test deletion of embeddings by user with database error."""
        mock_db_session.execute.side_effect = Exception("Database error")
        mock_db_session.rollback.return_value = None
        
        with pytest.raises(AgentError) as exc_info:
            delete_embeddings_by_user(mock_db_session, 1)
        
        assert "Failed to delete user embeddings" in str(exc_info.value)
        mock_db_session.rollback.assert_called_once()


class TestEmbeddingModel:
    """Test cases for the EmbeddingDB model."""
    
    def test_embedding_model_creation(self):
        """Test creating an EmbeddingDB model instance."""
        from agents.shared.models import EmbeddingDB
        import uuid
        
        embedding = EmbeddingDB(
            message_id=str(uuid.uuid4()),
            user_id=1,
            vector=[0.1] * 1536,
            metadata={"text": "test"}
        )
        
        assert embedding.user_id == 1
        assert len(embedding.vector) == 1536
        assert embedding.metadata["text"] == "test"
        assert embedding.created_at is not None
    
    def test_embedding_model_relationships(self):
        """Test embedding model relationships."""
        from agents.shared.models import EmbeddingDB, ChatMessageDB
        import uuid
        
        # Create message
        message = ChatMessageDB(
            id=str(uuid.uuid4()),
            conversation_id=str(uuid.uuid4()),
            role="user",
            content="test message"
        )
        
        # Create embedding
        embedding = EmbeddingDB(
            message_id=message.id,
            user_id=1,
            vector=[0.1] * 1536,
            metadata={"text": "test"}
        )
        
        # Test relationship
        assert embedding.message_id == message.id
        # Note: Actual relationship testing would require database setup


if __name__ == "__main__":
    pytest.main([__file__])

