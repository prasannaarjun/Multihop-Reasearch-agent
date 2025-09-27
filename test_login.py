#!/usr/bin/env python3
"""
Simple test script to verify login functionality
"""

import requests
import json
import time
import sys

def test_login():
    """Test the login endpoint"""
    url = 'http://127.0.0.1:8000/auth/login'
    data = {'email': 'test@example.com', 'password': 'testuser'}
    headers = {'Content-Type': 'application/json'}

    try:
        print("Testing login endpoint...")
        response = requests.post(url, json=data, headers=headers)
        print(f'Status Code: {response.status_code}')
        print(f'Response: {response.text}')
        
        if response.status_code == 200:
            print('✅ Login successful!')
            return True
        else:
            print('❌ Login failed')
            return False
    except requests.exceptions.ConnectionError:
        print('❌ Server is not running')
        return False
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get('http://127.0.0.1:8000/health')
        print(f'Health check: {response.status_code}')
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("Testing authentication endpoints...")
    
    if test_health():
        print("✅ Server is running")
        test_login()
    else:
        print("❌ Server is not responding")
        print("Please start the server with: python app.py")
