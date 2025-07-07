#!/usr/bin/env python3
"""
FlashSearch FastAPI REST Server
提供FlashSearch v2.5.0的HTTP API接口
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, AsyncGenerator
import asyncio
import json
import sys
import os
from datetime import datetime
import uvicorn
import logging

# 配置日志记录器
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.flash_s3_enhanced import flash_s3_enhanced
from src.core.langfuse_client import LangfuseObservabilityClient
from src.core.search_modes import get_available_modes, validate_mode

app = FastAPI(
    title="FlashSearch API Server",
    description="FlashSearch v2.5.0 - 增强搜索引擎 API",
    version="2.5.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response模型
class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str = Field(..., description="搜索查询", min_length=1, max_length=1000)
    mode: Optional[str] = Field("fast", description="搜索模式 (fast/normal/deep)")
    domain: Optional[str] = Field(None, description="搜索领域 (news, finance, tech, academic, policy)")
    enable_langfuse: Optional[bool] = Field(True, description="是否启用Langfuse追踪")
    max_results: Optional[int] = Field(12, description="最大搜索结果数", ge=1, le=50)
    timeout: Optional[int] = Field(1800, description="超时时间(秒)", ge=30, le=3600)

class SearchResponse(BaseModel):
    """搜索响应模型"""
    success: bool
    answer: str
    sources: List[Dict[str, Any]]
    stats: Dict[str, Any]
    trace_id: Optional[str] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    timestamp: str
    features: List[str]

# 全局状态
search_stats = {
    "total_searches": 0,
    "successful_searches": 0,
    "failed_searches": 0,
    "avg_response_time": 0.0
}

@app.get("/", response_model=Dict[str, str])
async def root():
    """根路径"""
    return {
        "message": "FlashSearch API Server v2.5.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="healthy",
        version="2.5.0",
        timestamp=datetime.now().isoformat(),
        features=[
            "Google关键词优化",
            "时间感知算子", 
            "新闻领域增强",
            "Langfuse集成",
            "多领域搜索"
        ]
    )

@app.get("/stats", response_model=Dict[str, Any])
async def get_stats():
    """获取统计信息"""
    return {
        **search_stats,
        "uptime": "运行中",
        "last_updated": datetime.now().isoformat()
    }

@app.get("/modes", response_model=Dict[str, Any])
async def get_search_modes():
    """获取可用的搜索模式"""
    return {
        "default": "fast",
        "modes": get_available_modes(),
        "description": "搜索模式控制速度与质量的权衡"
    }

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    执行FlashSearch搜索
    
    Args:
        request: 搜索请求参数
        
    Returns:
        SearchResponse: 搜索结果响应
    """
    start_time = asyncio.get_event_loop().time()
    search_stats["total_searches"] += 1
    
    logger.info(f"🔍 开始搜索: {request.query[:100]}...")
    logger.debug(f"搜索参数 - 模式: {request.mode}, 领域: {request.domain}, Langfuse: {request.enable_langfuse}")
    
    try:
        # 执行搜索
        logger.debug(f"调用flash_s3_enhanced搜索引擎 (模式: {request.mode})")
        # 传递question和mode参数
        result = await flash_s3_enhanced(question=request.query, mode=request.mode)
        
        # 计算响应时间
        response_time = asyncio.get_event_loop().time() - start_time
        
        # 更新统计
        search_stats["successful_searches"] += 1
        search_stats["avg_response_time"] = (
            (search_stats["avg_response_time"] * (search_stats["successful_searches"] - 1) + response_time) 
            / search_stats["successful_searches"]
        )
        
        logger.info(f"✅ 搜索完成: {len(result.get('answer', ''))}字符, {len(result.get('sources', []))}来源, {response_time:.2f}s")
        logger.debug(f"搜索统计 - 成功: {search_stats['successful_searches']}, 平均时间: {search_stats['avg_response_time']:.2f}s")
        
        # 构建响应
        return SearchResponse(
            success=True,
            answer=result.get("answer", ""),
            sources=result.get("sources", []),
            stats={
                **result.get("stats", {}),
                "response_time": round(response_time, 2),
                "api_version": "2.5.0"
            },
            trace_id=result.get("trace_id")
        )
        
    except Exception as e:
        search_stats["failed_searches"] += 1
        
        # 计算失败响应时间
        response_time = asyncio.get_event_loop().time() - start_time
        
        logger.error(f"❌ 搜索失败: {str(e)}")
        logger.debug(f"失败统计 - 总失败: {search_stats['failed_searches']}, 响应时间: {response_time:.2f}s")
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "query": request.query,
                "response_time": round(response_time, 2),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.post("/search/async")
async def search_async(request: SearchRequest, background_tasks: BackgroundTasks):
    """
    异步搜索 (后台任务)
    
    Returns:
        任务ID和状态
    """
    task_id = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(request.query) % 10000}"
    
    # 添加后台任务
    background_tasks.add_task(execute_background_search, task_id, request)
    
    return {
        "task_id": task_id,
        "status": "submitted",
        "message": "搜索任务已提交，正在后台处理",
        "query": request.query,
        "timestamp": datetime.now().isoformat()
    }

async def execute_background_search(task_id: str, request: SearchRequest):
    """执行后台搜索任务"""
    try:
        result = await flash_s3_enhanced(question=request.query, mode=request.mode)
        
        # 这里可以将结果保存到数据库或缓存
        print(f"后台任务 {task_id} 完成: {len(result.get('answer', ''))} 字符")
        
    except Exception as e:
        print(f"后台任务 {task_id} 失败: {e}")

