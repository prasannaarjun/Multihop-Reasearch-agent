#!/usr/bin/env python3
"""
Debug script to isolate login issues
"""

import traceback
import sys

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    try:
        from auth.database import get_db, User
        print("✅ Database imports OK")
        
        from auth.auth_service import AuthService
        print("✅ AuthService import OK")
        
        from auth.auth_models import UserLogin
        print("✅ Auth models import OK")
        
        from auth.auth_routes import auth_router
        print("✅ Auth routes import OK")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False

def test_database_connection():
    """Test database connection"""
    print("\nTesting database connection...")
    try:
        from auth.database import get_db, User
        db = next(get_db())
        users = db.query(User).all()
        print(f"✅ Database connection OK - found {len(users)} users")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        traceback.print_exc()
        return False

def test_auth_service():
    """Test authentication service"""
    print("\nTesting authentication service...")
    try:
        from auth.database import get_db
        from auth.auth_service import AuthService
        from auth.auth_models import UserLogin
        
        db = next(get_db())
        auth_service = AuthService(db)
        
        # Test password hashing
        password = "testuser"
        hashed = auth_service.get_password_hash(password)
        print(f"✅ Password hashing OK - {len(hashed)} chars")
        
        # Test password verification
        is_valid = auth_service.verify_password(password, hashed)
        print(f"✅ Password verification: {is_valid}")
        
        # Test user lookup
        user = auth_service.get_user_by_email("test@example.com")
        if user:
            print(f"✅ User lookup OK - {user.username}")
        else:
            print("❌ User not found")
            return False
        
        # Test authentication
        login_data = UserLogin(email="test@example.com", password="testuser")
        auth_user = auth_service.authenticate_user(login_data.email, login_data.password)
        if auth_user:
            print(f"✅ Authentication OK - {auth_user.username}")
        else:
            print("❌ Authentication failed")
            return False
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Auth service error: {e}")
        traceback.print_exc()
        return False

def test_login_flow():
    """Test the complete login flow"""
    print("\nTesting complete login flow...")
    try:
        from auth.database import get_db
        from auth.auth_service import AuthService
        from auth.auth_models import UserLogin
        
        db = next(get_db())
        auth_service = AuthService(db)
        
        login_data = UserLogin(email="test@example.com", password="testuser")
        token = auth_service.login_user(login_data)
        print(f"✅ Login flow OK - token type: {token.token_type}")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Login flow error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Debug Login Issues ===\n")
    
    success = True
    success &= test_imports()
    success &= test_database_connection()
    success &= test_auth_service()
    success &= test_login_flow()
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
