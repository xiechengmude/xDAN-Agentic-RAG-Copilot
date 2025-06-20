#!/usr/bin/env python3
"""
统一的RAG服务，整合检索和生成功能
"""

import os
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
import asyncio
import json

from src.clients.ragflow_client import RAGFlowClient
from src.clients.llm_client import LLMClient

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 环境变量配置
RAGFLOW_API_URL = os.getenv("RAGFLOW_API_URL", "http://150.109.16.195:7080")
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY", "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm")
LLM_API_URL = os.getenv("LLM_API_URL", "http://51.159.189.105:7032/v1")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "xDAN-R2-Qwen3-14b-RagRL-step450-0618")
DEFAULT_DATASET_ID = os.getenv("DEFAULT_DATASET_ID", "7e8d9e924cde11f0afc90242ac140006")

app = FastAPI(title="RAG Knowledge Service", version="1.0.0")

# 请求模型
class RAGRequest(BaseModel):
    question: str
    dataset_ids: Optional[List[str]] = None
    max_context_length: Optional[int] = 4000
    top_k: Optional[int] = 5
    similarity_threshold: Optional[float] = 0.1
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    stream: Optional[bool] = False

class RAGResponse(BaseModel):
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    context_used: str
    model_info: Dict[str, str]

# 依赖注入
def get_ragflow_client() -> RAGFlowClient:
    return RAGFlowClient(api_url=RAGFLOW_API_URL, api_key=RAGFLOW_API_KEY)

def get_llm_client() -> LLMClient:
    return LLMClient(base_url=LLM_API_URL, model_name=LLM_MODEL_NAME)

