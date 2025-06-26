#!/usr/bin/env python3
"""
RAG协调服务 - 基于架构文档的S3框架实现
负责协调RAGFlow（检索）和LiteLLM（生成）服务
"""

import os
import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
from pydantic import BaseModel, Field

# 导入核心组件
from src.core.s3_framework import S3FrameworkAgent
from src.clients.streaming_ragflow_client import StreamingRAGFlowClient
from src.clients.litellm_sdk_client import LiteLLMSDKClient

# 配置日志
logger = logging.getLogger(__name__)

class RAGRequest(BaseModel):
    """RAG请求模型"""
    question: str = Field(..., description="用户问题")
    dataset_ids: Optional[List[str]] = Field(default=None, description="数据集ID列表")
    max_context_length: Optional[int] = Field(default=4000, description="最大上下文长度")
    top_k: Optional[int] = Field(default=10, description="检索数量")
    similarity_threshold: Optional[float] = Field(default=0.1, description="相似度阈值")
    temperature: Optional[float] = Field(default=0.7, description="生成温度")
    max_tokens: Optional[int] = Field(default=2000, description="最大生成token数")
    stream: Optional[bool] = Field(default=False, description="是否流式返回")
    max_search_rounds: Optional[int] = Field(default=3, description="最大搜索轮数")

class RAGResponse(BaseModel):
    """RAG响应模型"""
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    context_used: str
    model_info: Dict[str, str]
    workflow_info: Dict[str, Any]
    search_rounds: int
    processing_time: float

