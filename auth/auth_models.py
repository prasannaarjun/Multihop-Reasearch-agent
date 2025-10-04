"""
Pydantic models for authentication API
"""

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
from .validators import (
    validate_username, validate_password, validate_email,
    validate_full_name, ValidationError as ValidatorError
)

class UserBase(BaseModel):
    """Base user model"""
    username: str
    email: EmailStr
    
    @field_validator('username')
    @classmethod
    def validate_username_field(cls, v):
        try:
            validate_username(v)
            return v.lower()
        except ValidatorError as e:
            raise ValueError(str(e))
    
    @field_validator('email')
    @classmethod
    def validate_email_field(cls, v):
        try:
            # EmailStr already validates format, but add our additional checks
            validate_email(str(v))
            return v
        except ValidatorError as e:
            raise ValueError(str(e))

class UserCreate(UserBase):
    """User creation model"""
    password: str
    full_name: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def validate_password_field(cls, v):
        try:
            validate_password(v)
            return v
        except ValidatorError as e:
            raise ValueError(str(e))
    
    @field_validator('full_name')
    @classmethod
    def validate_full_name_field(cls, v):
        if v is not None:
            try:
                validate_full_name(v)
            except ValidatorError as e:
                raise ValueError(str(e))
        return v

class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str

class UserResponse(UserBase):
    """User response model"""
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    full_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class TokenData(BaseModel):
    """Token data model for JWT payload"""
    email: Optional[str] = None
    user_id: Optional[int] = None
    is_admin: Optional[bool] = None

class PasswordChange(BaseModel):
    """Password change model"""
    current_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        try:
            validate_password(v)
            return v
        except ValidatorError as e:
            raise ValueError(str(e))

class UserUpdate(BaseModel):
    """User update model"""
    email: Optional[EmailStr] = None
    profile_data: Optional[str] = None

class SessionInfo(BaseModel):
    """Session information model"""
    session_id: int
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)
