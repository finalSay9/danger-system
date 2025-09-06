from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from enum import Enum
import re


class Gender(str, Enum):
    MALE = ('male')
    FEMALE = ('female')
    OTHER = ('other')

class UserBase(BaseModel):
    username: str
    email: EmailStr
    gender: Gender

    @field_validator('username')
    def validate_username(cls, value: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]{3,20}$", value):
            raise ValueError("Username must be 3-20 characters long and contain only letters, numbers, or underscores")
        return value
    
    @field_validator('email')
    def normalize_email(cls, value: EmailStr) -> str:
        return value.lower()


class UserCreate(UserBase):
   
    password: str
    first_name: Optional[str]=None
    last_name: Optional[str]=None


    @field_validator('password')
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError('password must be 8 characters long')
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", value):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("Password must contain at least one special character")
        return value
    
   

    



class UserResponse(UserBase):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: datetime
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)

    
class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator('email')
    def normalize_email(cls, value: EmailStr) -> EmailStr:
        return value.lower()


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: Optional[int] = None  # Seconds until expiration
    refresh_token: Optional[str] = None  # For refresh token support

class TokenData(BaseModel):
    email: EmailStr | None=None
    user_id: Optional[int] = None
    scopes: List[str] = []  # For r

