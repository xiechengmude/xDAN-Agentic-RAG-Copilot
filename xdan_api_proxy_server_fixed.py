#!/usr/bin/env python3
"""
xDAN RAG Copilot API Proxy Server - 严格按照文档规范实现
完全符合 xDAN-RAG-Copilot-API接口对接文档.md 的所有规范
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

from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Request, Depends, Query
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

# ==================== 认证 ====================

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证Bearer Token"""
    token = credentials.credentials
    # 简单验证 - 生产环境应该验证真实token
    if not token or not token.startswith('ragflow-'):
        raise HTTPException(
            status_code=401,
            detail=create_error_response(401, "Invalid token")
        )
    return token

# ==================== 模拟数据存储 ====================

class MockDataStore:
    def __init__(self):
        self.datasets = {}
        self.documents = {}
        self.chats = {}
        self.messages = {}
        self._init_sample_data()
    
    def _init_sample_data(self):
        """初始化示例数据"""
        # 示例知识库
        sample_dataset = {
            "id": "7e8d9e924cde11f0afc90242ac140006",
            "name": "360test00000",
            "description": "Sample dataset for testing",
            "document_count": 3,
            "chunk_count": 201,
            "token_num": 46759,
            "embedding_model": "BAAI/bge-m3@SILICONFLOW",
            "chunk_method": "naive",
            "status": "1",
            "create_date": "Thu, 19 Jun 2025 15:24:53 GMT",
            "update_date": "Mon, 23 Jun 2025 09:18:35 GMT",
            "parser_config": {
                "chunk_token_num": 512,
                "delimiter": "\n",
                "auto_keywords": 0,
                "auto_questions": 0
            }
        }
        self.datasets[sample_dataset["id"]] = sample_dataset
        
        # 示例文档
        sample_doc = {
            "id": "4cae901c4fda11f0a76c0242ac140006",
            "name": "debug_upload.txt",
            "size": 78,
            "type": "doc",
            "location": "debug_upload.txt",
            "dataset_id": "7e8d9e924cde11f0afc90242ac140006",
            "run": "DONE",
            "parser_config": {
                "chunk_token_num": 512,
                "delimiter": "\n"
            }
        }
        self.documents[sample_doc["id"]] = sample_doc

# 全局数据存储
data_store = MockDataStore()

# ==================== FastAPI应用 ====================

app = FastAPI(
    title="xDAN RAG Copilot API Proxy Server",
    description="完全符合文档规范的API代理服务",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 健康检查 ====================

@app.get("/health")
async def health_check():
    """健康检查"""
    return create_response(data={"status": "healthy", "service": "xDAN RAG Copilot API Proxy"})

# ==================== 知识库管理 ====================

@app.get("/api/v1/datasets")
async def get_datasets(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    name: Optional[str] = Query(None),
    token: str = Depends(verify_token)
):
    """获取知识库列表"""
    try:
        datasets = list(data_store.datasets.values())
        
        # 名称过滤
        if name:
            datasets = [d for d in datasets if name.lower() in d["name"].lower()]
        
        # 分页
        total = len(datasets)
        start = (page - 1) * page_size
        end = start + page_size
        datasets = datasets[start:end]
        
        meta = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_next": end < total,
            "has_prev": page > 1
        }
        
        return create_response(data=datasets, meta=meta)
    except Exception as e:
        logger.error(f"获取知识库列表失败: {e}")
        return create_error_response(500, str(e))

@app.post("/api/v1/datasets")
async def create_dataset(
    request: DatasetCreateRequest,
    token: str = Depends(verify_token)
):
    """创建知识库"""
    try:
        dataset_id = str(uuid.uuid4()).replace('-', '')
        
        dataset = {
            "id": dataset_id,
            "name": request.name,
            "description": request.description,
            "document_count": 0,
            "chunk_count": 0,
            "token_num": 0,
            "embedding_model": request.embedding_model,
            "chunk_method": request.chunk_method,
            "status": "1",
            "create_date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "update_date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "parser_config": request.parser_config or {
                "chunk_token_num": 512,
                "delimiter": "\n",
                "auto_keywords": 0,
                "auto_questions": 0
            }
        }
        
        data_store.datasets[dataset_id] = dataset
        
        return create_response(data={
            "id": dataset_id,
            "name": request.name,
            "status": "1"
        })
    except Exception as e:
        logger.error(f"创建知识库失败: {e}")
        return create_error_response(500, str(e))

