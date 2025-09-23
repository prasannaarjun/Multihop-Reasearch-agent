"""
Setup script for authentication module
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_authentication():
    """Setup authentication module"""
    print("Setting up authentication module...")
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("Creating .env file from template...")
        with open("env.example", "r") as f:
            env_content = f.read()
        
        with open(".env", "w") as f:
            f.write(env_content)
        
        print("Please edit .env file with your database configuration and secret key!")
        print("Default values:")
        print("- DATABASE_URL: postgresql://postgres:password@localhost:5432/research_agent_auth")
        print("- SECRET_KEY: your-secret-key-change-this-in-production")
        print()
    
    # Initialize database
    try:
        from auth.init_db import init_database
        init_database()
        print("Authentication setup completed successfully!")
        print()
        print("You can now:")
        print("1. Start the application with: python app.py")
        print("2. Register new users via /auth/register")
        print("3. Login via /auth/login")
        print("4. Access protected endpoints with JWT tokens")
        print()
        print("Default admin credentials:")
        print("Username: admin")
        print("Password: admin123")
        print("Email: admin@research-agent.com")
        print("WARNING: Change the admin password in production!")
        
    except Exception as e:
        print(f"Error setting up authentication: {e}")
        print("Make sure PostgreSQL is running and the database exists.")
        sys.exit(1)

if __name__ == "__main__":
    setup_authentication()
