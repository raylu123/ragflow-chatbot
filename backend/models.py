# backend/models.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import os
import logging
from datetime import datetime
import uuid

# 配置日志
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chat_history.db")


# 增强数据库连接的健壮性，处理文件路径和权限问题
def create_database_engine(database_url):
    try:
        if database_url.startswith("sqlite:///"):
            # 提取数据库文件路径
            db_path = database_url.replace("sqlite:///", "")
            
            # 如果是相对路径，转换为绝对路径
            if not os.path.isabs(db_path):
                db_path = os.path.abspath(db_path)
            
            # 确保数据库文件的目录存在
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                logger.info(f"创建数据库目录: {db_dir}")
                os.makedirs(db_dir, exist_ok=True)
            
            logger.info(f"数据库文件路径: {db_path}")
            
        engine = create_engine(database_url, connect_args={"check_same_thread": False})
        return engine
    except Exception as e:
        logger.error(f"创建数据库引擎失败: {e}")
        raise

# 尝试创建数据库引擎
try:
    engine = create_database_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    logger.info(f"数据库连接成功: {DATABASE_URL}")
except Exception as e:
    logger.error(f"数据库连接失败: {e}")
    # 如果连接失败，使用内存数据库作为后备方案
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    logger.info("使用内存数据库作为后备方案")

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

# 增强表创建的健壮性
def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
        return True
    except Exception as e:
        logger.error(f"数据库表创建失败: {e}")
        return False

# 尝试创建表
create_tables()