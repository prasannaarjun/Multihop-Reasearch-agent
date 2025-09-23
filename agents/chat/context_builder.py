"""
Context Builder for Chat Agent
Handles building context from conversation history for research.
"""

from typing import Dict, Any, List
from ..shared.models import Conversation, ChatMessage


class ContextBuilder:
    """
    Context builder that extracts relevant information from conversation history.
    """
    
    def __init__(self, max_context_messages: int = 5):
        """
        Initialize context builder.
        
        Args:
            max_context_messages: Maximum number of recent messages to include in context
        """
        self.max_context_messages = max_context_messages
    
    def build_research_context(self, conversation: Conversation) -> Dict[str, Any]:
        """
        Build context from conversation history for research.
        
        Args:
            conversation: The conversation to build context from
            
        Returns:
            Dictionary containing context information
        """
        if not conversation or not conversation.messages:
            return {}
        
        # Get recent messages
        recent_messages = conversation.get_recent_context(self.max_context_messages)
        
        # Extract relevant information from recent messages
        context_summary = []
        research_topics = []
        
        for msg in recent_messages:
            if msg.role == 'user':
                context_summary.append(f"Previous question: {msg.content}")
            elif msg.role == 'assistant' and msg.metadata and 'research_result' in msg.metadata:
                # Extract key topics from previous research
                research_result = msg.metadata['research_result']
                if 'subqueries' in research_result:
                    topics = [sq.get('subquery', '') for sq in research_result['subqueries']]
                    research_topics.extend(topics[:2])  # Top 2 topics per research
                    context_summary.append(f"Previously researched: {'; '.join(topics[:2])}")
        
        return {
            "conversation_id": conversation.id,
            "conversation_summary": conversation.get_conversation_summary(),
            "recent_context": ' '.join(context_summary),
            "research_topics": research_topics,
            "message_count": len(conversation.messages),
            "recent_messages": [msg.to_dict() for msg in recent_messages]
        }
    
    def enhance_question_with_context(self, question: str, context: Dict[str, Any]) -> str:
        """
        Enhance the question with conversation context.
        
        Args:
            question: The user's question
            context: Context from conversation history
            
        Returns:
            Enhanced question with context
        """
        if not context or not context.get('recent_context'):
            return question
        
        # Add context to the question for better research
        enhanced = f"{question}\n\nContext from our conversation: {context['recent_context']}"
        return enhanced
    
    def extract_research_topics(self, conversation: Conversation) -> List[str]:
        """
        Extract research topics from conversation history.
        
        Args:
            conversation: The conversation to extract topics from
            
        Returns:
            List of research topics
        """
        topics = []
        
        for msg in conversation.messages:
            if msg.role == 'assistant' and msg.metadata and 'research_result' in msg.metadata:
                research_result = msg.metadata['research_result']
                if 'subqueries' in research_result:
                    for sq in research_result['subqueries']:
                        if 'subquery' in sq:
                            topics.append(sq['subquery'])
        
        # Remove duplicates and return
        return list(dict.fromkeys(topics))
    
    def get_conversation_theme(self, conversation: Conversation) -> str:
        """
        Get the main theme or topic of the conversation.
        
        Args:
            conversation: The conversation to analyze
            
        Returns:
            Main theme of the conversation
        """
        if not conversation or not conversation.messages:
            return "General conversation"
        
        # Get user messages to determine theme
        user_messages = [msg for msg in conversation.messages if msg.role == 'user']
        
        if not user_messages:
            return "General conversation"
        
        # Simple theme extraction based on first few user messages
        themes = []
        for msg in user_messages[:3]:  # First 3 user messages
            content = msg.content.lower()
            if 'machine learning' in content or 'ml' in content:
                themes.append('machine learning')
            elif 'artificial intelligence' in content or 'ai' in content:
                themes.append('artificial intelligence')
            elif 'data science' in content:
                themes.append('data science')
            elif 'programming' in content or 'code' in content:
                themes.append('programming')
            elif 'research' in content:
                themes.append('research')
        
        if themes:
            # Return the most common theme
            from collections import Counter
            theme_counts = Counter(themes)
            return theme_counts.most_common(1)[0][0]
        
        return "General conversation"


if __name__ == "__main__":
    # Test the context builder
    from ..shared.models import Conversation, ChatMessage
    from datetime import datetime
    
    print("Testing Context Builder")
    print("=" * 50)
    
    # Create a test conversation
    conversation = Conversation(
        id="test-conv",
        title="Test Conversation",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        messages=[],
        context={}
    )
    
    # Add some test messages
    conversation.add_message("user", "What is machine learning?")
    conversation.add_message("assistant", "Machine learning is a subset of AI...", 
                           metadata={"research_result": {"subqueries": [{"subquery": "What is machine learning?"}]}})
    conversation.add_message("user", "How does it work in healthcare?")
    
    # Test context builder
    builder = ContextBuilder()
    context = builder.build_research_context(conversation)
    
    print("Context:")
    for key, value in context.items():
        print(f"  {key}: {value}")
    
    # Test question enhancement
    enhanced = builder.enhance_question_with_context("Tell me more about deep learning", context)
    print(f"\nEnhanced question: {enhanced}")
    
    # Test theme extraction
    theme = builder.get_conversation_theme(conversation)
    print(f"\nConversation theme: {theme}")
    
    print("\nTest completed!")
