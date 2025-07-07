#!/bin/bash

echo "🚀 启动带本地Langfuse追踪的服务器"

# 停止旧服务器
echo "停止旧服务器..."
pkill -f "python -m src.api.server" || true
sleep 2

# 设置环境变量 - 使用本地Langfuse
export LANGFUSE_ENABLED=true
export LANGFUSE_ENV=local
export LANGFUSE_LOCAL_HOST=http://localhost:3000
export LANGFUSE_LOCAL_PUBLIC_KEY=pk-lf-b5e54e4c-4e9a-4c20-b5a7-5148d0f9683e
export LANGFUSE_LOCAL_SECRET_KEY=sk-lf-ef7ef641-8f04-41ef-a474-338a80e7dedf

# 同时设置默认的环境变量（为了兼容当前代码）
export LANGFUSE_HOST=$LANGFUSE_LOCAL_HOST
export LANGFUSE_PUBLIC_KEY=$LANGFUSE_LOCAL_PUBLIC_KEY
export LANGFUSE_SECRET_KEY=$LANGFUSE_LOCAL_SECRET_KEY

echo "📍 Langfuse配置:"
echo "  - 环境: local"
echo "  - Host: $LANGFUSE_HOST"
echo "  - Public Key: ${LANGFUSE_PUBLIC_KEY:0:20}..."

# 启动服务器
echo "启动服务器..."
python -m src.api.server