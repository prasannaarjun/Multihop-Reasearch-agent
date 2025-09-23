"""
Test authentication integration with the frontend
"""
import pytest
import requests
import json
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_auth_endpoints_exist():
    """Test that all authentication endpoints are available"""
    
    # Test registration endpoint
    response = client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    })
    assert response.status_code == 201
    
    # Test login endpoint
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    
    # Test protected endpoint
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["username"] == "testuser"
    assert user_data["email"] == "test@example.com"

def test_protected_routes_require_auth():
    """Test that protected routes require authentication"""
    
    # Test ask endpoint without auth
    response = client.post("/ask", json={
        "question": "What is AI?",
        "per_sub_k": 3
    })
    assert response.status_code == 401
    
    # Test upload endpoint without auth
    response = client.post("/upload", files={"file": ("test.txt", "test content", "text/plain")})
    assert response.status_code == 401
    
    # Test chat endpoint without auth
    response = client.post("/chat", json={
        "message": "Hello",
        "conversation_id": None,
        "per_sub_k": 3,
        "include_context": True
    })
    assert response.status_code == 401

def test_auth_flow_integration():
    """Test complete authentication flow"""
    
    # Register user
    register_data = {
        "username": "integrationtest",
        "email": "integration@example.com",
        "password": "testpass123",
        "full_name": "Integration Test User"
    }
    
    response = client.post("/auth/register", json=register_data)
    assert response.status_code == 201
    
    # Login user
    login_data = {
        "email": "integration@example.com",
        "password": "testpass123"
    }
    
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    tokens = response.json()
    
    # Use token for protected operations
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    
    # Test user info
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    user_info = response.json()
    assert user_info["username"] == "integrationtest"
    
    # Test logout
    response = client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    
    # Verify token is invalidated
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401

if __name__ == "__main__":
    pytest.main([__file__])
