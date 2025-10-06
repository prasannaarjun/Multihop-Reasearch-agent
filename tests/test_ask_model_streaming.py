"""
Test for ask model functionality with streaming endpoints.
"""
import pytest
import json
from unittest.mock import Mock, patch
from frontend.src.services.apiService import ApiService


class TestAskModelStreaming:
    """Test ask model functionality with streaming."""
    
    def test_send_chat_message_streaming_with_ask_model(self):
        """Test that sendChatMessageStreaming includes selected_text when askModel is provided."""
        api_service = ApiService()
        
        # Mock the fetch function
        with patch('frontend.src.services.apiService.fetch') as mock_fetch:
            # Mock successful response
            mock_response = Mock()
            mock_response.ok = True
            mock_response.body = Mock()
            mock_response.body.getReader = Mock()
            
            # Mock reader
            mock_reader = Mock()
            mock_reader.read = Mock(return_value=Mock(done=True, value=b''))
            mock_response.body.getReader.return_value = mock_reader
            
            mock_fetch.return_value = mock_response
            
            # Test with askModel parameter
            api_service.sendChatMessageStreaming(
                message="Test question",
                conversationId="test-conv-123",
                perSubK=3,
                includeContext=True,
                askModel="Selected text to ask about",
                onChunk=None,
                onComplete=None,
                onError=None
            )
            
            # Verify the request body includes selected_text
            call_args = mock_fetch.call_args
            request_body = json.loads(call_args[1]['body'])
            
            assert request_body['message'] == "Test question"
            assert request_body['conversation_id'] == "test-conv-123"
            assert request_body['per_sub_k'] == 3
            assert request_body['include_context'] == True
            assert request_body['selected_text'] == "Selected text to ask about"
    
    def test_send_chat_message_streaming_without_ask_model(self):
        """Test that sendChatMessageStreaming works without askModel parameter."""
        api_service = ApiService()
        
        # Mock the fetch function
        with patch('frontend.src.services.apiService.fetch') as mock_fetch:
            # Mock successful response
            mock_response = Mock()
            mock_response.ok = True
            mock_response.body = Mock()
            mock_response.body.getReader = Mock()
            
            # Mock reader
            mock_reader = Mock()
            mock_reader.read = Mock(return_value=Mock(done=True, value=b''))
            mock_response.body.getReader.return_value = mock_reader
            
            mock_fetch.return_value = mock_response
            
            # Test without askModel parameter
            api_service.sendChatMessageStreaming(
                message="Test question",
                conversationId="test-conv-123",
                perSubK=3,
                includeContext=True,
                onChunk=None,
                onComplete=None,
                onError=None
            )
            
            # Verify the request body does not include selected_text
            call_args = mock_fetch.call_args
            request_body = json.loads(call_args[1]['body'])
            
            assert request_body['message'] == "Test question"
            assert request_body['conversation_id'] == "test-conv-123"
            assert request_body['per_sub_k'] == 3
            assert request_body['include_context'] == True
            assert 'selected_text' not in request_body


if __name__ == "__main__":
    pytest.main([__file__])
