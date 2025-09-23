"""
Shared Module
Contains shared utilities, interfaces, and common functionality.
"""

from .interfaces import IAgent, IRetriever, ILLMClient
from .models import ResearchResult, ChatMessage, Conversation, ConversationInfo, ChatResponse
from .exceptions import AgentError, RetrievalError, LLMError

__all__ = [
    'IAgent',
    'IRetriever', 
    'ILLMClient',
    'ResearchResult',
    'ChatMessage',
    'Conversation',
    'ConversationInfo',
    'ChatResponse',
    'AgentError',
    'RetrievalError',
    'LLMError'
]
