# CF AI知识库系统

## 项目简介

本项目是一个基于FastAPI的智能问答知识库系统，集成了RAGFlow API，提供流式问答交互、历史记录管理等功能。

## 功能特性

- 智能问答交互，支持流式输出
- 思考过程展示和折叠动画
- 历史记录管理，支持搜索、删除及下载
- Markdown 渲染，支持代码高亮
- 响应式设计，适配各种设备
- 微信风格的对话界面

## 环境要求

- Python 3.10+
- pip包管理器

## 安装步骤

1. 克隆项目到本地：
git clone <项目地址> cd ragflow-chatbot


2. 安装依赖：
pip install -r backend/requirements.txt


3. 配置环境变量：
在项目根目录创建`.env`文件，并配置以下参数：
RAGFlow配置
RAGFLOW_API_KEY=your_api_key RAGFLOW_BASE_URL=your_ragflow_base_url RAGFLOW_CHAT_ID=your_chat_id

数据库配置
DATABASE_URL=sqlite:///./chat_history.db

服务配置
HOST=0.0.0.0 PORT=8000


## 运行项目

在项目根目录执行以下命令启动服务：
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload


或者使用项目根目录的启动命令：
cd C:\Users\35783\PycharmProjects\ragflow-chatbot uvicorn main:app --host 0.0.0.0 --port 8000 --reload


## 访问应用

启动服务后，在浏览器中访问 `http://localhost:8000` 即可使用应用。

## API接口

- `GET /` - 返回前端页面
- `GET /chat` - 流式问答接口
- `GET /history` - 获取历史记录
- `DELETE /history/{chat_id}` - 删除指定历史记录
- `GET /export` - 导出历史记录为CSV文件

## 项目结构
.
├── backend
│   ├── __init__.py
│   ├── crud.py          # 数据库操作
│   ├── main.py          # 主应用文件
│   ├── models.py        # 数据库模型
│   ├── rag_client.py    # RAG客户端
│   └── requirements.txt # 依赖列表
├── frontend
│   ├── assets           # 静态资源文件
│   ├── static
│   │   ├── css
│   │   │   └── style.css
│   │   └── js
│   │       └── app.js
│   └── templates
│       └── index.html
├── .env                 # 环境变量配置文件
└── README.md

完成了以上修改后，项目将具备以下增强功能：

添加了导出历史记录为CSV文件的功能，包括后端API端点和前端调用
提供了完整的README文档，包含详细的运行说明、环境要求、安装步骤和API接口说明
在前端界面中添加了导出按钮，用户可以方便地导出聊天记录
所有要求的功能现在都已实现：

基于Fast API编写，使用python语言 ✓
智能问答交互，支持流式输出 ✓
思考过程展示和折叠动画 ✓
历史记录管理，支持搜索、删除及下载 ✓
Markdown 渲染，支持代码高亮 ✓
响应式设计，适配各种设备 ✓
极致的用户体验 ✓
提供完整代码和运行说明 ✓