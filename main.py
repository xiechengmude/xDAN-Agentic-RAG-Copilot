#!/usr/bin/env python3
"""
xDAN RAG Copilot 主入口文件
简化模块导入和启动流程
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ['PYTHONPATH'] = str(project_root)

# 导入应用
try:
    from src.api.server import app
except ImportError as e:
    print(f"模块导入失败: {e}")
    print("请确保已安装所有依赖:")
    print("  pip install -r requirements.txt")
    sys.exit(1)

if __name__ == "__main__":
    import uvicorn
    
    # 获取配置
    port = int(os.getenv('PORT', 8050))
    host = os.getenv('HOST', '0.0.0.0')
    
    print(f"启动 xDAN RAG Copilot API 服务")
    print(f"地址: http://{host}:{port}")
    print(f"文档: http://{host}:{port}/docs")
    print(f"健康检查: http://{host}:{port}/health")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )