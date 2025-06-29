#!/usr/bin/env python3
"""
DeepSearch API Server
专门用于DeepSearch框架的API服务器，包含详细的日志记录和调试功能
"""

import os
import sys
import json
import logging
import asyncio
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, AsyncGenerator, Union
from contextlib import asynccontextmanager

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import our modules
from src.core.config_loader import get_config
from src.core.deepsearch_framework import DeepSearchFramework

# ==================== 日志配置 ====================

# 创建logs目录
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# 配置详细的日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / f"deepsearch_api_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# 设置各个模块的日志级别
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 为关键组件设置详细日志
logging.getLogger("src.core.deepsearch_framework").setLevel(logging.DEBUG)
logging.getLogger("src.clients.brightdata_client").setLevel(logging.DEBUG)
logging.getLogger("src.clients.firecrawl_client").setLevel(logging.DEBUG)
logging.getLogger("src.clients.enhanced_litellm_client").setLevel(logging.DEBUG)

logger.info("🚀 DeepSearch API服务器启动中...")

# ==================== 配置加载 ====================

config_loader = get_config()
config = config_loader.config  # 获取实际的配置字典
logger.info(f"✅ 配置加载完成: {config}")

# ==================== 请求模型 ====================

class DeepSearchRequest(BaseModel):
    """DeepSearch请求模型"""
    question: str = Field(..., description="要搜索的问题", min_length=1)
    max_search_rounds: Optional[int] = Field(default=3, ge=1, le=10, description="最大搜索轮数")
    max_results_per_round: Optional[int] = Field(default=10, ge=1, le=20, description="每轮最大结果数")
    max_crawl_urls: Optional[int] = Field(default=3, ge=1, le=10, description="最大爬取URL数")
    stream: bool = Field(default=False, description="是否流式返回")

class BatchSearchRequest(BaseModel):
    """批量搜索请求模型"""
    questions: List[str] = Field(..., description="问题列表", min_items=1, max_items=50)
    max_search_rounds: Optional[int] = Field(default=3, ge=1, le=10)
    max_results_per_round: Optional[int] = Field(default=10, ge=1, le=20)
    max_crawl_urls: Optional[int] = Field(default=3, ge=1, le=10)

class ApiResponse(BaseModel):
    """统一的API响应格式"""
    code: int = Field(0, description="状态码，0表示成功")
    message: str = Field("Success", description="响应消息")
    data: Any = Field(None, description="响应数据")
    meta: Optional[Dict[str, Any]] = Field(None, description="元数据")

# ==================== 全局变量 ====================

deepsearch_framework = None

# ==================== 应用生命周期 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global deepsearch_framework
    
    logger.info("🔧 初始化DeepSearch框架...")
    try:
        # 从配置中提取Langfuse参数
        langfuse_config = config.get('observability', {}).get('langfuse', {})
        langfuse_enabled = langfuse_config.get('enabled', False)
        
        if langfuse_enabled:
            from src.clients.enhanced_litellm_client import EnhancedLiteLLMClient
            litellm_client = EnhancedLiteLLMClient(
                langfuse_public_key=langfuse_config.get('public_key'),
                langfuse_secret_key=langfuse_config.get('secret_key'),
                langfuse_host=langfuse_config.get('host')
            )
            logger.info("✅ Langfuse集成已启用")
        else:
            # 创建一个简单的LiteLLM客户端包装器
            from src.clients.litellm_client import LiteLLMClient
            litellm_client = LiteLLMClient()
            logger.info("ℹ️ 使用标准LiteLLM客户端（无Langfuse）")
        
        deepsearch_framework = DeepSearchFramework(litellm_client, config)
        logger.info("✅ DeepSearch框架初始化成功")
    except Exception as e:
        logger.error(f"❌ DeepSearch框架初始化失败: {e}")
        raise
    
    yield
    
    logger.info("🛑 DeepSearch API服务器关闭")

# ==================== 应用创建 ====================

