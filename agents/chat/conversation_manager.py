"""
Conversation Manager for Chat Agent
Handles conversation state, context, and chat-level interactions.
"""

import uuid
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from ..shared.interfaces import IConversationManager
from ..shared.models import Conversation, ChatMessage, ConversationDB, ChatMessageDB
from ..shared.exceptions import ConversationError


MAX_STORED_HIGHLIGHTS = 10


class ConversationManager(IConversationManager):
    """Manages chat conversations and state using PostgreSQL."""
    
    def __init__(self, db_session: Session, current_user_id: Optional[int] = None, is_admin: bool = False):
        """
        Initialize conversation manager.
        
        Args:
            db_session: SQLAlchemy database session
            current_user_id: ID of the current user (for isolation)
            is_admin: Whether the current user is an admin (can see all conversations)
        """
        self.db = db_session
        self.current_user_id = current_user_id
        self.is_admin = is_admin
        self.active_conversation_id: Optional[str] = None
    
    def _get_user_filter(self):
        """Get the user filter for queries (admin can see all)."""
        if self.is_admin:
            return True  # Admin can see all conversations
        elif self.current_user_id:
            return ConversationDB.user_id == self.current_user_id
        else:
            return False  # No user, no conversations
    
    def create_conversation(self, title: str = "New Conversation") -> str:
        """Create a new conversation."""
        if not self.current_user_id:
            raise ConversationError("User must be authenticated to create conversations")
        
        conversation_db = ConversationDB(
            user_id=self.current_user_id,
            title=title,
            conversation_metadata=json.dumps({})
        )
        self.db.add(conversation_db)
        self.db.commit()
        self.db.refresh(conversation_db)
        
        self.active_conversation_id = str(conversation_db.id)
        return str(conversation_db.id)
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        conversation_db = self._get_conversation_db(conversation_id)
        if not conversation_db:
            return None
        return self._db_to_conversation(conversation_db)
    
    def get_active_conversation(self) -> Optional[Conversation]:
        """Get the currently active conversation."""
        if self.active_conversation_id:
            return self.get_conversation(self.active_conversation_id)
        return None
    
    def set_active_conversation(self, conversation_id: str) -> bool:
        """Set the active conversation."""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            self.active_conversation_id = conversation_id
            return True
        return False
    
    def add_message(self, conversation_id: str, role: str, content: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> Optional[ChatMessage]:
        """Add a message to a conversation."""
        try:
            conv_uuid = uuid.UUID(conversation_id)
        except ValueError:
            return None
        
        # Verify conversation exists and user has access
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
        
        # Create message in database
        message_db = ChatMessageDB(
            conversation_id=str(conv_uuid),
            role=role,
            content=content,
            message_metadata=json.dumps(metadata or {})
        )
        self.db.add(message_db)
        
        # Update conversation timestamp
        conversation_db = self.db.query(ConversationDB).filter(ConversationDB.id == str(conv_uuid)).first()
        if conversation_db:
            conversation_db.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(message_db)
        
        return self._db_to_message(message_db)
    
    def get_conversation_history(self, conversation_id: str, max_messages: int = 50) -> List[ChatMessage]:
        """Get conversation history."""
        try:
            conv_uuid = uuid.UUID(conversation_id)
        except ValueError:
            return []
        
        # Verify access
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return []
        
        # Get messages from database
        messages_db = self.db.query(ChatMessageDB).filter(
            ChatMessageDB.conversation_id == conversation_id
        ).order_by(ChatMessageDB.created_at.desc()).limit(max_messages).all()
        
        return [self._db_to_message(msg) for msg in reversed(messages_db)]
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all conversations with basic info."""
        query = self.db.query(ConversationDB)
        
        # Apply user filter
        if not self.is_admin and self.current_user_id:
            query = query.filter(ConversationDB.user_id == self.current_user_id)
        elif not self.is_admin:
            return []  # No user, no conversations
        
        # Filter out system conversations for document uploads
        query = query.filter(
            ~ConversationDB.conversation_metadata.like('%"source": "document_upload"%')
        )
        
        conversations_db = query.order_by(ConversationDB.updated_at.desc()).all()
        
        conversations = []
        for conv_db in conversations_db:
            message_count = self.db.query(ChatMessageDB).filter(
                ChatMessageDB.conversation_id == conv_db.id
            ).count()
            
            conversations.append({
                'id': str(conv_db.id),
                'title': conv_db.title,
                'created_at': conv_db.created_at.isoformat(),
                'updated_at': conv_db.updated_at.isoformat(),
                'message_count': message_count,
                'is_active': str(conv_db.id) == self.active_conversation_id
            })
        
        return conversations
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        try:
            conv_uuid = uuid.UUID(conversation_id)
        except ValueError:
            return False
        
        # Verify access
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False
        
        # Delete from database (cascade will handle messages)
        conversation_db = self.db.query(ConversationDB).filter(ConversationDB.id == conversation_id).first()
        if conversation_db:
            self.db.delete(conversation_db)
            self.db.commit()
            
            if self.active_conversation_id == conversation_id:
                self.active_conversation_id = None
            return True
        return False
    
    def update_conversation_title(self, conversation_id: str, title: str) -> bool:
        """Update conversation title."""
        try:
            conv_uuid = uuid.UUID(conversation_id)
        except ValueError:
            return False
        
        # Verify access
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False
        
        # Update in database
        conversation_db = self.db.query(ConversationDB).filter(ConversationDB.id == conversation_id).first()
        if conversation_db:
            conversation_db.title = title
            conversation_db.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            return True
        return False
    
    def get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation context for research agent."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return {}
        
        # Build context from recent messages
        recent_messages = self.get_conversation_history(conversation_id, 10)
        context = {
            'conversation_id': conversation_id,
            'recent_messages': [msg.to_dict() for msg in recent_messages],
            'conversation_summary': self.get_conversation_summary(conversation_id),
            'message_count': len(recent_messages)
        }
        
        return context
    
    def get_conversation_summary(self, conversation_id: str) -> str:
        """Get a summary of the conversation."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return "Conversation not found."
        
        return conversation.get_conversation_summary()

    def add_highlight(self, conversation_id: str, highlight: str) -> Optional[List[str]]:
        """Append a highlight to the conversation metadata and return stored highlights."""
        conversation_db = self._get_conversation_db(conversation_id)
        if not conversation_db:
            return None

        metadata: Dict[str, Any] = {}
        if conversation_db.conversation_metadata:
            try:
                metadata = json.loads(conversation_db.conversation_metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}

        highlights = metadata.get("highlights", [])
        if not isinstance(highlights, list):
            highlights = []

        highlights.append(highlight)
        if MAX_STORED_HIGHLIGHTS and len(highlights) > MAX_STORED_HIGHLIGHTS:
            highlights = highlights[-MAX_STORED_HIGHLIGHTS:]

        metadata["highlights"] = highlights
        conversation_db.conversation_metadata = json.dumps(metadata)
        conversation_db.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(conversation_db)

        return highlights
    
    def _db_to_conversation(self, conv_db: ConversationDB) -> Conversation:
        """Convert ConversationDB to Conversation dataclass."""
        # Get messages for this conversation
        messages_db = self.db.query(ChatMessageDB).filter(
            ChatMessageDB.conversation_id == conv_db.id
        ).order_by(ChatMessageDB.created_at).all()
        
        messages = [self._db_to_message(msg) for msg in messages_db]
        
        # Parse metadata from JSON string
        metadata = {}
        if conv_db.conversation_metadata:
            try:
                metadata = json.loads(conv_db.conversation_metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}
        
        return Conversation(
            id=str(conv_db.id),
            title=conv_db.title,
            created_at=conv_db.created_at,
            updated_at=conv_db.updated_at,
            messages=messages,
            context=metadata,
            is_active=conv_db.is_active
        )
    
    def _db_to_message(self, msg_db: ChatMessageDB) -> ChatMessage:
        """Convert ChatMessageDB to ChatMessage dataclass."""
        # Parse metadata from JSON string
        metadata = {}
        if msg_db.message_metadata:
            try:
                metadata = json.loads(msg_db.message_metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}
        
        return ChatMessage(
            id=str(msg_db.id),
            role=msg_db.role,
            content=msg_db.content,
            timestamp=msg_db.created_at,
            metadata=metadata
        )

    def _get_conversation_db(self, conversation_id: str) -> Optional[ConversationDB]:
        """Internal helper to fetch a conversation DB record with access control."""
        try:
            uuid.UUID(conversation_id)
        except ValueError:
            return None

        query = self.db.query(ConversationDB).filter(ConversationDB.id == conversation_id)

        if not self.is_admin and self.current_user_id:
            query = query.filter(ConversationDB.user_id == self.current_user_id)
        elif not self.is_admin:
            return None

        return query.first()


if __name__ == "__main__":
    # Test the conversation manager
    print("Testing Conversation Manager")
    print("=" * 50)
    
    # Note: This test requires a database session and user authentication
    # For actual testing, use the test files in the tests/ directory
    print("Database-based ConversationManager requires:")
    print("- Database session (SessionLocal)")
    print("- Authenticated user (user_id)")
    print("- Admin privileges (is_admin)")
    print("\nUse tests/test_conversation_manager.py for proper testing")
