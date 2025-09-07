from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime, Enum as SqlEnum, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import CITEXT  # Optional: for PostgreSQL
from typing import Optional
import enum
from database import Base
from datetime import datetime
from fastapi import WebSocket, Depends
from sqlalchemy.orm import Session

# Association table for many-to-many relationship between User and Chat
chat_participants = Table(
    "chat_participants",
    Base.metadata,
    Column("chat_id", Integer, ForeignKey("chats.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True)
)

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
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    gender: Mapped[Optional[Gender]] = mapped_column(SqlEnum(Gender), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_login: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    chats = relationship("Chat", secondary=chat_participants, back_populates="participants")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")

    __table_args__ = (
        # Optional: Add check constraint for email format (PostgreSQL only)
        # CheckConstraint("email ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'", name='valid_email'),
    )


class Chat(Base):
    __tablename__ = "chats"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    chat_type: Mapped[ChatType] = mapped_column(SqlEnum(ChatType), nullable=False, default=ChatType.DIRECT)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    participants = relationship("User", secondary=chat_participants, back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)  # Made optional for group chats
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id"), nullable=False)  # 🔑 ADDED THIS LINE
    content: Mapped[str] = mapped_column(String(2000), nullable=False)
    message_type: Mapped[MessageType] = mapped_column(SqlEnum(MessageType), nullable=False, default=MessageType.TEXT)
    attachment_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    parent_message_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("messages.id"), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    sender: Mapped["User"] = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")
    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")
    
    # Self-referential relationship for reply messages
    parent_message: Mapped[Optional["Message"]] = relationship("Message", remote_side=[id])