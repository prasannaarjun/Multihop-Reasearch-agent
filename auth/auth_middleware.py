"""
JWT Authentication middleware for FastAPI
"""

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from .database import get_db
from .auth_service import AuthService
from .auth_models import TokenData

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)
optional_security = HTTPBearer(auto_error=False)

class AuthMiddleware:
    """Authentication middleware class"""
    
    @staticmethod
    def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ) -> TokenData:
        """Get current authenticated user from JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            if credentials is None:
                raise credentials_exception
            token = credentials.credentials
            auth_service = AuthService(db)
            token_data = auth_service.verify_token(token)
            
            if token_data is None:
                raise credentials_exception
                
            return token_data
        except Exception:
            raise credentials_exception
    
    @staticmethod
    def get_current_active_user(
        current_user: TokenData = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> TokenData:
        """Get current active user (not disabled)"""
        auth_service = AuthService(db)
        user = auth_service.get_user_by_id(current_user.user_id)
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        return current_user
    
    @staticmethod
    def get_current_admin_user(
        current_user: TokenData = Depends(get_current_active_user)
    ) -> TokenData:
        """Get current admin user"""
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    
    @staticmethod
    def get_optional_current_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
        db: Session = Depends(get_db)
    ) -> Optional[TokenData]:
        """Get current user if authenticated, None otherwise"""
        if not credentials:
            return None
        
        try:
            token = credentials.credentials
            auth_service = AuthService(db)
            token_data = auth_service.verify_token(token)
            return token_data
        except Exception:
            return None

# Convenience functions for dependency injection
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> TokenData:
    """Dependency to get current authenticated user"""
    return AuthMiddleware.get_current_user(credentials, db)

def get_current_active_user(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> TokenData:
    """Dependency to get current active user"""
    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(current_user.user_id)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return current_user

def get_current_admin_user(
    current_user: TokenData = Depends(get_current_active_user)
) -> TokenData:
    """Dependency to get current admin user"""
    return AuthMiddleware.get_current_admin_user(current_user)

def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: Session = Depends(get_db)
) -> Optional[TokenData]:
    """Dependency to get current user if authenticated"""
    return AuthMiddleware.get_optional_current_user(credentials, db)
