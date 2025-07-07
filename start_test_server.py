#!/usr/bin/env python3
"""
FlashSearch API 测试服务器启动脚本
用于端到端测试的简化服务器启动
"""

import os
import sys
import uvicorn
import signal
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def setup_environment():
    """设置测试环境"""
    # 设置环境变量
    os.environ["DISABLE_DATABASE"] = "true"
    os.environ["API_MODE"] = "flash_search"
    os.environ["ENABLE_TIME_AWARE"] = "true"
    os.environ["TEST_MODE"] = "true"
    os.environ["ENABLE_DATABASE"] = "false"
    os.environ["USE_MOCK_DB"] = "true"
    
    # 加载.env文件
    env_file = project_root / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
    
    print("✅ 测试环境配置完成")

def signal_handler(signum, frame):
    """处理中断信号"""
    print(f"\n收到信号 {signum}，正在关闭服务器...")
    sys.exit(0)

def main():
    """主函数"""
    print("🚀 启动 FlashSearch API 测试服务器")
    print("=" * 50)
    
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 设置环境
    setup_environment()
    
    # 配置参数
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info")
    
    print(f"📡 服务器配置:")
    print(f"   - 主机: {host}")
    print(f"   - 端口: {port}")
    print(f"   - 日志级别: {log_level}")
    print(f"   - 模式: 测试模式")
    
    # 检查API密钥
    required_keys = ["BRIGHTDATA_API_KEY", "FIRECRAWL_API_KEY", "DEEPSEEK_API_KEY"]
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        print(f"⚠️  缺少API密钥: {', '.join(missing_keys)}")
        print("某些功能可能无法正常工作")
    else:
        print("✅ 所有必需的API密钥已配置")
    
    print("\n🏃 启动API服务器...")
    
    try:
        # 启动服务器
        uvicorn.run(
            "test_api_server:app",
            host=host,
            port=port,
            log_level=log_level,
            reload=False,  # 测试模式下禁用reload
            access_log=True
        )
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()