#!/usr/bin/env python3
"""
运行搜索过程可视化API服务
"""

import os
import sys
import uvicorn
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """启动API服务"""
    print("🚀 启动RAGFlow搜索过程可视化API...")
    print(f"📁 项目根目录: {project_root}")
    
    # 检查演示文件是否存在
    demo_path = project_root / "examples" / "frontend" / "search_visualization.html"
    if demo_path.exists():
        print(f"✅ 演示页面就绪: {demo_path}")
    else:
        print("⚠️  演示页面未找到")
    
    # 配置信息
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    print(f"\n🌐 服务配置:")
    print(f"   主机: {host}")
    print(f"   端口: {port}")
    print(f"\n📍 访问地址:")
    print(f"   API文档: http://localhost:{port}/docs")
    print(f"   演示页面: http://localhost:{port}/demo")
    print(f"   健康检查: http://localhost:{port}/health")
    print(f"\n📡 API端点:")
    print(f"   SSE流式搜索: POST http://localhost:{port}/api/v2/search/stream")
    print(f"   完整搜索: POST http://localhost:{port}/api/v2/search/complete")
    print(f"   WebSocket: ws://localhost:{port}/ws/search/{{client_id}}")
    print("\n按 Ctrl+C 停止服务\n")
    
    # 启动服务
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()