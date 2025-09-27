#!/usr/bin/env python3
"""
Test script to verify authentication service functionality
"""

from auth.database import get_db
from auth.auth_service import AuthService
from auth.auth_models import UserLogin

def test_auth_service():
    """Test the authentication service directly"""
    print("Testing authentication service...")
    
    try:
        # Get database session
        db = next(get_db())
        auth_service = AuthService(db)
        
        # Test password hashing
        print("1. Testing password hashing...")
        password = "testuser"
        hashed = auth_service.get_password_hash(password)
        print(f"   Hash generated: {len(hashed)} characters")
        
        # Test password verification
        print("2. Testing password verification...")
        is_valid = auth_service.verify_password(password, hashed)
        print(f"   Password verification: {'✅ Success' if is_valid else '❌ Failed'}")
        
        # Test user lookup
        print("3. Testing user lookup...")
        user = auth_service.get_user_by_email("test@example.com")
        if user:
            print(f"   User found: {user.username} ({user.email})")
            print(f"   User active: {user.is_active}")
        else:
            print("   ❌ User not found")
            return False
        
        # Test authentication
        print("4. Testing user authentication...")
        login_data = UserLogin(email="test@example.com", password="testuser")
        authenticated_user = auth_service.authenticate_user(login_data.email, login_data.password)
        if authenticated_user:
            print(f"   ✅ Authentication successful: {authenticated_user.username}")
        else:
            print("   ❌ Authentication failed")
            return False
        
        # Test login (full flow)
        print("5. Testing full login flow...")
        try:
            token = auth_service.login_user(login_data)
            print(f"   ✅ Login successful!")
            print(f"   Access token: {token.access_token[:50]}...")
            print(f"   Token type: {token.token_type}")
            print(f"   Expires in: {token.expires_in} seconds")
            return True
        except Exception as e:
            print(f"   ❌ Login failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing auth service: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_auth_service()
    if success:
        print("\n✅ All authentication service tests passed!")
    else:
        print("\n❌ Some authentication service tests failed!")
        sys.exit(1)