@app.get("/api/v1/datasets/{dataset_id}")
async def get_dataset(
    dataset_id: str,
    token: str = Depends(verify_token)
):
    """获取知识库详情"""
    try:
        if dataset_id not in data_store.datasets:
            return create_error_response(404, "Dataset not found")
            
        return create_response(data=data_store.datasets[dataset_id])
    except Exception as e:
        logger.error(f"获取知识库详情失败: {e}")
        return create_error_response(500, str(e))

@app.put("/api/v1/datasets/{dataset_id}")
async def update_dataset(
    dataset_id: str,
    request: DatasetUpdateRequest,
    token: str = Depends(verify_token)
):
    """更新知识库"""
    try:
        if dataset_id not in data_store.datasets:
            return create_error_response(404, "Dataset not found")
            
        dataset = data_store.datasets[dataset_id]
        if request.name:
            dataset["name"] = request.name
        if request.description is not None:
            dataset["description"] = request.description
        dataset["update_date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        return create_response(data=dataset)
    except Exception as e:
        logger.error(f"更新知识库失败: {e}")
        return create_error_response(500, str(e))

@app.delete("/api/v1/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    token: str = Depends(verify_token)
):
    """删除知识库"""
    try:
        if dataset_id not in data_store.datasets:
            return create_error_response(404, "Dataset not found")
            
        # 同时删除相关文档
        docs_to_delete = [doc_id for doc_id, doc in data_store.documents.items() 
                         if doc["dataset_id"] == dataset_id]
        for doc_id in docs_to_delete:
            del data_store.documents[doc_id]
            
        del data_store.datasets[dataset_id]
        
        return create_response(message="删除成功")
    except Exception as e:
        logger.error(f"删除知识库失败: {e}")
        return create_error_response(500, str(e))

# ==================== 文档管理 ====================

@app.post("/api/v1/datasets/{dataset_id}/documents")
async def upload_document(
    dataset_id: str,
    file: UploadFile = File(...),
    token: str = Depends(verify_token)
):
    """上传文档 - 严格按照文档规范使用multipart/form-data"""
    try:
        if dataset_id not in data_store.datasets:
            return create_error_response(404, "Dataset not found")
            
        if not file.filename:
            return create_error_response(101, "No file part!")
            
        doc_id = str(uuid.uuid4()).replace('-', '')
        
        # 读取文件内容
        content = await file.read()
        
        document = {
            "id": doc_id,
            "name": file.filename,
            "size": len(content),
            "type": "doc",
            "location": file.filename,
            "dataset_id": dataset_id,
            "run": "DONE",  # 模拟解析完成状态
            "parser_config": {
                "chunk_token_num": 512,
                "delimiter": "\n"
            }
        }
        
        data_store.documents[doc_id] = document
        
        # 更新知识库文档数量
        data_store.datasets[dataset_id]["document_count"] += 1
        
        # 返回数组格式 - 严格按照文档规范
        return create_response(data=[document])
    except Exception as e:
        logger.error(f"上传文档失败: {e}")
        return create_error_response(500, str(e))

@app.get("/api/v1/datasets/{dataset_id}/documents")
async def get_documents(
    dataset_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    token: str = Depends(verify_token)
):
    """获取文档列表"""
    try:
        if dataset_id not in data_store.datasets:
            return create_error_response(404, "Dataset not found")
            
        docs = [doc for doc in data_store.documents.values() 
                if doc["dataset_id"] == dataset_id]
        
        total = len(docs)
        start = (page - 1) * page_size
        end = start + page_size
        docs = docs[start:end]
        
        return create_response(data={"docs": docs, "total": total})
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        return create_error_response(500, str(e))

@app.get("/api/v1/datasets/{dataset_id}/documents/{doc_id}")
async def get_document_content(
    dataset_id: str,
    doc_id: str,
    token: str = Depends(verify_token)
):
    """获取文档内容 - 返回纯文本"""
    try:
        if doc_id not in data_store.documents:
            raise HTTPException(status_code=404, detail="Document not found")
            
        doc = data_store.documents[doc_id]
        if doc["dataset_id"] != dataset_id:
            raise HTTPException(status_code=404, detail="Document not found in this dataset")
            
        # 返回文档的文本内容（纯文本格式，符合文档规范）
        content = "这是文档的文本内容示例。在实际实现中，这里应该返回文档的实际内容。"
        return Response(content=content, media_type="text/plain")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档内容失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/datasets/{dataset_id}/documents/{doc_id}")
async def delete_document(
    dataset_id: str,
    doc_id: str,
    token: str = Depends(verify_token)
):
    """删除单个文档"""
    try:
        if doc_id not in data_store.documents:
            return create_error_response(404, "Document not found")
            
        doc = data_store.documents[doc_id]
        if doc["dataset_id"] != dataset_id:
            return create_error_response(404, "Document not found in this dataset")
            
        del data_store.documents[doc_id]
        
        # 更新知识库文档数量
        if dataset_id in data_store.datasets:
            data_store.datasets[dataset_id]["document_count"] -= 1
            
        return create_response(message="删除成功")
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        return create_error_response(500, str(e))

@app.delete("/api/v1/datasets/{dataset_id}/documents")
async def bulk_delete_documents(
    dataset_id: str,
    request: BulkDeleteRequest,
    token: str = Depends(verify_token)
):
    """批量删除文档"""
    try:
        if dataset_id not in data_store.datasets:
            return create_error_response(404, "Dataset not found")
            
        deleted_count = 0
        for doc_id in request.ids:
            if doc_id in data_store.documents and data_store.documents[doc_id]["dataset_id"] == dataset_id:
                del data_store.documents[doc_id]
                deleted_count += 1
                
        # 更新知识库文档数量
        data_store.datasets[dataset_id]["document_count"] -= deleted_count
        
        return create_response(message=f"成功删除 {deleted_count} 个文档")
    except Exception as e:
        logger.error(f"批量删除文档失败: {e}")
        return create_error_response(500, str(e))

@app.get("/api/v1/datasets/{dataset_id}/documents/{doc_id}/download")
async def download_document(
    dataset_id: str,
    doc_id: str,
    token: str = Depends(verify_token)
):
    """下载文档"""
    try:
        if doc_id not in data_store.documents:
            return create_error_response(404, "Document not found")
            
        doc = data_store.documents[doc_id]
        if doc["dataset_id"] != dataset_id:
            return create_error_response(404, "Document not found in this dataset")
            
        # 创建临时文件用于下载
        content = f"这是文档 {doc['name']} 的内容"
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        temp_file.write(content.encode())
        temp_file.close()
        
        return FileResponse(
            temp_file.name,
            filename=doc["name"],
            media_type="application/octet-stream"
        )
    except Exception as e:
        logger.error(f"下载文档失败: {e}")
        return create_error_response(500, str(e))

# ==================== 对话管理 ====================

@app.post("/api/v1/chats")
async def create_chat(
    request: ChatCreateRequest,
    token: str = Depends(verify_token)
):
    """创建对话"""
    try:
        # 检查知识库是否存在且包含已解析文档
        for dataset_id in request.dataset_ids:
            if dataset_id not in data_store.datasets:
                return create_error_response(404, f"Dataset {dataset_id} not found")
                
            # 检查是否有已解析的文档
            has_parsed_docs = any(
                doc["dataset_id"] == dataset_id and doc["run"] == "DONE"
                for doc in data_store.documents.values()
            )
            if not has_parsed_docs:
                return create_error_response(100, f"The dataset {dataset_id} doesn't own parsed file")
        
        chat_id = str(uuid.uuid4()).replace('-', '')
        
        chat = {
            "id": chat_id,
            "name": request.name,
            "dataset_ids": request.dataset_ids,
            "description": request.description,
            "llm": {
                "model_name": "deepseek-ai/DeepSeek-V3@SILICONFLOW",
                "temperature": 0.1,
                "max_tokens": 512
            },
            "create_date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
        }
        
        data_store.chats[chat_id] = chat
        
        return create_response(data=chat)
    except Exception as e:
        logger.error(f"创建对话失败: {e}")
        return create_error_response(500, str(e))

@app.get("/api/v1/chats")
async def get_chats(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    token: str = Depends(verify_token)
):
    """获取对话列表"""
    try:
        chats = list(data_store.chats.values())
        
        total = len(chats)
        start = (page - 1) * page_size
        end = start + page_size
        chats = chats[start:end]
        
        meta = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_next": end < total,
            "has_prev": page > 1
        }
        
        return create_response(data=chats, meta=meta)
    except Exception as e:
        logger.error(f"获取对话列表失败: {e}")
        return create_error_response(500, str(e))

