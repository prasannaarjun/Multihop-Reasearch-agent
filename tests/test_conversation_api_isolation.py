"""
Tests for conversation API endpoints with user isolation.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import app
from auth.database import Base, User, UserSession
from auth.auth_service import AuthService
from auth.auth_models import UserCreate


class TestConversationAPIIsolation:
    """Test conversation API endpoints with user isolation."""
    
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
        """Create test users and return auth tokens."""
        auth_service = AuthService(db_session)
        
        # Create regular user
        user1_data = UserCreate(
            username="user1",
            email="user1@test.com",
            password="password123"
        )
        user1 = auth_service.create_user(user1_data)
        
        # Create admin user
        user2_data = UserCreate(
            username="admin",
            email="admin@test.com",
            password="password123"
        )
        user2 = auth_service.create_user(user2_data)
        user2.is_admin = True
        db_session.commit()
        
        # Create another regular user
        user3_data = UserCreate(
            username="user3",
            email="user3@test.com",
            password="password123"
        )
        user3 = auth_service.create_user(user3_data)
        
        # Get auth tokens
        token1 = auth_service.create_access_token(user1.email)
        token2 = auth_service.create_access_token(user2.email)
        token3 = auth_service.create_access_token(user3.email)
        
        return {
            "user1": {"user": user1, "token": token1},
            "admin": {"user": user2, "token": token2},
            "user3": {"user": user3, "token": token3}
        }
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_create_conversation_user_isolation(self, client, test_users):
        """Test that users can only create conversations for themselves."""
        # User1 creates a conversation
        response = client.post(
            "/conversations",
            json={"title": "User1's Conversation"},
            headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
        )
        assert response.status_code == 200
        data = response.json()
        conv_id = data["conversation_id"]
        
        # Verify conversation was created
        assert data["title"] == "User1's Conversation"
        assert conv_id is not None
    
    def test_list_conversations_user_isolation(self, client, test_users):
        """Test that users only see their own conversations."""
        # User1 creates conversations
        response1 = client.post(
            "/conversations",
            json={"title": "User1 Conversation 1"},
            headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
        )
        conv1_id = response1.json()["conversation_id"]
        
        response2 = client.post(
            "/conversations",
            json={"title": "User1 Conversation 2"},
            headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
        )
        conv2_id = response2.json()["conversation_id"]
        
        # User3 creates conversations
        response3 = client.post(
            "/conversations",
            json={"title": "User3 Conversation 1"},
            headers={"Authorization": f"Bearer {test_users['user3']['token']}"}
        )
        conv3_id = response3.json()["conversation_id"]
        
        # User1 should only see their own conversations
        response = client.get(
            "/conversations",
            headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
        )
        assert response.status_code == 200
        conversations = response.json()
        assert len(conversations) == 2
        
        conv_ids = [conv["id"] for conv in conversations]
        assert conv1_id in conv_ids
        assert conv2_id in conv_ids
        assert conv3_id not in conv_ids
        
        # User3 should only see their own conversations
        response = client.get(
            "/conversations",
            headers={"Authorization": f"Bearer {test_users['user3']['token']}"}
        )
        assert response.status_code == 200
        conversations = response.json()
        assert len(conversations) == 1
        assert conversations[0]["id"] == conv3_id
    
    def test_admin_can_see_all_conversations(self, client, test_users):
        """Test that admin can see all conversations."""
        # User1 creates conversations
        client.post(
            "/conversations",
            json={"title": "User1 Conversation"},
            headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
        )
        
        # User3 creates conversations
        client.post(
            "/conversations",
            json={"title": "User3 Conversation"},
            headers={"Authorization": f"Bearer {test_users['user3']['token']}"}
        )
        
        # Admin should see all conversations
        response = client.get(
            "/conversations",
            headers={"Authorization": f"Bearer {test_users['admin']['token']}"}
        )
        assert response.status_code == 200
        conversations = response.json()
        assert len(conversations) == 2
    
    def test_get_conversation_user_isolation(self, client, test_users):
        """Test that users can only access their own conversations."""
        # User1 creates a conversation
        response = client.post(
            "/conversations",
            json={"title": "User1's Private Conversation"},
            headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
        )
        conv_id = response.json()["conversation_id"]
        
        # User1 can access their own conversation
        response = client.get(
            f"/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "User1's Private Conversation"
        
        # User3 cannot access User1's conversation
        response = client.get(
            f"/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {test_users['user3']['token']}"}
        )
        assert response.status_code == 404
        assert "Conversation not found" in response.json()["detail"]
    
    def test_admin_can_access_any_conversation(self, client, test_users):
        """Test that admin can access any conversation."""
        # User1 creates a conversation
        response = client.post(
            "/conversations",
            json={"title": "User1's Conversation"},
            headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
        )
        conv_id = response.json()["conversation_id"]
        
        # Admin can access User1's conversation
        response = client.get(
            f"/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {test_users['admin']['token']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "User1's Conversation"
    
    def test_update_conversation_title_user_isolation(self, client, test_users):
        """Test that users can only update their own conversation titles."""
        # User1 creates a conversation
        response = client.post(
            "/conversations",
            json={"title": "Original Title"},
            headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
        )
        conv_id = response.json()["conversation_id"]
        
        # User1 can update their own conversation title
        response = client.put(
            f"/conversations/{conv_id}/title",
            json={"title": "Updated by User1"},
            headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
        )
        assert response.status_code == 200
        
        # User3 cannot update User1's conversation title
        response = client.put(
            f"/conversations/{conv_id}/title",
            json={"title": "Updated by User3"},
            headers={"Authorization": f"Bearer {test_users['user3']['token']}"}
        )
        assert response.status_code == 404
        assert "Conversation not found" in response.json()["detail"]
    
    def test_delete_conversation_user_isolation(self, client, test_users):
        """Test that users can only delete their own conversations."""
        # User1 creates a conversation
        response = client.post(
            "/conversations",
            json={"title": "User1's Conversation"},
            headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
        )
        conv_id = response.json()["conversation_id"]
        
        # User3 cannot delete User1's conversation
        response = client.delete(
            f"/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {test_users['user3']['token']}"}
        )
        assert response.status_code == 404
        assert "Conversation not found" in response.json()["detail"]
        
        # Verify conversation still exists
        response = client.get(
            f"/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
        )
        assert response.status_code == 200
        
        # User1 can delete their own conversation
        response = client.delete(
            f"/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
        )
        assert response.status_code == 200
        
        # Verify conversation is deleted
        response = client.get(
            f"/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
        )
        assert response.status_code == 404
    
    def test_admin_can_delete_any_conversation(self, client, test_users):
        """Test that admin can delete any conversation."""
        # User1 creates a conversation
        response = client.post(
            "/conversations",
            json={"title": "User1's Conversation"},
            headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
        )
        conv_id = response.json()["conversation_id"]
        
        # Admin can delete User1's conversation
        response = client.delete(
            f"/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {test_users['admin']['token']}"}
        )
        assert response.status_code == 200
        
        # Verify conversation is deleted
        response = client.get(
            f"/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
        )
        assert response.status_code == 404
    
    def test_unauthorized_access_blocked(self, client):
        """Test that unauthorized access is blocked."""
        fake_conv_id = str(uuid.uuid4())
        
        # Try to access conversations without authentication
        response = client.get("/conversations")
        assert response.status_code == 401
        
        # Try to create conversation without authentication
        response = client.post("/conversations", json={"title": "Test"})
        assert response.status_code == 401
        
        # Try to get conversation without authentication
        response = client.get(f"/conversations/{fake_conv_id}")
        assert response.status_code == 401
        
        # Try to update conversation without authentication
        response = client.put(f"/conversations/{fake_conv_id}/title", json={"title": "New Title"})
        assert response.status_code == 401
        
        # Try to delete conversation without authentication
        response = client.delete(f"/conversations/{fake_conv_id}")
        assert response.status_code == 401
    
    def test_chat_endpoint_user_isolation(self, client, test_users):
        """Test that chat endpoint creates user-scoped conversations."""
        # User1 sends a chat message
        response = client.post(
            "/chat",
            json={
                "message": "Hello, I need help with machine learning",
                "per_sub_k": 3,
                "include_context": True
            },
            headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
        )
        assert response.status_code == 200
        data = response.json()
        conv_id = data["conversation_id"]
        
        # User1 can access their conversation
        response = client.get(
            f"/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
        )
        assert response.status_code == 200
        
        # User3 cannot access User1's conversation
        response = client.get(
            f"/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {test_users['user3']['token']}"}
        )
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__])
