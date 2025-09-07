from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict,Field
from enum import Enum
import re
from pydantic_core.core_schema import ValidationInfo


class Gender(str, Enum):
    MALE = ('male')
    FEMALE = ('female')
    OTHER = ('other')

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"

class ChatType(str, Enum):
    DIRECT = "direct"
    GROUP = "group"

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

# --------- Message Schemas ---------
class MessageCreate(BaseModel):
    sender_id: int = Field(..., description="ID of the user sending the message")
    receiver_id: int = Field(..., description="ID of the user receiving the message")
    content: str = Field(..., min_length=1, max_length=2000, description="Message content (text, URL, etc.)")
    message_type: MessageType = Field(MessageType.TEXT, description="Type of message (text, image, file)")
    attachment_url: Optional[str] = Field(None, description="URL of an attached file or image")
    parent_message_id: Optional[int] = Field(None, description="ID of the parent message for replies")
    timestamp: Optional[datetime] = Field(None, description="Timestamp of message creation (set by backend)")
    is_read: bool = Field(False, description="Whether the message has been read")

    @field_validator("content")
    def validate_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message content cannot be empty")
        return value

    @field_validator("attachment_url")
    def validate_attachment_url(cls, value: Optional[str]) -> Optional[str]:
        if value and not re.match(r"^https?://[^\s/$.?#].[^\s]*$", value):
            raise ValueError("Invalid URL format for attachment")
        return value

    @field_validator("receiver_id")
    def validate_user_ids(cls, value: int, info: ValidationInfo) -> int:
        sender_id = info.data.get("sender_id")
        if sender_id is not None and value == sender_id:
            raise ValueError("Sender and receiver cannot be the same")
        return value

class MessageResponse(BaseModel):
    id: int = Field(..., description="Unique message ID")
    sender: UserResponse = Field(..., description="Sender user details")
    receiver_id: int = Field(..., description="ID of the user who received the message")
    content: str = Field(..., description="Message content")
    message_type: MessageType = Field(..., description="Type of message")
    attachment_url: Optional[str] = Field(None, description="URL of an attached file or image")
    parent_message_id: Optional[int] = Field(None, description="ID of the parent message for replies")
    timestamp: datetime = Field(..., description="Timestamp of message creation")
    is_read: bool = Field(..., description="Whether the message has been read")

    model_config = ConfigDict(from_attributes=True)

# --------- Chat Schemas ---------
class ChatCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the chat or group")
    chat_type: ChatType = Field(ChatType.DIRECT, description="Type of chat (direct or group)")
    participant_ids: List[int] = Field(..., min_items=2, description="List of user IDs participating in the chat")

    @field_validator("name")
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Chat name cannot be empty")
        return value

    @field_validator("participant_ids")
    def validate_participants(cls, value: List[int], values: dict) -> List[int]:
        if len(set(value)) != len(value):
            raise ValueError("Participant IDs must be unique")
        return value

class ChatResponse(BaseModel):
    id: int = Field(..., description="Unique chat ID")
    name: str = Field(..., description="Name of the chat or group")
    chat_type: ChatType = Field(..., description="Type of chat (direct or group)")
    participants: List[UserResponse] = Field(..., description="List of users in the chat")
    created_at: datetime = Field(..., description="Timestamp of chat creation")
    last_message: Optional[MessageResponse] = Field(None, description="Last message in the chat, if any")

    model_config = ConfigDict(from_attributes=True)

class PaginatedMessages(BaseModel):
    messages: List[MessageResponse] = Field(..., description="List of messages in the chat")
    total: int = Field(..., description="Total number of messages")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of messages per page")

    model_config = ConfigDict(from_attributes=True)