class RAGService:
    """
    RAG协调服务 - 基于架构文档设计
    
    职责：
    1. 协调RAGFlow（检索服务）和LiteLLM（生成服务）
    2. 实现S3框架工作流控制
    3. 提供统一的RAG API接口
    """
    
    def __init__(self, ragflow_api_url: str = None, ragflow_api_key: str = None,
                 litellm_api_url: str = None, litellm_api_key: str = None):
        """
        初始化RAG服务
        
        Args:
            ragflow_api_url: RAGFlow API地址
            ragflow_api_key: RAGFlow API密钥
            litellm_api_url: LiteLLM API地址
            litellm_api_key: LiteLLM API密钥
        """
        # 从环境变量获取配置
        self.ragflow_api_url = ragflow_api_url or os.getenv("RAGFLOW_API_URL", "http://150.109.16.195:7080")
        self.ragflow_api_key = ragflow_api_key or os.getenv("RAGFLOW_API_KEY")
        self.litellm_api_url = litellm_api_url or os.getenv("LITELLM_API_URL", "http://localhost:4000")
        self.litellm_api_key = litellm_api_key or os.getenv("LITELLM_API_KEY", "sk-ragflow-integration-key")
        
        # 默认数据集
        self.default_dataset_id = os.getenv("DEFAULT_DATASET_ID", "7e8d9e924cde11f0afc90242ac140006")
        
        if not self.ragflow_api_key:
            raise ValueError("RAGFlow API Key未设置")
        
        # 初始化客户端
        self._init_clients()
        
        # 初始化S3框架智能体
        self.s3_agent = S3FrameworkAgent(self.ragflow_client, self.litellm_client)
        
        logger.info("RAG协调服务初始化完成")
        logger.info(f"RAGFlow API: {self.ragflow_api_url}")
        logger.info(f"LiteLLM API: {self.litellm_api_url}")
        logger.info("架构：RAGFlow(检索) + LiteLLM(生成) + S3框架")
    
    def _init_clients(self):
        """初始化服务集成层的客户端"""
        try:
            # 初始化RAGFlow客户端（检索服务）
            self.ragflow_client = StreamingRAGFlowClient(
                api_url=self.ragflow_api_url,
                api_key=self.ragflow_api_key
            )
            logger.info("✅ RAGFlow检索客户端初始化成功")
            
            # 初始化LiteLLM SDK客户端（内核服务）
            self.litellm_client = LiteLLMSDKClient(
                default_model="gpt-4o-mini",
                verbose=False
            )
            logger.info("✅ LiteLLM SDK客户端初始化成功（内核服务模式）")
            
        except Exception as e:
            logger.error(f"客户端初始化失败: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """服务健康检查"""
        health_status = {
            "service": "RAG协调服务",
            "status": "healthy",
            "ragflow_status": "unknown",
            "litellm_status": "unknown",
            "s3_framework": "available",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 检查RAGFlow状态
            ragflow_health = self.ragflow_client.health_check()
            if ragflow_health.get('code') == 0:
                health_status["ragflow_status"] = "healthy"
            else:
                health_status["ragflow_status"] = "unhealthy"
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["ragflow_status"] = f"error: {e}"
            health_status["status"] = "degraded"
        
        try:
            # 检查LiteLLM SDK状态
            litellm_health = await self.litellm_client.health_check()
            if litellm_health.get("status") == "healthy":
                health_status["litellm_status"] = "healthy"
            else:
                health_status["litellm_status"] = "degraded"
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["litellm_status"] = f"error: {e}"
            health_status["status"] = "degraded"
        
        return health_status
    
    def retrieve_context(self, question: str, dataset_ids: List[str] = None, 
                        top_k: int = 10, similarity_threshold: float = 0.1) -> Dict[str, Any]:
        """
        S3框架的Search阶段：从知识库检索相关上下文
        （同步版本，供兼容性使用）
        """
        if not dataset_ids:
            dataset_ids = [self.default_dataset_id]
        
        try:
            result = self.ragflow_client.retrieve(
                question=question,
                dataset_ids=dataset_ids,
                top_k=top_k
            )
            
            if result.get("code") == 0:
                chunks = result.get("data", {}).get("chunks", [])
                return {
                    "success": True,
                    "chunks": chunks,
                    "total": len(chunks),
                    "query": question
                }
            else:
                return {
                    "success": False,
                    "error": result.get("message", "检索失败"),
                    "chunks": []
                }
        except Exception as e:
            logger.error(f"检索上下文失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "chunks": []
            }
    
    async def generate_answer(self, question: str, context: str, 
                             temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """
        S3框架的Synthesize阶段：基于上下文生成答案
        """
        try:
            system_prompt = """你是一个专业的问答助手。请基于提供的上下文信息准确回答用户的问题。

要求：
1. 答案要准确、相关、有帮助
2. 如果上下文中没有足够信息，请诚实说明
3. 保持答案的逻辑性和连贯性
4. 可以适当引用上下文中的关键信息"""

            user_prompt = f"""请基于以下上下文信息回答问题：

上下文信息：
{context}

问题：{question}

请提供准确、有用的回答："""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.litellm_client.chat_completion(
                messages=messages,
                use_case="generation",  # 使用生成模型配置
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"生成答案失败: {e}")
            return f"抱歉，在生成答案时遇到错误：{e}"
    
    async def generate_answer_stream(self, question: str, context: str,
                                   temperature: float = 0.7, max_tokens: int = 2000) -> AsyncGenerator[str, None]:
        """流式答案生成"""
        try:
            system_prompt = """你是一个专业的问答助手。请基于提供的上下文信息准确回答用户的问题。

要求：
1. 答案要准确、相关、有帮助
2. 如果上下文中没有足够信息，请诚实说明
3. 保持答案的逻辑性和连贯性
4. 可以适当引用上下文中的关键信息"""

            user_prompt = f"""请基于以下上下文信息回答问题：

上下文信息：
{context}

问题：{question}

请提供准确、有用的回答："""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            stream = await self.litellm_client.chat_completion(
                messages=messages,
                use_case="generation",  # 使用生成模型配置
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if hasattr(chunk, 'choices') and chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"流式生成答案失败: {e}")
            yield f"抱歉，在生成答案时遇到错误：{e}"
    
    async def ask(self, request: RAGRequest) -> RAGResponse:
        """
        核心RAG问答接口 - 使用S3框架
        
        Args:
            request: RAG请求对象
            
        Returns:
            RAG响应对象
        """
        start_time = datetime.now()
        logger.info(f"收到RAG请求: {request.question[:50]}...")
        
        # 设置默认数据集
        dataset_ids = request.dataset_ids or [self.default_dataset_id]
        
        try:
            # 执行S3工作流
            workflow_result = await self.s3_agent.execute_s3_workflow(
                question=request.question,
                dataset_ids=dataset_ids,
                max_rounds=request.max_search_rounds,
                top_k=request.top_k,
                stream=False  # ask接口不使用流式
            )
            
            # 提取结果
            final_answer = workflow_result.get("final_answer", "")
            selected_docs = workflow_result.get("selected_documents", [])
            search_rounds = len(workflow_result.get("rounds", []))
            
            # 格式化来源信息
            sources = []
            context_parts = []
            for i, doc in enumerate(selected_docs):
                source_info = {
                    "id": doc.get("id", f"doc_{i+1}"),
                    "content": doc.get("content", "")[:200] + "...",
                    "document_name": doc.get("document_name", "Unknown"),
                    "similarity": doc.get("similarity", 0),
                    "dataset_id": doc.get("dataset_id", "")
                }
                sources.append(source_info)
                context_parts.append(doc.get("content", ""))
            
            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 构建响应
            response = RAGResponse(
                question=request.question,
                answer=final_answer,
                sources=sources,
                context_used="\n\n".join(context_parts),
                model_info={
                    "retrieval_model": "RAGFlow",
                    "generation_model": "LiteLLM",
                    "framework": "S3 (Search-Select-Synthesize)"
                },
                workflow_info=workflow_result,
                search_rounds=search_rounds,
                processing_time=processing_time
            )
            
            logger.info(f"RAG请求完成: {search_rounds}轮搜索, {len(sources)}个来源, {processing_time:.2f}秒")
            return response
            
        except Exception as e:
            logger.error(f"RAG请求失败: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 返回错误响应
            return RAGResponse(
                question=request.question,
                answer=f"抱歉，在处理您的问题时遇到错误：{e}",
                sources=[],
                context_used="",
                model_info={
                    "retrieval_model": "RAGFlow",
                    "generation_model": "LiteLLM", 
                    "framework": "S3 (Search-Select-Synthesize)"
                },
                workflow_info={"error": str(e)},
                search_rounds=0,
                processing_time=processing_time
            )
    
    async def ask_stream(self, request: RAGRequest) -> AsyncGenerator[str, None]:
        """
        流式RAG问答接口 - 使用S3框架
        
        Args:
            request: RAG请求对象
            
        Yields:
            流式响应内容
        """
        logger.info(f"收到流式RAG请求: {request.question[:50]}...")
        
        # 设置默认数据集
        dataset_ids = request.dataset_ids or [self.default_dataset_id]
        
        try:
            # 先返回状态信息
            yield f"data: {json.dumps({'type': 'status', 'message': '开始执行S3工作流...'})}\n\n"
            
            # 执行S3工作流（流式版本）
            async for chunk in self.s3_agent.execute_s3_workflow(
                question=request.question,
                dataset_ids=dataset_ids,
                max_rounds=request.max_search_rounds,
                top_k=request.top_k,
                stream=True
            ):
                # 返回流式内容
                yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
            
            # 完成标记
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            logger.error(f"流式RAG请求失败: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    # 兼容性方法
    async def retrieve_chunks(self, question: str, dataset_ids: List[str] = None,
                             top_k: int = 10, similarity_threshold: float = 0.1) -> Dict[str, Any]:
        """兼容性接口：直接检索文档块"""
        return self.retrieve_context(question, dataset_ids, top_k, similarity_threshold)
    
    def get_available_datasets(self) -> List[Dict[str, Any]]:
        """获取可用数据集列表"""
        try:
            result = self.ragflow_client.list_datasets(page=1, page_size=50)
            if result.get("code") == 0:
                return result.get("data", [])
            return []
        except Exception as e:
            logger.error(f"获取数据集列表失败: {e}")
            return []