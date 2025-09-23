"""
Tests for database-based ConversationManager with user isolation.
"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from agents.chat.conversation_manager import ConversationManager
from agents.shared.models import ConversationDB, ChatMessageDB
from auth.database import Base, User, UserSession


class TestConversationManagerDB:
    """Test database-based conversation manager with user isolation."""
    
    @pytest.fixture
    def db_session(self):
        """Create an in-memory SQLite database for testing."""
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        yield session
        
        session.close()
    
    @pytest.fixture
    def test_users(self, db_session):
        """Create test users."""
        # Create regular user
        user1 = User(
            username="user1",
            email="user1@test.com",
            hashed_password="hashed_password_1",
            is_active=True,
            is_admin=False
        )
        
        # Create admin user
        user2 = User(
            username="admin",
            email="admin@test.com",
            hashed_password="hashed_password_admin",
            is_active=True,
            is_admin=True
        )
        
        # Create another regular user
        user3 = User(
            username="user3",
            email="user3@test.com",
            hashed_password="hashed_password_3",
            is_active=True,
            is_admin=False
        )
        
        db_session.add_all([user1, user2, user3])
        db_session.commit()
        db_session.refresh(user1)
        db_session.refresh(user2)
        db_session.refresh(user3)
        
        return {"user1": user1, "admin": user2, "user3": user3}
    
    @pytest.fixture
    def conversation_manager_user1(self, db_session, test_users):
        """Create conversation manager for user1."""
        return ConversationManager(
            db_session=db_session,
            current_user_id=test_users["user1"].id,
            is_admin=False
        )
    
    @pytest.fixture
    def conversation_manager_admin(self, db_session, test_users):
        """Create conversation manager for admin."""
        return ConversationManager(
            db_session=db_session,
            current_user_id=test_users["admin"].id,
            is_admin=True
        )
    
    @pytest.fixture
    def conversation_manager_user3(self, db_session, test_users):
        """Create conversation manager for user3."""
        return ConversationManager(
            db_session=db_session,
            current_user_id=test_users["user3"].id,
            is_admin=False
        )
    
    def test_create_conversation_user_isolation(self, db_session, conversation_manager_user1, test_users):
        """Test that users can only create conversations for themselves."""
        # User1 creates a conversation
        conv_id = conversation_manager_user1.create_conversation("User1's Conversation")
        
        # Verify conversation was created with correct user_id
        conversation = conversation_manager_user1.get_conversation(conv_id)
        assert conversation is not None
        assert conversation.title == "User1's Conversation"
        
        # Verify the conversation belongs to user1
        conv_db = db_session.query(ConversationDB).filter(ConversationDB.id == conv_id).first()
        assert conv_db.user_id == test_users["user1"].id
    
    def test_user_cannot_access_other_users_conversations(self, db_session, test_users, conversation_manager_user1, conversation_manager_user3):
        """Test that users cannot access conversations from other users."""
        # User1 creates a conversation
        conv_id = conversation_manager_user1.create_conversation("User1's Private Conversation")
        
        # User3 tries to access User1's conversation
        conversation = conversation_manager_user3.get_conversation(conv_id)
        assert conversation is None  # Should not be able to access
    
    def test_admin_can_access_all_conversations(self, db_session, test_users, conversation_manager_user1, conversation_manager_admin):
        """Test that admin can access all conversations."""
        # User1 creates a conversation
        conv_id = conversation_manager_user1.create_conversation("User1's Conversation")
        
        # Admin should be able to access User1's conversation
        conversation = conversation_manager_admin.get_conversation(conv_id)
        assert conversation is not None
        assert conversation.title == "User1's Conversation"
    
    def test_list_conversations_user_isolation(self, conversation_manager_user1, conversation_manager_user3):
        """Test that users only see their own conversations in the list."""
        # User1 creates conversations
        conv1_id = conversation_manager_user1.create_conversation("User1 Conversation 1")
        conv2_id = conversation_manager_user1.create_conversation("User1 Conversation 2")
        
        # User3 creates conversations
        conv3_id = conversation_manager_user3.create_conversation("User3 Conversation 1")
        
        # User1 should only see their own conversations
        user1_conversations = conversation_manager_user1.list_conversations()
        assert len(user1_conversations) == 2
        conv_ids = [conv["id"] for conv in user1_conversations]
        assert conv1_id in conv_ids
        assert conv2_id in conv_ids
        assert conv3_id not in conv_ids
        
        # User3 should only see their own conversations
        user3_conversations = conversation_manager_user3.list_conversations()
        assert len(user3_conversations) == 1
        assert user3_conversations[0]["id"] == conv3_id
    
    def test_admin_can_see_all_conversations(self, conversation_manager_user1, conversation_manager_user3, conversation_manager_admin):
        """Test that admin can see all conversations."""
        # User1 creates conversations
        conv1_id = conversation_manager_user1.create_conversation("User1 Conversation")
        
        # User3 creates conversations
        conv3_id = conversation_manager_user3.create_conversation("User3 Conversation")
        
        # Admin should see all conversations
        admin_conversations = conversation_manager_admin.list_conversations()
        assert len(admin_conversations) == 2
        conv_ids = [conv["id"] for conv in admin_conversations]
        assert conv1_id in conv_ids
        assert conv3_id in conv_ids
    
    def test_add_message_user_isolation(self, conversation_manager_user1, conversation_manager_user3):
        """Test that users can only add messages to their own conversations."""
        # User1 creates a conversation
        conv_id = conversation_manager_user1.create_conversation("User1's Conversation")
        
        # User1 adds a message (should succeed)
        message1 = conversation_manager_user1.add_message(conv_id, "user", "Hello from User1")
        assert message1 is not None
        assert message1.content == "Hello from User1"
        
        # User3 tries to add a message to User1's conversation (should fail)
        message2 = conversation_manager_user3.add_message(conv_id, "user", "Hello from User3")
        assert message2 is None  # Should not be able to add message
    
    def test_update_conversation_title_user_isolation(self, conversation_manager_user1, conversation_manager_user3):
        """Test that users can only update their own conversation titles."""
        # User1 creates a conversation
        conv_id = conversation_manager_user1.create_conversation("Original Title")
        
        # User1 updates title (should succeed)
        success = conversation_manager_user1.update_conversation_title(conv_id, "Updated by User1")
        assert success is True
        
        # User3 tries to update User1's conversation title (should fail)
        success = conversation_manager_user3.update_conversation_title(conv_id, "Updated by User3")
        assert success is False
    
    def test_delete_conversation_user_isolation(self, conversation_manager_user1, conversation_manager_user3):
        """Test that users can only delete their own conversations."""
        # User1 creates a conversation
        conv_id = conversation_manager_user1.create_conversation("User1's Conversation")
        
        # User3 tries to delete User1's conversation (should fail)
        success = conversation_manager_user3.delete_conversation(conv_id)
        assert success is False
        
        # Verify conversation still exists
        conversation = conversation_manager_user1.get_conversation(conv_id)
        assert conversation is not None
        
        # User1 deletes their own conversation (should succeed)
        success = conversation_manager_user1.delete_conversation(conv_id)
        assert success is True
        
        # Verify conversation is deleted
        conversation = conversation_manager_user1.get_conversation(conv_id)
        assert conversation is None
    
    def test_admin_can_delete_any_conversation(self, conversation_manager_user1, conversation_manager_admin):
        """Test that admin can delete any conversation."""
        # User1 creates a conversation
        conv_id = conversation_manager_user1.create_conversation("User1's Conversation")
        
        # Admin deletes User1's conversation (should succeed)
        success = conversation_manager_admin.delete_conversation(conv_id)
        assert success is True
        
        # Verify conversation is deleted
        conversation = conversation_manager_user1.get_conversation(conv_id)
        assert conversation is None
    
    def test_conversation_history_user_isolation(self, conversation_manager_user1, conversation_manager_user3):
        """Test that users can only access history of their own conversations."""
        # User1 creates a conversation and adds messages
        conv_id = conversation_manager_user1.create_conversation("User1's Conversation")
        conversation_manager_user1.add_message(conv_id, "user", "Hello")
        conversation_manager_user1.add_message(conv_id, "assistant", "Hi there!")
        
        # User1 can access conversation history
        history = conversation_manager_user1.get_conversation_history(conv_id)
        assert len(history) == 2
        
        # User3 cannot access User1's conversation history
        history = conversation_manager_user3.get_conversation_history(conv_id)
        assert len(history) == 0
    
    def test_unauthenticated_user_has_no_access(self, db_session):
        """Test that unauthenticated users have no access to conversations."""
        manager = ConversationManager(
            db_session=db_session,
            current_user_id=None,
            is_admin=False
        )
        
        # Should not be able to create conversations
        with pytest.raises(Exception):  # Should raise ConversationError
            manager.create_conversation("Test Conversation")
        
        # Should not be able to list conversations
        conversations = manager.list_conversations()
        assert len(conversations) == 0
        
        # Should not be able to access any conversation
        fake_conv_id = str(uuid.uuid4())
        conversation = manager.get_conversation(fake_conv_id)
        assert conversation is None
    
    def test_conversation_metadata_preservation(self, conversation_manager_user1):
        """Test that conversation metadata is preserved in JSONB."""
        # Create conversation with metadata
        conv_id = conversation_manager_user1.create_conversation("Test Conversation")
        
        # Add message with metadata
        metadata = {"research_result": {"question": "test", "answer": "test answer"}}
        message = conversation_manager_user1.add_message(conv_id, "assistant", "Test response", metadata)
        
        assert message is not None
        assert message.metadata == metadata
        
        # Verify metadata is stored in database
        conversation = conversation_manager_user1.get_conversation(conv_id)
        assert conversation is not None
        
        # Check that messages have metadata
        history = conversation_manager_user1.get_conversation_history(conv_id)
        assert len(history) == 1
        assert history[0].metadata == metadata
    
    def test_conversation_cascade_delete(self, db_session, conversation_manager_user1):
        """Test that deleting a conversation also deletes its messages."""
        # Create conversation and add messages
        conv_id = conversation_manager_user1.create_conversation("Test Conversation")
        conversation_manager_user1.add_message(conv_id, "user", "Hello")
        conversation_manager_user1.add_message(conv_id, "assistant", "Hi!")
        
        # Verify messages exist
        history = conversation_manager_user1.get_conversation_history(conv_id)
        assert len(history) == 2
        
        # Delete conversation
        success = conversation_manager_user1.delete_conversation(conv_id)
        assert success is True
        
        # Verify conversation and messages are deleted
        conversation = conversation_manager_user1.get_conversation(conv_id)
        assert conversation is None
        
        # Verify no messages remain in database
        remaining_messages = db_session.query(ChatMessageDB).filter(
            ChatMessageDB.conversation_id == conv_id
        ).count()
        assert remaining_messages == 0


if __name__ == "__main__":
    pytest.main([__file__])
