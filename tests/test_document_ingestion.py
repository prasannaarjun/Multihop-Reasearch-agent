"""
Tests for document ingestion functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from document_ingestion import (
    chunk_text,
    process_and_store_document,
    process_and_store_file_content,
    batch_process_directory,
    get_user_document_stats
)


class TestDocumentIngestion:
    """Test cases for document ingestion functions."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def mock_model(self):
        """Mock sentence transformer model."""
        import numpy as np
        mock_model = Mock()
        mock_model.encode.return_value = np.array([[0.1] * 1536])  # Mock embedding as numpy array
        return mock_model
    
    @pytest.fixture
    def sample_text(self):
        """Sample text for testing."""
        return "This is a sample text document for testing purposes. " * 50
    
    def test_chunk_text_short_text(self):
        """Test chunking short text."""
        short_text = "This is a short text."
        chunks = chunk_text(short_text, chunk_size=1000, overlap=200)
        
        assert len(chunks) == 1
        assert chunks[0] == short_text
    
    def test_chunk_text_long_text(self):
        """Test chunking long text."""
        long_text = "This is a sentence. " * 100  # ~2000 characters
        chunks = chunk_text(long_text, chunk_size=500, overlap=100)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 500 for chunk in chunks)
        assert all(len(chunk.strip()) > 0 for chunk in chunks)
    
    def test_chunk_text_with_overlap(self):
        """Test chunking with overlap."""
        text = "A" * 1000 + "B" * 1000 + "C" * 1000
        chunks = chunk_text(text, chunk_size=800, overlap=200)
        
        assert len(chunks) >= 2
        # Check that chunks don't exceed size limit
        assert all(len(chunk) <= 800 for chunk in chunks)
    
    def test_chunk_text_sentence_boundary(self):
        """Test chunking respects sentence boundaries."""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = chunk_text(text, chunk_size=20, overlap=5)
        
        # Should try to break at sentence boundaries
        assert len(chunks) > 1
        assert all(len(chunk.strip()) > 0 for chunk in chunks)
    
    @patch('document_ingestion.process_file')
    @patch('document_ingestion.store_embedding')
    def test_process_and_store_document_success(
        self, mock_store_embedding, mock_process_file,
        mock_db_session, mock_model, sample_text
    ):
        """Test successful document processing and storage."""
        # Setup mocks
        mock_process_file.return_value = sample_text
        mock_store_embedding.return_value = "emb-123"
        
        result = process_and_store_document(
            db_session=mock_db_session,
            user_id=1,
            file_path="test.txt",
            filename="test.txt",
            model=mock_model
        )
        
        assert result["success"] is True
        assert result["chunks_added"] > 0
        assert "word_count" in result
        assert "message_id" in result
        
        # Verify mocks were called
        mock_process_file.assert_called_once_with("test.txt")
        assert mock_store_embedding.call_count > 0
    
    @patch('document_ingestion.process_file')
    def test_process_and_store_document_empty_text(
        self, mock_process_file, mock_db_session, mock_model
    ):
        """Test document processing with empty text."""
        mock_process_file.return_value = ""
        
        result = process_and_store_document(
            db_session=mock_db_session,
            user_id=1,
            file_path="empty.txt",
            filename="empty.txt",
            model=mock_model
        )
        
        assert result["success"] is False
        assert "No text content extracted" in result["message"]
        assert result["chunks_added"] == 0
    
    @patch('document_ingestion.process_file')
    def test_process_and_store_document_processing_error(
        self, mock_process_file, mock_db_session, mock_model
    ):
        """Test document processing with processing error."""
        from document_processing import DocumentProcessingError
        mock_process_file.side_effect = DocumentProcessingError("Processing failed")
        
        result = process_and_store_document(
            db_session=mock_db_session,
            user_id=1,
            file_path="error.txt",
            filename="error.txt",
            model=mock_model
        )
        
        assert result["success"] is False
        assert "Document processing error" in result["message"]
        assert result["chunks_added"] == 0
    
    @patch('document_ingestion.process_file')
    @patch('document_ingestion.store_embedding')
    def test_process_and_store_document_storage_error(
        self, mock_store_embedding, mock_process_file,
        mock_db_session, mock_model, sample_text
    ):
        """Test document processing with storage error."""
        mock_process_file.return_value = sample_text
        mock_store_embedding.side_effect = Exception("Storage failed")
        
        result = process_and_store_document(
            db_session=mock_db_session,
            user_id=1,
            file_path="test.txt",
            filename="test.txt",
            model=mock_model
        )
        
        assert result["success"] is False
        assert "Error processing document" in result["message"]
        assert result["chunks_added"] == 0
    
    def test_process_and_store_file_content_success(
        self, mock_db_session, mock_model, sample_text
    ):
        """Test processing file content from bytes."""
        file_content = sample_text.encode('utf-8')
        
        with patch('document_ingestion.process_and_store_document') as mock_process:
            mock_process.return_value = {
                "success": True,
                "message": "Success",
                "chunks_added": 5,
                "word_count": 100
            }
            
            result = process_and_store_file_content(
                db_session=mock_db_session,
                user_id=1,
                file_content=file_content,
                filename="test.txt",
                model=mock_model
            )
            
            assert result["success"] is True
            assert result["chunks_added"] == 5
            mock_process.assert_called_once()
    
    def test_process_and_store_file_content_unsupported_type(
        self, mock_db_session, mock_model
    ):
        """Test processing unsupported file type."""
        file_content = b"Some content"
        
        result = process_and_store_file_content(
            db_session=mock_db_session,
            user_id=1,
            file_content=file_content,
            filename="test.xyz",  # Unsupported extension
            model=mock_model
        )
        
        assert result["success"] is False
        assert "Unsupported file type" in result["message"]
        assert result["chunks_added"] == 0
    
    @patch('document_ingestion.process_and_store_document')
    def test_batch_process_directory_success(
        self, mock_process_document, mock_db_session, mock_model
    ):
        """Test batch processing directory."""
        # Create temporary directory with test files
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create test files
            test_file1 = Path(tmp_dir) / "test1.txt"
            test_file2 = Path(tmp_dir) / "test2.txt"
            test_file1.write_text("Content 1")
            test_file2.write_text("Content 2")
            
            # Mock the process function
            mock_process_document.return_value = {
                "success": True,
                "message": "Success",
                "chunks_added": 3
            }
            
            result = batch_process_directory(
                db_session=mock_db_session,
                user_id=1,
                data_dir=tmp_dir,
                model=mock_model
            )
            
            assert result["success"] is True
            assert result["files_processed"] == 2
            assert result["total_chunks"] == 6
            assert len(result["errors"]) == 0
    
    @patch('document_ingestion.process_and_store_document')
    def test_batch_process_directory_no_files(
        self, mock_process_document, mock_db_session, mock_model
    ):
        """Test batch processing directory with no supported files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create unsupported file
            test_file = Path(tmp_dir) / "test.xyz"
            test_file.write_text("Content")
            
            result = batch_process_directory(
                db_session=mock_db_session,
                user_id=1,
                data_dir=tmp_dir,
                model=mock_model
            )
            
            assert result["success"] is False
            assert "No supported files found" in result["message"]
            assert result["files_processed"] == 0
            assert result["total_chunks"] == 0
    
    @patch('document_ingestion.process_and_store_document')
    def test_batch_process_directory_with_errors(
        self, mock_process_document, mock_db_session, mock_model
    ):
        """Test batch processing directory with some errors."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create test files
            test_file1 = Path(tmp_dir) / "test1.txt"
            test_file2 = Path(tmp_dir) / "test2.txt"
            test_file1.write_text("Content 1")
            test_file2.write_text("Content 2")
            
            # Mock the process function to return mixed results
            mock_process_document.side_effect = [
                {"success": True, "message": "Success", "chunks_added": 3},
                {"success": False, "message": "Error", "chunks_added": 0}
            ]
            
            result = batch_process_directory(
                db_session=mock_db_session,
                user_id=1,
                data_dir=tmp_dir,
                model=mock_model
            )
            
            assert result["success"] is True  # At least one file succeeded
            assert result["files_processed"] == 1
            assert result["total_chunks"] == 3
            assert len(result["errors"]) == 1
    
    def test_get_user_document_stats_success(self, mock_db_session):
        """Test getting user document statistics."""
        # Mock query results
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 50
        
        mock_files_result = Mock()
        mock_files_result.scalar.return_value = 10
        
        mock_types_result = Mock()
        mock_types_result.__iter__ = Mock(return_value=iter([
            Mock(file_type=".txt", count=30),
            Mock(file_type=".pdf", count=20)
        ]))
        
        # Mock execute calls
        mock_db_session.execute.side_effect = [
            mock_count_result,  # Count query
            mock_files_result,  # Files query
            mock_types_result   # Types query
        ]
        
        stats = get_user_document_stats(mock_db_session, user_id=1)
        
        assert stats["total_embeddings"] == 50
        assert stats["unique_files"] == 10
        assert stats["file_types"][".txt"] == 30
        assert stats["file_types"][".pdf"] == 20
        assert stats["user_id"] == 1
    
    def test_get_user_document_stats_error(self, mock_db_session):
        """Test getting user document statistics with error."""
        mock_db_session.execute.side_effect = Exception("Database error")
        
        stats = get_user_document_stats(mock_db_session, user_id=1)
        
        assert "error" in stats
        assert stats["total_embeddings"] == 0
        assert stats["unique_files"] == 0
        assert stats["file_types"] == {}
        assert stats["user_id"] == 1


if __name__ == "__main__":
    pytest.main([__file__])

