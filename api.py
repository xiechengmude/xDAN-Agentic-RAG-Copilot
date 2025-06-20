from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.responses import StreamingResponse
from typing import Dict, List, Any, Optional
import json
import asyncio
from src.core.models import (
    ChatCompletionRequest, ChatCompletionResponse, DatasetCreateRequest,
    DatasetResponse, DocumentListRequest, RetrievalRequest, ErrorResponse
)
from src.clients.ragflow_client import RAGFlowClient
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 默认知识库配置
DEFAULT_DATASET_ID = "7e8d9e924cde11f0afc90242ac140006"  # 360test 知识库 ID

# 创建 FastAPI 应用
app = FastAPI(
    title="RAGFlow API 客户端",
    description="RAGFlow API 的封装和扩展",
    version="0.1.0"
)

# 创建 RAGFlow 客户端实例
ragflow_client = RAGFlowClient()

# 依赖项：获取 RAGFlow 客户端
def get_ragflow_client():
    return ragflow_client

# =============== OpenAI 兼容 API ===============

@app.post("/v1/chats/{chat_id}/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    chat_id: str,
    request: ChatCompletionRequest,
    client: RAGFlowClient = Depends(get_ragflow_client)
):
    """
    创建聊天完成
    """
    try:
        if request.stream:
            # 处理流式响应
            response = client.create_chat_completion(
                chat_id=chat_id,
                model=request.model,
                messages=[msg.dict() for msg in request.messages],
                stream=True
            )
            
            async def stream_generator():
                for line in response.iter_lines():
                    if line:
                        yield f"{line.decode('utf-8')}\n\n"
            
            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream"
            )
        else:
            # 处理非流式响应
            response = client.create_chat_completion(
                chat_id=chat_id,
                model=request.model,
                messages=[msg.dict() for msg in request.messages],
                stream=False
            )
            return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/agents/{agent_id}/chat/completions", response_model=ChatCompletionResponse)
async def create_agent_completion(
    agent_id: str,
    request: ChatCompletionRequest,
    client: RAGFlowClient = Depends(get_ragflow_client)
):
    """
    创建 Agent 完成
    """
    try:
        if request.stream:
            # 处理流式响应
            response = client.create_agent_completion(
                agent_id=agent_id,
                model=request.model,
                messages=[msg.dict() for msg in request.messages],
                stream=True
            )
            
            async def stream_generator():
                for line in response.iter_lines():
                    if line:
                        yield f"{line.decode('utf-8')}\n\n"
            
            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream"
            )
        else:
            # 处理非流式响应
            response = client.create_agent_completion(
                agent_id=agent_id,
                model=request.model,
                messages=[msg.dict() for msg in request.messages],
                stream=False
            )
            return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============== 数据集管理 API ===============

@app.post("/v1/datasets", response_model=DatasetResponse)
async def create_dataset(
    request: DatasetCreateRequest,
    client: RAGFlowClient = Depends(get_ragflow_client)
):
    """
    创建数据集
    """
    try:
        response = client.create_dataset(
            name=request.name,
            avatar=request.avatar,
            description=request.description,
            embedding_model=request.embedding_model,
            permission=request.permission,
            chunk_method=request.chunk_method,
            pagerank=request.pagerank,
            parser_config=request.parser_config
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/v1/datasets", response_model=DatasetResponse)
async def delete_datasets(
    ids: Optional[List[str]] = None,
    client: RAGFlowClient = Depends(get_ragflow_client)
):
    """
    删除数据集
    """
    try:
        response = client.delete_datasets(ids=ids)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/v1/datasets/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: str,
    request: dict,
    client: RAGFlowClient = Depends(get_ragflow_client)
):
    """
    更新数据集
    """
    try:
        response = client.update_dataset(dataset_id=dataset_id, **request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/datasets", response_model=Dict)
async def list_datasets(
    page: int = 1,
    page_size: int = 30,
    orderby: str = "create_time",
    desc: bool = True,
    name: Optional[str] = None,
    id: Optional[str] = None,
    client: RAGFlowClient = Depends(get_ragflow_client)
):
    """
    列出数据集
    """
    try:
        response = client.list_datasets(
            page=page,
            page_size=page_size,
            orderby=orderby,
            desc=desc,
            name=name,
            id=id
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============== 文档管理 API ===============

@app.get("/v1/datasets/{dataset_id}/documents", response_model=Dict)
async def list_documents(
    dataset_id: str,
    request: DocumentListRequest = Depends(),
    client: RAGFlowClient = Depends(get_ragflow_client)
):
    """
    列出数据集中的文档
    """
    try:
        response = client.list_documents(
            dataset_id=dataset_id,
            page=request.page,
            page_size=request.page_size,
            orderby=request.orderby,
            desc=request.desc,
            keywords=request.keywords,
            id=request.id,
            name=request.name
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/v1/datasets/{dataset_id}/documents", response_model=Dict)
async def delete_documents(
    dataset_id: str,
    ids: Optional[List[str]] = None,
    client: RAGFlowClient = Depends(get_ragflow_client)
):
    """
    删除数据集中的文档
    """
    try:
        response = client.delete_documents(
            dataset_id=dataset_id,
            document_ids=ids
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/datasets/{dataset_id}/chunks", response_model=Dict)
async def parse_documents(
    dataset_id: str,
    document_ids: List[str],
    client: RAGFlowClient = Depends(get_ragflow_client)
):
    """
    解析文档
    """
    try:
        response = client.parse_documents(
            dataset_id=dataset_id,
            document_ids=document_ids
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/datasets/{dataset_id}/documents/{document_id}/download")
async def download_document(
    dataset_id: str,
    document_id: str,
    client: RAGFlowClient = Depends(get_ragflow_client)
):
    """
    下载文档原始文件
    """
    try:
        file_content = client.download_document(
            dataset_id=dataset_id,
            document_id=document_id
        )
        
        # 获取文档信息以获取文件名
        doc_info = client.get_document_status(dataset_id, document_id)
        filename = "document"
        if doc_info and 'name' in doc_info:
            filename = doc_info['name']
        
        return Response(
            content=file_content,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/datasets/{dataset_id}/documents/{document_id}/status", response_model=Dict)
async def get_document_status(
    dataset_id: str,
    document_id: str,
    client: RAGFlowClient = Depends(get_ragflow_client)
):
    """
    获取文档状态信息
    """
    try:
        status = client.get_document_status(
            dataset_id=dataset_id,
            document_id=document_id
        )
        
        if status is None:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 提取关键状态信息
        return {
            "code": 0,
            "data": {
                "id": status.get("id"),
                "name": status.get("name"),
                "status": status.get("status", ""),
                "progress": status.get("progress", 0.0),
                "progress_msg": status.get("progress_msg", ""),
                "process_begin_at": status.get("process_begin_at"),
                "process_duration": status.get("process_duation", 0.0),
                "chunk_count": status.get("chunk_count", 0)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============== 检索 API ===============

@app.post("/v1/retrieval", response_model=Dict)
async def retrieve_chunks(
    request: RetrievalRequest,
    client: RAGFlowClient = Depends(get_ragflow_client)
):
    """
    检索文本块
    """
    try:
        # 确保至少有一个ID列表不为空
        dataset_ids = request.dataset_ids
        document_ids = request.document_ids
        
        if not dataset_ids and not document_ids:
            dataset_ids = [DEFAULT_DATASET_ID]
        
        # 构建参数字典，只包含非None值
        params = {
            "question": request.question,
            "page": request.page or 1,
            "page_size": request.page_size or 30,
            "similarity_threshold": request.similarity_threshold or 0.2,
            "vector_similarity_weight": request.vector_similarity_weight or 0.3,
            "top_k": request.top_k or 1024,
            "keyword": request.keyword or False,
            "highlight": request.highlight or False
        }
        
        # 只添加非空的ID列表
        if dataset_ids:
            params["dataset_ids"] = dataset_ids
        if document_ids:
            params["document_ids"] = document_ids
        if request.rerank_id:
            params["rerank_id"] = request.rerank_id
            
        response = client.retrieve_chunks(**params)
        return response
        
    except ValueError as e:
        # 返回符合官方格式的错误响应
        raise HTTPException(
            status_code=400, 
            detail={"code": 102, "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={"code": 500, "message": f"Internal server error: {str(e)}"}
        )

# 异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return Response(
        content=json.dumps({
            "code": exc.status_code,
            "message": exc.detail
        }),
        status_code=exc.status_code,
        media_type="application/json"
    )
