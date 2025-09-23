"""
Shared interfaces for the multi-hop research agent system.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from .models import ResearchResult, ChatMessage, Conversation


class IAgent(ABC):
    """Base interface for all agents."""
    
    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """Process input data and return results."""
        pass


class IRetriever(ABC):
    """Interface for document retrieval systems."""
    
    @abstractmethod
    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query."""
        pass


class ILLMClient(ABC):
    """Interface for LLM clients."""
    
    @abstractmethod
    def generate_text(self, prompt: str, system_prompt: str = None, max_tokens: int = 1000) -> str:
        """Generate text using the LLM."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM client is available."""
        pass


class IQueryPlanner(ABC):
    """Interface for query planning systems."""
    
    @abstractmethod
    def generate_subqueries(self, question: str) -> List[str]:
        """Generate subqueries from a main question."""
        pass


class IAnswerSynthesizer(ABC):
    """Interface for answer synthesis systems."""
    
    @abstractmethod
    def synthesize_answer(self, question: str, subquery_results: List[Dict[str, Any]]) -> str:
        """Synthesize final answer from subquery results."""
        pass


class IConversationManager(ABC):
    """Interface for conversation management."""
    
    @abstractmethod
    def create_conversation(self, title: str = "New Conversation") -> str:
        """Create a new conversation."""
        pass
    
    @abstractmethod
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        pass
    
    @abstractmethod
    def add_message(self, conversation_id: str, role: str, content: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> Optional[ChatMessage]:
        """Add a message to a conversation."""
        pass
    
    @abstractmethod
    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all conversations."""
        pass
