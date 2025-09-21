"""
Chat Manager for Multi-hop Research Agent
Handles conversation state, context, and chat-level interactions.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json
import os


@dataclass
class Message:
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
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
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
    messages: List[Message]
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
        data['messages'] = [Message.from_dict(msg) for msg in data['messages']]
        return cls(**data)
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Message:
        """Add a new message to the conversation."""
        message = Message(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.updated_at = datetime.now()
        return message
    
    def get_recent_context(self, max_messages: int = 10) -> List[Message]:
        """Get recent messages for context."""
        return self.messages[-max_messages:] if self.messages else []
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation."""
        if not self.messages:
            return "No messages yet."
        
        user_messages = [msg for msg in self.messages if msg.role == 'user']
        if not user_messages:
            return "No user messages yet."
        
        # Create a simple summary from user messages
        topics = []
        for msg in user_messages[:3]:  # First 3 user messages
            if len(msg.content) > 50:
                topics.append(msg.content[:50] + "...")
            else:
                topics.append(msg.content)
        
        return f"Topics discussed: {'; '.join(topics)}"


class ChatManager:
    """Manages chat conversations and state."""
    
    def __init__(self, persist_directory: str = "chat_data"):
        self.persist_directory = persist_directory
        self.conversations: Dict[str, Conversation] = {}
        self.active_conversation_id: Optional[str] = None
        
        # Ensure persist directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Load existing conversations
        self._load_conversations()
    
    def _load_conversations(self):
        """Load conversations from disk."""
        conversations_file = os.path.join(self.persist_directory, "conversations.json")
        if os.path.exists(conversations_file):
            try:
                with open(conversations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for conv_data in data.get('conversations', []):
                        conv = Conversation.from_dict(conv_data)
                        self.conversations[conv.id] = conv
            except Exception as e:
                print(f"Error loading conversations: {e}")
    
    def _save_conversations(self):
        """Save conversations to disk."""
        conversations_file = os.path.join(self.persist_directory, "conversations.json")
        try:
            data = {
                'conversations': [conv.to_dict() for conv in self.conversations.values()],
                'active_conversation_id': self.active_conversation_id
            }
            with open(conversations_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving conversations: {e}")
    
    def create_conversation(self, title: str = "New Conversation") -> str:
        """Create a new conversation."""
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(
            id=conversation_id,
            title=title,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            messages=[],
            context={}
        )
        self.conversations[conversation_id] = conversation
        self.active_conversation_id = conversation_id
        self._save_conversations()
        return conversation_id
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        return self.conversations.get(conversation_id)
    
    def get_active_conversation(self) -> Optional[Conversation]:
        """Get the currently active conversation."""
        if self.active_conversation_id:
            return self.conversations.get(self.active_conversation_id)
        return None
    
    def set_active_conversation(self, conversation_id: str) -> bool:
        """Set the active conversation."""
        if conversation_id in self.conversations:
            self.active_conversation_id = conversation_id
            self._save_conversations()
            return True
        return False
    
    def add_message(self, conversation_id: str, role: str, content: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> Optional[Message]:
        """Add a message to a conversation."""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return None
        
        message = conversation.add_message(role, content, metadata)
        self._save_conversations()
        return message
    
    def get_conversation_history(self, conversation_id: str, max_messages: int = 50) -> List[Message]:
        """Get conversation history."""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return []
        
        return conversation.get_recent_context(max_messages)
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all conversations with basic info."""
        conversations = []
        for conv in self.conversations.values():
            conversations.append({
                'id': conv.id,
                'title': conv.title,
                'created_at': conv.created_at.isoformat(),
                'updated_at': conv.updated_at.isoformat(),
                'message_count': len(conv.messages),
                'is_active': conv.id == self.active_conversation_id
            })
        
        # Sort by updated_at descending
        conversations.sort(key=lambda x: x['updated_at'], reverse=True)
        return conversations
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            if self.active_conversation_id == conversation_id:
                self.active_conversation_id = None
            self._save_conversations()
            return True
        return False
    
    def update_conversation_title(self, conversation_id: str, title: str) -> bool:
        """Update conversation title."""
        conversation = self.conversations.get(conversation_id)
        if conversation:
            conversation.title = title
            conversation.updated_at = datetime.now()
            self._save_conversations()
            return True
        return False
    
    def get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation context for research agent."""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return {}
        
        # Build context from recent messages
        recent_messages = conversation.get_recent_context(10)
        context = {
            'conversation_id': conversation_id,
            'recent_messages': [msg.to_dict() for msg in recent_messages],
            'conversation_summary': conversation.get_conversation_summary(),
            'message_count': len(conversation.messages)
        }
        
        return context


# Global chat manager instance
chat_manager = ChatManager()


if __name__ == "__main__":
    # Test the chat manager
    print("Testing Chat Manager")
    print("=" * 50)
    
    # Create a test conversation
    conv_id = chat_manager.create_conversation("Test Conversation")
    print(f"Created conversation: {conv_id}")
    
    # Add some messages
    chat_manager.add_message(conv_id, "user", "Hello, I need help with machine learning")
    chat_manager.add_message(conv_id, "assistant", "I'd be happy to help you with machine learning! What specific topic would you like to explore?")
    chat_manager.add_message(conv_id, "user", "What are the best algorithms for image classification?")
    
    # Get conversation history
    history = chat_manager.get_conversation_history(conv_id)
    print(f"\nConversation history ({len(history)} messages):")
    for msg in history:
        print(f"  {msg.role}: {msg.content[:50]}...")
    
    # List conversations
    conversations = chat_manager.list_conversations()
    print(f"\nAll conversations ({len(conversations)}):")
    for conv in conversations:
        print(f"  {conv['title']} - {conv['message_count']} messages")
    
    print("\nTest completed!")
