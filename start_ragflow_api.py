#!/usr/bin/env python3
"""
启动完整的RAGFlow API代理服务
包含所有知识库管理、文档处理、对话等功能
"""

import uvicorn
import os
from pathlib import Path

def main():
    """启动RAGFlow API代理服务"""
    
    # 确保在正确的目录
    os.chdir(Path(__file__).parent)
    
    # 启动服务
    print("🚀 启动RAGFlow API代理服务...")
    print(f"📁 工作目录: {os.getcwd()}")
    print(f"🌐 服务地址: http://localhost:8001")
    print(f"📚 API文档: http://localhost:8001/docs")
    print(f"💡 测试端点: http://localhost:8001/api/v1/datasets")
    
    uvicorn.run(
        "api_proxy:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()