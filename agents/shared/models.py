"""
Shared data models for the multi-hop research agent system.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class MessageRole(Enum):
    """Message roles in conversations."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """Represents a single message in a conversation."""
    id: str
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class Conversation:
    """Represents a conversation session."""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessage]
    context: Dict[str, Any]
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['messages'] = [msg.to_dict() for msg in self.messages]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """Create from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        data['messages'] = [ChatMessage.from_dict(msg) for msg in data['messages']]
        return cls(**data)
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> ChatMessage:
        """Add a new message to the conversation."""
        import uuid
        now = datetime.now()
        message = ChatMessage(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=now,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.updated_at = now
        return message
    
    def get_recent_context(self, max_messages: int = 10) -> List[ChatMessage]:
        """Get recent messages for context."""
        return self.messages[-max_messages:] if self.messages else []
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation."""
        if not self.messages:
            return "No messages yet."
        
        # Simple summary based on message count and recent topics
        user_messages = [msg for msg in self.messages if msg.role == 'user']
        assistant_messages = [msg for msg in self.messages if msg.role == 'assistant']
        
        summary_parts = [
            f"Conversation with {len(user_messages)} user messages and {len(assistant_messages)} assistant responses."
        ]
        
        if user_messages:
            # Get the first few words of the first user message as topic hint
            first_message = user_messages[0].content[:50]
            summary_parts.append(f"Started with: {first_message}...")
        
        return " ".join(summary_parts)


@dataclass
class SubqueryResult:
    """Result from processing a single subquery."""
    subquery: str
    summary: str
    documents: List[Dict[str, Any]]
    success: bool = True
    error: Optional[str] = None


@dataclass
class ResearchResult:
    """Complete result from a research query."""
    question: str
    answer: str
    subqueries: List[SubqueryResult]
    citations: List[Dict[str, Any]]
    total_documents: int
    processing_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class ConversationInfo:
    """Information about a conversation for API responses."""
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    is_active: bool


@dataclass
class ChatResponse:
    """Response from chat agent."""
    conversation_id: str
    message_id: str
    answer: str
    conversation_title: str
    message_count: int
    context_used: bool
    timestamp: str
    research_result: Optional[ResearchResult] = None
    error: Optional[str] = None