app = FastAPI(
    title="DeepSearch API Server",
    description="专门用于DeepSearch框架的API服务器",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 中间件 ====================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件"""
    start_time = time.time()
    request_id = str(uuid.uuid4())[:8]
    
    logger.info(f"🔵 [REQ-{request_id}] {request.method} {request.url}")
    logger.debug(f"🔵 [REQ-{request_id}] Headers: {dict(request.headers)}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"🟢 [REQ-{request_id}] {response.status_code} - {process_time:.3f}s")
    
    return response

# ==================== 辅助函数 ====================

def success_response(data: Any = None, message: str = "Success", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    """创建成功响应"""
    return {
        "code": 0,
        "message": message,
        "data": data,
        "meta": meta
    }

def error_response(code: int, message: str, data: Any = None) -> Dict[str, Any]:
    """创建错误响应"""
    return {
        "code": code,
        "message": message,
        "data": data
    }

def get_deepsearch_framework():
    """获取DeepSearch框架实例"""
    if deepsearch_framework is None:
        raise HTTPException(status_code=500, detail="DeepSearch框架未初始化")
    return deepsearch_framework

# ==================== API路由 ====================

@app.get("/", response_model=ApiResponse)
async def root():
    """根路径"""
    return success_response({
        "service": "DeepSearch API Server",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    })

@app.get("/health", response_model=ApiResponse)
async def health_check():
    """健康检查"""
    logger.debug("🏥 健康检查请求")
    
    try:
        framework = get_deepsearch_framework()
        status = {
            "status": "healthy",
            "deepsearch_framework": "initialized",
            "brightdata_client": "available" if hasattr(framework, 'brightdata_client') else "unavailable",
            "firecrawl_client": "available" if hasattr(framework, 'firecrawl_client') else "unavailable",
            "litellm_client": "available" if hasattr(framework, 'litellm_client') else "unavailable",
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"✅ 健康检查通过: {status}")
        return success_response(status)
    except Exception as e:
        logger.error(f"❌ 健康检查失败: {e}")
        return error_response(500, f"健康检查失败: {str(e)}")

@app.post("/api/v1/search", response_model=ApiResponse)
async def deepsearch(
    request: DeepSearchRequest,
    framework: DeepSearchFramework = Depends(get_deepsearch_framework)
):
    """执行DeepSearch搜索"""
    search_id = str(uuid.uuid4())[:8]
    logger.info(f"🔍 [SEARCH-{search_id}] 开始DeepSearch: {request.question}")
    logger.debug(f"🔍 [SEARCH-{search_id}] 搜索参数: {request.dict()}")
    
    try:
        start_time = time.time()
        
        # 执行搜索
        logger.info(f"🔍 [SEARCH-{search_id}] 调用DeepSearch框架...")
        
        # 收集异步生成器的结果
        result = None
        async for chunk in framework.execute_deepsearch_workflow(
            question=request.question,
            max_rounds=request.max_search_rounds,
            num_results=request.max_results_per_round,
            stream=request.stream
        ):
            if isinstance(chunk, dict):
                # 如果是流式响应，取最后一个完整结果
                if "workflow_result" in chunk:
                    result = chunk["workflow_result"]
                elif "final_answer" in chunk:
                    result = chunk
                else:
                    result = chunk
        
        search_time = time.time() - start_time
        logger.info(f"✅ [SEARCH-{search_id}] DeepSearch完成 - {search_time:.3f}s")
        logger.debug(f"✅ [SEARCH-{search_id}] 搜索结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        return success_response(
            data=result,
            meta={
                "search_id": search_id,
                "search_time": round(search_time, 3),
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ [SEARCH-{search_id}] DeepSearch失败: {e}", exc_info=True)
        return error_response(500, f"搜索失败: {str(e)}", {"search_id": search_id})

@app.post("/api/v1/search/batch", response_model=ApiResponse)
async def batch_deepsearch(
    request: BatchSearchRequest,
    framework: DeepSearchFramework = Depends(get_deepsearch_framework)
):
    """批量执行DeepSearch搜索"""
    batch_id = str(uuid.uuid4())[:8]
    logger.info(f"📦 [BATCH-{batch_id}] 开始批量DeepSearch: {len(request.questions)}个问题")
    logger.debug(f"📦 [BATCH-{batch_id}] 问题列表: {request.questions}")
    
    try:
        start_time = time.time()
        results = []
        
        for i, question in enumerate(request.questions, 1):
            question_id = f"{batch_id}-{i}"
            logger.info(f"🔍 [BATCH-{batch_id}] 处理问题 {i}/{len(request.questions)}: {question}")
            
            try:
                question_start = time.time()
                
                # 收集异步生成器的结果
                result = None
                async for chunk in framework.execute_deepsearch_workflow(
                    question=question,
                    max_rounds=request.max_search_rounds,
                    num_results=request.max_results_per_round,
                    stream=False
                ):
                    if isinstance(chunk, dict):
                        # 取最后一个完整结果
                        if "workflow_result" in chunk:
                            result = chunk["workflow_result"]
                        elif "final_answer" in chunk:
                            result = chunk
                        else:
                            result = chunk
                
                question_time = time.time() - question_start
                
                results.append({
                    "question_id": question_id,
                    "question": question,
                    "result": result,
                    "search_time": round(question_time, 3),
                    "status": "success"
                })
                
                logger.info(f"✅ [BATCH-{batch_id}] 问题 {i} 完成 - {question_time:.3f}s")
                
            except Exception as e:
                logger.error(f"❌ [BATCH-{batch_id}] 问题 {i} 失败: {e}")
                results.append({
                    "question_id": question_id,
                    "question": question,
                    "result": None,
                    "error": str(e),
                    "status": "failed"
                })
        
        total_time = time.time() - start_time
        successful_count = sum(1 for r in results if r["status"] == "success")
        
        logger.info(f"📦 [BATCH-{batch_id}] 批量搜索完成: {successful_count}/{len(request.questions)} 成功 - {total_time:.3f}s")
        
        return success_response(
            data={
                "batch_id": batch_id,
                "total_questions": len(request.questions),
                "successful_count": successful_count,
                "failed_count": len(request.questions) - successful_count,
                "results": results
            },
            meta={
                "batch_id": batch_id,
                "total_time": round(total_time, 3),
                "average_time": round(total_time / len(request.questions), 3),
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ [BATCH-{batch_id}] 批量搜索失败: {e}", exc_info=True)
        return error_response(500, f"批量搜索失败: {str(e)}", {"batch_id": batch_id})

@app.get("/api/v1/config", response_model=ApiResponse)
async def get_config_info():
    """获取配置信息"""
    logger.debug("⚙️ 获取配置信息")
    
    try:
        config_info = {
            "deepsearch": {
                "max_search_rounds": config.get('deepsearch', {}).get('max_search_rounds', 5),
                "max_results_per_round": config.get('deepsearch', {}).get('max_results_per_round', 10),
                "max_crawl_urls": config.get('deepsearch', {}).get('max_crawl_urls', 3),
                "relevance_threshold": config.get('deepsearch', {}).get('relevance_threshold', 0.7)
            },
            "external_services": {
                "brightdata": {
                    "enabled": bool(config.get('external_services', {}).get('brightdata', {}).get('api_key')),
                    "timeout": config.get('external_services', {}).get('brightdata', {}).get('timeout', 30)
                },
                "firecrawl": {
                    "enabled": bool(config.get('external_services', {}).get('firecrawl', {}).get('api_key')),
                    "timeout": config.get('external_services', {}).get('firecrawl', {}).get('timeout', 60)
                }
            },
            "models": {
                "default_model": config.get('models', {}).get('default_model', 'deepseek-chat'),
                "s3_framework": config.get('models', {}).get('s3_framework', {})
            }
        }
        
        logger.info(f"⚙️ 配置信息: {config_info}")
        return success_response(config_info)
        
    except Exception as e:
        logger.error(f"❌ 获取配置信息失败: {e}")
        return error_response(500, f"获取配置失败: {str(e)}")

# ==================== 异常处理 ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理"""
    logger.error(f"❌ HTTP异常: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.status_code, exc.detail)
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    logger.error(f"❌ 未处理异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=error_response(500, f"内部服务器错误: {str(exc)}")
    )

# ==================== 主函数 ====================

if __name__ == "__main__":
    logger.info("🚀 启动DeepSearch API服务器...")
    
    # 从配置获取端口，默认8051
    port = config.get('service', {}).get('deepsearch_port', 8051)
    
    uvicorn.run(
        "src.api.deepsearch_server:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # 生产环境建议关闭
        log_level="info",
        access_log=True
    ) 