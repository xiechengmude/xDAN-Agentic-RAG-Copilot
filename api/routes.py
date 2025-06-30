"""
API路由定义 - 处理搜索请求
遵循DRY原则，复用现有DeepSearch框架
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
import uuid
import time
import json
import asyncio
from typing import AsyncGenerator
import logging

from api.models import (
    SearchRequest, SearchResponse, SearchRound, 
    SearchSource, HealthResponse, ErrorResponse, StreamChunk
)

logger = logging.getLogger(__name__)

# 创建路由器
search_router = APIRouter()
health_router = APIRouter()

# 服务启动时间
SERVICE_START_TIME = time.time()

@health_router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查端点"""
    from main import get_deepsearch_framework
    
    # 检查各服务状态
    services_status = {
        "deepsearch": False,
        "litellm": False,
        "brightdata": False,
        "firecrawl": False
    }
    
    try:
        framework = get_deepsearch_framework()
        if framework:
            services_status["deepsearch"] = True
            services_status["litellm"] = framework.litellm_client is not None
            # 可以添加更多服务检查
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
    
    return HealthResponse(
        status="healthy" if all(services_status.values()) else "degraded",
        version="1.0.0",
        uptime=time.time() - SERVICE_START_TIME,
        services=services_status
    )

@search_router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest, background_tasks: BackgroundTasks):
    """同步搜索端点"""
    from main import get_deepsearch_framework
    
    request_id = f"req_{uuid.uuid4().hex[:8]}"
    logger.info(f"[{request_id}] 收到搜索请求: {request.question[:50]}...")
    
    framework = get_deepsearch_framework()
    if not framework:
        raise HTTPException(status_code=503, detail="DeepSearch服务不可用")
    
    start_time = time.time()
    
    try:
        # 根据搜索模式设置参数
        max_rounds = {
            "flash": min(2, request.max_rounds),
            "standard": min(5, request.max_rounds),
            "deep": request.max_rounds
        }.get(request.mode, request.max_rounds)
        
        # 执行搜索
        workflow_result = None
        async for result in framework.execute_deepsearch_workflow(
            question=request.question,
            max_rounds=max_rounds,
            num_results=10,
            stream=False
        ):
            workflow_result = result
            break  # 非流式模式只获取最终结果
        
        if not workflow_result:
            raise HTTPException(status_code=500, detail="搜索执行失败")
        
        # 构建响应
        rounds = []
        for round_data in workflow_result.get("rounds", []):
            rounds.append(SearchRound(
                round=round_data["round"],
                query=round_data["search_query"],
                results_count=round_data["search_results_count"],
                selected_urls=round_data["selected_urls"],
                thinking=round_data.get("decision", {}).get("thinking"),
                duration=round_data.get("duration", 0)
            ))
        
        # 提取信息源
        sources = []
        for content in workflow_result.get("extracted_content", []):
            if content.get("extraction_success"):
                sources.append(SearchSource(
                    url=content["url"],
                    title=content.get("title", ""),
                    snippet=content.get("extracted_content", "")[:200],
                    relevance_score=0.8  # 可以基于内容计算相关性
                ))
        
        response = SearchResponse(
            request_id=request_id,
            question=request.question,
            answer=workflow_result.get("final_answer", ""),
            rounds=rounds,
            sources=sources,
            total_duration=time.time() - start_time
        )
        
        logger.info(f"[{request_id}] 搜索完成，耗时: {response.total_duration:.1f}秒")
        return response
        
    except Exception as e:
        logger.error(f"[{request_id}] 搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@search_router.post("/search/stream")
async def search_stream(request: SearchRequest):
    """流式搜索端点"""
    from main import get_deepsearch_framework
    
    request_id = f"req_{uuid.uuid4().hex[:8]}"
    logger.info(f"[{request_id}] 收到流式搜索请求: {request.question[:50]}...")
    
    framework = get_deepsearch_framework()
    if not framework:
        raise HTTPException(status_code=503, detail="DeepSearch服务不可用")
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        """生成流式响应"""
        try:
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'data': request_id})}\n\n"
            
            # 执行搜索
            async for chunk in framework.execute_deepsearch_workflow(
                question=request.question,
                max_rounds=request.max_rounds,
                num_results=10,
                stream=True
            ):
                if isinstance(chunk, str):
                    # 流式内容
                    event = StreamChunk(type="content", data=chunk)
                    yield f"data: {event.model_dump_json()}\n\n"
                elif isinstance(chunk, dict):
                    # 最终结果
                    event = StreamChunk(
                        type="complete", 
                        data=json.dumps(chunk),
                        metadata={"request_id": request_id}
                    )
                    yield f"data: {event.model_dump_json()}\n\n"
                
                # 保持连接活跃
                await asyncio.sleep(0.01)
            
            # 发送结束事件
            yield f"data: {json.dumps({'type': 'end', 'data': 'success'})}\n\n"
            
        except Exception as e:
            logger.error(f"[{request_id}] 流式搜索失败: {e}")
            error_event = StreamChunk(type="error", data=str(e))
            yield f"data: {error_event.model_dump_json()}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Request-ID": request_id
        }
    )

@search_router.get("/search/{request_id}/status")
async def get_search_status(request_id: str):
    """获取搜索状态（用于异步模式）"""
    # 这里可以实现基于Redis或数据库的状态查询
    return {
        "request_id": request_id,
        "status": "completed",
        "message": "搜索已完成"
    }