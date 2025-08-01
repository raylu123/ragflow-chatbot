# backend/crud.py
from sqlalchemy.orm import Session
from .models import ChatSession, ChatMessage
from typing import List
import csv
from io import StringIO
from datetime import datetime
import pytz
import uuid

def create_chat_session(db: Session, title: str = None):
    """创建新的聊天会话"""
    session = ChatSession(title=title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def save_chat_message(db: Session, session_id: int, role: str, content: str, thinking_content: str = None):
    """保存聊天消息到指定会话"""
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        thinking_content=thinking_content
    )
    db.add(message)
    # 更新会话的更新时间
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session:
        session.updated_at = datetime.utcnow()
        if not session.title and role == "user":
            # 使用用户的第一条消息作为会话标题
            session.title = content[:100]  # 限制标题长度
    db.commit()
    return message

def get_chat_sessions(db: Session, keyword: str = None, page: int = 1, page_size: int = 10):
    """获取聊天会话列表"""
    query = db.query(ChatSession)
    if keyword:
        query = query.filter(ChatSession.title.contains(keyword))
    
    # 使用中国上海时区，按更新时间倒序排列（最新的在前）
    return query.order_by(ChatSession.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

def get_chat_session_by_id(db: Session, session_id: int):
    """根据ID获取聊天会话"""
    return db.query(ChatSession).filter(ChatSession.id == session_id).first()

def get_chat_session_by_uuid(db: Session, session_uuid: str):
    """根据UUID获取聊天会话"""
    return db.query(ChatSession).filter(ChatSession.session_id == session_uuid).first()

def get_chat_messages_by_session(db: Session, session_id: int):
    """获取指定会话的所有消息"""
    return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp).all()

def get_chat_messages_by_session_uuid(db: Session, session_uuid: str):
    """根据会话UUID获取所有消息"""
    session = db.query(ChatSession).filter(ChatSession.session_id == session_uuid).first()
    if not session:
        return None
    return db.query(ChatMessage).filter(ChatMessage.session_id == session.id).order_by(ChatMessage.timestamp).all()

def delete_chat_session(db: Session, session_id: int):
    """删除聊天会话及其所有消息"""
    # 先删除所有相关消息
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    # 再删除会话
    db.query(ChatSession).filter(ChatSession.id == session_id).delete()
    db.commit()

def delete_all_chat_sessions(db: Session):
    """删除所有聊天会话和消息"""
    db.query(ChatMessage).delete()
    db.query(ChatSession).delete()
    db.commit()
    return True

def export_chats(db: Session):
    """导出所有聊天记录"""
    sessions = db.query(ChatSession).order_by(ChatSession.created_at).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["session_id", "session_title", "role", "content", "thinking_content", "timestamp"])
    
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    for session in sessions:
        messages = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).order_by(ChatMessage.timestamp).all()
        for message in messages:
            # 转换为上海时区
            local_timestamp = message.timestamp.replace(tzinfo=pytz.utc).astimezone(shanghai_tz)
            writer.writerow([
                session.session_id, 
                session.title or "", 
                message.role, 
                message.content, 
                message.thinking_content or "",
                local_timestamp
            ])
    output.seek(0)
    
    # 添加BOM以支持Excel正确显示中文
    csv_data = '\ufeff' + output.getvalue()
    return csv_data