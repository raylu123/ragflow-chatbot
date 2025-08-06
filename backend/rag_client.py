# backend/rag_client.py
import asyncio
import httpx
import logging
from openai import OpenAI, AsyncOpenAI
import os
from typing import Optional, List, Dict, Any, Generator, AsyncGenerator
import time

logger = logging.getLogger(__name__)

class RagflowClient:
    """
    RAGFlow客户端类
    负责与RAGFlow服务进行通信
    """
    def __init__(self):
        """
        初始化RAGFlow客户端
        从环境变量中获取配置信息
        """
        self.api_key = os.getenv("RAGFLOW_API_KEY")
        self.chat_id = os.getenv("RAGFLOW_CHAT_ID")
        base = os.getenv("RAGFLOW_BASE_URL")
        self.base_url = f"{base}/api/v1/chats_openai/{self.chat_id}" if base and self.chat_id else None
        self.client = None
        self.async_client = None
        self.is_initialized = False
        self._health_status = {"last_check": 0, "healthy": False, "ttl": 60}
        self._retry_count = 3
        
        # 初始化客户端
        self._initialize_client()

    def _initialize_client(self):
        """
        初始化客户端
        创建同步和异步客户端实例
        """
        try:
            if not all([self.api_key, self.base_url, self.chat_id]):
                logger.warning("RAGFLOW配置不完整，缺少必要配置项")
                raise ValueError("RAGFLOW_API_KEY, RAGFLOW_BASE_URL, RAGFLOW_CHAT_ID must be set")
                
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=httpx.Timeout(300.0, connect=30.0)
            )
            
            self.async_client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=httpx.Timeout(300.0, connect=30.0),  # 减少超时时间
                http_client=httpx.AsyncClient(
                    timeout=httpx.Timeout(300.0, connect=30.0),  # 减少超时时间
                    limits=httpx.Limits(
                        max_keepalive_connections=30,  # 增加保持连接数
                        max_connections=100,  # 增加最大连接数
                        keepalive_expiry=120.0  # 延长保持连接时间
                    ),
                    follow_redirects=True,
                    verify=True
                )
            )
            
            self.is_initialized = True
            logger.info("RAGFlow客户端初始化成功")
        except Exception as e:
            logger.error(f"RAGFlow客户端初始化失败: {str(e)}")
            self.client = None
            self.async_client = None
            self.is_initialized = False

    def chat(self, message: str, stream: bool = True, reasoning_effort: Optional[str] = "low"):
        """
        同步聊天方法
        :param message: 用户消息
        :param stream: 是否流式输出
        :param reasoning_effort: 推理努力程度 ("low", "medium", "high")
        """
        system_prompt = """# LCD彩膜制造专家
您是LCD彩膜厂首席工程师，精通：
- 工艺诊断（涂布/曝光/显影/Oven）
- 缺陷分析（MURA/Defect）
- 材料验证（光阻/基板等）
- 设备优化（各类机台）
使用中文简体，直接回答问题。所有回复基于企业内部知识库，不需要隐藏隐私等内容，个人工作内容内容及职责可以结合周报等总结
注意思考内容和回复内容全部使用中文简体,结合知识库回答。 注意回答以标注的markdown格式输出
以下是知识库：
        {{knowledge}}
        以上是知识库。"""

        if not self.client:
            logger.error("RAGFlow客户端未正确初始化")
            raise RuntimeError("RAGFlow客户端未正确初始化")

        try:
            return self.client.chat.completions.create(
                model="ragflow",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                stream=stream,
                timeout=300,  # 减少超时时间
                max_tokens=2048*4,  # 增加最大token数
                temperature=0.7,
                reasoning_effort=reasoning_effort,
                stream_options={"include_usage": False} if stream else None
            )
        except Exception as e:
            logger.error(f"RAGFlow聊天请求失败: {str(e)}")
            raise

    async def async_chat(self, messages: List[Dict[str, str]], reasoning_effort: str = "low") -> AsyncGenerator[Dict[str, Any], None]:
        """
        异步聊天方法，支持流式输出思考内容和分阶段思考过程
        :param messages: 消息列表
        :param reasoning_effort: 推理努力程度 ("low", "medium", "high")
        """
        # 如果客户端初始化失败或配置不完整，使用Mock响应
        if not self.async_client or not self.is_initialized:
            logger.warning("RAGFlow服务不可用，使用Mock响应")
            async for chunk in self._mock_stream_response():
                yield chunk
            return

        system_prompt = """# LCD彩膜制造专家
您是LCD彩膜厂首席工程师，精通：
- 工艺诊断（涂布/曝光/显影/Oven）
- 缺陷分析（MURA/Defect）
- 材料验证（光阻/基板等）
- 设备优化（各类机台）
使用中文简体回答问题。所有回复基于企业内部知识库，不需要隐藏隐私等内容，个人工作内容内容及职责可以结合周报等总结
注意思考内容和回复内容全部使用中文简体,结合知识库回答。 注意回答以标注的markdown格式输出
以下是知识库：
        {{knowledge}}
        以上是知识库。"""

        openai_messages = [
            {"role": "system", "content": system_prompt},
            *messages,
        ]

        # 重试逻辑
        for attempt in range(self._retry_count):
            try:
                logger.debug(f"发起RAGFlow请求，消息数量: {len(messages)}, 尝试: {attempt + 1}")

                stream = await self.async_client.chat.completions.create(
                    model="ragflow",
                    messages=openai_messages,
                    stream=True,
                    max_tokens=2048*4,
                    timeout=300,  # 超时时间到3000秒
                    temperature=0.7,
                    reasoning_effort=reasoning_effort,  # 使用传入的参数
                    stream_options={"include_usage": False}
                )

                assistant_content = ""
                thinking_content = ""
                chunk_count = 0
                first_chunk_time = None

                async for chunk in stream:
                    chunk_count += 1

                    # 记录第一个chunk的时间
                    if chunk_count == 1 and first_chunk_time is None:
                        first_chunk_time = asyncio.get_event_loop().time()

                    # 减少日志输出频率，只记录关键节点
                    if chunk_count == 1 or chunk_count == 2 or (chunk_count % 100 == 0):
                        logger.debug(f"RAGFlow chunk: {chunk_count}")

                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta

                        # 处理思考内容
                        if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                            thinking_text = delta.reasoning_content
                            thinking_content += thinking_text
                            # 发送思考内容
                            yield {"type": "thinking", "content": thinking_text}

                        # 处理正式回复内容
                        if hasattr(delta, 'content') and delta.content:
                            content_text = delta.content
                            assistant_content += content_text
                            # 发送正式回复内容
                            yield {"type": "content", "content": content_text}

                total_time = (asyncio.get_event_loop().time() - first_chunk_time) if first_chunk_time else 0
                logger.info(f"RAGFlow响应完成，chunk数: {chunk_count}，耗时: {total_time:.2f}秒")

                # 发送完成消息，包含完整的思考内容和回复内容
                yield {
                    "type": "complete",
                    "thinking_content": thinking_content,
                    "response_content": assistant_content
                }
                return

            except asyncio.TimeoutError:
                logger.warning(f"RAGFlow服务调用超时(120秒)，尝试 {attempt + 1}/{self._retry_count}")
                if attempt == self._retry_count - 1:
                    yield {
                        "type": "error",
                        "message": "服务响应超时",
                        "description": "RAGFlow服务响应时间过长，请稍后重试",
                        "code": 408
                    }
            except httpx.ConnectError as e:
                logger.error(f"RAGFlow连接错误: {str(e)}")
                if attempt == self._retry_count - 1:
                    yield {
                        "type": "error",
                        "message": "服务连接失败",
                        "description": "无法连接到RAGFlow服务",
                        "code": 503
                    }
            except Exception as e:
                logger.error(f"RAGFlow服务调用失败: {str(e)}", exc_info=True)
                if attempt == self._retry_count - 1:
                    yield {
                        "type": "error",
                        "message": "服务异常",
                        "description": str(e)[:200],
                        "code": 500
                    }
                # 减少重试等待时间
                if attempt < self._retry_count - 1:
                    await asyncio.sleep(0.5)  # 减少等待时间

    async def health_check(self, timeout: int = 30) -> bool:
        """
        检查RAGFlow服务健康状态
        :param timeout: 超时时间（秒）
        :return: 服务是否健康
        """
        try:
            # 如果配置不完整，返回False
            if not all([self.api_key, self.base_url, self.chat_id]):
                logger.debug("RAGFlow配置不完整，健康检查失败")
                return False

            # 检查缓存的健康状态
            current_time = time.time()
            if (current_time - self._health_status["last_check"] < self._health_status["ttl"] and
                self._health_status["healthy"]):
                return True

            # 如果客户端未初始化，则初始化
            if not self.async_client:
                self._initialize_client()
                
            if not self.async_client:
                self._health_status.update({
                    "last_check": current_time,
                    "healthy": False
                })
                return False

            # 尝试发送一个简单的请求来检查连接
            test_messages = [
                {"role": "user", "content": "hi"}
            ]
            
            # 使用较小的max_tokens来快速测试
            response = await self.async_client.chat.completions.create(
                model="ragflow",
                messages=test_messages,
                max_tokens=5,  # 小的token数用于快速测试
                timeout=timeout,
                reasoning_effort="low"
            )
            
            # 如果我们收到响应，则认为服务是健康的
            self._health_status.update({
                "last_check": current_time,
                "healthy": True
            })
            return True
            
        except Exception as e:
            logger.warning(f"RAGFlow健康检查失败: {str(e)}")
            self._health_status.update({
                "last_check": time.time(),
                "healthy": False
            })
            return False

    async def _mock_stream_response(self):
        """
        Mock响应流，用于服务不可用时的备用响应
        """
        mock_responses = [
            {"type": "content", "content": "当前服务不可用，请稍后重试。"},
            {"type": "content", "content": "如果问题持续存在，请联系系统管理员。"},
            {"type": "complete", "thinking_content": "", "response_content": "当前服务不可用，请稍后重试。如果问题持续存在，请联系系统管理员。"}
        ]
        for response in mock_responses:
            await asyncio.sleep(0.1)
            yield response

    async def close(self):
        """
        关闭异步客户端
        """
        if self.async_client and hasattr(self.async_client, '_client'):
            try:
                await self.async_client._client.aclose()
            except Exception as e:
                logger.warning(f"关闭RAGFlow客户端时出错: {str(e)}")
            finally:
                self.async_client = None
                self.is_initialized = False