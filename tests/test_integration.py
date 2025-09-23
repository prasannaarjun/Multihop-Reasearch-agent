"""
Integration tests for the modular agent system.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from agents.research import ResearchAgent, DocumentRetriever, QueryPlanner, AnswerSynthesizer
from agents.chat import ChatAgent, ConversationManager, ContextBuilder, ResponseGenerator
from agents.shared.models import ResearchResult, SubqueryResult, ChatMessage, Conversation, ChatResponse
from agents.shared.exceptions import AgentError


class TestModularIntegration:
    """Test integration between modular components."""
    
    @pytest.fixture
    def setup_integration(self, temp_dir, mock_retriever, mock_llm_client):
        """Set up integration test fixtures."""
        # Mock retriever
        mock_retriever.retrieve.return_value = [
            {
                'title': 'Test Document',
                'full_text': 'This is a test document about machine learning.',
                'score': 0.9,
                'filename': 'test.txt'
            }
        ]
        
        # Mock LLM client
        mock_llm_client.is_available.return_value = True
        mock_llm_client.generate_subqueries.return_value = [
            'What is machine learning?',
            'How does machine learning work?'
        ]
        mock_llm_client.generate_text.return_value = "Machine learning is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed."
        
        # Initialize research agent
        research_agent = ResearchAgent(
            mock_retriever, 
            mock_llm_client, 
            use_llm=True
        )
        
        # Initialize chat agent
        conversation_manager = ConversationManager(persist_directory=temp_dir)
        chat_agent = ChatAgent(research_agent, conversation_manager)
        
        return {
            'research_agent': research_agent,
            'chat_agent': chat_agent,
            'conversation_manager': conversation_manager,
            'mock_retriever': mock_retriever,
            'mock_llm_client': mock_llm_client
        }
    
    def test_research_agent_integration(self, setup_integration):
        """Test research agent with all components integrated."""
        research_agent = setup_integration['research_agent']
        mock_retriever = setup_integration['mock_retriever']
        mock_llm_client = setup_integration['mock_llm_client']
        
        # Test research processing
        result = research_agent.process("What is machine learning?", per_sub_k=1)
        
        assert isinstance(result, ResearchResult)
        assert result.question == "What is machine learning?"
        assert isinstance(result.answer, str)
        assert len(result.subqueries) == 2
        assert result.total_documents > 0
        assert result.processing_time > 0
        
        # Verify subqueries were generated
        subquery_texts = [sq.subquery for sq in result.subqueries]
        assert "What is machine learning?" in subquery_texts
        assert "How does machine learning work?" in subquery_texts
        
        # Verify documents were retrieved
        assert mock_retriever.retrieve.called
        
        # Verify LLM was used for subquery generation
        mock_llm_client.generate_subqueries.assert_called_once()
    
    def test_chat_agent_integration(self, setup_integration):
        """Test chat agent with research agent integration."""
        chat_agent = setup_integration['chat_agent']
        mock_retriever = setup_integration['mock_retriever']
        
        # Test chat processing
        response = chat_agent.process("What is machine learning?")
        
        assert isinstance(response, ChatResponse)
        assert hasattr(response, 'conversation_id')
        assert hasattr(response, 'answer')
        assert hasattr(response, 'research_result')
        
        # Verify conversation was created
        assert response.conversation_id is not None
        
        # Verify research was performed
        assert mock_retriever.retrieve.called
    
    def test_conversation_context_integration(self, setup_integration):
        """Test conversation context building and usage."""
        chat_agent = setup_integration['chat_agent']
        conversation_manager = setup_integration['conversation_manager']
        mock_retriever = setup_integration['mock_retriever']
        
        # Create a conversation with history
        conv_id = chat_agent.create_conversation("Test Conversation")
        
        # Add some messages
        conversation_manager.add_message(conv_id, "user", "What is AI?")
        conversation_manager.add_message(conv_id, "assistant", "AI is...")
        
        # Process a follow-up question
        response = chat_agent.process("Tell me more about machine learning", conversation_id=conv_id)
        
        assert isinstance(response, ChatResponse)
        assert response.conversation_id == conv_id
        
        # Verify context was used
        assert mock_retriever.retrieve.called
    
    def test_error_handling_integration(self, setup_integration):
        """Test error handling across components."""
        research_agent = setup_integration['research_agent']
        chat_agent = setup_integration['chat_agent']
        mock_retriever = setup_integration['mock_retriever']
        
        # Mock retriever to raise error
        mock_retriever.retrieve.side_effect = Exception("Retrieval error")
        
        # Test research agent error handling - it should handle errors gracefully
        result = research_agent.process("Test question")
        
        assert isinstance(result, ResearchResult)
        assert not result.subqueries[0].success  # First subquery should fail
        assert "error" in result.subqueries[0].error.lower()
        
        # Test chat agent error handling
        response = chat_agent.process("Test question")
        
        assert isinstance(response, ChatResponse)
        # Check that the response indicates some kind of error or limitation
        response_lower = response.answer.lower()
        assert any(keyword in response_lower for keyword in ["error", "couldn't", "could not", "apologize", "encountered"])
    
    def test_llm_fallback_integration(self, setup_integration):
        """Test fallback when LLM is not available."""
        mock_retriever = setup_integration['mock_retriever']
        mock_llm_client = setup_integration['mock_llm_client']
        
        # Mock LLM as unavailable
        mock_llm_client.is_available.return_value = False
        
        # Create research agent with LLM fallback
        research_agent_no_llm = ResearchAgent(
            mock_retriever,
            mock_llm_client,
            use_llm=True
        )
        
        # Test processing
        result = research_agent_no_llm.process("What is machine learning?")
        
        assert isinstance(result, ResearchResult)
        assert isinstance(result.answer, str)
        
        # Verify rule-based subquery generation was used
        mock_llm_client.generate_subqueries.assert_not_called()
    
    def test_conversation_management_integration(self, setup_integration):
        """Test conversation management with chat agent."""
        chat_agent = setup_integration['chat_agent']
        
        # Create conversation
        conv_id = chat_agent.create_conversation("Test Conversation")
        
        # Add messages
        chat_agent.conversation_manager.add_message(conv_id, "user", "Hello")
        chat_agent.conversation_manager.add_message(conv_id, "assistant", "Hi there!")
        
        # Test conversation history
        history = chat_agent.get_conversation_history(conv_id)
        assert len(history) == 2
        
        # Test conversation listing
        conversations = chat_agent.list_conversations()
        assert len(conversations) == 1
        assert conversations[0]["title"] == "Test Conversation"
        
        # Test conversation deletion
        success = chat_agent.delete_conversation(conv_id)
        assert success == True
        
        # Verify conversation is deleted
        conversations = chat_agent.list_conversations()
        assert len(conversations) == 0
    
    def test_response_generation_integration(self, setup_integration):
        """Test response generation with research results."""
        chat_agent = setup_integration['chat_agent']
        
        # Create test research result
        subquery_results = [
            SubqueryResult(
                subquery="What is machine learning?",
                summary="ML is a subset of AI that enables computers to learn from data.",
                documents=[],
                success=True
            )
        ]
        
        research_result = ResearchResult(
            question="What is machine learning?",
            answer="Machine learning is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed.",
            subqueries=subquery_results,
            citations=[{"title": "ML Basics", "filename": "ml.txt", "score": 0.9}],
            total_documents=1
        )
        
        # Test response generation
        context = {"message_count": 1, "recent_context": ""}
        response = chat_agent.response_generator.generate_chat_response(research_result, context)
        
        assert isinstance(response, str)
        assert "machine learning" in response.lower()
        assert "Research Process" in response
        assert "Sources" in response
    
    def test_context_building_integration(self, setup_integration):
        """Test context building with conversation history."""
        chat_agent = setup_integration['chat_agent']
        
        # Create conversation with research history
        conv_id = chat_agent.create_conversation("ML Discussion")
        
        # Add messages with research metadata
        chat_agent.conversation_manager.add_message(
            conv_id, 
            "assistant", 
            "ML is a subset of AI...",
            metadata={
                "research_result": {
                    "subqueries": [
                        {"subquery": "What is machine learning?"},
                        {"subquery": "How does ML work?"}
                    ]
                }
            }
        )
        
        # Test context building
        conversation = chat_agent.conversation_manager.get_conversation(conv_id)
        context = chat_agent.context_builder.build_research_context(conversation)
        
        assert "conversation_id" in context
        assert "recent_context" in context
        assert "research_topics" in context
        assert "machine learning" in context["research_topics"][0].lower()
    
    def test_full_workflow_integration(self, setup_integration):
        """Test complete workflow from question to response."""
        chat_agent = setup_integration['chat_agent']
        mock_retriever = setup_integration['mock_retriever']
        
        # Create conversation
        conv_id = chat_agent.create_conversation("Full Workflow Test")
        
        # Process initial question
        response1 = chat_agent.process("What is machine learning?", conversation_id=conv_id)
        
        assert isinstance(response1, ChatResponse)
        assert "machine learning" in response1.answer.lower()
        
        # Process follow-up question
        response2 = chat_agent.process("How is it used in healthcare?", conversation_id=conv_id)
        
        assert isinstance(response2, ChatResponse)
        assert "healthcare" in response2.answer.lower()
        
        # Verify conversation history
        history = chat_agent.get_conversation_history(conv_id)
        assert len(history) == 4  # 2 user messages + 2 assistant responses
        
        # Verify research was performed for both questions
        assert mock_retriever.retrieve.call_count >= 2
    
    def test_performance_integration(self, setup_integration):
        """Test performance characteristics of integrated system."""
        import time
        
        research_agent = setup_integration['research_agent']
        
        # Test processing time
        start_time = time.time()
        result = research_agent.process("What is artificial intelligence?", per_sub_k=1)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        assert isinstance(result, ResearchResult)
        # Processing time might be 0 for very fast operations, so check it's not negative
        assert result.processing_time >= 0
        assert processing_time < 10  # Should complete within 10 seconds
        
        # Test memory usage (basic check)
        assert isinstance(result.answer, str)
        assert len(result.answer) > 0

