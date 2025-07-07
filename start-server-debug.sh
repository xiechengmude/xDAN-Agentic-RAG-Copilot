#!/bin/bash

# S3框架API服务器启动脚本 - DEBUG模式
# 设置环境变量并启动服务

echo "🚀 启动S3框架API服务器 (DEBUG模式)"
echo "📍 模式: RAG + DeepSearch"
echo "📍 时间: $(date)"

# 设置环境变量
export PYTHONPATH="${PWD}:${PYTHONPATH}"

# 设置日志级别
export LOG_LEVEL="DEBUG"
export PYTHONUNBUFFERED=1

# RAGFlow配置
export RAGFLOW_API_URL="http://150.109.16.195:7080"
export RAGFLOW_API_KEY="ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm"

# 数据库配置
export DB_HOST="localhost"
export DB_PORT="5433"
export DB_NAME="xdan_rag_service"
export DB_USER="ragflow_user"
export DB_PASSWORD="ragflow123"

# LLM Provider配置
export DEEPSEEK_API_KEY="sk-6a32ae2b5dc440558aa628eec3dfda07"

# Langfuse配置（本地）
export LANGFUSE_ENABLED="true"
export LANGFUSE_ENV="local"
export LANGFUSE_HOST="http://localhost:3000"
export LANGFUSE_PUBLIC_KEY="pk-lf-a9584006-ab4a-4301-a1a1-691eb6f0377a"
export LANGFUSE_SECRET_KEY="sk-lf-e3aec777-8820-480f-95aa-37498c76cbe4"

# 代理配置（如果需要）
export HTTP_PROXY="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"

# 创建日志目录
mkdir -p logs

echo "✅ 环境变量已设置"
echo "📊 RAGFlow: $RAGFLOW_API_URL"
echo "🗃️ 数据库: $DB_HOST:$DB_PORT/$DB_NAME"
echo "🔍 Langfuse: $LANGFUSE_HOST"
echo "📝 日志级别: DEBUG"

# 测试RAGFlow连接
echo ""
echo "🔍 测试RAGFlow连接..."
response=$(curl -s -H "Authorization: Bearer $RAGFLOW_API_KEY" "$RAGFLOW_API_URL/api/v1/datasets?page=1&page_size=5")
if echo "$response" | grep -q '"code":0'; then
    echo "✅ RAGFlow连接正常"
else
    echo "❌ RAGFlow连接失败:"
    echo "$response"
    echo ""
    echo "⚠️ 将在没有RAG功能的情况下启动服务器"
fi

echo ""
echo "🚀 启动API服务器 (DEBUG模式)..."
echo "📍 监听端口: 8050"
echo "📍 文档: http://localhost:8050/docs"
echo "📍 日志: 实时输出到控制台"

# 启动服务器 - 直接输出到控制台以便实时查看DEBUG日志
python -m src.api.server