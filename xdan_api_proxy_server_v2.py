#!/usr/bin/env python3
"""
xDAN RAG Copilot API Proxy Server V2 - 改进的认证机制
- 第三方调用者无需提供 RAGFlow API key
- 服务器端统一处理 RAGFlow 认证
- 支持为第三方调用者配置独立的认证
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, AsyncGenerator
import asyncio
from contextlib import asynccontextmanager
import uuid
import tempfile
import requests
from functools import wraps

from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Request, Depends, Query, Header
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== 配置 ====================

# RAGFlow 配置（从环境变量或配置文件读取）
RAGFLOW_API_URL = os.getenv("RAGFLOW_API_URL", "http://150.109.16.195:7080")
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY", "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm")

# 第三方调用者的认证配置（生产环境应该从数据库或配置文件读取）
ALLOWED_API_KEYS = {
    "xdan-demo-key-123456": {
        "name": "Demo Client",
        "permissions": ["read", "write"],
        "rate_limit": 100  # 每分钟请求数
    },
    "xdan-prod-key-789012": {
        "name": "Production Client",
        "permissions": ["read", "write"],
        "rate_limit": 1000
    }
}

# ==================== 统一响应格式 ====================

def create_response(code: int = 0, message: str = "Success", data: Any = None, meta: Dict = None) -> Dict:
    """创建统一格式的响应"""
    response = {
        "code": code,
        "message": message,
        "data": data
    }
    if meta:
        response["meta"] = meta
    return response

def create_error_response(code: int, message: str) -> Dict:
    """创建错误响应"""
    return create_response(code=code, message=message, data=None)

# ==================== 数据模型 ====================

class DatasetCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    embedding_model: str = "BAAI/bge-m3@SILICONFLOW"
    chunk_method: str = "naive"
    parser_config: Optional[Dict] = {
        "chunk_token_num": 512,
        "delimiter": "\n",
        "auto_keywords": 0,
        "auto_questions": 0
    }

class DatasetUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ChatCreateRequest(BaseModel):
    name: str
    dataset_ids: List[str]
    description: Optional[str] = ""

class ChatMessageRequest(BaseModel):
    content: str

class RetrievalRequest(BaseModel):
    question: str
    dataset_ids: List[str]
    page: int = 1
    page_size: int = 5

class BulkDeleteRequest(BaseModel):
    ids: List[str]

# ==================== 认证中间件 ====================

async def verify_api_key(
    api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None)
):
    """
    验证第三方调用者的 API Key
    支持两种方式：
    1. X-API-Key header
    2. Authorization: Bearer <api_key>
    """
    key = None
    
    # 优先检查 X-API-Key
    if api_key:
        key = api_key
    # 其次检查 Authorization header
    elif authorization:
        if authorization.startswith("Bearer "):
            key = authorization[7:]
    
    # 验证 key
    if not key or key not in ALLOWED_API_KEYS:
        raise HTTPException(
            status_code=401,
            detail=create_error_response(401, "未授权：无效的 API Key")
        )
    
    # 返回客户端信息
    client_info = ALLOWED_API_KEYS[key]
    return {
        "api_key": key,
        "client_name": client_info["name"],
        "permissions": client_info["permissions"]
    }

# ==================== RAGFlow API 客户端 ====================

class RAGFlowClient:
    """RAGFlow API 客户端 - 处理所有与 RAGFlow 的交互"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """发送请求到 RAGFlow"""
        url = f"{self.base_url}{endpoint}"
        
        # 确保所有请求都带有认证头
        if "headers" in kwargs:
            kwargs["headers"].update(self.headers)
        else:
            kwargs["headers"] = self.headers.copy()
            
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"RAGFlow API 请求失败: {e}")
            raise HTTPException(
                status_code=500,
                detail=create_error_response(500, f"上游服务错误: {str(e)}")
            )
    
    # 数据集相关方法
    def create_dataset(self, data: Dict) -> Dict:
        return self._make_request("POST", "/api/v1/datasets", json=data)
    
    def list_datasets(self, page: int = 1, page_size: int = 10) -> Dict:
        return self._make_request("GET", "/api/v1/datasets", params={"page": page, "size": page_size})
    
    def get_dataset(self, dataset_id: str) -> Dict:
        return self._make_request("GET", f"/api/v1/datasets/{dataset_id}")
    
    def update_dataset(self, dataset_id: str, data: Dict) -> Dict:
        return self._make_request("PUT", f"/api/v1/datasets/{dataset_id}", json=data)
    
    def delete_dataset(self, dataset_id: str) -> Dict:
        return self._make_request("DELETE", f"/api/v1/datasets/{dataset_id}")
    
    # 文档相关方法
    def upload_document(self, dataset_id: str, file_data, parser_id: str = "default") -> Dict:
        files = {"file": file_data}
        data = {"parser_id": parser_id}
        # 文件上传时不设置 Content-Type
        headers = {"Authorization": f"Bearer {self.api_key}"}
        return self._make_request(
            "POST", 
            f"/api/v1/datasets/{dataset_id}/documents",
            files=files,
            data=data,
            headers=headers
        )
    
    def list_documents(self, dataset_id: str, page: int = 1, page_size: int = 10) -> Dict:
        return self._make_request(
            "GET", 
            f"/api/v1/datasets/{dataset_id}/documents",
            params={"page": page, "size": page_size}
        )
    
    # 对话相关方法
    def create_chat(self, data: Dict) -> Dict:
        return self._make_request("POST", "/api/v1/chats", json=data)
    
    def list_chats(self, page: int = 1, page_size: int = 10) -> Dict:
        return self._make_request("GET", "/api/v1/chats", params={"page": page, "size": page_size})
    
    def send_message(self, chat_id: str, message: str) -> Dict:
        return self._make_request(
            "POST",
            f"/api/v1/chats/{chat_id}/completions",
            json={"question": message}
        )
    
    # 检索相关方法
    def retrieval(self, data: Dict) -> Dict:
        return self._make_request("POST", "/api/v1/retrieval", json=data)

# 创建全局 RAGFlow 客户端实例
ragflow_client = RAGFlowClient(RAGFLOW_API_URL, RAGFLOW_API_KEY)

# ==================== FastAPI 应用 ====================

app = FastAPI(
    title="xDAN RAG Copilot API Proxy V2",
    description="改进的 API 代理服务，第三方调用者无需 RAGFlow API key",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 健康检查接口 ====================

@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查接口 - 无需认证"""
    return create_response(data={
        "status": "healthy",
        "service": "xDAN RAG Copilot API Proxy V2",
        "timestamp": datetime.now().isoformat()
    })

