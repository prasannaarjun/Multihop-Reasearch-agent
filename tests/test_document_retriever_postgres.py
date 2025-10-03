"""
Tests for the updated Postgres-based document retriever.
"""

import pytest
from unittest.mock import Mock, patch
from agents.research.document_retriever import DocumentRetriever
from agents.shared.exceptions import RetrievalError


class TestDocumentRetrieverPostgres:
    """Test cases for the Postgres-based document retriever."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def mock_model(self):
        """Mock sentence transformer model."""
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1] * 1536]  # Mock embedding
        return mock_model
    
    @pytest.fixture
    def retriever(self, mock_db_session, mock_model):
        """Create document retriever instance."""
        return DocumentRetriever(mock_db_session, mock_model, user_id=1)
    
    def test_retriever_initialization(self, mock_db_session, mock_model):
        """Test document retriever initialization."""
        retriever = DocumentRetriever(mock_db_session, mock_model, user_id=1)
        
        assert retriever.db_session == mock_db_session
        assert retriever.model == mock_model
        assert retriever.user_id == 1
    
    @patch('agents.research.document_retriever.retrieve_similar_embeddings')
    def test_retrieve_success(self, mock_retrieve_embeddings, retriever):
        """Test successful document retrieval."""
        # Mock embedding results
        mock_results = [
            {
                "id": "emb-1",
                "message_id": "msg-1",
                "user_id": 1,
                "metadata": {
                    "text": "This is sample text content for testing.",
                    "title": "Test Document",
                    "filename": "test.txt",
                    "chunk_index": 0
                },
                "created_at": "2023-01-01T00:00:00",
                "similarity_score": 0.95
            },
            {
                "id": "emb-2",
                "message_id": "msg-2",
                "user_id": 1,
                "metadata": {
                    "text": "Another sample text content.",
                    "title": "Another Document",
                    "filename": "test2.txt",
                    "chunk_index": 0
                },
                "created_at": "2023-01-01T00:00:00",
                "similarity_score": 0.87
            }
        ]
        
        mock_retrieve_embeddings.return_value = mock_results
        
        results = retriever.retrieve("test query", top_k=3)
        
        assert len(results) == 2
        assert results[0]["doc_id"] == "emb-1"
        assert results[0]["title"] == "Test Document"
        assert results[0]["score"] == 0.95
        assert results[0]["filename"] == "test.txt"
        assert results[0]["full_text"] == "This is sample text content for testing."
        assert results[0]["message_id"] == "msg-1"
        assert results[0]["chunk_index"] == 0
        
        # Verify model.encode was called
        retriever.model.encode.assert_called_once_with(["test query"], normalize_embeddings=True)
        
        # Verify retrieve_similar_embeddings was called
        mock_retrieve_embeddings.assert_called_once_with(
            db_session=retriever.db_session,
            user_id=1,
            query_vector=[0.1] * 1536,
            k=3
        )
    
    @patch('agents.research.document_retriever.retrieve_similar_embeddings')
    def test_retrieve_no_results(self, mock_retrieve_embeddings, retriever):
        """Test document retrieval with no results."""
        mock_retrieve_embeddings.return_value = []
        
        results = retriever.retrieve("test query", top_k=3)
        
        assert len(results) == 0
    
    @patch('agents.research.document_retriever.retrieve_similar_embeddings')
    def test_retrieve_empty_text_content(self, mock_retrieve_embeddings, retriever):
        """Test document retrieval with empty text content."""
        mock_results = [
            {
                "id": "emb-1",
                "message_id": "msg-1",
                "user_id": 1,
                "metadata": {
                    "text": "",  # Empty text
                    "title": "Test Document",
                    "filename": "test.txt",
                    "chunk_index": 0
                },
                "created_at": "2023-01-01T00:00:00",
                "similarity_score": 0.95
            }
        ]
        
        mock_retrieve_embeddings.return_value = mock_results
        
        results = retriever.retrieve("test query", top_k=3)
        
        # Empty text content should be filtered out
        assert len(results) == 0
    
    @patch('agents.research.document_retriever.retrieve_similar_embeddings')
    def test_retrieve_missing_metadata(self, mock_retrieve_embeddings, retriever):
        """Test document retrieval with missing metadata."""
        mock_results = [
            {
                "id": "emb-1",
                "message_id": "msg-1",
                "user_id": 1,
                "metadata": {},  # Empty metadata
                "created_at": "2023-01-01T00:00:00",
                "similarity_score": 0.95
            }
        ]
        
        mock_retrieve_embeddings.return_value = mock_results
        
        results = retriever.retrieve("test query", top_k=3)
        
        # Missing text content should be filtered out
        assert len(results) == 0
    
    @patch('agents.research.document_retriever.retrieve_similar_embeddings')
    def test_retrieve_long_text_snippet(self, mock_retrieve_embeddings, retriever):
        """Test document retrieval with long text creates snippet."""
        long_text = "This is a very long text content that should be truncated to create a snippet for display purposes. " * 10
        
        mock_results = [
            {
                "id": "emb-1",
                "message_id": "msg-1",
                "user_id": 1,
                "metadata": {
                    "text": long_text,
                    "title": "Test Document",
                    "filename": "test.txt",
                    "chunk_index": 0
                },
                "created_at": "2023-01-01T00:00:00",
                "similarity_score": 0.95
            }
        ]
        
        mock_retrieve_embeddings.return_value = mock_results
        
        results = retriever.retrieve("test query", top_k=3)
        
        assert len(results) == 1
        assert len(results[0]["snippet"]) <= 203  # 200 chars + "..."
        assert results[0]["snippet"].endswith("...")
        assert results[0]["full_text"] == long_text
    
    @patch('agents.research.document_retriever.retrieve_similar_embeddings')
    def test_retrieve_retrieval_error(self, mock_retrieve_embeddings, retriever):
        """Test document retrieval with retrieval error."""
        mock_retrieve_embeddings.side_effect = Exception("Database error")
        
        with pytest.raises(RetrievalError) as exc_info:
            retriever.retrieve("test query", top_k=3)
        
        assert "Failed to retrieve documents" in str(exc_info.value)
    
    @patch('agents.research.document_retriever.get_embedding_stats')
    def test_get_collection_stats_success(self, mock_get_stats, retriever):
        """Test getting collection statistics successfully."""
        # Mock embedding stats
        mock_get_stats.return_value = {
            "total_embeddings": 100,
            "unique_messages": 50,
            "embedding_dimension": 1536
        }
        
        # Mock file types query result
        mock_types_result = Mock()
        mock_types_result.__iter__ = Mock(return_value=iter([
            Mock(file_type=".txt", count=60),
            Mock(file_type=".pdf", count=40)
        ]))
        
        # Mock filenames query result
        mock_filenames_result = Mock()
        mock_filenames_result.__iter__ = Mock(return_value=iter([
            Mock(filename="file1.txt"),
            Mock(filename="file2.pdf"),
            Mock(filename="file3.txt")
        ]))
        
        # Mock execute calls
        retriever.db_session.execute.side_effect = [
            mock_types_result,    # File types query
            mock_filenames_result # Filenames query
        ]
        
        stats = retriever.get_collection_stats()
        
        assert stats["total_documents"] == 100
        assert stats["unique_files"] == 3
        assert stats["file_types"][".txt"] == 60
        assert stats["file_types"][".pdf"] == 40
        assert stats["collection_name"] == "postgres_embeddings"
        assert stats["embedding_dimension"] == 1536
        
        # Verify get_embedding_stats was called
        mock_get_stats.assert_called_once_with(retriever.db_session, retriever.user_id)
    
    @patch('agents.research.document_retriever.get_embedding_stats')
    def test_get_collection_stats_embedding_error(self, mock_get_stats, retriever):
        """Test getting collection statistics with embedding stats error."""
        mock_get_stats.return_value = {
            "error": "Database error",
            "total_embeddings": 0,
            "unique_messages": 0,
            "embedding_dimension": 1536
        }
        
        stats = retriever.get_collection_stats()
        
        assert "error" in stats
        assert stats["total_documents"] == 0
        assert stats["unique_files"] == 0
        assert stats["file_types"] == {}
        assert stats["collection_name"] == "postgres_embeddings"
    
    @patch('agents.research.document_retriever.get_embedding_stats')
    def test_get_collection_stats_database_error(self, mock_get_stats, retriever):
        """Test getting collection statistics with database error."""
        mock_get_stats.return_value = {
            "total_embeddings": 100,
            "unique_messages": 50,
            "embedding_dimension": 1536
        }
        
        retriever.db_session.execute.side_effect = Exception("Database error")
        
        stats = retriever.get_collection_stats()
        
        assert "error" in stats
        assert stats["total_documents"] == 0
        assert stats["unique_files"] == 0
        assert stats["file_types"] == {}
        assert stats["collection_name"] == "postgres_embeddings"


if __name__ == "__main__":
    pytest.main([__file__])

