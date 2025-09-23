"""
Tests for authentication module
"""

import pytest
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Set test database URL
os.environ["DATABASE_URL"] = "sqlite:///./test_auth.db"
os.environ["SECRET_KEY"] = "test-secret-key"

from auth.database import Base, get_db
from auth.auth_service import AuthService
from auth.auth_models import UserCreate, UserLogin
from app import app

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def setup_database():
    """Setup test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    os.remove("test_auth.db")

@pytest.fixture
def client(setup_database):
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def auth_service(setup_database):
    """Create auth service for testing"""
    db = TestingSessionLocal()
    try:
        yield AuthService(db)
    finally:
        db.close()

class TestAuthService:
    """Test authentication service"""
    
    def test_create_user(self, auth_service):
        """Test user creation"""
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        
        user = auth_service.create_user(user_data)
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active == True
        assert user.is_admin == False
    
    def test_create_duplicate_user(self, auth_service):
        """Test creating duplicate user fails"""
        user_data = UserCreate(
            username="testuser2",
            email="test2@example.com",
            password="testpassword123"
        )
        
        # Create first user
        auth_service.create_user(user_data)
        
        # Try to create duplicate username
        user_data2 = UserCreate(
            username="testuser2",
            email="test3@example.com",
            password="testpassword123"
        )
        
        with pytest.raises(ValueError, match="Username already registered"):
            auth_service.create_user(user_data2)
    
    def test_authenticate_user(self, auth_service):
        """Test user authentication"""
        user_data = UserCreate(
            username="testuser3",
            email="test3@example.com",
            password="testpassword123"
        )
        
        auth_service.create_user(user_data)
        
        # Test valid credentials
        user = auth_service.authenticate_user("testuser3", "testpassword123")
        assert user is not None
        assert user.username == "testuser3"
        
        # Test invalid credentials
        user = auth_service.authenticate_user("testuser3", "wrongpassword")
        assert user is None
        
        user = auth_service.authenticate_user("nonexistent", "testpassword123")
        assert user is None
    
    def test_login_user(self, auth_service):
        """Test user login"""
        user_data = UserCreate(
            username="testuser4",
            email="test4@example.com",
            password="testpassword123"
        )
        
        auth_service.create_user(user_data)
        
        login_data = UserLogin(username="testuser4", password="testpassword123")
        token = auth_service.login_user(login_data)
        
        assert token.access_token is not None
        assert token.token_type == "bearer"
        assert token.user.username == "testuser4"
        assert token.expires_in > 0
    
    def test_verify_token(self, auth_service):
        """Test token verification"""
        user_data = UserCreate(
            username="testuser5",
            email="test5@example.com",
            password="testpassword123"
        )
        
        user = auth_service.create_user(user_data)
        login_data = UserLogin(username="testuser5", password="testpassword123")
        token = auth_service.login_user(login_data)
        
        # Verify token
        token_data = auth_service.verify_token(token.access_token)
        assert token_data is not None
        assert token_data.username == "testuser5"
        assert token_data.user_id == user.id
        assert token_data.is_admin == False
        
        # Test invalid token
        invalid_token_data = auth_service.verify_token("invalid_token")
        assert invalid_token_data is None

class TestAuthAPI:
    """Test authentication API endpoints"""
    
    def test_register_user(self, client):
        """Test user registration endpoint"""
        user_data = {
            "username": "apiuser",
            "email": "api@example.com",
            "password": "testpassword123"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["username"] == "apiuser"
        assert data["email"] == "api@example.com"
        assert "id" in data
        assert data["is_active"] == True
        assert data["is_admin"] == False
    
    def test_register_duplicate_user(self, client):
        """Test registering duplicate user fails"""
        user_data = {
            "username": "apiuser2",
            "email": "api2@example.com",
            "password": "testpassword123"
        }
        
        # Register first user
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        
        # Try to register duplicate
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_login_user(self, client):
        """Test user login endpoint"""
        # Register user first
        user_data = {
            "username": "loginuser",
            "email": "login@example.com",
            "password": "testpassword123"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        
        # Login user
        login_data = {
            "username": "loginuser",
            "password": "testpassword123"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert data["user"]["username"] == "loginuser"
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]
    
    def test_protected_endpoint_without_auth(self, client):
        """Test accessing protected endpoint without authentication"""
        response = client.post("/ask", json={"question": "test question"})
        assert response.status_code == 401
    
    def test_protected_endpoint_with_auth(self, client):
        """Test accessing protected endpoint with authentication"""
        # Register and login user
        user_data = {
            "username": "protecteduser",
            "email": "protected@example.com",
            "password": "testpassword123"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        
        login_data = {
            "username": "protecteduser",
            "password": "testpassword123"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to access protected endpoint
        response = client.post("/ask", json={"question": "test question"}, headers=headers)
        # This might fail due to research agent not being initialized in test
        # but we're testing that authentication works
        assert response.status_code in [200, 503]  # 503 if agent not initialized
    
    def test_get_current_user_info(self, client):
        """Test getting current user information"""
        # Register and login user
        user_data = {
            "username": "infouser",
            "email": "info@example.com",
            "password": "testpassword123"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        
        login_data = {
            "username": "infouser",
            "password": "testpassword123"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get user info
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["username"] == "infouser"
        assert data["email"] == "info@example.com"
        assert "id" in data
        assert "created_at" in data

if __name__ == "__main__":
    pytest.main([__file__])
