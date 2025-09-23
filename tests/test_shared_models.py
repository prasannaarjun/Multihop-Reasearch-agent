"""
Tests for shared data models.
"""

import pytest
from datetime import datetime
from agents.shared.models import (
    ChatMessage, Conversation, ResearchResult, SubqueryResult, 
    ConversationInfo, ChatResponse, MessageRole
)


class TestChatMessage:
    """Test ChatMessage model."""
    
    def test_chat_message_creation(self):
        """Test creating a ChatMessage."""
        timestamp = datetime.now()
        message = ChatMessage(
            id="msg-1",
            role="user",
            content="Hello world",
            timestamp=timestamp,
            metadata={"test": "value"}
        )
        
        assert message.id == "msg-1"
        assert message.role == "user"
        assert message.content == "Hello world"
        assert message.timestamp == timestamp
        assert message.metadata["test"] == "value"
    
    def test_chat_message_to_dict(self):
        """Test converting ChatMessage to dictionary."""
        timestamp = datetime.now()
        message = ChatMessage(
            id="msg-1",
            role="user",
            content="Hello world",
            timestamp=timestamp
        )
        
        data = message.to_dict()
        
        assert isinstance(data, dict)
        assert data["id"] == "msg-1"
        assert data["role"] == "user"
        assert data["content"] == "Hello world"
        assert data["timestamp"] == timestamp.isoformat()
    
    def test_chat_message_from_dict(self):
        """Test creating ChatMessage from dictionary."""
        timestamp = datetime.now()
        data = {
            "id": "msg-1",
            "role": "user",
            "content": "Hello world",
            "timestamp": timestamp.isoformat()
        }
        
        message = ChatMessage.from_dict(data)
        
        assert message.id == "msg-1"
        assert message.role == "user"
        assert message.content == "Hello world"
        assert message.timestamp == timestamp


class TestConversation:
    """Test Conversation model."""
    
    def test_conversation_creation(self):
        """Test creating a Conversation."""
        now = datetime.now()
        conversation = Conversation(
            id="conv-1",
            title="Test Conversation",
            created_at=now,
            updated_at=now,
            messages=[],
            context={}
        )
        
        assert conversation.id == "conv-1"
        assert conversation.title == "Test Conversation"
        assert conversation.created_at == now
        assert conversation.updated_at == now
        assert len(conversation.messages) == 0
        assert conversation.is_active == True
    
    def test_add_message(self):
        """Test adding a message to conversation."""
        now = datetime.now()
        conversation = Conversation(
            id="conv-1",
            title="Test Conversation",
            created_at=now,
            updated_at=now,
            messages=[],
            context={}
        )
        
        message = conversation.add_message("user", "Hello", {"test": "value"})
        
        assert isinstance(message, ChatMessage)
        assert message.role == "user"
        assert message.content == "Hello"
        assert message.metadata["test"] == "value"
        assert len(conversation.messages) == 1
        assert conversation.updated_at >= message.timestamp
    
    def test_get_recent_context(self):
        """Test getting recent context."""
        conversation = Conversation(
            id="conv-1",
            title="Test Conversation",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            messages=[],
            context={}
        )
        
        # Add multiple messages
        conversation.add_message("user", "Message 1")
        conversation.add_message("assistant", "Response 1")
        conversation.add_message("user", "Message 2")
        conversation.add_message("assistant", "Response 2")
        conversation.add_message("user", "Message 3")
        
        # Test getting recent context
        recent = conversation.get_recent_context(max_messages=3)
        assert len(recent) == 3
        assert recent[0].content == "Message 2"
        assert recent[1].content == "Response 2"
        assert recent[2].content == "Message 3"
    
    def test_get_conversation_summary(self):
        """Test getting conversation summary."""
        conversation = Conversation(
            id="conv-1",
            title="Test Conversation",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            messages=[],
            context={}
        )
        
        # Test empty conversation
        summary = conversation.get_conversation_summary()
        assert summary == "No messages yet."
        
        # Add user messages
        conversation.add_message("user", "What is machine learning?")
        conversation.add_message("assistant", "ML is a subset of AI...")
        conversation.add_message("user", "How does it work?")
        
        summary = conversation.get_conversation_summary()
        assert "machine learning" in summary.lower()
        assert "conversation with 2 user messages and 1 assistant responses" in summary.lower()
    
    def test_conversation_to_dict(self):
        """Test converting Conversation to dictionary."""
        now = datetime.now()
        conversation = Conversation(
            id="conv-1",
            title="Test Conversation",
            created_at=now,
            updated_at=now,
            messages=[],
            context={}
        )
        
        data = conversation.to_dict()
        
        assert isinstance(data, dict)
        assert data["id"] == "conv-1"
        assert data["title"] == "Test Conversation"
        assert data["created_at"] == now.isoformat()
        assert data["updated_at"] == now.isoformat()
        assert isinstance(data["messages"], list)


