"""
Test database connection
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Environment variables:")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")
print(f"SECRET_KEY: {os.getenv('SECRET_KEY')}")

# Test database connection
try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/research_agent_auth")
    print(f"\nTrying to connect to: {DATABASE_URL}")
    
    engine = create_engine(DATABASE_URL)
    
    # Test connection
    with engine.connect() as conn:
        from sqlalchemy import text
        result = conn.execute(text("SELECT 1"))
        print("✓ Database connection successful!")
        print(f"Test query result: {result.fetchone()}")
        
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    print("\nPlease check:")
    print("1. PostgreSQL is running")
    print("2. Database exists")
    print("3. User has proper permissions")
    print("4. .env file has correct DATABASE_URL")
