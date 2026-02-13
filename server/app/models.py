"""
Pydantic models for the store platform API.
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr


# Store models (current functionality)
class StoreCreate(BaseModel):
    """Model for creating a new store"""
    name: str
    engine: Literal["woocommerce", "medusa"]


class StoreResponse(BaseModel):
    """Model for store API responses"""
    id: str
    name: str
    engine: str
    namespace: Optional[str] = None
    host: Optional[str] = None
    status: str
    url: Optional[str] = None
    created_at: datetime
    error: Optional[str] = None
    password: Optional[str] = None
    creator_id: Optional[str] = None
    creator_name: Optional[str] = None


class StoreStatusUpdate(BaseModel):
    """Model for orchestrator status callbacks"""
    status: Literal["PROVISIONING", "READY", "FAILED"]
    url: Optional[str] = None
    error: Optional[str] = None
    password: Optional[str] = None


# Auth models
class UserSignup(BaseModel):
    """Model for user signup"""
    email: EmailStr
    password: str
    name: str


class UserLogin(BaseModel):
    """Model for user login"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Model for user API responses"""
    id: str
    email: str
    name: str
    created_at: datetime


class TokenResponse(BaseModel):
    """Model for auth token response"""
    access_token: str
    token_type: str
    user: UserResponse


class SessionResponse(BaseModel):
    """Model for session API responses"""
    id: str
    user_id: str
    created_at: datetime
    expires_at: datetime