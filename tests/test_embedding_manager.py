"""
Tests for the embedding manager script.
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embedding_manager import EmbeddingManager


class TestEmbeddingManager:
    """Test cases for the EmbeddingManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.manager = EmbeddingManager()
        self.manager.db = self.mock_db
    
    def test_list_users_with_embeddings_success(self):
        """Test successful listing of users with embeddings."""
        # Mock database result
        mock_result = Mock()
        mock_row1 = Mock()
        mock_row1.id = 1
        mock_row1.username = "testuser1"
        mock_row1.email = "test1@example.com"
        mock_row1.full_name = "Test User 1"
        mock_row1.created_at = datetime(2024, 1, 1)
        mock_row1.last_login = datetime(2024, 1, 15)
        mock_row1.embedding_count = 5
        mock_row1.unique_messages = 3
        mock_row1.first_embedding = datetime(2024, 1, 2)
        mock_row1.last_embedding = datetime(2024, 1, 14)
        
        mock_row2 = Mock()
        mock_row2.id = 2
        mock_row2.username = "testuser2"
        mock_row2.email = "test2@example.com"
        mock_row2.full_name = "Test User 2"
        mock_row2.created_at = datetime(2024, 1, 5)
        mock_row2.last_login = None
        mock_row2.embedding_count = 0
        mock_row2.unique_messages = 0
        mock_row2.first_embedding = None
        mock_row2.last_embedding = None
        
        mock_result.__iter__ = Mock(return_value=iter([mock_row1, mock_row2]))
        self.mock_db.execute.return_value = mock_result
        
        # Test the method
        users = self.manager.list_users_with_embeddings()
        
        # Assertions
        assert len(users) == 2
        assert users[0]['id'] == 1
        assert users[0]['username'] == "testuser1"
        assert users[0]['embedding_count'] == 5
        assert users[1]['id'] == 2
        assert users[1]['embedding_count'] == 0
        assert users[1]['last_login'] is None
    
    def test_list_users_with_embeddings_error(self):
        """Test error handling in list_users_with_embeddings."""
        # Mock database error
        self.mock_db.execute.side_effect = Exception("Database error")
        
        # Test the method
        users = self.manager.list_users_with_embeddings()
        
        # Should return empty list on error
        assert users == []
    
    def test_get_user_embeddings_success(self):
        """Test successful retrieval of user embeddings."""
        # Mock database result
        mock_result = Mock()
        mock_row = Mock()
        mock_row.id = "emb1"
        mock_row.message_id = "msg1"
        mock_row.created_at = datetime(2024, 1, 10)
        mock_row.embedding_metadata = {"test": "data"}
        mock_row.role = "user"
        mock_row.content = "This is a test message content that is longer than 100 characters to test the truncation functionality in the display method"
        mock_row.message_created_at = datetime(2024, 1, 10)
        mock_row.conversation_title = "Test Conversation"
        mock_row.conversation_id = "conv1"
        
        mock_result.__iter__ = Mock(return_value=iter([mock_row]))
        self.mock_db.execute.return_value = mock_result
        
        # Test the method
        embeddings = self.manager.get_user_embeddings(1, 10)
        
        # Assertions
        assert len(embeddings) == 1
        assert embeddings[0]['id'] == "emb1"
        assert embeddings[0]['message_id'] == "msg1"
        assert embeddings[0]['message_role'] == "user"
        assert len(embeddings[0]['message_content']) <= 103  # 100 + "..."
        assert "..." in embeddings[0]['message_content']
    
    def test_get_user_embeddings_error(self):
        """Test error handling in get_user_embeddings."""
        # Mock database error
        self.mock_db.execute.side_effect = Exception("Database error")
        
        # Test the method
        embeddings = self.manager.get_user_embeddings(1, 10)
        
        # Should return empty list on error
        assert embeddings == []
    
    def test_format_datetime(self):
        """Test datetime formatting."""
        # Test with valid datetime
        dt = datetime(2024, 1, 15, 14, 30, 45)
        formatted = self.manager.format_datetime(dt)
        assert formatted == "2024-01-15 14:30:45"
        
        # Test with None
        formatted_none = self.manager.format_datetime(None)
        assert formatted_none == "N/A"
    
    def test_clear_user_embeddings_success(self):
        """Test successful clearing of user embeddings."""
        # Mock the delete function
        with patch('embedding_manager.delete_embeddings_by_user') as mock_delete:
            mock_delete.return_value = 5
            
            # Test the method
            count = self.manager.clear_user_embeddings(1)
            
            # Assertions
            assert count == 5
            mock_delete.assert_called_once_with(self.mock_db, 1)
    
    def test_clear_user_embeddings_error(self):
        """Test error handling in clear_user_embeddings."""
        # Mock the delete function to raise an exception
        with patch('embedding_manager.delete_embeddings_by_user') as mock_delete:
            mock_delete.side_effect = Exception("Delete error")
            
            # Test the method
            count = self.manager.clear_user_embeddings(1)
            
            # Should return 0 on error
            assert count == 0
    
    def test_clear_all_embeddings_success(self):
        """Test successful clearing of all embeddings."""
        # Mock database operations
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 10
        self.mock_db.execute.return_value = mock_count_result
        
        # Test the method
        count = self.manager.clear_all_embeddings()
        
        # Assertions
        assert count == 10
        assert self.mock_db.execute.call_count == 2  # Count query + delete query
        self.mock_db.commit.assert_called_once()
    
    def test_clear_all_embeddings_error(self):
        """Test error handling in clear_all_embeddings."""
        # Mock database error
        self.mock_db.execute.side_effect = Exception("Database error")
        
        # Test the method
        count = self.manager.clear_all_embeddings()
        
        # Should return 0 on error
        assert count == 0
        self.mock_db.rollback.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
