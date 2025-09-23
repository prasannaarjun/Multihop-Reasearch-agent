"""
Conversation Manager for Chat Agent
Handles conversation state, context, and chat-level interactions.
"""

import uuid
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from ..shared.interfaces import IConversationManager
from ..shared.models import Conversation, ChatMessage
from ..shared.exceptions import ConversationError


class ConversationManager(IConversationManager):
    """Manages chat conversations and state."""
    
    def __init__(self, persist_directory: str = "chat_data"):
        """
        Initialize conversation manager.
        
        Args:
            persist_directory: Directory to persist conversation data
        """
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
                   metadata: Optional[Dict[str, Any]] = None) -> Optional[ChatMessage]:
        """Add a message to a conversation."""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return None
        
        message = conversation.add_message(role, content, metadata)
        self._save_conversations()
        return message
    
    def get_conversation_history(self, conversation_id: str, max_messages: int = 50) -> List[ChatMessage]:
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
    
    def get_conversation_summary(self, conversation_id: str) -> str:
        """Get a summary of the conversation."""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return "Conversation not found."
        
        return conversation.get_conversation_summary()


if __name__ == "__main__":
    # Test the conversation manager
    print("Testing Conversation Manager")
    print("=" * 50)
    
    # Create a test conversation
    manager = ConversationManager()
    conv_id = manager.create_conversation("Test Conversation")
    print(f"Created conversation: {conv_id}")
    
    # Add some messages
    manager.add_message(conv_id, "user", "Hello, I need help with machine learning")
    manager.add_message(conv_id, "assistant", "I'd be happy to help you with machine learning! What specific topic would you like to explore?")
    manager.add_message(conv_id, "user", "What are the best algorithms for image classification?")
    
    # Get conversation history
    history = manager.get_conversation_history(conv_id)
    print(f"\nConversation history ({len(history)} messages):")
    for msg in history:
        print(f"  {msg.role}: {msg.content[:50]}...")
    
    # List conversations
    conversations = manager.list_conversations()
    print(f"\nAll conversations ({len(conversations)}):")
    for conv in conversations:
        print(f"  {conv['title']} - {conv['message_count']} messages")
    
    print("\nTest completed!")