@app.post("/search/stream")
async def search_stream(request: SearchRequest):
    """
    SSE流式搜索接口
    
    Args:
        request: 搜索请求参数
        
    Returns:
        StreamingResponse: Server-Sent Events 流式响应
    """
    async def generate_search_events() -> AsyncGenerator[str, None]:
        """生成搜索事件流"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'message': '开始搜索...', 'query': request.query, 'mode': request.mode, 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
            # 发送搜索状态事件
            yield f"data: {json.dumps({'type': 'searching', 'message': '正在执行S3架构搜索...', 'stage': 'search', 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
            # 模拟搜索进度
            await asyncio.sleep(1)
            yield f"data: {json.dumps({'type': 'progress', 'message': '搜索阶段完成，开始选择相关内容...', 'stage': 'select', 'progress': 33, 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
            await asyncio.sleep(1)
            yield f"data: {json.dumps({'type': 'progress', 'message': '选择阶段完成，开始生成答案...', 'stage': 'synthesize', 'progress': 66, 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
            # 执行实际搜索
            logger.info(f"🔍 [SSE] 开始流式搜索: {request.query[:100]}...")
            result = await flash_s3_enhanced(question=request.query, mode=request.mode)
            
            # 计算响应时间
            response_time = asyncio.get_event_loop().time() - start_time
            
            # 发送搜索结果
            yield f"data: {json.dumps({'type': 'result', 'message': '搜索完成', 'progress': 100, 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
            # 发送答案（分块发送以模拟流式输出）
            answer = result.get("answer", "")
            chunk_size = 100  # 每次发送100字符
            
            for i in range(0, len(answer), chunk_size):
                chunk = answer[i:i+chunk_size]
                yield f"data: {json.dumps({'type': 'answer_chunk', 'content': chunk, 'is_final': i + chunk_size >= len(answer), 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)  # 模拟流式输出延迟
            
            # 发送来源信息
            sources = result.get("sources", [])
            for idx, source in enumerate(sources):
                yield f"data: {json.dumps({'type': 'source', 'index': idx + 1, 'source': source, 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.2)
            
            # 发送统计信息
            stats = {
                **result.get("stats", {}),
                "response_time": round(response_time, 2),
                "api_version": "2.5.0"
            }
            yield f"data: {json.dumps({'type': 'stats', 'stats': stats, 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
            # 发送完成事件
            yield f"data: {json.dumps({'type': 'done', 'message': '搜索完成', 'response_time': round(response_time, 2), 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
            logger.info(f"✅ [SSE] 流式搜索完成: {len(answer)}字符, {len(sources)}来源, {response_time:.2f}s")
            
        except Exception as e:
            # 发送错误事件
            error_time = asyncio.get_event_loop().time() - start_time
            error_data = {
                'type': 'error',
                'error': str(e),
                'query': request.query,
                'response_time': round(error_time, 2),
                'timestamp': datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
            logger.error(f"❌ [SSE] 流式搜索失败: {str(e)}")
    
    return StreamingResponse(
        generate_search_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# 验证端点
class ValidateRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)

@app.post("/validate")
async def validate_query(request: ValidateRequest):
    """验证查询是否有效"""
    query = request.query
    try:
        # 简单验证逻辑
        if len(query.strip()) < 3:
            return {"valid": False, "message": "查询太短，至少需要3个字符"}
        
        if not any(c.isalnum() for c in query):
            return {"valid": False, "message": "查询必须包含字母或数字"}
            
        return {
            "valid": True, 
            "message": "查询有效",
            "suggested_domain": suggest_domain(query)
        }
        
    except Exception as e:
        return {"valid": False, "message": f"验证失败: {e}"}

def suggest_domain(query: str) -> Optional[str]:
    """根据查询建议搜索领域"""
    query_lower = query.lower()
    
    # 新闻关键词
    if any(word in query_lower for word in ["新闻", "最新", "报道", "事件", "突发"]):
        return "news"
    
    # 财经关键词  
    if any(word in query_lower for word in ["财报", "股价", "投资", "金融", "经济"]):
        return "finance"
    
    # 技术关键词
    if any(word in query_lower for word in ["技术", "编程", "算法", "开发", "api"]):
        return "tech"
    
    # 学术关键词
    if any(word in query_lower for word in ["研究", "论文", "学术", "分析", "报告"]):
        return "academic"
    
    # 政策关键词
    if any(word in query_lower for word in ["政策", "法规", "政府", "官方", "法律"]):
        return "policy"
    
    return None

if __name__ == "__main__":
    import argparse
    import logging
    
    parser = argparse.ArgumentParser(description="FlashSearch API Server")
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机")
    parser.add_argument("--port", type=int, default=8060, help="服务器端口 (默认: 8060)")
    parser.add_argument("--reload", action="store_true", help="开发模式重载")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"], help="日志级别")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数")
    
    args = parser.parse_args()
    
    # 配置日志级别
    if args.log_level == "debug":
        logging.basicConfig(level=logging.DEBUG)
        print("🐛 Debug模式已启用")
    elif args.log_level == "info":
        logging.basicConfig(level=logging.INFO)
    
    print(f"🚀 启动FlashSearch API Server v2.5.0")
    print(f"📡 服务地址: http://{args.host}:{args.port}")
    print(f"📚 API文档: http://{args.host}:{args.port}/docs")
    print(f"🏥 健康检查: http://{args.host}:{args.port}/health")
    print(f"📊 统计信息: http://{args.host}:{args.port}/stats")
    print(f"🔧 日志级别: {args.log_level.upper()}")
    if args.reload:
        print("🔄 开发模式: 热重载已启用")
    
    uvicorn.run(
        "flash_search_api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
        access_log=True,
        workers=args.workers if not args.reload else 1,
        loop="asyncio"
    )