#!/usr/bin/env python3
"""
DeepSearch API Server - 基于FastAPI的RESTful服务
遵循KISS和DRY原则，提供简洁高效的搜索API
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import logging
from typing import Optional
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import SearchRequest, SearchResponse, HealthResponse
from api.routes import search_router, health_router
from api.middleware import setup_middleware
from src.clients.enhanced_litellm_client import EnhancedLiteLLMClient
from src.core.deepsearch_framework import DeepSearchFramework

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局客户端实例
clients = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理 - 初始化和清理资源"""
    # 启动时初始化
    logger.info("初始化DeepSearch API服务...")
    
    # 创建LiteLLM客户端
    clients['litellm'] = EnhancedLiteLLMClient()
    
    # 创建DeepSearch框架实例（使用轻量版v1.2.1）
    clients['deepsearch'] = DeepSearchFramework(
        litellm_client=clients['litellm'],
        prompt_version="v1.2.1",
        enable_time_aware=True
    )
    
    logger.info("DeepSearch API服务初始化完成")
    
    yield
    
    # 关闭时清理
    logger.info("清理资源...")
    clients.clear()

# 创建FastAPI应用
app = FastAPI(
    title="DeepSearch API",
    description="基于S3架构的智能搜索API服务",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 设置中间件
setup_middleware(app)

# 注册路由
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(search_router, prefix="/api/v1", tags=["search"])

@app.get("/", tags=["root"])
async def root():
    """API根路径"""
    return {
        "service": "DeepSearch API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

# 依赖注入函数
def get_deepsearch_framework():
    """获取DeepSearch框架实例"""
    return clients.get('deepsearch')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )