#!/usr/bin/env python3
"""
xDAN RAG Copilot API Proxy Server V4 - 优化版
- 包含V3的所有功能
- 解决聊天列表响应过大的问题
- 过滤冗余字段，优化数据传输
"""

import os
import sys
import json
import logging
import time
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, AsyncGenerator
from contextlib import asynccontextmanager
import uuid
import tempfile
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from functools import wraps

# 加载环境变量
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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== 配置 ====================

# RAGFlow 配置
RAGFLOW_API_URL = os.getenv("RAGFLOW_API_URL", "http://150.109.16.195:7080")
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY", "ragflow-g4ZWE3OTNhNDUxYTExZjA4YTljMDI0Mm")

# 第三方调用者的认证配置
ALLOWED_API_KEYS = {
    "xdan-demo-key-123456": {
        "name": "Demo Client",
        "permissions": ["read", "write"],
        "rate_limit": 100
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

# ==================== 数据过滤 ====================

def filter_chat_object(chat: Dict) -> Dict:
    """
    过滤聊天对象中的冗余字段
    将2.4KB的对象压缩到约200B
    """
    filtered = {
        "id": chat.get("id"),
        "name": chat.get("name"),
        "description": chat.get("description"),
        "create_date": chat.get("create_date"),
        "update_date": chat.get("update_date"),
        "status": chat.get("status", "1"),
        "language": chat.get("language", "English")
    }
    
    # 提取数据集的简要信息
    datasets = chat.get("datasets", [])
    if datasets:
        filtered["dataset_info"] = [{
            "id": ds.get("id"),
            "name": ds.get("name"),
            "doc_num": ds.get("doc_num", 0),
            "chunk_num": ds.get("chunk_num", 0)
        } for ds in datasets]
    
    # 提取LLM的简要信息
    llm = chat.get("llm", {})
    if llm:
        filtered["llm_model"] = llm.get("model_name", "unknown")
    
    # 提取prompt类型
    filtered["prompt_type"] = chat.get("prompt_type", "simple")
    
    return filtered

def filter_dataset_object(dataset: Dict) -> Dict:
    """过滤数据集对象中的冗余字段"""
    return {
        "id": dataset.get("id"),
        "name": dataset.get("name"),
        "description": dataset.get("description"),
        "document_count": dataset.get("doc_num", 0),
        "chunk_count": dataset.get("chunk_num", 0),
        "token_count": dataset.get("token_num", 0),
        "language": dataset.get("language", "English"),
        "created_at": dataset.get("create_date"),
        "updated_at": dataset.get("update_date"),
        "status": dataset.get("status", "1")
    }

# ==================== 数据模型 ====================

class DatasetCreateRequest(BaseModel):
    name: str = Field(..., description="数据集名称")
    description: str = Field(default="", description="数据集描述")
    embedding_model: str = Field(default="BAAI/bge-m3@SILICONFLOW", description="嵌入模型")
    chunk_method: str = Field(default="naive", description="分块方法")
    chunk_size: int = Field(default=512, description="分块大小")
    parser_config: Dict = Field(default_factory=dict, description="解析器配置")

class DocumentStatusResponse(BaseModel):
    id: str
    name: str
    status: str  # parsing, parsed, failed
    progress: float
    error_message: Optional[str] = None

class ChatCreateRequest(BaseModel):
    name: str
    dataset_ids: List[str]
    description: Optional[str] = ""

class ChatMessageRequest(BaseModel):
    content: str
    stream: bool = False

class ChatDetailRequest(BaseModel):
    include_datasets: bool = False
    include_llm_config: bool = False
    include_prompt: bool = False

# ==================== 认证 ====================

async def verify_api_key(
    api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None)
):
    """验证第三方调用者的 API Key"""
    key = None
    
    if api_key:
        key = api_key
    elif authorization and authorization.startswith("Bearer "):
        key = authorization[7:]
    
    if not key or key not in ALLOWED_API_KEYS:
        raise HTTPException(
            status_code=401,
            detail=create_error_response(401, "未授权：无效的 API Key")
        )
    
    client_info = ALLOWED_API_KEYS[key]
    return {
        "api_key": key,
        "client_name": client_info["name"],
        "permissions": client_info["permissions"]
    }

# ==================== 增强的 RAGFlow 客户端 ====================

class EnhancedRAGFlowClient:
    """增强的 RAGFlow 客户端 - 带重试和错误处理"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        # 配置重试策略 - 解决502错误
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "POST", "DELETE", "OPTIONS", "TRACE"],
            backoff_factor=1,
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 设置默认超时
        self.timeout = 30
        
        # 设置请求头
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "xDAN-RAG-Proxy/4.0"
        })
    
    def _handle_response(self, response: requests.Response) -> Dict:
        """统一处理响应"""
        try:
            # 处理502等错误
            if response.status_code == 502:
                raise HTTPException(
                    status_code=503,
                    detail=create_error_response(503, "RAGFlow服务暂时不可用，请稍后重试")
                )
            
            response.raise_for_status()
            
            # 对于大响应，使用流式读取
            if int(response.headers.get('content-length', 0)) > 10240:  # 10KB
                logger.info(f"Large response detected: {response.headers.get('content-length')} bytes")
            
            result = response.json()
            
            # RAGFlow返回格式检查
            if isinstance(result, dict) and "code" in result:
                if result["code"] != 0:
                    # RAGFlow业务错误
                    error_msg = result.get("message", "Unknown error")
                    logger.error(f"RAGFlow error: {error_msg}")
                    
                    # 特殊处理某些错误
                    if "hasn't parsed files" in error_msg:
                        raise HTTPException(
                            status_code=400,
                            detail=create_error_response(400, "数据集尚未包含已解析的文档，请先上传并等待文档处理完成")
                        )
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail=create_error_response(400, error_msg)
                        )
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 401:
                    raise HTTPException(
                        status_code=500,
                        detail=create_error_response(500, "RAGFlow认证失败")
                    )
            raise HTTPException(
                status_code=503,
                detail=create_error_response(503, f"请求失败: {str(e)}")
            )
    
    # 数据集相关方法
    def create_dataset(self, data: Dict) -> Dict:
        """创建数据集"""
        # 转换参数格式
        ragflow_data = {
            "name": data["name"],
            "description": data.get("description", ""),
            "embedding_model": data.get("embedding_model", "BAAI/bge-m3@SILICONFLOW"),
            "chunk_method": data.get("chunk_method", "naive"),
            "parser_config": {
                "chunk_token_num": data.get("chunk_size", 512),
                "delimiter": "\n!?。；！？",
                "layout_recognize": True,
                "auto_keywords": 0,
                "auto_questions": 0
            }
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/datasets",
            json=ragflow_data,
            timeout=self.timeout
        )
        
        result = self._handle_response(response)
        
        # 处理返回的数据格式
        if result.get("code") == 0 and isinstance(result.get("data"), bool):
            # 如果data是bool类型，尝试从响应中提取实际的数据集信息
            logger.warning("RAGFlow returned bool data, attempting to list datasets to get the new dataset info")
            
            # 等待一下让数据集创建完成
            time.sleep(1)
            
            # 列出数据集找到刚创建的
            list_resp = self.session.get(
                f"{self.base_url}/api/v1/datasets",
                timeout=self.timeout
            )
            list_result = self._handle_response(list_resp)
            
            if list_result.get("data"):
                # 找到名称匹配的最新数据集
                for ds in list_result["data"]:
                    if ds.get("name") == data["name"]:
                        result["data"] = ds
                        break
        
        return result
    
    def list_datasets(self, page: int = 1, page_size: int = 10, id: str = None, name: str = None) -> Dict:
        """列出数据集，支持按ID和名称过滤"""
        params = {"page": page, "page_size": page_size}
        
        if id:
            params["id"] = id
        if name:
            params["name"] = name
            
        response = self.session.get(
            f"{self.base_url}/api/v1/datasets",
            params=params,
            timeout=self.timeout
        )
        return self._handle_response(response)
    
    def get_dataset(self, dataset_id: str) -> Dict:
        """获取数据集详情"""
        response = self.session.get(
            f"{self.base_url}/api/v1/datasets/{dataset_id}",
            timeout=self.timeout
        )
        return self._handle_response(response)
    
    # 文档相关方法
    def upload_document(self, dataset_id: str, file_name: str, file_content: bytes, 
                       content_type: str = "text/plain", parser_id: str = "naive") -> Dict:
        """上传文档到数据集"""
        files = {
            "file": (file_name, file_content, content_type)
        }
        data = {
            "parser_id": parser_id
        }
        
        # 文件上传时不设置Content-Type header
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        response = self.session.post(
            f"{self.base_url}/api/v1/datasets/{dataset_id}/documents",
            files=files,
            data=data,
            headers=headers,
            timeout=60  # 文件上传需要更长的超时时间
        )
        
        return self._handle_response(response)
    
    def list_documents(self, dataset_id: str, page: int = 1) -> Dict:
        """列出数据集的文档"""
        response = self.session.get(
            f"{self.base_url}/api/v1/datasets/{dataset_id}/documents",
            params={"page": page},
            timeout=self.timeout
        )
        return self._handle_response(response)
    
    def get_document_status(self, dataset_id: str, doc_id: str) -> Optional[DocumentStatusResponse]:
        """查询文档解析状态"""
        try:
            # 获取文档列表
            result = self.list_documents(dataset_id)
            documents = result.get("data", [])
            
            # 查找特定文档
            for doc in documents:
                if doc.get("id") == doc_id:
                    return DocumentStatusResponse(
                        id=doc.get("id"),
                        name=doc.get("name", ""),
                        status=doc.get("status", "unknown"),
                        progress=doc.get("progress", 0),
                        error_message=doc.get("error_message")
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document status: {e}")
            return None
    
    # 对话相关方法
    def create_chat(self, data: Dict) -> Dict:
        """创建对话"""
        chat_data = {
            "name": data.get("name", "新对话"),
            "dataset_ids": data.get("dataset_ids", [])
        }
        
        # 可选参数
        if "description" in data:
            chat_data["description"] = data["description"]
        
        response = self.session.post(
            f"{self.base_url}/api/v1/chats",
            json=chat_data,
            timeout=self.timeout
        )
        
        return self._handle_response(response)
    
    def list_chats(self, page: int = 1, page_size: int = 10) -> Dict:
        """
        获取聊天列表 - V4优化版
        使用流式读取处理大响应
        """
        params = {"page": page}
        
        # 限制page_size避免响应过大
        if page_size > 20:
            logger.warning(f"page_size {page_size} too large, limiting to 20")
            page_size = 20
        
        if page_size:
            params["page_size"] = page_size
        
        response = self.session.get(
            f"{self.base_url}/api/v1/chats",
            params=params,
            timeout=self.timeout,
            stream=True  # 使用流式读取
        )
        
        # 对于聊天列表，特殊处理大响应
        if response.status_code == 200:
            try:
                # 读取完整响应
                content = response.content
                result = json.loads(content)
                
                # 过滤聊天对象
                if result.get("code") == 0 and isinstance(result.get("data"), list):
                    filtered_chats = [filter_chat_object(chat) for chat in result["data"]]
                    result["data"] = filtered_chats
                    
                    # 记录优化效果
                    original_size = len(content)
                    filtered_size = len(json.dumps(result))
                    logger.info(f"Chat list response optimized: {original_size} -> {filtered_size} bytes "
                              f"({(1 - filtered_size/original_size)*100:.1f}% reduction)")
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse chat list response: {e}")
                raise HTTPException(
                    status_code=502,
                    detail=create_error_response(502, "RAGFlow返回的数据格式错误")
                )
        else:
            return self._handle_response(response)
    
    def get_chat(self, chat_id: str) -> Dict:
        """获取聊天详情 - 包含完整信息"""
        response = self.session.get(
            f"{self.base_url}/api/v1/chats/{chat_id}",
            timeout=self.timeout
        )
        return self._handle_response(response)
    
    def send_message(self, chat_id: str, message: str, stream: bool = False) -> Dict:
        """发送消息"""
        payload = {
            "question": message,
            "stream": stream
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/chats/{chat_id}/completions",
            json=payload,
            timeout=60  # 聊天需要更长时间
        )
        
        return self._handle_response(response)

# 创建全局客户端实例
ragflow_client = EnhancedRAGFlowClient(RAGFLOW_API_URL, RAGFLOW_API_KEY)

# ==================== FastAPI 应用 ====================

app = FastAPI(
    title="xDAN RAG Copilot API Proxy V4",
    description="优化版API代理服务，解决响应数据过大问题",
    version="4.0.0",
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

# ==================== 健康检查 ====================

@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查接口"""
    return create_response(data={
        "status": "healthy",
        "service": "xDAN RAG Copilot API Proxy V4",
        "timestamp": datetime.now().isoformat(),
        "features": ["document_upload", "retry_mechanism", "status_query", "response_optimization"]
    })

@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """详细健康检查"""
    health_status = {
        "service": "healthy",
        "ragflow": "unknown",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # 测试RAGFlow连接
        result = ragflow_client.list_datasets()
        if result.get("code") == 0:
            health_status["ragflow"] = "healthy"
        else:
            health_status["ragflow"] = "unhealthy"
            health_status["service"] = "degraded"
    except Exception as e:
        health_status["ragflow"] = f"unreachable: {str(e)}"
        health_status["service"] = "degraded"
    
    return create_response(data=health_status)

# ==================== 数据集接口 ====================

@app.post("/api/v1/datasets", tags=["Datasets"])
async def create_dataset(
    request: DatasetCreateRequest,
    client_info: Dict = Depends(verify_api_key)
):
    """创建数据集"""
    logger.info(f"客户端 {client_info['client_name']} 创建数据集: {request.name}")
    
    try:
        result = ragflow_client.create_dataset(request.dict())
        return create_response(data=filter_dataset_object(result.get("data", {})))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建数据集失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

@app.get("/api/v1/datasets", tags=["Datasets"])
async def list_datasets(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    client_info: Dict = Depends(verify_api_key)
):
    """获取数据集列表"""
    logger.info(f"客户端 {client_info['client_name']} 请求数据集列表")
    
    try:
        result = ragflow_client.list_datasets(page)
        data = result.get("data", [])
        
        # 过滤数据集对象
        filtered_data = [filter_dataset_object(ds) for ds in data] if isinstance(data, list) else []
        
        return create_response(data=filtered_data, meta={
            "page": page,
            "page_size": page_size,
            "total": len(filtered_data)
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据集列表失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

@app.get("/api/v1/datasets/{dataset_id}", tags=["Datasets"])
async def get_dataset_detail(
    dataset_id: str,
    client_info: Dict = Depends(verify_api_key)
):
    """获取数据集详情 - 使用列表API过滤"""
    logger.info(f"客户端 {client_info['client_name']} 获取数据集详情: {dataset_id}")
    
    try:
        # RAGFlow不支持单个数据集查询，使用列表API过滤
        result = ragflow_client.list_datasets(id=dataset_id, page_size=1)
        datasets = result.get("data", [])
        
        if not datasets:
            raise HTTPException(status_code=404, detail=create_error_response(404, "数据集不存在"))
        
        data = datasets[0]  # 获取第一个匹配的数据集
        
        # 过滤并增强数据集信息
        filtered_data = filter_dataset_object(data)
        
        # 添加状态分析
        doc_count = filtered_data.get("document_count", 0)
        chunk_count = filtered_data.get("chunk_count", 0)
        token_count = filtered_data.get("token_count", 0)
        
        # 判断数据集可用性
        if doc_count == 0:
            rag_status = "empty"
            rag_message = "数据集为空，需要上传文档"
        elif chunk_count == 0:
            rag_status = "parsing"
            rag_message = "文档正在解析中，暂时无法进行RAG对话"
        elif token_count == 0:
            rag_status = "processing"
            rag_message = "文档解析完成，正在生成向量，稍后可进行RAG对话"
        else:
            rag_status = "ready"
            rag_message = "数据集就绪，可进行RAG对话"
        
        filtered_data["rag_availability"] = {
            "status": rag_status,
            "message": rag_message,
            "can_chat": rag_status == "ready",
            "can_retrieve": rag_status == "ready"
        }
        
        return create_response(data=filtered_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据集详情失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

# ==================== 文档接口 ====================

@app.post("/api/v1/datasets/{dataset_id}/documents", tags=["Documents"])
async def upload_document(
    dataset_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    parser_id: str = Form("naive"),
    client_info: Dict = Depends(verify_api_key)
):
    """上传文档到数据集"""
    logger.info(f"客户端 {client_info['client_name']} 上传文档到数据集: {dataset_id}")
    logger.info(f"文件名: {file.filename}, 类型: {file.content_type}, 解析器: {parser_id}")
    
    try:
        # 读取文件内容
        file_content = await file.read()
        
        # 上传文档
        result = ragflow_client.upload_document(
            dataset_id=dataset_id,
            file_name=file.filename,
            file_content=file_content,
            content_type=file.content_type or "application/octet-stream",
            parser_id=parser_id
        )
        
        doc_data = result.get("data", {})
        
        # 如果是dict类型，说明上传成功
        if isinstance(doc_data, dict):
            doc_id = doc_data.get("id")
            logger.info(f"文档上传成功: {doc_id}")
            
            # 添加后台任务来跟踪解析状态
            if doc_id:
                background_tasks.add_task(
                    track_document_parsing,
                    dataset_id,
                    doc_id,
                    file.filename
                )
            
            return create_response(data={
                "id": doc_id,
                "name": file.filename,
                "status": "uploading",
                "message": "文档已上传，正在处理中..."
            })
        else:
            # 处理其他返回格式
            return create_response(data={
                "name": file.filename,
                "status": "uploaded",
                "message": "文档已上传"
            })
            
    except HTTPException:
        raise
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
        result = ragflow_client.list_documents(dataset_id, page)
        documents = result.get("data", [])
        
        # 确保documents是列表类型
        if not isinstance(documents, list):
            logger.warning(f"文档列表返回类型异常: {type(documents)}, 值: {documents}")
            documents = []
        
        # 格式化文档信息
        formatted_docs = []
        for doc in documents:
            # 确保doc是字典类型
            if not isinstance(doc, dict):
                logger.warning(f"文档对象类型异常: {type(doc)}, 值: {doc}")
                continue
                
            formatted_docs.append({
                "id": doc.get("id"),
                "name": doc.get("name"),
                "status": doc.get("status", "unknown"),
                "progress": doc.get("progress", 0),
                "size": doc.get("size", 0),
                "created_at": doc.get("created_at"),
                "chunk_count": doc.get("chunk_count", 0)
            })
        
        return create_response(data=formatted_docs, meta={
            "page": page,
            "page_size": page_size,
            "total": len(formatted_docs)
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

@app.get("/api/v1/datasets/{dataset_id}/documents/{doc_id}/status", tags=["Documents"])
async def get_document_status(
    dataset_id: str,
    doc_id: str,
    client_info: Dict = Depends(verify_api_key)
):
    """查询文档解析状态"""
    logger.info(f"客户端 {client_info['client_name']} 查询文档状态: {doc_id}")
    
    try:
        status = ragflow_client.get_document_status(dataset_id, doc_id)
        
        if status:
            return create_response(data=status.dict())
        else:
            raise HTTPException(
                status_code=404,
                detail=create_error_response(404, "文档未找到")
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询文档状态失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

# ==================== 对话接口 - V4优化版 ====================

@app.post("/api/v1/chats", tags=["Chats"])
async def create_chat(
    request: ChatCreateRequest,
    client_info: Dict = Depends(verify_api_key)
):
    """创建对话 - 支持空数据集的兼容模式"""
    logger.info(f"客户端 {client_info['client_name']} 创建对话: {request.name}")
    
    try:
        # 检查数据集可用性
        available_datasets = []
        unavailable_datasets = []
        
        for dataset_id in request.dataset_ids:
            try:
                dataset_result = ragflow_client.get_dataset(dataset_id)
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
        
        # 根据可用数据集情况决定聊天模式
        if available_datasets:
            # RAG模式：有可用数据集
            chat_mode = "rag"
            datasets_for_chat = available_datasets
            logger.info(f"RAG模式聊天，使用数据集: {available_datasets}")
        else:
            # 普通模式：无可用数据集，使用基础LLM对话
            chat_mode = "basic"
            datasets_for_chat = []
            logger.info("基础LLM模式聊天，无数据集增强")
        
        # 创建聊天（允许空数据集）
        chat_request = {
            "name": request.name,
            "dataset_ids": datasets_for_chat,
            "description": request.description or f"聊天模式: {chat_mode}"
        }
        
        result = ragflow_client.create_chat(chat_request)
        chat_data = result.get("data", {})
        
        # 增强响应信息
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
    page_size: int = Query(10, ge=1, le=20),  # 限制最大20
    client_info: Dict = Depends(verify_api_key)
):
    """
    获取聊天列表 - V4优化版
    自动过滤冗余字段，减少响应大小
    """
    logger.info(f"客户端 {client_info['client_name']} 请求聊天列表 (page={page}, page_size={page_size})")
    
    try:
        # 使用优化的list_chats方法
        result = ragflow_client.list_chats(page, page_size)
        
        # 结果已经被过滤
        data = result.get("data", [])
        
        return create_response(data=data, meta={
            "page": page,
            "page_size": page_size,
            "total": len(data) if isinstance(data, list) else 0,
            "optimized": True  # 标记响应已优化
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取聊天列表失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

@app.get("/api/v1/chats/{chat_id}", tags=["Chats"])
async def get_chat_detail(
    chat_id: str,
    include_datasets: bool = Query(False, description="是否包含完整数据集信息"),
    include_llm_config: bool = Query(False, description="是否包含LLM配置"),
    include_prompt: bool = Query(False, description="是否包含提示词配置"),
    client_info: Dict = Depends(verify_api_key)
):
    """
    获取聊天详情 - 可选择包含的信息
    """
    logger.info(f"客户端 {client_info['client_name']} 获取聊天详情: {chat_id}")
    
    try:
        result = ragflow_client.get_chat(chat_id)
        chat_data = result.get("data", {})
        
        if isinstance(chat_data, dict):
            # 基础信息
            filtered_chat = filter_chat_object(chat_data)
            
            # 根据请求参数添加额外信息
            if include_datasets:
                filtered_chat["datasets"] = chat_data.get("datasets", [])
            
            if include_llm_config:
                filtered_chat["llm"] = chat_data.get("llm", {})
            
            if include_prompt:
                filtered_chat["prompt"] = chat_data.get("prompt", {})
            
            return create_response(data=filtered_chat)
        else:
            return create_response(data=chat_data)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取聊天详情失败: {e}")
        raise HTTPException(status_code=500, detail=create_error_response(500, str(e)))

@app.post("/api/v1/chats/{chat_id}/completions", tags=["Chats"])
async def chat_completion(
    chat_id: str,
    request: ChatMessageRequest,
    client_info: Dict = Depends(verify_api_key)
):
    """发送消息并获取回复"""
    logger.info(f"客户端 {client_info['client_name']} 发送消息到对话: {chat_id}")
    
    try:
        result = ragflow_client.send_message(chat_id, request.content, request.stream)
        
        # 格式化响应
        data = result.get("data", {})
        
        # 处理不同的响应格式
        if isinstance(data, dict):
            answer = data.get("answer", "")
            references = data.get("references", [])
        else:
            # 如果data是其他格式（如bool），尝试从result中提取
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

# ==================== 检索接口 ====================

class RetrievalRequest(BaseModel):
    question: str = Field(..., description="检索问题")
    dataset_ids: List[str] = Field(..., description="要检索的数据集ID列表")
    top_k: int = Field(default=5, ge=1, le=20, description="返回的最相关结果数量")

@app.post("/api/v1/retrieval", tags=["Retrieval"])
async def retrieve_documents(
    request: RetrievalRequest,
    client_info: Dict = Depends(verify_api_key)
):
    """检索相关文档片段"""
    logger.info(f"客户端 {client_info['client_name']} 执行检索: {request.question[:50]}...")
    
    try:
        # 检查数据集可用性
        available_datasets = []
        for dataset_id in request.dataset_ids:
            try:
                dataset_result = ragflow_client.get_dataset(dataset_id)
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
        
        # 执行检索
        result = ragflow_client.retrieve(
            question=request.question,
            dataset_ids=available_datasets,
            top_k=request.top_k
        )
        
        retrieval_data = result.get("data", {})
        chunks = retrieval_data.get("chunks", [])
        
        # 格式化检索结果
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


# ==================== 辅助函数 ====================

async def track_document_parsing(dataset_id: str, doc_id: str, doc_name: str):
    """后台任务：跟踪文档解析状态"""
    logger.info(f"开始跟踪文档解析: {doc_name} (ID: {doc_id})")
    
    max_attempts = 60  # 最多检查60次
    interval = 2  # 每2秒检查一次
    
    for i in range(max_attempts):
        await asyncio.sleep(interval)
        
        try:
            status = ragflow_client.get_document_status(dataset_id, doc_id)
            
            if status:
                logger.info(f"文档 {doc_name} 状态: {status.status}, 进度: {status.progress}%")
                
                if status.status in ["parsed", "done"]:
                    logger.info(f"文档 {doc_name} 解析完成！")
                    break
                elif status.status in ["failed", "error"]:
                    logger.error(f"文档 {doc_name} 解析失败: {status.error_message}")
                    break
        except Exception as e:
            logger.error(f"检查文档状态时出错: {e}")
    
    logger.info(f"停止跟踪文档: {doc_name}")

# ==================== 启动服务 ====================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8050))
    logger.info(f"启动 xDAN RAG Copilot API Proxy Server V4 在端口 {port}")
    logger.info(f"Swagger文档地址: http://localhost:{port}/docs")
    logger.info(f"RAGFlow 后端地址: {RAGFLOW_API_URL}")
    logger.info(f"已配置 {len(ALLOWED_API_KEYS)} 个客户端 API Key")
    logger.info("V4新特性: 响应数据优化，过滤冗余字段，解决IncompleteRead问题")
    
    uvicorn.run(
        "xdan_api_proxy_server_v4:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )