"""
Authentication module for Multi-hop Research Agent
Provides JWT-based authentication with PostgreSQL backend
"""

from .auth_service import AuthService
from .auth_models import UserCreate, UserLogin, Token, UserResponse, TokenData
from .auth_routes import auth_router
from .auth_middleware import AuthMiddleware, get_current_active_user, get_optional_current_user, get_current_admin_user
from .database import get_db, engine, Base

__all__ = [
    "AuthService",
    "UserCreate", 
    "UserLogin",
    "Token",
    "UserResponse",
    "TokenData",
    "auth_router",
    "AuthMiddleware",
    "get_current_active_user",
    "get_optional_current_user", 
    "get_current_admin_user",
    "get_db",
    "engine",
    "Base"
]
