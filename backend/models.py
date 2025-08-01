# backend/models.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import os
from datetime import datetime
import uuid

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chat_history.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联的消息
    messages = relationship("ChatMessage", back_populates="session", order_by="ChatMessage.timestamp")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String(10))  # user 或 assistant
    content = Column(Text)
    thinking_content = Column(Text)  # 存储思考过程
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # 关联的会话
    session = relationship("ChatSession", back_populates="messages")

Base.metadata.create_all(bind=engine)