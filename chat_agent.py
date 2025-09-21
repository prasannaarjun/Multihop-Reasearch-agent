"""
Chat-enhanced Research Agent
Extends the base research agent with conversation capabilities.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from agent import ResearchAgent
from chat_manager import chat_manager, Conversation
import json


class ChatResearchAgent(ResearchAgent):
    """Research agent with chat capabilities."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_manager = chat_manager
    
    def chat_ask(self, question: str, conversation_id: Optional[str] = None, 
                 per_sub_k: int = 3, include_context: bool = True) -> Dict[str, Any]:
        """
        Ask a question in a chat context with conversation history.
        
        Args:
            question: The user's question
            conversation_id: ID of the conversation (creates new if None)
            per_sub_k: Number of documents per subquery
            include_context: Whether to include conversation context
            
        Returns:
            Dictionary with answer, conversation info, and metadata
        """
        # Get or create conversation
        if not conversation_id:
            conversation_id = self.chat_manager.create_conversation(
                title=question[:50] + "..." if len(question) > 50 else question
            )
        
        conversation = self.chat_manager.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Add user message to conversation
        user_message = self.chat_manager.add_message(
            conversation_id, 
            "user", 
            question,
            metadata={"per_sub_k": per_sub_k}
        )
        
        # Build context for research
        research_context = {}
        if include_context:
            research_context = self._build_research_context(conversation_id)
        
        # Perform research with context
        try:
            # Enhance question with context if available
            enhanced_question = self._enhance_question_with_context(question, research_context)
            
            # Get research results
            research_result = self.ask(enhanced_question, per_sub_k=per_sub_k)
            
            # Generate chat response
            chat_response = self._generate_chat_response(research_result, research_context)
            
            # Add assistant message to conversation
            assistant_message = self.chat_manager.add_message(
                conversation_id,
                "assistant",
                chat_response,
                metadata={
                    "research_result": research_result,
                    "subqueries": research_result.get('subqueries', []),
                    "citations_count": len(research_result.get('citations', [])),
                    "total_documents": research_result.get('total_documents', 0)
                }
            )
            
            return {
                "conversation_id": conversation_id,
                "question": question,
                "answer": chat_response,
                "research_result": research_result,
                "message_id": assistant_message.id,
                "conversation_title": conversation.title,
                "message_count": len(conversation.messages),
                "context_used": bool(research_context.get('recent_messages')),
                "timestamp": assistant_message.timestamp.isoformat()
            }
            
        except Exception as e:
            # Add error message to conversation
            error_message = f"I encountered an error while researching your question: {str(e)}"
            self.chat_manager.add_message(
                conversation_id,
                "assistant",
                error_message,
                metadata={"error": str(e), "error_type": type(e).__name__}
            )
            
            return {
                "conversation_id": conversation_id,
                "question": question,
                "answer": error_message,
                "error": str(e),
                "conversation_title": conversation.title,
                "message_count": len(conversation.messages),
                "timestamp": datetime.now().isoformat()
            }
    
    def _build_research_context(self, conversation_id: str) -> Dict[str, Any]:
        """Build context from conversation history for research."""
        context = self.chat_manager.get_conversation_context(conversation_id)
        
        # Extract relevant information from recent messages
        recent_messages = context.get('recent_messages', [])
        if not recent_messages:
            return {}
        
        # Build context summary
        context_summary = []
        for msg in recent_messages[-5:]:  # Last 5 messages
            if msg['role'] == 'user':
                context_summary.append(f"Previous question: {msg['content']}")
            elif msg['role'] == 'assistant' and 'research_result' in msg.get('metadata', {}):
                # Extract key topics from previous research
                research_result = msg['metadata']['research_result']
                if 'subqueries' in research_result:
                    topics = [sq.get('subquery', '') for sq in research_result['subqueries']]
                    context_summary.append(f"Previously researched: {'; '.join(topics[:2])}")
        
        return {
            "conversation_summary": context.get('conversation_summary', ''),
            "recent_context": ' '.join(context_summary),
            "message_count": context.get('message_count', 0)
        }
    
    def _enhance_question_with_context(self, question: str, context: Dict[str, Any]) -> str:
        """Enhance the question with conversation context."""
        if not context or not context.get('recent_context'):
            return question
        
        # Add context to the question for better research
        enhanced = f"{question}\n\nContext from our conversation: {context['recent_context']}"
        return enhanced
    
    def _generate_chat_response(self, research_result: Dict[str, Any], 
                               context: Dict[str, Any]) -> str:
        """Generate a conversational response from research results."""
        answer = research_result.get('answer', '')
        subqueries = research_result.get('subqueries', [])
        citations = research_result.get('citations', [])
        
        # Start with the main answer
        response_parts = [answer]
        
        # Add context-aware introduction if this is a follow-up
        if context and context.get('message_count', 0) > 1:
            response_parts.insert(0, "Based on our conversation and the research I've conducted, here's what I found:\n\n")
        
        # Add research process summary if there are subqueries
        if subqueries:
            response_parts.append(f"\n**Research Process:** I broke down your question into {len(subqueries)} key areas to ensure comprehensive coverage.")
        
        # Add source information
        if citations:
            unique_sources = len(set(citation.get('filename', '') for citation in citations))
            response_parts.append(f"\n**Sources:** I consulted {len(citations)} relevant documents from {unique_sources} different sources.")
        
        # Add follow-up suggestion
        response_parts.append("\n\nIs there anything specific about this topic you'd like me to explore further, or do you have any other questions?")
        
        return '\n'.join(response_parts)
    
    def get_conversation_history(self, conversation_id: str, max_messages: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history."""
        messages = self.chat_manager.get_conversation_history(conversation_id, max_messages)
        return [msg.to_dict() for msg in messages]
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all conversations."""
        return self.chat_manager.list_conversations()
    
    def create_conversation(self, title: str = "New Conversation") -> str:
        """Create a new conversation."""
        return self.chat_manager.create_conversation(title)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        return self.chat_manager.delete_conversation(conversation_id)
    
    def update_conversation_title(self, conversation_id: str, title: str) -> bool:
        """Update conversation title."""
        return self.chat_manager.update_conversation_title(conversation_id, title)


if __name__ == "__main__":
    # Test the chat research agent
    print("Testing Chat Research Agent")
    print("=" * 50)
    
    # This would require the research agent to be initialized
    # For now, just test the chat manager
    from chat_manager import chat_manager
    
    # Create a test conversation
    conv_id = chat_manager.create_conversation("Test Research Chat")
    print(f"Created conversation: {conv_id}")
    
    # Add some test messages
    chat_manager.add_message(conv_id, "user", "What is machine learning?")
    chat_manager.add_message(conv_id, "assistant", "Machine learning is a subset of artificial intelligence...")
    
    # Get conversation info
    conv = chat_manager.get_conversation(conv_id)
    print(f"Conversation title: {conv.title}")
    print(f"Message count: {len(conv.messages)}")
    
    print("Test completed!")
