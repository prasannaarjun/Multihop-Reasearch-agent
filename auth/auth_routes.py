"""
Authentication API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from .database import get_db, User
from .auth_service import AuthService
from .auth_models import (
    UserCreate, UserLogin, Token, UserResponse,
    PasswordChange, UserUpdate, SessionInfo, RefreshRequest, LogoutRequest
)
from .auth_middleware import get_current_active_user, get_current_admin_user, TokenData

# Create router
auth_router = APIRouter(prefix="/auth", tags=["authentication"])

@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    auth_service = AuthService(db)
    
    try:
        user = auth_service.create_user(user_data)
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )

@auth_router.post("/login", response_model=Token)
async def login_user(
    user_login: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """Login user and set refresh token cookie; return access token JSON"""
    auth_service = AuthService(db)
    
    try:
        # Get client IP and user agent
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        token, refresh_token = auth_service.login_user(
            user_login, 
            ip_address=client_ip, 
            user_agent=user_agent
        )
        # Determine cookie security flags based on environment
        origin = request.headers.get("origin", "") or ""
        is_localhost = origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1")
        is_https = origin.startswith("https://")
        # Cookie flags: HTTPS => SameSite=None + Secure; Localhost HTTP => SameSite=Lax without Secure
        if is_https:
            use_secure = True
            samesite_mode = "None"
        elif is_localhost:
            use_secure = False
            samesite_mode = "Lax"
        else:
            use_secure = False
            samesite_mode = "Lax"
        refresh_max_age = 60 * 60 * 24 * 7  # 7 days

        # Include refresh_token in body as dev fallback when cookie is blocked
        token_payload = token.model_dump()
        token_payload["refresh_token"] = refresh_token
        response = JSONResponse(content=jsonable_encoder(token_payload))
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=use_secure,
            samesite=samesite_mode,
            max_age=refresh_max_age,
            path="/",
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during login"
        )

@auth_router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    auth_service = AuthService(db)
    # Prefer cookie; fallback to JSON body for backward compatibility
    cookie_refresh = request.cookies.get("refresh_token")
    body_refresh = None
    # Try Pydantic model for clarity if body provided
    try:
        data = await request.json()
        if isinstance(data, dict) and "refresh_token" in data:
            body_refresh = RefreshRequest(**data).refresh_token
    except Exception:
        pass
    provided_refresh = cookie_refresh or body_refresh
    if not provided_refresh:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="refresh_token is required"
        )

    token = auth_service.refresh_access_token(provided_refresh)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Refresh cookie expiry
    origin = request.headers.get("origin", "") or ""
    is_localhost = origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1")
    is_https = origin.startswith("https://")
    if is_https:
        use_secure = True
        samesite_mode = "None"
    elif is_localhost:
        use_secure = False
        samesite_mode = "Lax"
    else:
        use_secure = False
        samesite_mode = "Lax"
    refresh_max_age = 60 * 60 * 24 * 7

    response = JSONResponse(content=jsonable_encoder(token.model_dump()))
    if cookie_refresh:
        response.set_cookie(
            key="refresh_token",
            value=cookie_refresh,
            httponly=True,
            secure=use_secure,
            samesite=samesite_mode,
            max_age=refresh_max_age,
            path="/",
        )
    return response

@auth_router.post("/logout")
async def logout_user(
    request: Request,
    db: Session = Depends(get_db)
):
    """Logout user by invalidating refresh token"""
    auth_service = AuthService(db)
    
    # Prefer cookie; fallback to JSON body
    cookie_refresh = request.cookies.get("refresh_token")
    body_refresh = None
    try:
        data = await request.json()
        if isinstance(data, dict) and "refresh_token" in data:
            body_refresh = LogoutRequest(**data).refresh_token
    except Exception:
        pass
    provided_refresh = cookie_refresh or body_refresh
    if not provided_refresh:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="refresh_token is required"
        )

    success = auth_service.logout_user(provided_refresh)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token"
        )

    # Clear cookie
    origin = request.headers.get("origin", "") or ""
    is_localhost = origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1")
    is_https = origin.startswith("https://")
    if is_https:
        use_secure = True
        samesite_mode = "None"
    elif is_localhost:
        use_secure = False
        samesite_mode = "Lax"
    else:
        use_secure = False
        samesite_mode = "Lax"

    response = JSONResponse(content={"message": "Successfully logged out"})
    response.delete_cookie(
        key="refresh_token",
        path="/",
        secure=use_secure,
        samesite=samesite_mode,
    )
    return response

@auth_router.post("/logout-all")
async def logout_all_sessions(
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Logout all sessions for current user"""
    auth_service = AuthService(db)
    
    sessions_count = auth_service.logout_all_sessions(current_user.user_id)
    return {"message": f"Logged out from {sessions_count} sessions"}

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(current_user.user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)

@auth_router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user information"""
    auth_service = AuthService(db)
    
    try:
        user = auth_service.update_user(current_user.user_id, user_update.model_dump(exclude_unset=True))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user"
        )

@auth_router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change current user password"""
    auth_service = AuthService(db)
    
    try:
        success = auth_service.change_password(current_user.user_id, password_change)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error changing password"
        )

@auth_router.get("/sessions", response_model=List[SessionInfo])
async def get_user_sessions(
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's active sessions"""
    auth_service = AuthService(db)
    sessions = auth_service.get_user_sessions(current_user.user_id)
    
    return [
        SessionInfo(
            session_id=session.id,
            created_at=session.created_at,
            expires_at=session.expires_at,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            is_active=session.is_active
        )
        for session in sessions
    ]

# Admin routes
@auth_router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: TokenData = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    auth_service = AuthService(db)
    users = db.query(User).all()
    
    return [UserResponse.model_validate(user) for user in users]

@auth_router.put("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    current_user: TokenData = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Deactivate a user account (admin only)"""
    auth_service = AuthService(db)
    
    success = auth_service.deactivate_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deactivated successfully"}

@auth_router.put("/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    current_user: TokenData = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Activate a user account (admin only)"""
    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    return {"message": "User activated successfully"}

@auth_router.put("/users/{user_id}/admin")
async def toggle_admin_status(
    user_id: int,
    is_admin: bool,
    current_user: TokenData = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Toggle admin status for a user (admin only)"""
    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_admin = is_admin
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    return {"message": f"User admin status set to {is_admin}"}
