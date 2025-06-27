#!/bin/bash

# 启动本地S3测试环境
echo "🚀 启动本地S3架构测试环境"
echo "================================"

# 激活虚拟环境
source venv/bin/activate

# 检查端口是否被占用
if lsof -Pi :8050 -sTCP:LISTEN -t >/dev/null; then
    echo "⚠️  端口8050已被占用，停止现有服务..."
    pkill -f "main.py"
    sleep 2
fi

echo "🔧 启动API服务器 (端口8050)..."
echo "📝 日志将显示完整的[S3_TRACE]链路追踪"
echo "================================"

# 启动服务器并显示S3追踪日志
python main.py 2>&1 | grep --line-buffered -E "(S3_TRACE|启动|ERROR|INFO.*S3|智能体)"