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
    status: str
    url: Optional[str] = None
    created_at: datetime
    error: Optional[str] = None


# Future auth models (when authentication is added)
class UserCreate(BaseModel):
    """Model for creating a new user"""
    email: EmailStr
    password: str
    name: str


class UserResponse(BaseModel):
    """Model for user API responses"""
    id: str
    email: str
    name: str
    created_at: datetime
    is_active: bool


class SessionCreate(BaseModel):
    """Model for creating a user session"""
    user_id: str
    expires_at: datetime


class SessionResponse(BaseModel):
    """Model for session API responses"""
    id: str
    user_id: str
    created_at: datetime
    expires_at: datetime