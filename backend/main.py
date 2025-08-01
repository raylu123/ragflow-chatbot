# backend/main.py
import os
import sys
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .rag_client import RagflowClient
from .models import SessionLocal, ChatMessage
from .crud import (
    create_chat_session, save_chat_message, get_chat_sessions, 
    delete_chat_session, export_chats, delete_all_chat_sessions,
    get_chat_session_by_uuid, get_chat_messages_by_session_uuid,
    get_chat_session_by_id
)
from typing import Optional
import json
from dotenv import load_dotenv

import logging
from logging.handlers import TimedRotatingFileHandler
# 注意：确保你已经正确导入了settings
# from your_project import settings

# 设置环境变量确保 UTF-8 编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 配置日志
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 控制台处理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)

# 每日轮转的文件处理器
# when='midnight' 表示每天午夜轮转
# interval=1 表示间隔1天
# backupCount=30 表示保留30天的日志文件
file_handler = TimedRotatingFileHandler(
    "app.log",
    when='midnight',
    interval=1,
    backupCount=30,
    encoding='utf-8'
)
file_handler.setFormatter(log_formatter)
# 为轮转的日志文件添加后缀，例如 app.log.2023-10-01
file_handler.suffix = "%Y-%m-%d"

# 设置日志级别
log_level = logging.INFO

# 配置根日志
logging.basicConfig(
    level=log_level,
    handlers=[console_handler, file_handler]
)

logger = logging.getLogger(__name__)

# 加载.env文件
load_dotenv()

# 初始化RAG客户端
rag = RagflowClient()

app = FastAPI()

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "frontend", "static")), name="static")
app.mount("/assets", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "frontend", "assets")), name="assets")
app.mount("/vendor", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "frontend", "vendor")), name="vendor")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Session-ID"],
    max_age=86400
)

