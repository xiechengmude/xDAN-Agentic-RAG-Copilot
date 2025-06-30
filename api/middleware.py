"""
API中间件 - 错误处理、日志记录、请求追踪
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
import time
import logging
import traceback
from typing import Callable
import uuid

logger = logging.getLogger(__name__)

async def error_handler_middleware(request: Request, call_next: Callable) -> Response:
    """全局错误处理中间件"""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"未处理的异常: {e}")
        logger.error(traceback.format_exc())
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "服务器内部错误",
                "detail": str(e) if logger.level == logging.DEBUG else None
            }
        )

async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """请求日志中间件"""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    # 记录请求
    logger.info(f"[{request_id}] {request.method} {request.url.path}")
    
    # 处理请求
    response = await call_next(request)
    
    # 记录响应
    duration = time.time() - start_time
    logger.info(
        f"[{request_id}] {request.method} {request.url.path} "
        f"- {response.status_code} - {duration:.3f}s"
    )
    
    # 添加响应头
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration:.3f}"
    
    return response

async def rate_limit_middleware(request: Request, call_next: Callable) -> Response:
    """简单的速率限制中间件"""
    # 这里可以实现基于Redis的速率限制
    # 暂时使用简单的内存计数器作为示例
    
    client_ip = request.client.host if request.client else "unknown"
    
    # TODO: 实现真正的速率限制逻辑
    # 例如：每个IP每分钟最多60个请求
    
    response = await call_next(request)
    return response

def setup_middleware(app):
    """设置所有中间件"""
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from fastapi.middleware.gzip import GZipMiddleware
    
    # 添加中间件（注意顺序，后添加的先执行）
    app.middleware("http")(error_handler_middleware)
    app.middleware("http")(logging_middleware)
    app.middleware("http")(rate_limit_middleware)
    
    # 添加标准中间件
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # 生产环境应启用
    # app.add_middleware(
    #     TrustedHostMiddleware, 
    #     allowed_hosts=["example.com", "*.example.com"]
    # )