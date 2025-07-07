#!/bin/bash

# S3框架API服务器启动脚本 - 无数据库模式
# 仅用于测试S3框架功能

echo "🚀 启动S3框架API服务器 (无数据库模式)"
echo "📍 模式: RAG + DeepSearch (无数据库)"
echo "📍 时间: $(date)"

# 设置环境变量
export PYTHONPATH="${PWD}:${PYTHONPATH}"

# 设置日志级别
export LOG_LEVEL="DEBUG"
export PYTHONUNBUFFERED=1

# RAGFlow配置
export RAGFLOW_API_URL="http://150.109.16.195:7080"
export RAGFLOW_API_KEY="ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm"

# 禁用数据库相关功能
export DB_ENABLED="false"
export LANGFUSE_ENABLED="false"

# LLM Provider配置
export DEEPSEEK_API_KEY="sk-6a32ae2b5dc440558aa628eec3dfda07"

# 代理配置（如果需要）
export HTTP_PROXY="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"

echo "✅ 环境变量已设置"
echo "📊 RAGFlow: $RAGFLOW_API_URL"
echo "📝 日志级别: DEBUG"
echo "⚠️  数据库功能已禁用"

# 测试RAGFlow连接
echo ""
echo "🔍 测试RAGFlow连接..."
response=$(curl -s -H "Authorization: Bearer $RAGFLOW_API_KEY" "$RAGFLOW_API_URL/api/v1/datasets?page=1&page_size=5")
if echo "$response" | grep -q '"code":0'; then
    echo "✅ RAGFlow连接正常"
else
    echo "❌ RAGFlow连接失败:"
    echo "$response"
fi

echo ""
echo "🚀 启动API服务器 (无数据库模式)..."
echo "📍 监听端口: 8050"
echo "📍 文档: http://localhost:8050/docs"

# 创建一个修改版的服务器启动文件
cat > src/api/server_no_db.py << 'EOF'
#!/usr/bin/env python3
"""
简化版API服务器 - 仅测试S3框架功能
"""

import os
import logging
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any
import uvicorn

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import S3 service
from src.services.service_factory import get_default_service
from src.clients.ragflow_client import RAGFlowClient

# Global S3 service instance
s3_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global s3_service
    
    logger.info("初始化S3服务...")
    try:
        s3_service = get_default_service()
        logger.info("S3服务初始化成功")
    except Exception as e:
        logger.error(f"S3服务初始化失败: {e}")
        s3_service = None
    
    yield
    
    logger.info("服务已关闭")

app = FastAPI(
    title="S3 Framework Test Server",
    description="简化版API服务器，仅用于测试S3框架功能",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/v1/test/s3-search")
async def test_s3_search(request: Dict[str, Any]):
    """测试S3搜索功能"""
    if not s3_service:
        raise HTTPException(status_code=503, detail="S3 service not available")
    
    question = request.get("question", "")
    dataset_ids = request.get("dataset_ids", ["7e8d9e924cde11f0afc90242ac140006"])
    
    logger.info(f"[S3_TEST] Question: {question}")
    logger.info(f"[S3_TEST] Dataset IDs: {dataset_ids}")
    
    try:
        result = None
        async for res in s3_service.ask(
            question=question,
            dataset_ids=dataset_ids,
            max_rounds=3,
            stream=False
        ):
            result = res
            break
        
        return JSONResponse(content={
            "code": 0,
            "message": "Success",
            "data": result
        })
    except Exception as e:
        logger.error(f"[S3_TEST] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy", "s3_service": s3_service is not None}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8050, log_level="info")
EOF

# 启动服务器
python src/api/server_no_db.py