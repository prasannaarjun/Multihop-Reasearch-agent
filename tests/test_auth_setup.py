"""
Simple test script to verify authentication setup
"""

import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_auth_setup():
    """Test authentication setup"""
    print("Testing authentication setup...")
    
    # Test 1: Register a new user
    print("\n1. Testing user registration...")
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        if response.status_code == 201:
            print("✓ User registration successful")
            user_info = response.json()
            print(f"  User ID: {user_info['id']}")
            print(f"  Username: {user_info['username']}")
            print(f"  Email: {user_info['email']}")
        else:
            print(f"✗ User registration failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server. Make sure the server is running on localhost:8000")
        return False
    except Exception as e:
        print(f"✗ Error during registration: {e}")
        return False
    
    # Test 2: Login user
    print("\n2. Testing user login...")
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            print("✓ User login successful")
            token_info = response.json()
            print(f"  Access token: {token_info['access_token'][:20]}...")
            print(f"  Token type: {token_info['token_type']}")
            print(f"  Expires in: {token_info['expires_in']} seconds")
            access_token = token_info['access_token']
        else:
            print(f"✗ User login failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error during login: {e}")
        return False
    
    # Test 3: Access protected endpoint
    print("\n3. Testing protected endpoint access...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        if response.status_code == 200:
            print("✓ Protected endpoint access successful")
            user_info = response.json()
            print(f"  Current user: {user_info['username']}")
            print(f"  Email: {user_info['email']}")
            print(f"  Is admin: {user_info['is_admin']}")
        else:
            print(f"✗ Protected endpoint access failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error accessing protected endpoint: {e}")
        return False
    
    # Test 4: Test without authentication
    print("\n4. Testing access without authentication...")
    try:
        response = requests.get(f"{BASE_URL}/auth/me")
        if response.status_code == 401:
            print("✓ Unauthenticated access properly blocked")
        else:
            print(f"✗ Unauthenticated access should be blocked: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error testing unauthenticated access: {e}")
        return False
    
    print("\n✓ All authentication tests passed!")
    return True

if __name__ == "__main__":
    success = test_auth_setup()
    if success:
        print("\n🎉 Authentication module is working correctly!")
        print("\nNext steps:")
        print("1. Start the server: python app.py")
        print("2. Access the API documentation at: http://localhost:8000/docs")
        print("3. Register new users or use the default admin account")
        print("4. Use JWT tokens to access protected endpoints")
    else:
        print("\n❌ Authentication setup has issues. Please check the errors above.")