# 依赖注入数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    """应用启动时的预热任务"""
    logger.info("应用正在启动...")
    
    # 预热数据库连接
    db = SessionLocal()
    try:
        # 执行一个简单的查询来预热数据库
        db.query(ChatMessage).first()
        logger.info("数据库连接预热完成")
    except Exception as e:
        logger.error(f"数据库预热失败: {e}")
    finally:
        db.close()
    
    # 预热RAG客户端
    if rag.is_initialized:
        try:
            # 发送一个测试请求来预热RAG服务
            test_messages = [{"role": "user", "content": "你好"}]
            # 使用低优先级的推理进行预热
            response = rag.chat("你好", stream=False, reasoning_effort="low")
            logger.info("RAG客户端预热完成")
        except Exception as e:
            logger.error(f"RAG客户端预热失败: {e}")
    else:
        logger.warning("RAG客户端未初始化，跳过预热")
    
    logger.info("应用启动完成")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理任务"""
    logger.info("应用正在关闭...")
    if rag.client:
        rag.client.close()
    if rag.async_client:
        await rag.async_client.close()
    logger.info("应用关闭完成")

@app.get("/health")
async def health_check():
    """健康检查端点"""
    db_healthy = False
    rag_healthy = False
    
    # 检查数据库连接
    db = SessionLocal()
    try:
        db.query(ChatMessage).first()
        db_healthy = True
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
    finally:
        db.close()
    
    # 检查RAG服务
    if rag.is_initialized:
        try:
            # 简单测试RAG服务可用性
            rag_healthy = True
        except Exception as e:
            logger.error(f"RAG服务健康检查失败: {e}")
    else:
        rag_healthy = False
    
    if db_healthy and rag_healthy:
        return {"status": "healthy", "database": "ok", "rag_service": "ok"}
    else:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "database": "ok" if db_healthy else "error",
                "rag_service": "ok" if rag_healthy else "error"
            }
        )


# 根路径路由，返回前端页面
@app.get("/", response_class=HTMLResponse)
async def read_root():
    # 读取前端HTML文件
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "templates", "index.html")
    try:
        with open(frontend_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Welcome to RAGFlow Chatbot</h1><p>Frontend files not found.</p>", status_code=200)

class ChatRequest(BaseModel):
    message: str
    deep_thinking: bool = False

class SaveChatRequest(BaseModel):
    question: str
    answer: str
    thinking_content: Optional[str] = None

@app.get("/chat")
async def chat_sse(message: str, deep_thinking: bool = False, db: Session = Depends(get_db)):
    if not rag:
        def error_stream():
            yield f"data: {json.dumps({'type':'error','message':'RAG client not configured properly. Check environment variables.'})}\n\n"
            yield f"data: [DONE]\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")
    
    try:
        # 立即创建新的聊天会话并保存用户消息，提升响应速度
        session = create_chat_session(db, title=message[:50])
        session_id = session.id
        save_chat_message(db, session_id, "user", message)
        
        # 根据深度思考选项设置reasoning_effort参数
        reasoning_effort = "high" if deep_thinking else "low"
        
        # 构造消息
        messages = [{"role": "user", "content": message}]
        
        # 立即获取异步生成器，不等待
        response_stream = rag.async_chat(messages, reasoning_effort=reasoning_effort)
        
        # 用于存储完整响应以保存到数据库
        full_content = ""
        thinking_content = ""
        
        async def event_stream():
            nonlocal full_content, thinking_content
            try:
                # 立即开始处理流
                async for chunk in response_stream:
                    if chunk["type"] == "thinking":
                        thinking_content += chunk["content"]
                        yield f"data: {json.dumps({'type':'thinking','content':chunk['content']})}\n\n"
                    elif chunk["type"] == "content":
                        full_content += chunk["content"]
                        yield f"data: {json.dumps({'type':'content','content':chunk['content']})}\n\n"
                    elif chunk["type"] == "complete":
                        thinking_content = chunk.get("thinking_content", thinking_content)
                        full_content = chunk.get("response_content", full_content)
                        
                        # 异步保存助手回复到数据库
                        save_chat_message(db, session_id, "assistant", full_content, thinking_content)
                        
                        # 重新获取session对象，确保它与当前数据库会话绑定
                        updated_session = get_chat_session_by_id(db, session_id)
                        
                        # 发送完成信号，包含完整的思考和回复内容
                        yield f"data: {json.dumps({'type':'complete','thinking_content':thinking_content,'response_content':full_content, 'session_id': updated_session.session_id if updated_session else session.session_id})}\n\n"
                        break
                    elif chunk["type"] == "error":
                        yield f"data: {json.dumps({'type':'error','message':chunk['message']})}\n\n"
                        yield f"data: [DONE]\n\n"
                        return
                
                # 发送最终完成信号
                yield f"data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type':'error','message':str(e)})}\n\n"
                yield f"data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")
    except Exception as e:
        def error_stream():
            yield f"data: {json.dumps({'type':'error','message':str(e)})}\n\n"
            yield f"data: [DONE]\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")
@app.get("/history")
def history_endpoint(db: Session = Depends(get_db), q: str = Query(None), page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50)):
    sessions = get_chat_sessions(db, keyword=q, page=page, page_size=page_size)
    # 转换为上海时区
    import pytz
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    
    result = []
    for session in sessions:
        # 获取会话的最新消息作为预览
        latest_message = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).order_by(ChatMessage.timestamp.desc()).first()
        
        if latest_message:
            local_timestamp = session.updated_at.replace(tzinfo=pytz.utc).astimezone(shanghai_tz) if session.updated_at else session.created_at.replace(tzinfo=pytz.utc).astimezone(shanghai_tz)
            result.append({
                "id": session.id,
                "session_id": session.session_id,
                "title": session.title or "无标题对话",
                "preview": latest_message.content[:100] + ("..." if len(latest_message.content) > 100 else ""),
                "timestamp": local_timestamp.isoformat()
            })
    
    return result

@app.post("/history")
def save_chat_endpoint(chat: SaveChatRequest, db: Session = Depends(get_db)):
    # 创建新的聊天会话
    session = create_chat_session(db, title=chat.question[:50])
    
    # 保存用户消息
    save_chat_message(db, session.id, "user", chat.question)
    
    # 保存助手回复
    save_chat_message(db, session.id, "assistant", chat.answer, chat.thinking_content)
    
    return {"ok": True, "session_id": session.session_id}

@app.get("/history/{session_uuid}")
def get_chat_history_endpoint(session_uuid: str, db: Session = Depends(get_db)):
    # 根据UUID获取会话
    session = get_chat_session_by_uuid(db, session_uuid)
    if not session:
        return JSONResponse(status_code=404, content={"message": "Chat session not found"})
    
    # 获取会话中的所有消息
    messages = get_chat_messages_by_session_uuid(db, session_uuid)
    if messages is None:
        return JSONResponse(status_code=404, content={"message": "Chat session not found"})
    
    # 转换为上海时区
    import pytz
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    
    result_messages = []
    for message in messages:
        local_timestamp = message.timestamp.replace(tzinfo=pytz.utc).astimezone(shanghai_tz)
        result_messages.append({
            "role": message.role,
            "content": message.content,
            "thinking_content": message.thinking_content,
            "timestamp": local_timestamp.isoformat()
        })
    
    return {"messages": result_messages, "session_id": session.session_id, "title": session.title}

@app.delete("/history/{session_id}")
def delete_endpoint(session_id: int, db: Session = Depends(get_db)):
    delete_chat_session(db, session_id)
    return {"ok": True}

@app.delete("/history")
def delete_all_endpoint(db: Session = Depends(get_db)):
    delete_all_chat_sessions(db)
    return {"ok": True}

@app.get("/export")
def export_endpoint(db: Session = Depends(get_db)):
    csv_data = export_chats(db)
    headers = {
        'Content-Disposition': 'attachment; filename="chat_history.csv"',
        'Content-Type': 'text/csv; charset=utf-8',
    }
    return Response(content=csv_data, headers=headers)