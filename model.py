from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime, Enum as SqlEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import CITEXT  # Optional: for PostgreSQL
from typing import Optional
import enum
from database import Base
from datetime import datetime



class Gender(str, enum.Enum):
    MALE = 'male'
    FEMALE = 'female'
    OTHER = 'other'

class MessageType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"

class ChatType(str, enum.Enum):
    DIRECT = "direct"
    GROUP = "group"


class User(Base):
    __tablename__ = 'users'
    """Database model for users."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)  # Use String(255) for non-PostgreSQL
    first_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    gender: Mapped[Optional[Gender]] = mapped_column(SqlEnum(Gender), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_login: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        # Optional: Add check constraint for email format (PostgreSQL only)
        # CheckConstraint("email ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'", name='valid_email'),
    )

class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(String(2000), nullable=False)
    message_type: Mapped[MessageType] = mapped_column(SqlEnum(MessageType), nullable=False, default=MessageType.TEXT)
    attachment_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    parent_message_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("messages.id"), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sender: Mapped["User"] = relationship("User", foreign_keys=[sender_id])
    receiver: Mapped["User"] = relationship("User", foreign_keys=[receiver_id])

class Chat(Base):
    __tablename__ = "chats"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    chat_type: Mapped[ChatType] = mapped_column(SqlEnum(ChatType), nullable=False, default=ChatType.DIRECT)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    participants = relationship("User", secondary="chat_participants", back_populates="chats")
    messages = relationship("Message", back_populates="chat")

class ChatParticipant(Base):
    __tablename__ = "chat_participants"
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)