@app.get("/api/v1/chats/{chat_id}")
async def get_chat(
    chat_id: str,
    token: str = Depends(verify_token)
):
    """获取对话详情"""
    try:
        if chat_id not in data_store.chats:
            return create_error_response(404, "Chat not found")
            
        return create_response(data=data_store.chats[chat_id])
    except Exception as e:
        logger.error(f"获取对话详情失败: {e}")
        return create_error_response(500, str(e))

@app.post("/api/v1/chats/{chat_id}/completions")
async def send_message(
    chat_id: str,
    request: ChatMessageRequest,
    token: str = Depends(verify_token)
):
    """发送消息 - SSE流式响应"""
    try:
        if chat_id not in data_store.chats:
            return create_error_response(404, "Chat not found")
            
        session_id = str(uuid.uuid4()).replace('-', '')
        
        async def generate_sse_response():
            # 第一条消息：包含回答内容
            response_data = {
                "code": 0,
                "message": "",
                "data": {
                    "answer": f"Hi! 您问的是：{request.content}。这是一个模拟回答。",
                    "reference": {
                        "chunks": [
                            {
                                "id": "chunk123",
                                "content_ltks": "相关的知识片段内容...",
                                "similarity": 0.85,
                                "document_name": "相关文档.pdf"
                            }
                        ]
                    },
                    "audio_binary": None,
                    "id": None,
                    "session_id": session_id
                }
            }
            yield f"data:{json.dumps(response_data, ensure_ascii=False)}\n\n"
            
            # 第二条消息：表示结束
            end_data = {
                "code": 0,
                "message": "",
                "data": True
            }
            yield f"data:{json.dumps(end_data, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate_sse_response(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        return create_error_response(500, str(e))

