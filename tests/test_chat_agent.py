"""
Tests for chat agent components.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from agents.chat import ChatAgent, ConversationManager, ContextBuilder, ResponseGenerator
from agents.shared.models import ResearchResult, SubqueryResult, ChatMessage, Conversation, ChatResponse
from agents.shared.exceptions import AgentError, ConversationError


class TestConversationManager:
    """Test ConversationManager functionality."""
    
    def test_init(self, temp_dir):
        """Test ConversationManager initialization."""
        manager = ConversationManager(persist_directory=temp_dir)
        assert manager.persist_directory == temp_dir
        assert isinstance(manager.conversations, dict)
    
    def test_create_conversation(self, temp_dir):
        """Test conversation creation."""
        manager = ConversationManager(persist_directory=temp_dir)
        conv_id = manager.create_conversation("Test Conversation")
        
        assert isinstance(conv_id, str)
        assert conv_id in manager.conversations
        
        conversation = manager.get_conversation(conv_id)
        assert conversation is not None
        assert conversation.title == "Test Conversation"
        assert len(conversation.messages) == 0
    
    def test_add_message(self, temp_dir):
        """Test adding messages to conversation."""
        manager = ConversationManager(persist_directory=temp_dir)
        conv_id = manager.create_conversation("Test Conversation")
        
        message = manager.add_message(conv_id, "user", "Hello world")
        
        assert message is not None
        assert message.role == "user"
        assert message.content == "Hello world"
        assert isinstance(message.timestamp, datetime)
        
        conversation = manager.get_conversation(conv_id)
        assert len(conversation.messages) == 1
    
    def test_get_conversation_history(self, temp_dir):
        """Test getting conversation history."""
        manager = ConversationManager(persist_directory=temp_dir)
        conv_id = manager.create_conversation("Test Conversation")
        
        # Add multiple messages
        manager.add_message(conv_id, "user", "Message 1")
        manager.add_message(conv_id, "assistant", "Response 1")
        manager.add_message(conv_id, "user", "Message 2")
        
        history = manager.get_conversation_history(conv_id)
        
        assert len(history) == 3
        assert history[0].content == "Message 1"
        assert history[1].content == "Response 1"
        assert history[2].content == "Message 2"
    
    def test_list_conversations(self, temp_dir):
        """Test listing conversations."""
        manager = ConversationManager(persist_directory=temp_dir)
        conv1_id = manager.create_conversation("Conversation 1")
        conv2_id = manager.create_conversation("Conversation 2")
        
        conversations = manager.list_conversations()
        
        assert len(conversations) == 2
        titles = [conv['title'] for conv in conversations]
        assert "Conversation 1" in titles
        assert "Conversation 2" in titles
    
    def test_delete_conversation(self, temp_dir):
        """Test conversation deletion."""
        manager = ConversationManager(persist_directory=temp_dir)
        conv_id = manager.create_conversation("Test Conversation")
        
        # Verify conversation exists
        assert conv_id in manager.conversations
        
        # Delete conversation
        success = manager.delete_conversation(conv_id)
        
        assert success == True
        assert conv_id not in manager.conversations
    
    def test_update_conversation_title(self, temp_dir):
        """Test updating conversation title."""
        manager = ConversationManager(persist_directory=temp_dir)
        conv_id = manager.create_conversation("Original Title")
        
        success = manager.update_conversation_title(conv_id, "New Title")
        
        assert success == True
        conversation = manager.get_conversation(conv_id)
        assert conversation.title == "New Title"
    
    def test_get_conversation_context(self, temp_dir):
        """Test getting conversation context."""
        manager = ConversationManager(persist_directory=temp_dir)
        conv_id = manager.create_conversation("Test Conversation")
        
        # Add messages with metadata
        manager.add_message(conv_id, "user", "What is AI?")
        manager.add_message(conv_id, "assistant", "AI is...", 
                           metadata={"research_result": {"subqueries": [{"subquery": "What is AI?"}]}})
        
        context = manager.get_conversation_context(conv_id)
        
        assert 'conversation_id' in context
        assert 'recent_messages' in context
        assert 'conversation_summary' in context
        assert 'message_count' in context
        assert context['message_count'] == 2


class TestContextBuilder:
    """Test ContextBuilder functionality."""
    
    def test_init(self):
        """Test ContextBuilder initialization."""
        builder = ContextBuilder()
        assert builder is not None
    
    def test_build_research_context(self, sample_conversation):
        """Test building research context from conversation."""
        builder = ContextBuilder()
        
        context = builder.build_research_context(sample_conversation)
        
        assert 'conversation_id' in context
        assert 'recent_context' in context
        assert 'research_topics' in context
        assert 'message_count' in context
        assert 'recent_messages' in context
        
        assert context['message_count'] == 3
        assert 'machine learning' in context['recent_context'].lower()
    
    def test_enhance_question_with_context(self):
        """Test enhancing question with context."""
        builder = ContextBuilder()
        question = "Tell me more about deep learning"
        context = {
            'recent_context': 'Previous discussion about machine learning and neural networks'
        }
        
        enhanced = builder.enhance_question_with_context(question, context)
        
        assert question in enhanced
        assert 'Previous discussion' in enhanced
    
    def test_enhance_question_no_context(self):
        """Test enhancing question without context."""
        builder = ContextBuilder()
        question = "What is AI?"
        context = {}
        
        enhanced = builder.enhance_question_with_context(question, context)
        
        assert enhanced == question
    
    def test_extract_research_topics(self, sample_conversation):
        """Test extracting research topics from conversation."""
        builder = ContextBuilder()
        
        # Add messages with research results
        sample_conversation.add_message("assistant", "Response 1", 
                                       metadata={"research_result": {"subqueries": [{"subquery": "What is machine learning?"}]}})
        sample_conversation.add_message("assistant", "Response 2", 
                                       metadata={"research_result": {"subqueries": [{"subquery": "How does deep learning work?"}]}})
        
        topics = builder.extract_research_topics(sample_conversation)
        
        assert "What is machine learning?" in topics
        assert "How does deep learning work?" in topics
    
    def test_get_conversation_theme(self, sample_conversation):
        """Test getting conversation theme."""
        builder = ContextBuilder()
        
        theme = builder.get_conversation_theme(sample_conversation)
        
        assert theme == "machine learning"


class TestResponseGenerator:
    """Test ResponseGenerator functionality."""
    
    def test_init(self):
        """Test ResponseGenerator initialization."""
        generator = ResponseGenerator()
        assert generator is not None
    
    def test_generate_chat_response(self, sample_research_result):
        """Test generating chat response from research result."""
        generator = ResponseGenerator()
        
        context = {"message_count": 3, "recent_context": "Previous discussion about AI"}
        
        response = generator.generate_chat_response(sample_research_result, context)
        
        assert isinstance(response, str)
        assert "Based on our conversation" in response
        assert "Research Process" in response
        assert "Sources" in response
        assert "explore further" in response
    
    def test_generate_error_response(self):
        """Test generating error response."""
        generator = ResponseGenerator()
        error = "Database connection failed"
        context = {"message_count": 1}
        
        response = generator.generate_error_response(error, context)
        
        assert "apologize" in response.lower()
        assert error in response
        assert "try rephrasing" in response.lower()
    
    def test_generate_greeting_response(self):
        """Test generating greeting response."""
        generator = ResponseGenerator()
        context = {}
        
        response = generator.generate_greeting_response(context)
        
        assert "Hello" in response
        assert "research assistant" in response.lower()
        assert "What would you like to research" in response
    
    def test_generate_follow_up_suggestions(self, sample_research_result):
        """Test generating follow-up suggestions."""
        generator = ResponseGenerator()
        
        suggestions = generator.generate_follow_up_suggestions(sample_research_result)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any("machine learning" in s.lower() for s in suggestions)
    
    def test_format_citations(self):
        """Test formatting citations."""
        generator = ResponseGenerator()
        citations = [
            {"title": "ML Basics", "filename": "ml.txt", "score": 0.9},
            {"title": "AI Guide", "filename": "ai.pdf", "score": 0.8}
        ]
        
        formatted = generator.format_citations(citations, max_citations=2)
        
        assert "Sources consulted" in formatted
        assert "ML Basics" in formatted
        assert "AI Guide" in formatted
        assert "Relevance: 0.90" in formatted
        assert "Relevance: 0.80" in formatted


class TestChatAgent:
    """Test ChatAgent functionality."""
    
    def test_init(self, mock_retriever, mock_llm_client, temp_dir):
        """Test ChatAgent initialization."""
        from agents.research import ResearchAgent
        
        research_agent = ResearchAgent(mock_retriever, mock_llm_client, use_llm=True)
        conversation_manager = ConversationManager(persist_directory=temp_dir)
        chat_agent = ChatAgent(research_agent, conversation_manager)
        
        assert chat_agent.research_agent == research_agent
        assert chat_agent.conversation_manager == conversation_manager
        assert isinstance(chat_agent.context_builder, ContextBuilder)
        assert isinstance(chat_agent.response_generator, ResponseGenerator)
    
    def test_process_new_conversation(self, mock_retriever, mock_llm_client, temp_dir):
        """Test processing message in new conversation."""
        from agents.research import ResearchAgent
        
        research_agent = ResearchAgent(mock_retriever, mock_llm_client, use_llm=True)
        conversation_manager = ConversationManager(persist_directory=temp_dir)
        chat_agent = ChatAgent(research_agent, conversation_manager)
        
        # Mock research result
        mock_research_result = ResearchResult(
            question="Test question",
            answer="Test answer",
            subqueries=[],
            citations=[],
            total_documents=0
        )
        
        with patch.object(research_agent, 'process', return_value=mock_research_result):
            response = chat_agent.process("Test question")
        
        assert isinstance(response, ChatResponse)
        assert response.conversation_id is not None
        assert response.answer is not None
    
    def test_process_existing_conversation(self, mock_retriever, mock_llm_client, temp_dir):
        """Test processing message in existing conversation."""
        from agents.research import ResearchAgent
        
        research_agent = ResearchAgent(mock_retriever, mock_llm_client, use_llm=True)
        conversation_manager = ConversationManager(persist_directory=temp_dir)
        chat_agent = ChatAgent(research_agent, conversation_manager)
        
        # Create conversation first
        conv_id = chat_agent.create_conversation("Test Conversation")
        
        # Mock research result
        mock_research_result = ResearchResult(
            question="Test question",
            answer="Test answer",
            subqueries=[],
            citations=[],
            total_documents=0
        )
        
        with patch.object(research_agent, 'process', return_value=mock_research_result):
            response = chat_agent.process("Test question", conversation_id=conv_id)
        
        assert response.conversation_id == conv_id
    
    def test_process_error_handling(self, mock_retriever, mock_llm_client, temp_dir):
        """Test error handling in message processing."""
        from agents.research import ResearchAgent
        
        research_agent = ResearchAgent(mock_retriever, mock_llm_client, use_llm=True)
        conversation_manager = ConversationManager(persist_directory=temp_dir)
        chat_agent = ChatAgent(research_agent, conversation_manager)
        
        # Mock research error
        with patch.object(research_agent, 'process', side_effect=Exception("Research error")):
            response = chat_agent.process("Test question")
        
        assert isinstance(response, ChatResponse)
        assert "error" in response.answer.lower()
        assert response.error is not None
    
    def test_chat_ask_legacy_method(self, mock_retriever, mock_llm_client, temp_dir):
        """Test legacy chat_ask method."""
        from agents.research import ResearchAgent
        
        research_agent = ResearchAgent(mock_retriever, mock_llm_client, use_llm=True)
        conversation_manager = ConversationManager(persist_directory=temp_dir)
        chat_agent = ChatAgent(research_agent, conversation_manager)
        
        # Mock the process method
        mock_response = ChatResponse(
            conversation_id="test-conv",
            message_id="msg-id",
            answer="Test answer",
            conversation_title="Test Conversation",
            message_count=1,
            context_used=False,
            timestamp=datetime.now().isoformat()
        )
        
        with patch.object(chat_agent, 'process', return_value=mock_response):
            result = chat_agent.chat_ask("Test question")
        
        assert isinstance(result, dict)
        assert 'conversation_id' in result
        assert 'answer' in result
        assert 'research_result' in result
    
    def test_get_conversation_history(self, mock_retriever, mock_llm_client, temp_dir):
        """Test getting conversation history."""
        from agents.research import ResearchAgent
        
        research_agent = ResearchAgent(mock_retriever, mock_llm_client, use_llm=True)
        conversation_manager = ConversationManager(persist_directory=temp_dir)
        chat_agent = ChatAgent(research_agent, conversation_manager)
        
        conv_id = "test-conv"
        mock_messages = [Mock(), Mock()]
        conversation_manager.get_conversation_history.return_value = mock_messages
        
        # Mock message to_dict method
        for msg in mock_messages:
            msg.to_dict.return_value = {"id": "msg-id", "content": "test"}
        
        history = chat_agent.get_conversation_history(conv_id)
        
        assert len(history) == 2
        conversation_manager.get_conversation_history.assert_called_once_with(conv_id, 50)
    
    def test_list_conversations(self, mock_retriever, mock_llm_client, temp_dir):
        """Test listing conversations."""
        from agents.research import ResearchAgent
        
        research_agent = ResearchAgent(mock_retriever, mock_llm_client, use_llm=True)
        conversation_manager = ConversationManager(persist_directory=temp_dir)
        chat_agent = ChatAgent(research_agent, conversation_manager)
        
        mock_conversations = [{"id": "conv1", "title": "Conv 1"}]
        conversation_manager.list_conversations.return_value = mock_conversations
        
        conversations = chat_agent.list_conversations()
        
        assert conversations == mock_conversations
        conversation_manager.list_conversations.assert_called_once()
    
    def test_create_conversation(self, mock_retriever, mock_llm_client, temp_dir):
        """Test creating conversation."""
        from agents.research import ResearchAgent
        
        research_agent = ResearchAgent(mock_retriever, mock_llm_client, use_llm=True)
        conversation_manager = ConversationManager(persist_directory=temp_dir)
        chat_agent = ChatAgent(research_agent, conversation_manager)
        
        conv_id = "new-conv-id"
        conversation_manager.create_conversation.return_value = conv_id
        
        result = chat_agent.create_conversation("New Conversation")
        
        assert result == conv_id
        conversation_manager.create_conversation.assert_called_once_with("New Conversation")
    
    def test_delete_conversation(self, mock_retriever, mock_llm_client, temp_dir):
        """Test deleting conversation."""
        from agents.research import ResearchAgent
        
        research_agent = ResearchAgent(mock_retriever, mock_llm_client, use_llm=True)
        conversation_manager = ConversationManager(persist_directory=temp_dir)
        chat_agent = ChatAgent(research_agent, conversation_manager)
        
        conv_id = "conv-to-delete"
        conversation_manager.delete_conversation.return_value = True
        
        result = chat_agent.delete_conversation(conv_id)
        
        assert result == True
        conversation_manager.delete_conversation.assert_called_once_with(conv_id)
    
    def test_update_conversation_title(self, mock_retriever, mock_llm_client, temp_dir):
        """Test updating conversation title."""
        from agents.research import ResearchAgent
        
        research_agent = ResearchAgent(mock_retriever, mock_llm_client, use_llm=True)
        conversation_manager = ConversationManager(persist_directory=temp_dir)
        chat_agent = ChatAgent(research_agent, conversation_manager)
        
        conv_id = "conv-to-update"
        conversation_manager.update_conversation_title.return_value = True
        
        result = chat_agent.update_conversation_title(conv_id, "New Title")
        
        assert result == True
        conversation_manager.update_conversation_title.assert_called_once_with(conv_id, "New Title")
