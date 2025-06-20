#!/usr/bin/env python3
"""
简化的演示服务器 - 专注于搜索可视化功能
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json
import asyncio
import time
from datetime import datetime
from typing import AsyncGenerator
import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.enhanced_s3_rag_service_v2 import EnhancedS3RAGServiceV2, StreamingEnhancedS3Service
from src.clients.ragflow_sdk_wrapper import RAGFlowSDKWrapper
from src.clients.llm_client import LLMClient
from src.api.search_process_api import SearchRequest, EventType, SearchEvent
from config.settings import (
    RAGFLOW_API_URL, RAGFLOW_API_KEY, DEFAULT_DATASET_ID,
    S3_SEARCH_MODEL_NAME, S3_SEARCH_MODEL_URL, S3_SEARCH_API_KEY,
    S3_GENERATOR_MODEL_NAME, S3_GENERATOR_MODEL_URL, S3_GENERATOR_API_KEY
)

app = FastAPI(title="搜索过程可视化演示", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局服务实例
streaming_service = None

def get_streaming_service():
    """获取流式服务实例"""
    global streaming_service
    if not streaming_service:
        ragflow_client = RAGFlowSDKWrapper(
            api_url=RAGFLOW_API_URL,
            api_key=RAGFLOW_API_KEY
        )
        
        search_llm_client = LLMClient(
            base_url=S3_SEARCH_MODEL_URL,
            api_key=S3_SEARCH_API_KEY,
            model_name=S3_SEARCH_MODEL_NAME
        )
        
        generator_llm_client = LLMClient(
            base_url=S3_GENERATOR_MODEL_URL,
            api_key=S3_GENERATOR_API_KEY,
            model_name=S3_GENERATOR_MODEL_NAME
        )
        
        streaming_service = StreamingEnhancedS3Service(
            ragflow_client=ragflow_client,
            search_llm_client=search_llm_client,
            generator_llm_client=generator_llm_client
        )
    
    return streaming_service

@app.get("/")
async def root():
    """根路径 - 返回演示页面"""
    demo_file = os.path.join("examples", "frontend", "search_visualization.html")
    if os.path.exists(demo_file):
        return FileResponse(demo_file)
    else:
        return {"message": "演示文件未找到", "path": demo_file}

@app.get("/demo")
async def demo():
    """演示页面"""
    demo_file = os.path.join("examples", "frontend", "search_visualization.html")
    return FileResponse(demo_file)

@app.post("/api/search/stream")
async def stream_search_process(request: SearchRequest):
    """
    流式返回搜索过程
    使用Server-Sent Events (SSE)格式
    """
    service = get_streaming_service()
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """生成SSE事件"""
        event_queue = asyncio.Queue()
        
        async def event_callback(event: SearchEvent):
            await event_queue.put(event)
        
        # 设置事件回调
        service.set_event_callback(event_callback)
        
        # 启动搜索任务
        search_task = asyncio.create_task(
            service.s3_search_process_streaming(
                question=request.question,
                dataset_ids=request.dataset_ids or [DEFAULT_DATASET_ID],
                max_rounds=request.max_rounds,
                top_k=request.top_k,
                similarity_threshold=request.similarity_threshold
            )
        )
        
        # 持续发送事件直到搜索完成
        while not search_task.done() or not event_queue.empty():
            try:
                # 等待事件，超时检查任务是否完成
                event = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                yield f"data: {event.json()}\n\n"
            except asyncio.TimeoutError:
                continue
        
        # 获取搜索结果
        search_result = await search_task
        
        # 生成答案
        if search_result.get('selected_documents'):
            yield f"data: {json.dumps({'event_type': EventType.ANSWER_GENERATION_START, 'timestamp': datetime.now().isoformat(), 'data': {'message': '正在生成答案...'}})}\n\n"
            
            answer = service.synthesize_answer(
                question=request.question,
                selected_docs=search_result['selected_documents']
            )
            
            yield f"data: {json.dumps({'event_type': EventType.ANSWER_GENERATED, 'timestamp': datetime.now().isoformat(), 'data': {'answer': answer}})}\n\n"
        
        # 发送结束信号
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no",  # 禁用Nginx缓冲
        }
    )

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "search-visualization-demo"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动搜索过程可视化演示服务...")
    print("📍 访问地址: http://localhost:8000")
    print("📡 API端点: POST http://localhost:8000/api/search/stream")
    print("\n按 Ctrl+C 停止服务\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)