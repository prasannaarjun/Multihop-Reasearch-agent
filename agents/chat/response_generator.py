"""
Response Generator for Chat Agent
Handles generating conversational responses from research results.
"""

from typing import Dict, Any, Optional, List
from ..shared.models import ResearchResult, ChatMessage


class ResponseGenerator:
    """
    Response generator that creates conversational responses from research results.
    """
    
    def __init__(self):
        """Initialize response generator."""
        pass
    
    def generate_chat_response(self, research_result: ResearchResult, 
                             context: Dict[str, Any]) -> str:
        """
        Generate a conversational response from research results.
        
        Args:
            research_result: The research result to generate response from
            context: Conversation context
            
        Returns:
            Conversational response text
        """
        answer = research_result.answer
        subqueries = research_result.subqueries
        citations = research_result.citations
        
        # Start with the main answer
        response_parts = [answer]
        
        # Add context-aware introduction if this is a follow-up
        if context and context.get('message_count', 0) > 1:
            response_parts.insert(0, "Based on our conversation and the research I've conducted, here's what I found:\n\n")
        
        # Add research process summary if there are subqueries
        if subqueries:
            successful_subqueries = [sq for sq in subqueries if sq.success]
            response_parts.append(f"\n**Research Process:** I broke down your question into {len(successful_subqueries)} key areas to ensure comprehensive coverage.")
        
        # Add source information
        if citations:
            unique_sources = len(set(citation.get('filename', '') for citation in citations))
            response_parts.append(f"\n**Sources:** I consulted {len(citations)} relevant documents from {unique_sources} different sources.")
        
        # Add follow-up suggestion
        response_parts.append("\n\nIs there anything specific about this topic you'd like me to explore further, or do you have any other questions?")
        
        return '\n'.join(response_parts)
    
    def generate_error_response(self, error: str, context: Dict[str, Any]) -> str:
        """
        Generate an error response.
        
        Args:
            error: Error message
            context: Conversation context
            
        Returns:
            Error response text
        """
        response_parts = [
            "I apologize, but I encountered an error while researching your question.",
            f"Error: {error}",
            "\nPlease try rephrasing your question or let me know if you'd like to explore a different topic."
        ]
        
        return '\n'.join(response_parts)
    
    def generate_greeting_response(self, context: Dict[str, Any]) -> str:
        """
        Generate a greeting response for new conversations.
        
        Args:
            context: Conversation context
            
        Returns:
            Greeting response text
        """
        return ("Hello! I'm your research assistant. I can help you explore complex topics by breaking them down into focused research areas and finding relevant information from our document collection.\n\n"
                "What would you like to research today?")
    
    def generate_follow_up_suggestions(self, research_result: ResearchResult) -> List[str]:
        """
        Generate follow-up question suggestions based on research results.
        
        Args:
            research_result: The research result to generate suggestions from
            
        Returns:
            List of suggested follow-up questions
        """
        suggestions = []
        
        # Extract topics from subqueries
        topics = []
        topic_phrases = []
        for sq in research_result.subqueries:
            if sq.success and sq.summary:
                # Extract key terms from subquery
                words = sq.subquery.lower().split()
                key_words = [w for w in words if len(w) > 3 and w not in ['what', 'how', 'why', 'when', 'where', 'which']]
                topics.extend(key_words[:2])  # Top 2 words per subquery
                # Also check for common phrases
                topic_phrases.append(sq.subquery.lower())
        
        # Generate suggestions based on topics
        if 'machine' in topics and 'learning' in topics or any('machine learning' in phrase for phrase in topic_phrases):
            suggestions.extend([
                "Can you tell me more about specific machine learning algorithms?",
                "What are the latest trends in machine learning?",
                "How is machine learning being used in different industries?"
            ])
        
        if 'artificial' in topics and 'intelligence' in topics:
            suggestions.extend([
                "What are the ethical implications of AI?",
                "How does AI differ from traditional programming?",
                "What are the limitations of current AI systems?"
            ])
        
        if 'data' in topics and 'science' in topics:
            suggestions.extend([
                "What tools are commonly used in data science?",
                "How do you become a data scientist?",
                "What are the biggest challenges in data science?"
            ])
        
        # Generic suggestions if no specific topics found
        if not suggestions:
            suggestions = [
                "Can you provide more details about this topic?",
                "What are the practical applications of this?",
                "Are there any recent developments in this area?"
            ]
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def format_citations(self, citations: List[Dict[str, Any]], max_citations: int = 5) -> str:
        """
        Format citations for display.
        
        Args:
            citations: List of citation dictionaries
            max_citations: Maximum number of citations to show
            
        Returns:
            Formatted citations text
        """
        if not citations:
            return ""
        
        citation_text = "\n**Sources consulted:**\n"
        
        for i, citation in enumerate(citations[:max_citations], 1):
            title = citation.get('title', 'Unknown')
            filename = citation.get('filename', 'Unknown')
            score = citation.get('score', 0)
            
            citation_text += f"{i}. {title} ({filename}) - Relevance: {score:.2f}\n"
        
        if len(citations) > max_citations:
            citation_text += f"... and {len(citations) - max_citations} more sources\n"
        
        return citation_text


if __name__ == "__main__":
    # Test the response generator
    from ..shared.models import ResearchResult, SubqueryResult
    from datetime import datetime
    
    print("Testing Response Generator")
    print("=" * 50)
    
    # Create test research result
    subquery_results = [
        SubqueryResult(
            subquery="What is machine learning?",
            summary="Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.",
            documents=[],
            success=True
        ),
        SubqueryResult(
            subquery="How does machine learning work?",
            summary="Machine learning works by using algorithms to identify patterns in data and make predictions or decisions based on those patterns.",
            documents=[],
            success=True
        )
    ]
    
    research_result = ResearchResult(
        question="What is machine learning and how does it work?",
        answer="Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It works by using algorithms to identify patterns in data and make predictions or decisions based on those patterns.",
        subqueries=subquery_results,
        citations=[
            {"title": "Introduction to ML", "filename": "ml_basics.txt", "score": 0.95},
            {"title": "ML Algorithms", "filename": "algorithms.txt", "score": 0.87}
        ],
        total_documents=2,
        processing_time=1.5
    )
    
    # Test response generator
    generator = ResponseGenerator()
    
    # Test chat response
    context = {"message_count": 3, "recent_context": "Previous discussion about AI"}
    response = generator.generate_chat_response(research_result, context)
    print("Chat Response:")
    print(response)
    
    # Test follow-up suggestions
    suggestions = generator.generate_follow_up_suggestions(research_result)
    print(f"\nFollow-up suggestions: {suggestions}")
    
    # Test error response
    error_response = generator.generate_error_response("Database connection failed", context)
    print(f"\nError response: {error_response}")
    
    print("\nTest completed!")