class TestResearchResult:
    """Test ResearchResult model."""
    
    def test_research_result_creation(self):
        """Test creating a ResearchResult."""
        subqueries = [
            SubqueryResult(
                subquery="What is ML?",
                summary="ML is a subset of AI.",
                documents=[],
                success=True
            )
        ]
        
        result = ResearchResult(
            question="What is machine learning?",
            answer="Machine learning is a subset of AI.",
            subqueries=subqueries,
            citations=[{"title": "ML Guide", "score": 0.9}],
            total_documents=1,
            processing_time=1.5,
            metadata={"test": "value"}
        )
        
        assert result.question == "What is machine learning?"
        assert result.answer == "Machine learning is a subset of AI."
        assert len(result.subqueries) == 1
        assert len(result.citations) == 1
        assert result.total_documents == 1
        assert result.processing_time == 1.5
        assert result.metadata["test"] == "value"
    
    def test_research_result_to_dict(self):
        """Test converting ResearchResult to dictionary."""
        subqueries = [
            SubqueryResult(
                subquery="What is ML?",
                summary="ML is a subset of AI.",
                documents=[],
                success=True
            )
        ]
        
        result = ResearchResult(
            question="What is machine learning?",
            answer="Machine learning is a subset of AI.",
            subqueries=subqueries,
            citations=[],
            total_documents=0
        )
        
        data = result.to_dict()
        
        assert isinstance(data, dict)
        assert data["question"] == "What is machine learning?"
        assert data["answer"] == "Machine learning is a subset of AI."
        assert len(data["subqueries"]) == 1
        assert data["total_documents"] == 0


class TestSubqueryResult:
    """Test SubqueryResult model."""
    
    def test_subquery_result_creation(self):
        """Test creating a SubqueryResult."""
        result = SubqueryResult(
            subquery="What is ML?",
            summary="ML is a subset of AI.",
            documents=[{"title": "ML Guide"}],
            success=True,
            error=None
        )
        
        assert result.subquery == "What is ML?"
        assert result.summary == "ML is a subset of AI."
        assert len(result.documents) == 1
        assert result.success == True
        assert result.error is None
    
    def test_subquery_result_with_error(self):
        """Test creating a SubqueryResult with error."""
        result = SubqueryResult(
            subquery="What is ML?",
            summary="",
            documents=[],
            success=False,
            error="No documents found"
        )
        
        assert result.subquery == "What is ML?"
        assert result.summary == ""
        assert len(result.documents) == 0
        assert result.success == False
        assert result.error == "No documents found"


class TestMessageRole:
    """Test MessageRole enum."""
    
    def test_message_role_values(self):
        """Test MessageRole enum values."""
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"


class TestConversationInfo:
    """Test ConversationInfo model."""
    
    def test_conversation_info_creation(self):
        """Test creating a ConversationInfo."""
        now = datetime.now()
        info = ConversationInfo(
            id="conv-1",
            title="Test Conversation",
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            message_count=5,
            is_active=True
        )
        
        assert info.id == "conv-1"
        assert info.title == "Test Conversation"
        assert info.message_count == 5
        assert info.is_active == True
    
    def test_conversation_info_attributes(self):
        """Test ConversationInfo attributes."""
        now = datetime.now()
        info = ConversationInfo(
            id="conv-1",
            title="Test Conversation",
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            message_count=5,
            is_active=True
        )
        
        assert info.id == "conv-1"
        assert info.title == "Test Conversation"
        assert info.message_count == 5
        assert info.is_active == True
        assert info.created_at == now.isoformat()
        assert info.updated_at == now.isoformat()


class TestChatResponse:
    """Test ChatResponse model."""
    
    def test_chat_response_creation(self):
        """Test creating a ChatResponse."""
        now = datetime.now()
        response = ChatResponse(
            conversation_id="conv-1",
            message_id="msg-1",
            answer="Test answer",
            conversation_title="Test Conversation",
            message_count=1,
            context_used=False,
            timestamp=now.isoformat()
        )
        
        assert response.conversation_id == "conv-1"
        assert response.message_id == "msg-1"
        assert response.answer == "Test answer"
        assert response.conversation_title == "Test Conversation"
        assert response.message_count == 1
        assert response.context_used == False
        assert response.timestamp == now.isoformat()
    
    def test_chat_response_attributes(self):
        """Test ChatResponse attributes."""
        now = datetime.now()
        response = ChatResponse(
            conversation_id="conv-1",
            message_id="msg-1",
            answer="Test answer",
            conversation_title="Test Conversation",
            message_count=1,
            context_used=False,
            timestamp=now.isoformat()
        )
        
        assert response.conversation_id == "conv-1"
        assert response.message_id == "msg-1"
        assert response.answer == "Test answer"
        assert response.conversation_title == "Test Conversation"
        assert response.message_count == 1
        assert response.context_used == False
        assert response.timestamp == now.isoformat()
        assert response.research_result is None
        assert response.error is None