class RAGService:
    def __init__(self, ragflow_client: RAGFlowClient, llm_client: LLMClient):
        self.ragflow_client = ragflow_client
        self.llm_client = llm_client
    
    def retrieve_context(self, question: str, dataset_ids: List[str], top_k: int = 5, 
                        similarity_threshold: float = 0.1) -> tuple[str, List[Dict[str, Any]]]:
        """从知识库检索相关上下文"""
        try:
            response = self.ragflow_client.retrieve_chunks(
                question=question,
                dataset_ids=dataset_ids,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                highlight=True
            )
            
            if not response.get('data', {}).get('chunks'):
                return "", []
            
            chunks = response['data']['chunks']
            sources = []
            context_parts = []
            
            for chunk in chunks:
                # 提取文档信息作为来源
                source = {
                    'document_id': chunk.get('document_id', ''),
                    'document_name': chunk.get('document_name', ''),
                    'chunk_id': chunk.get('id', ''),
                    'similarity': chunk.get('similarity', 0),
                    'content_preview': chunk.get('content_with_weight', '')[:200] + '...'
                }
                sources.append(source)
                
                # 构建上下文
                content = chunk.get('content_with_weight', '')
                if content:
                    context_parts.append(f"文档: {chunk.get('document_name', '未知')}\n内容: {content}")
            
            context = "\n\n".join(context_parts)
            return context, sources
            
        except Exception as e:
            logger.error(f"检索上下文时出错: {e}")
            return "", []
    
    def generate_answer(self, question: str, context: str, temperature: float = 0.7, 
                       max_tokens: int = 1000) -> str:
        """基于上下文生成答案"""
        try:
            prompt = f"""基于以下上下文信息，回答用户的问题。请确保答案准确、相关且有帮助。

上下文信息：
{context}

用户问题：{question}

请基于上述上下文信息回答问题。如果上下文中没有相关信息，请说明无法从提供的信息中找到答案。"""

            messages = [
                {"role": "system", "content": "你是一个专业的知识问答助手，能够基于提供的上下文信息准确回答用户问题。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.llm_client.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.get('choices', [{}])[0].get('message', {}).get('content', '抱歉，无法生成答案。')
            
        except Exception as e:
            logger.error(f"生成答案时出错: {e}")
            return f"生成答案时出现错误: {str(e)}"
    
    async def generate_answer_stream(self, question: str, context: str, temperature: float = 0.7, 
                                   max_tokens: int = 1000) -> AsyncGenerator[str, None]:
        """流式生成答案"""
        try:
            prompt = f"""基于以下上下文信息，回答用户的问题。请确保答案准确、相关且有帮助。

上下文信息：
{context}

用户问题：{question}

请基于上述上下文信息回答问题。如果上下文中没有相关信息，请说明无法从提供的信息中找到答案。"""

            messages = [
                {"role": "system", "content": "你是一个专业的知识问答助手，能够基于提供的上下文信息准确回答用户问题。"},
                {"role": "user", "content": prompt}
            ]
            
            async for chunk in self.llm_client.chat_completion_stream(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"流式生成答案时出错: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

def get_rag_service(
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client),
    llm_client: LLMClient = Depends(get_llm_client)
) -> RAGService:
    return RAGService(ragflow_client, llm_client)

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "RAG Knowledge Service"}

@app.post("/v1/rag/ask", response_model=RAGResponse)
async def ask_question(request: RAGRequest, rag_service: RAGService = Depends(get_rag_service)):
    """RAG问答端点 - 整合检索和生成"""
    try:
        # 使用默认数据集ID如果未指定
        dataset_ids = request.dataset_ids or [DEFAULT_DATASET_ID]
        
        # 步骤1: 检索相关上下文
        logger.info(f"检索问题: {request.question}")
        context, sources = rag_service.retrieve_context(
            question=request.question,
            dataset_ids=dataset_ids,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        
        if not context:
            return RAGResponse(
                question=request.question,
                answer="抱歉，在知识库中没有找到与您问题相关的信息。",
                sources=[],
                context_used="",
                model_info={"retrieval": "RAGFlow", "generation": LLM_MODEL_NAME}
            )
        
        # 限制上下文长度
        if len(context) > request.max_context_length:
            context = context[:request.max_context_length] + "..."
        
        # 步骤2: 基于上下文生成答案
        logger.info("生成答案...")
        answer = rag_service.generate_answer(
            question=request.question,
            context=context,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return RAGResponse(
            question=request.question,
            answer=answer,
            sources=sources,
            context_used=context,
            model_info={"retrieval": "RAGFlow", "generation": LLM_MODEL_NAME}
        )
        
    except Exception as e:
        logger.error(f"RAG问答处理出错: {e}")
        raise HTTPException(status_code=500, detail=f"处理问答请求时出错: {str(e)}")

@app.post("/v1/rag/ask-stream")
async def ask_question_stream(request: RAGRequest, rag_service: RAGService = Depends(get_rag_service)):
    """RAG问答流式端点"""
    try:
        # 使用默认数据集ID如果未指定
        dataset_ids = request.dataset_ids or [DEFAULT_DATASET_ID]
        
        # 检索相关上下文
        logger.info(f"检索问题: {request.question}")
        context, sources = rag_service.retrieve_context(
            question=request.question,
            dataset_ids=dataset_ids,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        
        if not context:
            async def no_context_response():
                yield f"data: {json.dumps({'answer': '抱歉，在知识库中没有找到与您问题相关的信息。', 'sources': []})}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(no_context_response(), media_type="text/plain")
        
        # 限制上下文长度
        if len(context) > request.max_context_length:
            context = context[:request.max_context_length] + "..."
        
        # 流式生成答案
        async def stream_response():
            # 首先发送源信息
            yield f"data: {json.dumps({'sources': sources, 'context_preview': context[:200] + '...'})}\n\n"
            
            # 然后流式发送答案
            async for chunk in rag_service.generate_answer_stream(
                question=request.question,
                context=context,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            ):
                yield chunk
            
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(stream_response(), media_type="text/plain")
        
    except Exception as e:
        logger.error(f"流式RAG问答处理出错: {e}")
        raise HTTPException(status_code=500, detail=f"处理流式问答请求时出错: {str(e)}")

@app.get("/v1/rag/datasets")
async def list_datasets(ragflow_client: RAGFlowClient = Depends(get_ragflow_client)):
    """列出可用的数据集"""
    try:
        response = ragflow_client.list_datasets()
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