# ==================== 数据集相关接口 ====================

@app.get("/api/v1/datasets", tags=["Datasets"])
async def list_datasets(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    client_info: Dict = Depends(verify_api_key)
):
    """获取数据集列表"""
    logger.info(f"客户端 {client_info['client_name']} 请求数据集列表")
    
    try:
        result = ragflow_client.list_datasets(page, page_size)
        return create_response(data=result.get("data", []), meta={
            "page": page,
            "page_size": page_size,
            "total": result.get("total", 0)
        })
    except Exception as e:
        logger.error(f"获取数据集列表失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

@app.post("/api/v1/datasets", tags=["Datasets"])
async def create_dataset(
    request: DatasetCreateRequest,
    client_info: Dict = Depends(verify_api_key)
):
    """创建数据集"""
    logger.info(f"客户端 {client_info['client_name']} 创建数据集: {request.name}")
    
    try:
        # 转换请求格式以适配 RAGFlow API
        ragflow_data = {
            "name": request.name,
            "description": request.description,
            "embedding_model": request.embedding_model,
            "chunk_method": request.chunk_method,
            "parser_config": request.parser_config
        }
        
        result = ragflow_client.create_dataset(ragflow_data)
        return create_response(data=result.get("data"))
    except Exception as e:
        logger.error(f"创建数据集失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

@app.get("/api/v1/datasets/{dataset_id}", tags=["Datasets"])
async def get_dataset(
    dataset_id: str,
    client_info: Dict = Depends(verify_api_key)
):
    """获取数据集详情"""
    logger.info(f"客户端 {client_info['client_name']} 获取数据集: {dataset_id}")
    
    try:
        result = ragflow_client.get_dataset(dataset_id)
        return create_response(data=result.get("data"))
    except Exception as e:
        logger.error(f"获取数据集失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

@app.put("/api/v1/datasets/{dataset_id}", tags=["Datasets"])
async def update_dataset(
    dataset_id: str,
    request: DatasetUpdateRequest,
    client_info: Dict = Depends(verify_api_key)
):
    """更新数据集"""
    logger.info(f"客户端 {client_info['client_name']} 更新数据集: {dataset_id}")
    
    try:
        update_data = request.dict(exclude_unset=True)
        result = ragflow_client.update_dataset(dataset_id, update_data)
        return create_response(data=result.get("data"))
    except Exception as e:
        logger.error(f"更新数据集失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

@app.delete("/api/v1/datasets/{dataset_id}", tags=["Datasets"])
async def delete_dataset(
    dataset_id: str,
    client_info: Dict = Depends(verify_api_key)
):
    """删除数据集"""
    logger.info(f"客户端 {client_info['client_name']} 删除数据集: {dataset_id}")
    
    try:
        result = ragflow_client.delete_dataset(dataset_id)
        return create_response(message="数据集删除成功")
    except Exception as e:
        logger.error(f"删除数据集失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

# ==================== 文档相关接口 ====================

@app.post("/api/v1/datasets/{dataset_id}/documents", tags=["Documents"])
async def upload_document(
    dataset_id: str,
    file: UploadFile = File(...),
    parser_id: str = Form("default"),
    client_info: Dict = Depends(verify_api_key)
):
    """上传文档到数据集"""
    logger.info(f"客户端 {client_info['client_name']} 上传文档到数据集: {dataset_id}")
    
    try:
        # 读取文件内容
        file_content = await file.read()
        file_data = (file.filename, file_content, file.content_type)
        
        result = ragflow_client.upload_document(dataset_id, file_data, parser_id)
        return create_response(data=result.get("data"))
    except Exception as e:
        logger.error(f"上传文档失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

@app.get("/api/v1/datasets/{dataset_id}/documents", tags=["Documents"])
async def list_documents(
    dataset_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    client_info: Dict = Depends(verify_api_key)
):
    """获取数据集的文档列表"""
    logger.info(f"客户端 {client_info['client_name']} 获取数据集文档列表: {dataset_id}")
    
    try:
        result = ragflow_client.list_documents(dataset_id, page, page_size)
        return create_response(data=result.get("data", []), meta={
            "page": page,
            "page_size": page_size,
            "total": result.get("total", 0)
        })
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

# ==================== 对话相关接口 ====================

@app.post("/api/v1/chats", tags=["Chats"])
async def create_chat(
    request: ChatCreateRequest,
    client_info: Dict = Depends(verify_api_key)
):
    """创建对话"""
    logger.info(f"客户端 {client_info['client_name']} 创建对话: {request.name}")
    
    try:
        chat_data = {
            "name": request.name,
            "assistant_id": str(uuid.uuid4()),  # RAGFlow 可能需要
            "dataset_ids": request.dataset_ids
        }
        
        result = ragflow_client.create_chat(chat_data)
        return create_response(data=result.get("data"))
    except Exception as e:
        logger.error(f"创建对话失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

@app.get("/api/v1/chats", tags=["Chats"])
async def list_chats(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    client_info: Dict = Depends(verify_api_key)
):
    """获取对话列表"""
    logger.info(f"客户端 {client_info['client_name']} 获取对话列表")
    
    try:
        result = ragflow_client.list_chats(page, page_size)
        return create_response(data=result.get("data", []), meta={
            "page": page,
            "page_size": page_size,
            "total": result.get("total", 0)
        })
    except Exception as e:
        logger.error(f"获取对话列表失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

@app.post("/api/v1/chats/{chat_id}/completions", tags=["Chats"])
async def send_message(
    chat_id: str,
    request: ChatMessageRequest,
    client_info: Dict = Depends(verify_api_key)
):
    """发送消息到对话"""
    logger.info(f"客户端 {client_info['client_name']} 发送消息到对话: {chat_id}")
    
    try:
        result = ragflow_client.send_message(chat_id, request.content)
        return create_response(data=result.get("data"))
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

# ==================== 检索接口 ====================

@app.post("/api/v1/retrieval", tags=["Retrieval"])
async def retrieval(
    request: RetrievalRequest,
    client_info: Dict = Depends(verify_api_key)
):
    """知识库检索"""
    logger.info(f"客户端 {client_info['client_name']} 执行检索: {request.question}")
    
    try:
        retrieval_data = {
            "question": request.question,
            "dataset_ids": request.dataset_ids,
            "page": request.page,
            "size": request.page_size
        }
        
        result = ragflow_client.retrieval(retrieval_data)
        return create_response(data=result.get("data"))
    except Exception as e:
        logger.error(f"检索失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

# ==================== 启动服务 ====================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8050))
    logger.info(f"启动 xDAN RAG Copilot API Proxy Server V2 在端口 {port}")
    logger.info(f"Swagger文档地址: http://localhost:{port}/docs")
    logger.info(f"RAGFlow 后端地址: {RAGFLOW_API_URL}")
    logger.info(f"已配置 {len(ALLOWED_API_KEYS)} 个客户端 API Key")
    
    uvicorn.run(
        "xdan_api_proxy_server_v2:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )