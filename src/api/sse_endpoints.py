"""
SSE (Server-Sent Events) 端点实现
用于替代 WebSocket 提供实时数据推送
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import asyncio
import json
from datetime import datetime

from ..clients.ragflow_client import RAGFlowClient

router = APIRouter(prefix="/api/v1", tags=["SSE"])

def get_ragflow_client():
    """获取 RAGFlow 客户端实例"""
    from ...api import ragflow_client
    return ragflow_client


@router.get("/datasets/{dataset_id}/documents/{document_id}/status/stream")
async def stream_document_status(
    dataset_id: str,
    document_id: str,
    client: RAGFlowClient = Depends(get_ragflow_client)
):
    """
    使用 SSE 流式推送文档处理状态
    
    返回格式:
    data: {"type": "status", "doc_id": "xxx", "status": "parsing", "progress": 0.5}
    """
    async def generate_status_updates() -> AsyncGenerator[str, None]:
        """生成状态更新事件"""
        previous_status = None
        previous_progress = None
        retry_count = 0
        max_retries = 300  # 最多查询5分钟（300秒）
        
        while retry_count < max_retries:
            try:
                # 获取文档状态
                doc_status = client.get_document_status(dataset_id, document_id)
                
                if doc_status is None:
                    # 文档不存在
                    error_data = {
                        "type": "error",
                        "error": "Document not found"
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    break
                
                current_status = doc_status.get("status", "")
                current_progress = doc_status.get("progress", 0.0)
                
                # 只在状态或进度变化时发送更新
                if (current_status != previous_status or 
                    current_progress != previous_progress):
                    
                    status_data = {
                        "type": "status",
                        "doc_id": document_id,
                        "status": current_status,
                        "progress": current_progress,
                        "progress_msg": doc_status.get("progress_msg", ""),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    yield f"data: {json.dumps(status_data)}\n\n"
                    
                    previous_status = current_status
                    previous_progress = current_progress
                
                # 如果解析完成或失败，结束流
                if current_status in ["PARSE_SUCCESS", "PARSE_FAILED", "2", "3"]:
                    # 发送最终状态
                    final_data = {
                        "type": "complete",
                        "doc_id": document_id,
                        "status": current_status,
                        "success": current_status in ["PARSE_SUCCESS", "2"]
                    }
                    yield f"data: {json.dumps(final_data)}\n\n"
                    break
                
                # 等待1秒后再次检查
                await asyncio.sleep(1)
                retry_count += 1
                
            except Exception as e:
                # 发送错误信息
                error_data = {
                    "type": "error",
                    "error": str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                break
        
        # 超时处理
        if retry_count >= max_retries:
            timeout_data = {
                "type": "timeout",
                "doc_id": document_id,
                "message": "Status check timeout after 5 minutes"
            }
            yield f"data: {json.dumps(timeout_data)}\n\n"
    
    return StreamingResponse(
        generate_status_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
        }
    )


@router.post("/chats/{chat_id}/stream")
async def stream_chat_response(
    chat_id: str,
    request: dict,
    client: RAGFlowClient = Depends(get_ragflow_client)
):
    """
    使用 SSE 流式返回对话响应
    
    请求体:
    {
        "messages": [{"role": "user", "content": "你好"}],
        "dataset_id": "xxx"  # 可选，指定知识库
    }
    
    返回格式:
    data: {"type": "message", "content": "你好", "done": false}
    """
    async def generate_chat_stream() -> AsyncGenerator[str, None]:
        """生成聊天流式响应"""
        try:
            messages = request.get("messages", [])
            dataset_id = request.get("dataset_id")
            
            # 如果指定了知识库，先进行检索
            if dataset_id and messages:
                user_question = messages[-1].get("content", "")
                retrieval_result = client.retrieve_chunks(
                    question=user_question,
                    dataset_ids=[dataset_id],
                    top_k=5
                )
                
                # 将检索结果作为上下文
                if retrieval_result.get("code") == 0:
                    chunks = retrieval_result.get("data", {}).get("chunks", [])
                    if chunks:
                        context = "\n\n".join([
                            f"[来源: {chunk.get('document_name', '未知')}]\n{chunk.get('content', '')}"
                            for chunk in chunks[:3]  # 只使用前3个最相关的片段
                        ])
                        
                        # 构建带上下文的提示
                        messages.append({
                            "role": "system",
                            "content": f"请基于以下知识库内容回答用户问题：\n\n{context}"
                        })
            
            # 调用聊天接口（这里需要根据实际的 RAGFlow API 调整）
            # 假设 RAGFlow 支持流式响应
            response = client.create_chat_completion(
                chat_id=chat_id,
                messages=messages,
                stream=True
            )
            
            # 处理流式响应
            for line in response.iter_lines():
                if line:
                    # 解析 SSE 格式的数据
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]  # 移除 "data: " 前缀
                        
                        if data_str == "[DONE]":
                            # 发送结束信号
                            done_data = {
                                "type": "message",
                                "content": "",
                                "done": True
                            }
                            yield f"data: {json.dumps(done_data)}\n\n"
                            break
                        
                        try:
                            data = json.loads(data_str)
                            # 提取内容
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            
                            if content:
                                message_data = {
                                    "type": "message",
                                    "content": content,
                                    "done": False
                                }
                                yield f"data: {json.dumps(message_data)}\n\n"
                        
                        except json.JSONDecodeError:
                            continue
            
        except Exception as e:
            # 发送错误信息
            error_data = {
                "type": "error",
                "error": str(e),
                "done": True
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_chat_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# 批量文件状态监控（可选实现）
@router.get("/datasets/{dataset_id}/documents/status/stream")
async def stream_multiple_documents_status(
    dataset_id: str,
    doc_ids: str,  # 逗号分隔的文档ID列表
    client: RAGFlowClient = Depends(get_ragflow_client)
):
    """
    批量监控多个文档的处理状态
    
    参数:
    - doc_ids: 逗号分隔的文档ID列表，如 "id1,id2,id3"
    """
    document_ids = doc_ids.split(",")
    
    async def generate_batch_status() -> AsyncGenerator[str, None]:
        """生成批量状态更新"""
        status_tracker = {doc_id: {"status": None, "progress": 0} for doc_id in document_ids}
        all_completed = False
        retry_count = 0
        max_retries = 300
        
        while not all_completed and retry_count < max_retries:
            try:
                # 获取所有文档的状态
                docs_response = client.list_documents(
                    dataset_id=dataset_id,
                    page_size=100  # 确保能获取所有文档
                )
                
                if docs_response.get("code") == 0:
                    all_docs = docs_response.get("data", [])
                    
                    # 更新状态跟踪器
                    for doc in all_docs:
                        doc_id = doc.get("id")
                        if doc_id in status_tracker:
                            old_status = status_tracker[doc_id]["status"]
                            old_progress = status_tracker[doc_id]["progress"]
                            
                            new_status = doc.get("status", "")
                            new_progress = doc.get("progress", 0.0)
                            
                            # 如果状态或进度有变化，发送更新
                            if old_status != new_status or old_progress != new_progress:
                                status_tracker[doc_id]["status"] = new_status
                                status_tracker[doc_id]["progress"] = new_progress
                                
                                update_data = {
                                    "type": "batch_status",
                                    "doc_id": doc_id,
                                    "status": new_status,
                                    "progress": new_progress,
                                    "progress_msg": doc.get("progress_msg", "")
                                }
                                yield f"data: {json.dumps(update_data)}\n\n"
                    
                    # 检查是否所有文档都完成
                    all_completed = all(
                        status["status"] in ["PARSE_SUCCESS", "PARSE_FAILED", "2", "3"]
                        for status in status_tracker.values()
                        if status["status"] is not None
                    )
                
                if not all_completed:
                    await asyncio.sleep(1)
                    retry_count += 1
                
            except Exception as e:
                error_data = {
                    "type": "error",
                    "error": str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                break
        
        # 发送完成信号
        complete_data = {
            "type": "batch_complete",
            "summary": {
                doc_id: status["status"] 
                for doc_id, status in status_tracker.items()
            }
        }
        yield f"data: {json.dumps(complete_data)}\n\n"
    
    return StreamingResponse(
        generate_batch_status(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )