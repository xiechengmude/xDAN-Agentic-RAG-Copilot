#!/usr/bin/env python3
"""
启动API服务器
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 启动服务器
if __name__ == "__main__":
    import uvicorn
    from src.api.server import app
    
    print("="*60)
    print("启动xDAN统一API服务器")
    print("="*60)
    print("端口: 9099")
    print("文档: http://localhost:9099/docs")
    print("健康检查: http://localhost:9099/health")
    print("查看[S3_TRACE]日志了解S3架构执行过程")
    print("="*60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9099,
        log_level="info"
    )