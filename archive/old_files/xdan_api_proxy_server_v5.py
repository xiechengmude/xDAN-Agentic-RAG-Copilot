#!/usr/bin/env python3
"""
xDAN RAG Copilot API Proxy Server V5 - Streaming Enhanced
- Includes all V4 features
- Enhanced streaming chat support with proper SSE handling
- OpenAI-compatible endpoints for better LiteLLM integration
- Automatic fallback mechanisms for streaming
"""

import os
import sys
import json
import logging
import time
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, AsyncGenerator, Iterator, Union
from contextlib import asynccontextmanager
import uuid
import tempfile
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from functools import wraps

# Add src directory to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger = logging.getLogger(__name__)
    logger.info("已加载 .env 环境变量文件")
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("python-dotenv 未安装，使用系统环境变量")

from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Request, Depends, Query, Header, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import the new streaming client
try:
    from clients.streaming_ragflow_client import StreamingRAGFlowClient
    logger.info("Successfully imported StreamingRAGFlowClient")
except ImportError as e:
    logger.error(f"Failed to import StreamingRAGFlowClient: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== Configuration ====================

RAGFLOW_API_URL = os.getenv("RAGFLOW_API_URL", "http://150.109.16.195:7080")
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY")

if not RAGFLOW_API_KEY:
    logger.error("RAGFLOW_API_KEY 环境变量未设置")
    sys.exit(1)

# API Keys for client authentication
ALLOWED_API_KEYS = {
    "test-key-001": "Test Client 1",
    "test-key-002": "Test Client 2", 
    "xdan-key-001": "xDAN Client",
    os.getenv("CLIENT_API_KEY", "fallback-key"): "Default Client"
}

# ==================== Models ====================

class ChatCreateRequest(BaseModel):
    name: str = Field(..., description="聊天名称")
    dataset_ids: List[str] = Field(default=[], description="数据集ID列表")
    description: Optional[str] = Field(None, description="聊天描述")

class ChatMessageRequest(BaseModel):
    content: str = Field(..., description="消息内容")
    stream: bool = Field(default=False, description="是否流式返回")

class RetrievalRequest(BaseModel):
    question: str = Field(..., description="检索问题")
    dataset_ids: List[str] = Field(..., description="要检索的数据集ID列表")
    top_k: int = Field(default=5, ge=1, le=20, description="返回的最相关结果数量")

class OpenAIMessage(BaseModel):
    role: str = Field(..., description="角色: system, user, assistant")
    content: str = Field(..., description="消息内容")

class OpenAIChatRequest(BaseModel):
    model: str = Field(default="ragflow", description="模型名称")
    messages: List[OpenAIMessage] = Field(..., description="消息列表")
    stream: bool = Field(default=False, description="是否流式返回")
    temperature: Optional[float] = Field(default=0.7, description="温度参数")
    max_tokens: Optional[int] = Field(None, description="最大token数")

# ==================== Client Management ====================

def verify_api_key(authorization: str = Header(None, description="Bearer token")):
    """验证API密钥"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization format")
    
    api_key = authorization[7:]  # Remove "Bearer " prefix
    
    if api_key not in ALLOWED_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return {
        "api_key": api_key,
        "client_name": ALLOWED_API_KEYS[api_key]
    }

# ==================== Response Helpers ====================

def create_response(data: Any = None, message: str = "Success") -> Dict:
    """创建标准响应格式"""
    return {
        "code": 0,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }

def create_error_response(code: int, message: str, data: Any = None) -> Dict:
    """创建错误响应格式"""
    return {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }

# ==================== Enhanced RAGFlow Client ====================

# Create global streaming client instance
streaming_client = StreamingRAGFlowClient(RAGFLOW_API_URL, RAGFLOW_API_KEY)

def filter_chat_object(chat_data: Dict) -> Dict:
    """过滤聊天对象，只保留必要字段"""
    return {
        "id": chat_data.get("id"),
        "name": chat_data.get("name"),
        "description": chat_data.get("description"),
        "create_date": chat_data.get("create_date"),
        "update_date": chat_data.get("update_date"),
        "status": chat_data.get("status"),
        "language": chat_data.get("language"),
        "llm_model": chat_data.get("llm", {}).get("model_name") if chat_data.get("llm") else None,
        "prompt_type": chat_data.get("prompt_type"),
    }

# ==================== FastAPI Application ====================

app = FastAPI(
    title="xDAN RAG Copilot API Proxy V5",
    description="Enhanced streaming API proxy service with OpenAI compatibility",
    version="5.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Health Check ====================

@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查接口"""
    return create_response(data={
        "status": "healthy",
        "service": "xDAN RAG Copilot API Proxy V5",
        "timestamp": datetime.now().isoformat(),
        "features": ["streaming_chat", "openai_compatibility", "auto_fallback", "sse_support"]
    })

@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """详细健康检查"""
    health_status = {
        "service": "healthy",
        "ragflow": "unknown",
        "streaming": "unknown",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # Test RAGFlow connection
        result = streaming_client.list_datasets(page=1, page_size=1)
        if result.get("code") == 0:
            health_status["ragflow"] = "healthy"
            health_status["streaming"] = "available"
        else:
            health_status["ragflow"] = "unhealthy"
            health_status["service"] = "degraded"
    except Exception as e:
        health_status["ragflow"] = f"unreachable: {str(e)}"
        health_status["service"] = "degraded"
        health_status["streaming"] = "unavailable"
    
    return create_response(data=health_status)

# ==================== Dataset Management ====================

@app.get("/api/v1/datasets", tags=["Datasets"])
async def list_datasets(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=20),
    client_info: Dict = Depends(verify_api_key)
):
    """获取数据集列表"""
    logger.info(f"客户端 {client_info['client_name']} 请求数据集列表")
    
    try:
        result = streaming_client.list_datasets(page, page_size)
        return create_response(data=result.get("data", []), message="Success")
    except Exception as e:
        logger.error(f"获取数据集列表失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

@app.get("/api/v1/datasets/{dataset_id}", tags=["Datasets"])
async def get_dataset_details(
    dataset_id: str,
    client_info: Dict = Depends(verify_api_key)
):
    """获取数据集详情"""
    logger.info(f"客户端 {client_info['client_name']} 请求数据集详情: {dataset_id}")
    
    try:
        result = streaming_client.get_dataset(dataset_id)
        if result.get("code") == 0:
            dataset_data = result.get("data", {})
            
            # Add RAG availability check
            chunk_count = dataset_data.get("chunk_num", 0)
            dataset_data["rag_availability"] = {
                "status": "ready" if chunk_count > 0 else "empty",
                "message": "可用于RAG聊天" if chunk_count > 0 else "数据集为空，需要上传文档",
                "can_chat": chunk_count > 0,
                "can_retrieve": chunk_count > 0
            }
            
            return create_response(data=dataset_data)
        else:
            raise HTTPException(status_code=404, detail=create_error_response(404, "Dataset not found"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据集详情失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

# ==================== Document Management ====================

@app.get("/api/v1/datasets/{dataset_id}/documents", tags=["Documents"])
async def list_documents(
    dataset_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=20),
    client_info: Dict = Depends(verify_api_key)
):
    """获取文档列表"""
    logger.info(f"客户端 {client_info['client_name']} 请求文档列表: {dataset_id}")
    
    try:
        result = streaming_client.list_documents(dataset_id, page, page_size)
        return create_response(data=result.get("data", []))
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

# ==================== Chat Management ====================

@app.post("/api/v1/chats", tags=["Chats"])
async def create_chat(
    request: ChatCreateRequest,
    client_info: Dict = Depends(verify_api_key)
):
    """创建对话 - 支持空数据集的兼容模式"""
    logger.info(f"客户端 {client_info['client_name']} 创建对话: {request.name}")
    
    try:
        # Check dataset availability
        available_datasets = []
        unavailable_datasets = []
        
        for dataset_id in request.dataset_ids:
            try:
                dataset_result = streaming_client.get_dataset(dataset_id)
                dataset_data = dataset_result.get("data", {})
                
                if dataset_data:
                    chunk_count = dataset_data.get("chunk_num", 0)
                    if chunk_count > 0:
                        available_datasets.append(dataset_id)
                    else:
                        unavailable_datasets.append({
                            "id": dataset_id,
                            "reason": "no_content",
                            "message": "数据集无内容或正在解析中"
                        })
                else:
                    unavailable_datasets.append({
                        "id": dataset_id,
                        "reason": "not_found",
                        "message": "数据集不存在"
                    })
            except Exception as e:
                unavailable_datasets.append({
                    "id": dataset_id,
                    "reason": "error",
                    "message": f"检查失败: {str(e)}"
                })
        
        # Determine chat mode based on available datasets
        if available_datasets:
            chat_mode = "rag"
            datasets_for_chat = available_datasets
            logger.info(f"RAG模式聊天，使用数据集: {available_datasets}")
        else:
            chat_mode = "basic"
            datasets_for_chat = []
            logger.info("基础LLM模式聊天，无数据集增强")
        
        # Create chat (allow empty datasets)
        chat_request = {
            "name": request.name,
            "dataset_ids": datasets_for_chat,
            "description": request.description or f"聊天模式: {chat_mode}"
        }
        
        result = streaming_client.create_chat(chat_request)
        chat_data = result.get("data", {})
        
        # Enhance response information
        if isinstance(chat_data, dict):
            enhanced_response = {
                **filter_chat_object(chat_data),
                "chat_mode": chat_mode,
                "available_datasets": available_datasets,
                "unavailable_datasets": unavailable_datasets,
                "capabilities": {
                    "rag_enabled": len(available_datasets) > 0,
                    "basic_chat": True,
                    "document_search": len(available_datasets) > 0
                }
            }
            return create_response(data=enhanced_response)
        else:
            return create_response(data=chat_data)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建对话失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

@app.get("/api/v1/chats", tags=["Chats"])
async def list_chats(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=20),
    client_info: Dict = Depends(verify_api_key)
):
    """获取聊天列表 - V5优化版"""
    logger.info(f"客户端 {client_info['client_name']} 请求聊天列表 (page={page}, page_size={page_size})")
    
    try:
        result = streaming_client.list_chats(page, page_size)
        
        # Filter chat objects to reduce response size
        if result.get("code") == 0:
            chats = result.get("data", [])
            filtered_chats = [filter_chat_object(chat) for chat in chats]
            
            return create_response(data=filtered_chats)
        else:
            return create_response(data=[])
            
    except Exception as e:
        logger.error(f"获取聊天列表失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

@app.get("/api/v1/chats/{chat_id}", tags=["Chats"])
async def get_chat_details(
    chat_id: str,
    client_info: Dict = Depends(verify_api_key)
):
    """获取聊天详情"""
    logger.info(f"客户端 {client_info['client_name']} 请求聊天详情: {chat_id}")
    
    try:
        result = streaming_client.get_chat(chat_id)
        
        if result.get("code") == 0:
            chat_data = result.get("data", {})
            filtered_chat = filter_chat_object(chat_data)
            return create_response(data=filtered_chat)
        else:
            raise HTTPException(status_code=404, detail=create_error_response(404, "Chat not found"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取聊天详情失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

# ==================== Chat Completions (Legacy) ====================

@app.post("/api/v1/chats/{chat_id}/completions", tags=["Chats"])
async def chat_completion(
    chat_id: str,
    request: ChatMessageRequest,
    client_info: Dict = Depends(verify_api_key)
):
    """发送消息并获取回复 - 支持流式和非流式"""
    logger.info(f"客户端 {client_info['client_name']} 发送消息到对话: {chat_id} (stream={request.stream})")
    
    try:
        if request.stream:
            return StreamingResponse(
                _stream_chat_completion(chat_id, request.content),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            result = streaming_client.send_message(chat_id, request.content, stream=False)
            
            # Format response
            data = result.get("data", {})
            
            # Handle different response formats
            if isinstance(data, dict):
                answer = data.get("answer", "")
                references = data.get("references", [])
            else:
                answer = str(data) if data is not None else ""
                references = []
            
            return create_response(data={
                "id": f"msg_{uuid.uuid4()}",
                "chat_id": chat_id,
                "content": answer,
                "references": references,
                "created_at": datetime.now().isoformat()
            })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"聊天失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

async def _stream_chat_completion(chat_id: str, message: str) -> AsyncGenerator[str, None]:
    """流式聊天完成生成器"""
    try:
        # Get streaming iterator
        stream_iter = streaming_client.send_message(chat_id, message, stream=True)
        
        if hasattr(stream_iter, '__iter__'):
            for chunk in stream_iter:
                if chunk.get('chunk_type') == 'error':
                    yield f"data: {json.dumps({'error': chunk.get('error')})}\n\n"
                    break
                elif chunk.get('chunk_type') == 'content':
                    # Format as server-sent event
                    response_data = {
                        "code": 0,
                        "message": "",
                        "data": {
                            "answer": chunk.get('content', ''),
                            "reference": {},
                            "audio_binary": None,
                            "id": None,
                            "session_id": chunk.get('session_id')
                        }
                    }
                    yield f"data:{json.dumps(response_data)}\n\n"
        
        # Send completion marker
        yield f"data:{json.dumps({'code': 0, 'data': True})}\n\n"
        
    except Exception as e:
        logger.error(f"流式聊天失败: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

# ==================== OpenAI-Compatible Endpoints ====================

@app.post("/api/v1/chats/{chat_id}/openai/completions", tags=["OpenAI Compatible"])
async def openai_chat_completion(
    chat_id: str,
    request: OpenAIChatRequest,
    client_info: Dict = Depends(verify_api_key)
):
    """OpenAI兼容的聊天完成接口"""
    logger.info(f"客户端 {client_info['client_name']} OpenAI聊天请求: {chat_id} (stream={request.stream})")
    
    try:
        if request.stream:
            return StreamingResponse(
                _stream_openai_completion(chat_id, request),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            # Convert to OpenAI format
            messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
            result = streaming_client.send_message_openai_compatible(
                chat_id, messages, request.model, stream=False
            )
            return result
    except Exception as e:
        logger.error(f"OpenAI聊天失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

async def _stream_openai_completion(chat_id: str, request: OpenAIChatRequest) -> AsyncGenerator[str, None]:
    """OpenAI兼容的流式完成生成器"""
    try:
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        stream_iter = streaming_client.send_message_openai_compatible(
            chat_id, messages, request.model, stream=True
        )
        
        if hasattr(stream_iter, '__iter__'):
            for chunk in stream_iter:
                if chunk.get('error'):
                    yield f"data: {json.dumps(chunk)}\n\n"
                    break
                else:
                    yield f"data: {json.dumps(chunk)}\n\n"
        
        # Send done marker
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"OpenAI流式聊天失败: {e}")
        yield f"data: {json.dumps({'error': {'message': str(e), 'type': 'streaming_error'}})}\n\n"

# ==================== Retrieval ====================

@app.post("/api/v1/retrieval", tags=["Retrieval"])
async def retrieve_documents(
    request: RetrievalRequest,
    client_info: Dict = Depends(verify_api_key)
):
    """检索相关文档片段"""
    logger.info(f"客户端 {client_info['client_name']} 执行检索: {request.question[:50]}...")
    
    try:
        # Check dataset availability
        available_datasets = []
        for dataset_id in request.dataset_ids:
            try:
                dataset_result = streaming_client.get_dataset(dataset_id)
                dataset_data = dataset_result.get("data", {})
                
                if dataset_data and dataset_data.get("chunk_num", 0) > 0:
                    available_datasets.append(dataset_id)
                else:
                    logger.warning(f"数据集 {dataset_id} 无可用内容，跳过检索")
            except Exception as e:
                logger.warning(f"检查数据集 {dataset_id} 失败: {e}")
                continue
        
        if not available_datasets:
            return create_response(data={
                "chunks": [],
                "total": 0,
                "message": "所选数据集均无可检索内容，请先上传并解析文档"
            })
        
        # Execute retrieval
        result = streaming_client.retrieve(
            question=request.question,
            dataset_ids=available_datasets,
            top_k=request.top_k
        )
        
        retrieval_data = result.get("data", {})
        chunks = retrieval_data.get("chunks", [])
        
        # Format retrieval results
        formatted_chunks = []
        for chunk in chunks:
            if isinstance(chunk, dict):
                formatted_chunks.append({
                    "id": chunk.get("id"),
                    "content": chunk.get("content_with_weight", chunk.get("content", "")),
                    "similarity": chunk.get("similarity", 0),
                    "document_name": chunk.get("document_name", ""),
                    "dataset_id": chunk.get("dataset_id", ""),
                    "position": chunk.get("position", 0)
                })
        
        return create_response(data={
            "chunks": formatted_chunks,
            "total": len(formatted_chunks),
            "query": request.question,
            "searched_datasets": available_datasets,
            "skipped_datasets": list(set(request.dataset_ids) - set(available_datasets))
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检索失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

# ==================== Startup ====================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8055))  # Use different port for V5
    logger.info(f"启动 xDAN RAG Copilot API Proxy Server V5 在端口 {port}")
    logger.info(f"Swagger文档地址: http://localhost:{port}/docs")
    logger.info(f"RAGFlow 后端地址: {RAGFLOW_API_URL}")
    logger.info(f"已配置 {len(ALLOWED_API_KEYS)} 个客户端 API Key")
    logger.info("V5新特性: 增强流式聊天支持，OpenAI兼容端点，自动回退机制")
    
    uvicorn.run(
        "xdan_api_proxy_server_v5:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )