from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any, Dict

class UserRegister(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_email: str

class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: str
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

class RequestBase(BaseModel):
    message: str

class RequestCreate(BaseModel):
    message: str
    name: Optional[str] = "Anonymous"
    email: Optional[str] = None
    request_type: Optional[str] = "message"
    amount: Optional[str] = None
    transaction_id: Optional[str] = None
    is_anonymous: Optional[bool] = False

class RequestOut(RequestBase):
    id: int
    name: Optional[str] = None
    email: Optional[str] = None
    photo_path: Optional[str] = None
    request_type: Optional[str] = "request"
    amount: Optional[str] = None
    transaction_id: Optional[str] = None
    is_anonymous: Optional[bool] = False
    created_at: datetime
    status: str

    class Config:
        from_attributes = True

class VerificationLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    ip_address: Optional[str] = None
    status: str
    details: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class LinkCreate(BaseModel):
    title: str
    target_url: str

class LinkOut(BaseModel):
    id: int
    title: str
    target_url: str
    short_code: str
    clicks: int
    created_at: datetime

    class Config:
        from_attributes = True
