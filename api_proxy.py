#!/usr/bin/env python3
"""
完整的RAGFlow API代理服务
严格按照 docs/API接口对接文档.md 中的接口定义
"""

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Any, Optional
import httpx
import json
import os
from dotenv import load_dotenv
import asyncio
from datetime import datetime

# 加载环境变量
load_dotenv()

# 配置
RAGFLOW_API_URL = os.getenv("RAGFLOW_API_URL", "http://150.109.16.195:7080")
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY", "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm")

# 创建 FastAPI 应用
app = FastAPI(
    title="xDAN Rag Copilot API Service",
    description="完整的RAGFlow API代理，包含所有知识库管理、文档处理、对话和检索功能",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP客户端配置
client = httpx.AsyncClient(
    base_url=RAGFLOW_API_URL,
    headers={
        "Authorization": f"Bearer {RAGFLOW_API_KEY}",
        "Content-Type": "application/json"
    },
    timeout=60.0
)

# =============== 知识库管理 API ===============

@app.get("/api/v1/datasets")
async def list_datasets(
    page: int = 1,
    page_size: int = 12,
    name: Optional[str] = None
):
    """获取知识库列表"""
    params = {
        "page": page,
        "page_size": page_size
    }
    if name:
        params["name"] = name
    
    response = await client.get("/api/v1/datasets", params=params)
    return response.json()

@app.post("/api/v1/datasets")
async def create_dataset(request: Request):
    """创建知识库"""
    data = await request.json()
    response = await client.post("/api/v1/datasets", json=data)
    return response.json()

@app.put("/api/v1/datasets/{dataset_id}")
async def update_dataset(dataset_id: str, request: Request):
    """更新知识库"""
    data = await request.json()
    response = await client.put(f"/api/v1/datasets/{dataset_id}", json=data)
    return response.json()

@app.delete("/api/v1/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str):
    """删除知识库"""
    response = await client.delete(f"/api/v1/datasets/{dataset_id}")
    return response.json()

# =============== 文档管理 API ===============

@app.post("/api/v1/datasets/{dataset_id}/documents")
async def upload_document(
    dataset_id: str,
    file: UploadFile = File(...)
):
    """上传文档"""
    # 读取文件内容
    content = await file.read()
    
    # 使用multipart/form-data上传
    files = {
        'file': (file.filename, content, file.content_type or 'application/octet-stream')
    }
    
    # 创建新的客户端，不设置Content-Type让httpx自动处理
    upload_client = httpx.AsyncClient(
        base_url=RAGFLOW_API_URL,
        headers={
            "Authorization": f"Bearer {RAGFLOW_API_KEY}"
        },
        timeout=60.0
    )
    
    response = await upload_client.post(
        f"/api/v1/datasets/{dataset_id}/documents",
        files=files
    )
    
    await upload_client.aclose()
    return response.json()

@app.get("/api/v1/datasets/{dataset_id}/documents")
async def list_documents(
    dataset_id: str,
    page: int = 1,
    page_size: int = 20
):
    """获取文档列表"""
    params = {
        "page": page,
        "page_size": page_size
    }
    
    response = await client.get(f"/api/v1/datasets/{dataset_id}/documents", params=params)
    return response.json()

@app.get("/api/v1/datasets/{dataset_id}/documents/{doc_id}")
async def get_document_content(dataset_id: str, doc_id: str):
    """获取文档内容"""
    response = await client.get(f"/api/v1/datasets/{dataset_id}/documents/{doc_id}")
    return Response(content=response.content, media_type="text/plain")

@app.delete("/api/v1/datasets/{dataset_id}/documents/{doc_id}")
async def delete_document(dataset_id: str, doc_id: str):
    """删除单个文档"""
    response = await client.delete(f"/api/v1/datasets/{dataset_id}/documents/{doc_id}")
    return response.json()

@app.delete("/api/v1/datasets/{dataset_id}/documents")
async def batch_delete_documents(dataset_id: str, request: Request):
    """批量删除文档"""
    data = await request.json()
    response = await client.delete(f"/api/v1/datasets/{dataset_id}/documents", json=data)
    return response.json()

@app.get("/api/v1/datasets/{dataset_id}/documents/{doc_id}/download")
async def download_document(dataset_id: str, doc_id: str):
    """下载文档"""
    response = await client.get(f"/api/v1/datasets/{dataset_id}/documents/{doc_id}/download")
    
    # 获取文件名
    content_disposition = response.headers.get('content-disposition', '')
    filename = "document"
    if 'filename=' in content_disposition:
        filename = content_disposition.split('filename=')[1].strip('"')
    
    return Response(
        content=response.content,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

# =============== 对话管理 API ===============

@app.post("/api/v1/chats")
async def create_chat(request: Request):
    """创建对话"""
    data = await request.json()
    response = await client.post("/api/v1/chats", json=data)
    return response.json()

@app.post("/api/v1/chats/{chat_id}/completions")
async def send_message(chat_id: str, request: Request):
    """发送消息（SSE流式响应）"""
    data = await request.json()
    
    # 创建流式请求
    async with client.stream(
        'POST',
        f"/api/v1/chats/{chat_id}/completions",
        json=data
    ) as response:
        async def generate():
            async for chunk in response.aiter_bytes():
                if chunk:
                    yield chunk
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

@app.get("/api/v1/chats/{chat_id}/messages")
async def get_chat_history(
    chat_id: str,
    page: int = 1,
    page_size: int = 20
):
    """获取对话历史"""
    params = {
        "page": page,
        "page_size": page_size
    }
    
    response = await client.get(f"/api/v1/chats/{chat_id}/messages", params=params)
    return response.json()

@app.delete("/api/v1/chats/{chat_id}")
async def delete_chat(chat_id: str):
    """删除对话"""
    response = await client.delete(f"/api/v1/chats/{chat_id}")
    return response.json()

# =============== 检索接口 ===============

@app.post("/api/v1/retrieval")
async def retrieval(request: Request):
    """知识库检索"""
    data = await request.json()
    response = await client.post("/api/v1/retrieval", json=data)
    return response.json()

# =============== 健康检查 ===============

@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": "RAGFlow API Proxy Service",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "endpoints": {
            "datasets": "/api/v1/datasets",
            "chats": "/api/v1/chats",
            "retrieval": "/api/v1/retrieval"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查RAGFlow服务是否可用
        response = await client.get("/api/v1/datasets", params={"page": 1, "page_size": 1})
        ragflow_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        ragflow_status = "unreachable"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ragflow_status": ragflow_status,
        "ragflow_url": RAGFLOW_API_URL
    }

# 关闭时清理
@app.on_event("shutdown")
async def shutdown():
    await client.aclose()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8050)