@app.get("/api/v1/chats/{chat_id}/messages")
async def get_chat_messages(
    chat_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    token: str = Depends(verify_token)
):
    """获取对话历史"""
    try:
        if chat_id not in data_store.chats:
            return create_error_response(404, "Chat not found")
            
        # 模拟消息历史
        messages = [
            {
                "id": "msg1",
                "role": "user",
                "content": "你好",
                "timestamp": datetime.now().isoformat()
            },
            {
                "id": "msg2", 
                "role": "assistant",
                "content": "您好！我是您的AI助手，有什么可以帮助您的吗？",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        total = len(messages)
        start = (page - 1) * page_size
        end = start + page_size
        messages = messages[start:end]
        
        meta = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_next": end < total,
            "has_prev": page > 1
        }
        
        return create_response(data=messages, meta=meta)
    except Exception as e:
        logger.error(f"获取对话历史失败: {e}")
        return create_error_response(500, str(e))

@app.delete("/api/v1/chats/{chat_id}")
async def delete_chat(
    chat_id: str,
    token: str = Depends(verify_token)
):
    """删除对话"""
    try:
        if chat_id not in data_store.chats:
            return create_error_response(404, "Chat not found")
            
        del data_store.chats[chat_id]
        
        return create_response(message="删除成功")
    except Exception as e:
        logger.error(f"删除对话失败: {e}")
        return create_error_response(500, str(e))

# ==================== 检索接口 ====================

@app.post("/api/v1/retrieval")
async def retrieval(
    request: RetrievalRequest,
    token: str = Depends(verify_token)
):
    """知识库检索"""
    try:
        # 检查知识库是否存在
        for dataset_id in request.dataset_ids:
            if dataset_id not in data_store.datasets:
                return create_error_response(404, f"Dataset {dataset_id} not found")
        
        # 模拟检索结果
        chunks = [
            {
                "id": "chunk123",
                "content_ltks": f"这是关于'{request.question}'的相关内容片段...",
                "similarity": 0.694,
                "document_name": "业务手册.pdf",
                "dataset_id": request.dataset_ids[0]
            },
            {
                "id": "chunk456",
                "content_ltks": f"另一个关于'{request.question}'的内容片段...",
                "similarity": 0.625,
                "document_name": "操作指南.pdf",
                "dataset_id": request.dataset_ids[0]
            }
        ]
        
        # 分页处理
        total = len(chunks)
        start = (request.page - 1) * request.page_size
        end = start + request.page_size
        chunks = chunks[start:end]
        
        return create_response(data={"chunks": chunks})
    except Exception as e:
        logger.error(f"检索失败: {e}")
        return create_error_response(500, str(e))

# ==================== 启动服务 ====================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8050))  # 使用文档中指定的8050端口
    logger.info(f"启动 xDAN RAG Copilot API Proxy Server 在端口 {port}")
    logger.info(f"Swagger文档地址: http://localhost:{port}/docs")
    
    uvicorn.run(
        "xdan_api_proxy_server_fixed:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )