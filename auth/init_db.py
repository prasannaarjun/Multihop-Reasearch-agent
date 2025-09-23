"""
Database initialization script
"""

import os
from dotenv import load_dotenv
from .database import create_tables, engine, Base
from .auth_service import AuthService
from .database import SessionLocal

load_dotenv()

def init_database():
    """Initialize the database with tables and create admin user"""
    print("Creating database tables...")
    create_tables()
    print("Database tables created successfully!")
    
    # Create admin user if it doesn't exist
    db = SessionLocal()
    try:
        auth_service = AuthService(db)
        
        # Check if admin user exists
        admin_user = auth_service.get_user_by_username("admin")
        if not admin_user:
            print("Creating admin user...")
            from .auth_models import UserCreate
            
            admin_data = UserCreate(
                username="admin",
                email="admin@research-agent.com",
                password="admin123"  # Change this in production!
            )
            
            admin_user = auth_service.create_user(admin_data)
            admin_user.is_admin = True
            admin_user.is_active = True
            db.commit()
            
            print("Admin user created successfully!")
            print("Username: admin")
            print("Password: admin123")
            print("Email: admin@research-agent.com")
            print("WARNING: Change the admin password in production!")
        else:
            print("Admin user already exists")
            
    except Exception as e:
        print(f"Error creating admin user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
