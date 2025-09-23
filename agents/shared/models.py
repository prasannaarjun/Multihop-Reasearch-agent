"""
Shared data models for the multi-hop research agent system.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import uuid

# SQLAlchemy imports for database models
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


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


# SQLAlchemy Database Models
# Import Base from auth.database to ensure all models share the same metadata
from auth.database import Base
from sqlalchemy import event
from sqlalchemy.engine import Engine


# Database-agnostic column types
def get_uuid_column():
    """Get UUID column type based on database dialect."""
    from sqlalchemy.dialects import sqlite
    from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
    
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if hasattr(dbapi_connection, 'execute'):
            # Check if it's SQLite
            if 'sqlite' in str(type(dbapi_connection)):
                # Use String for SQLite, UUID for PostgreSQL
                return String(36)
        return PostgresUUID(as_uuid=True)
    
    return PostgresUUID(as_uuid=True)


def get_json_column():
    """Get JSON column type based on database dialect."""
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy import JSON
    
    # For now, use JSON for compatibility, JSONB for PostgreSQL
    return JSONB


class ConversationDB(Base):
    """SQLAlchemy model for conversations stored in database."""
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    conversation_metadata = Column(Text, nullable=True)  # Store as JSON string for compatibility
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationship to messages
    messages = relationship("ChatMessageDB", back_populates="conversation", cascade="all, delete-orphan")
    
    # Relationship to user
    user = relationship("User", back_populates="conversations")


class ChatMessageDB(Base):
    """SQLAlchemy model for chat messages stored in database."""
    __tablename__ = "chat_messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    message_metadata = Column(Text, nullable=True)  # Store as JSON string for compatibility
    
    # Relationship to conversation
    conversation = relationship("ConversationDB", back_populates="messages")
