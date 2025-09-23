"""
Chat Agent for Multi-hop Research
Main chat agent that orchestrates chat functionality with research capabilities.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from ..shared.interfaces import IAgent
from ..shared.models import ResearchResult, ChatResponse, ChatMessage
from ..shared.exceptions import AgentError, ConversationError
from .conversation_manager import ConversationManager
from .context_builder import ContextBuilder
from .response_generator import ResponseGenerator


class ChatAgent(IAgent):
    """
    Chat agent that extends research capabilities with conversation management.
    """
    
    def __init__(self, research_agent, conversation_manager: ConversationManager = None):
        """
        Initialize chat agent.
        
        Args:
            research_agent: Research agent instance
            conversation_manager: Conversation manager instance
        """
        self.research_agent = research_agent
        self.conversation_manager = conversation_manager or ConversationManager()
        self.context_builder = ContextBuilder()
        self.response_generator = ResponseGenerator()
    
    def process(self, message: str, conversation_id: Optional[str] = None, 
                per_sub_k: int = 3, include_context: bool = True) -> ChatResponse:
        """
        Process a chat message and return a response.
        
        Args:
            message: User's message
            conversation_id: ID of the conversation (creates new if None)
            per_sub_k: Number of documents per subquery
            include_context: Whether to include conversation context
            
        Returns:
            ChatResponse with answer and conversation info
        """
        try:
            # Get or create conversation
            if not conversation_id:
                conversation_id = self.conversation_manager.create_conversation(
                    title=message[:50] + "..." if len(message) > 50 else message
                )
            
            conversation = self.conversation_manager.get_conversation(conversation_id)
            if not conversation:
                raise ConversationError(f"Conversation {conversation_id} not found")
            
            # Add user message to conversation
            user_message = self.conversation_manager.add_message(
                conversation_id, 
                "user", 
                message,
                metadata={"per_sub_k": per_sub_k}
            )
            
            # Build context for research
            research_context = {}
            if include_context:
                research_context = self.context_builder.build_research_context(conversation)
            
            # Perform research with context
            try:
                # Enhance question with context if available
                enhanced_question = self.context_builder.enhance_question_with_context(
                    message, research_context
                )
                
                # Get research results
                research_result = self.research_agent.process(enhanced_question, per_sub_k=per_sub_k)
                
                # Generate chat response
                chat_response = self.response_generator.generate_chat_response(
                    research_result, research_context
                )
                
                # Add assistant message to conversation
                assistant_message = self.conversation_manager.add_message(
                    conversation_id,
                    "assistant",
                    chat_response,
                    metadata={
                        "research_result": research_result.to_dict(),
                        "subqueries": [sq.__dict__ for sq in research_result.subqueries],
                        "citations_count": len(research_result.citations),
                        "total_documents": research_result.total_documents
                    }
                )
                
                return ChatResponse(
                    conversation_id=conversation_id,
                    message_id=assistant_message.id,
                    answer=chat_response,
                    conversation_title=conversation.title,
                    message_count=len(conversation.messages),
                    context_used=bool(research_context.get('recent_messages')),
                    timestamp=assistant_message.timestamp.isoformat(),
                    research_result=research_result
                )
                
            except Exception as e:
                # Add error message to conversation
                error_message = f"I encountered an error while researching your question: {str(e)}"
                self.conversation_manager.add_message(
                    conversation_id,
                    "assistant",
                    error_message,
                    metadata={"error": str(e), "error_type": type(e).__name__}
                )
                
                return ChatResponse(
                    conversation_id=conversation_id,
                    message_id="error",
                    answer=error_message,
                    conversation_title=conversation.title,
                    message_count=len(conversation.messages),
                    context_used=False,
                    timestamp=datetime.now().isoformat(),
                    error=str(e)
                )
                
        except Exception as e:
            raise AgentError(f"Failed to process chat message: {str(e)}")
    
    def chat_ask(self, question: str, conversation_id: Optional[str] = None, 
                 per_sub_k: int = 3, include_context: bool = True) -> Dict[str, Any]:
        """
        Ask a question in a chat context with conversation history.
        Legacy method for backward compatibility.
        
        Args:
            question: The user's question
            conversation_id: ID of the conversation (creates new if None)
            per_sub_k: Number of documents per subquery
            include_context: Whether to include conversation context
            
        Returns:
            Dictionary with answer, conversation info, and metadata
        """
        response = self.process(question, conversation_id, per_sub_k, include_context)
        
        # Convert to legacy format
        return {
            "conversation_id": response.conversation_id,
            "question": question,
            "answer": response.answer,
            "research_result": response.research_result.to_dict() if response.research_result else None,
            "message_id": response.message_id,
            "conversation_title": response.conversation_title,
            "message_count": response.message_count,
            "context_used": response.context_used,
            "timestamp": response.timestamp,
            "error": response.error
        }
    
    def get_conversation_history(self, conversation_id: str, max_messages: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history."""
        messages = self.conversation_manager.get_conversation_history(conversation_id, max_messages)
        return [msg.to_dict() for msg in messages]
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all conversations."""
        return self.conversation_manager.list_conversations()
    
    def create_conversation(self, title: str = "New Conversation") -> str:
        """Create a new conversation."""
        return self.conversation_manager.create_conversation(title)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        return self.conversation_manager.delete_conversation(conversation_id)
    
    def update_conversation_title(self, conversation_id: str, title: str) -> bool:
        """Update conversation title."""
        return self.conversation_manager.update_conversation_title(conversation_id, title)
    
    def get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation context."""
        conversation = self.conversation_manager.get_conversation(conversation_id)
        if not conversation:
            return {}
        
        return self.context_builder.build_research_context(conversation)
    
    def generate_follow_up_suggestions(self, conversation_id: str) -> List[str]:
        """Generate follow-up question suggestions for a conversation."""
        conversation = self.conversation_manager.get_conversation(conversation_id)
        if not conversation or not conversation.messages:
            return []
        
        # Get the last assistant message with research result
        for msg in reversed(conversation.messages):
            if msg.role == "assistant" and msg.metadata and "research_result" in msg.metadata:
                research_data = msg.metadata["research_result"]
                # Convert back to ResearchResult object
                research_result = ResearchResult(**research_data)
                return self.response_generator.generate_follow_up_suggestions(research_result)
        
        return []


if __name__ == "__main__":
    # Test the chat agent
    from ..research.research_agent import ResearchAgent
    from ..research.document_retriever import DocumentRetriever
    from embeddings import load_index
    from ollama_client import OllamaClient
    
    print("Testing Chat Agent")
    print("=" * 50)
    
    try:
        # Initialize research agent
        collection, model = load_index("chroma_db")
        retriever = DocumentRetriever(collection, model)
        llm_client = OllamaClient()
        research_agent = ResearchAgent(retriever, llm_client)
        
        # Create chat agent
        chat_agent = ChatAgent(research_agent)
        
        # Test chat functionality
        conv_id = chat_agent.create_conversation("Test Chat")
        print(f"Created conversation: {conv_id}")
        
        # Test chat ask
        response = chat_agent.chat_ask("What is machine learning?", conv_id)
        print(f"Response: {response['answer'][:200]}...")
        
        # Test follow-up
        response2 = chat_agent.chat_ask("How does it work in healthcare?", conv_id)
        print(f"Follow-up response: {response2['answer'][:200]}...")
        
        # Test conversation history
        history = chat_agent.get_conversation_history(conv_id)
        print(f"Conversation has {len(history)} messages")
        
        print("Test completed!")
        
    except Exception as e:
        print(f"Error: {e}")
