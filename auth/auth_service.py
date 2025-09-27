"""
Authentication service with JWT handling and user management
"""

import os
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy import and_
from .database import User, UserSession
from .auth_models import UserCreate, UserLogin, TokenData, UserResponse, PasswordChange, Token

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Password hashing - using bcrypt directly
BCRYPT_ROUNDS = 12

class AuthService:
    """Authentication service class"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        # Ensure password is not longer than 72 bytes (bcrypt limit)
        if len(plain_password.encode('utf-8')) > 72:
            plain_password = plain_password[:72]
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        # Ensure password is not longer than 72 bytes (bcrypt limit)
        if len(password.encode('utf-8')) > 72:
            password = password[:72]
        salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            is_admin: bool = payload.get("is_admin", False)
            
            if email is None or user_id is None:
                return None
                
            return TokenData(email=email, user_id=user_id, is_admin=is_admin)
        except JWTError:
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username.lower()).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email.lower()).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if user already exists
        if self.get_user_by_username(user_data.username):
            raise ValueError("Username already registered")
        
        if self.get_user_by_email(user_data.email):
            raise ValueError("Email already registered")
        
        # Create user
        hashed_password = self.get_password_hash(user_data.password)
        db_user = User(
            username=user_data.username.lower(),
            email=user_data.email.lower(),
            hashed_password=hashed_password,
            full_name=user_data.full_name
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password"""
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    def login_user(self, user_login: UserLogin, ip_address: str = None, user_agent: str = None) -> Token:
        """Login a user and return tokens"""
        user = self.authenticate_user(user_login.email, user_login.password)
        if not user:
            raise ValueError("Invalid email or password")
        
        if not user.is_active:
            raise ValueError("User account is disabled")
        
        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        # Create tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = self.create_access_token(
            data={"sub": user.email, "user_id": user.id, "is_admin": user.is_admin},
            expires_delta=access_token_expires
        )
        
        refresh_token = self.create_refresh_token(
            data={"sub": user.email, "user_id": user.id, "is_admin": user.is_admin}
        )
        
        # Create session record
        session = UserSession(
            user_id=user.id,
            session_token=refresh_token,
            expires_at=datetime.utcnow() + refresh_token_expires,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(session)
        self.db.commit()
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Token]:
        """Refresh access token using refresh token"""
        token_data = self.verify_token(refresh_token)
        if not token_data or not token_data.user_id:
            return None
        
        # Check if session exists and is active
        session = self.db.query(UserSession).filter(
            and_(
                UserSession.session_token == refresh_token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).first()
        
        if not session:
            return None
        
        user = self.get_user_by_id(token_data.user_id)
        if not user or not user.is_active:
            return None
        
        # Create new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"sub": user.email, "user_id": user.id, "is_admin": user.is_admin},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )
    
    def logout_user(self, refresh_token: str) -> bool:
        """Logout user by deactivating session"""
        session = self.db.query(UserSession).filter(
            UserSession.session_token == refresh_token
        ).first()
        
        if session:
            session.is_active = False
            self.db.commit()
            return True
        return False
    
    def logout_all_sessions(self, user_id: int) -> int:
        """Logout all sessions for a user"""
        sessions = self.db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        ).all()
        
        for session in sessions:
            session.is_active = False
        
        self.db.commit()
        return len(sessions)
    
    def change_password(self, user_id: int, password_change: PasswordChange) -> bool:
        """Change user password"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Verify current password
        if not self.verify_password(password_change.current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")
        
        # Update password
        user.hashed_password = self.get_password_hash(password_change.new_password)
        user.updated_at = datetime.utcnow()
        self.db.commit()
        
        # Logout all sessions for security
        self.logout_all_sessions(user_id)
        
        return True
    
    def update_user(self, user_id: int, user_update: Dict[str, Any]) -> Optional[User]:
        """Update user information"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Check email uniqueness if email is being updated
        if "email" in user_update and user_update["email"] != user.email:
            existing_user = self.get_user_by_email(user_update["email"])
            if existing_user:
                raise ValueError("Email already registered")
        
        # Update fields
        for field, value in user_update.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user account"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        self.db.commit()
        
        # Logout all sessions
        self.logout_all_sessions(user_id)
        
        return True
    
    def get_user_sessions(self, user_id: int) -> list:
        """Get all active sessions for a user"""
        sessions = self.db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).all()
        return sessions
