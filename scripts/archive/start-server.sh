#!/bin/bash

# S3框架API服务器启动脚本
# 设置环境变量并启动服务

echo "🚀 启动S3框架API服务器"
echo "📍 模式: RAG + DeepSearch"
echo "📍 时间: $(date)"

# 设置环境变量
export PYTHONPATH="${PWD}:${PYTHONPATH}"

# RAGFlow配置
export RAGFLOW_API_URL="http://150.109.16.195:7080"
export RAGFLOW_API_KEY="ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm"  # 修复后的API Key

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
export LANGFUSE_PUBLIC_KEY="pk-lf-e3343ef3-ddba-4bd5-aab5-2dd1b18bcb2c"
export LANGFUSE_SECRET_KEY="sk-lf-41d1a54b-e886-4858-ab99-8e7c4071c2fb"

# 代理配置（如果需要）
export HTTP_PROXY="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"

# 创建日志目录
mkdir -p logs

echo "✅ 环境变量已设置"
echo "📊 RAGFlow: $RAGFLOW_API_URL"
echo "🗃️ 数据库: $DB_HOST:$DB_PORT/$DB_NAME"
echo "🔍 Langfuse: $LANGFUSE_HOST"

# 测试RAGFlow连接
echo ""
echo "🔍 测试RAGFlow连接..."
response=$(curl -s -H "Authorization: Bearer $RAGFLOW_API_KEY" "$RAGFLOW_API_URL/api/v1/datasets?page=1&page_size=5")
if echo "$response" | grep -q '"code":0'; then
    echo "✅ RAGFlow连接正常"
    # 显示知识库信息
    echo "📚 可用知识库:"
    echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('code') == 0:
        datasets = data.get('data', {}).get('datasets', [])
        for ds in datasets[:3]:  # 显示前3个
            print(f'  - {ds.get(\"name\", \"Unknown\")} (ID: {ds.get(\"id\", \"Unknown\")})')
            doc_count = ds.get('document_count', 0)
            chunk_count = ds.get('chunk_count', 0)
            print(f'    文档: {doc_count}, 片段: {chunk_count}')
    else:
        print(f'  ❌ {data.get(\"message\", \"Unknown error\")}')
except:
    print('  ❌ 解析响应失败')
"
else
    echo "❌ RAGFlow连接失败:"
    echo "$response"
    echo ""
    echo "⚠️ 将在没有RAG功能的情况下启动服务器"
fi

echo ""
echo "🚀 启动API服务器..."
echo "📍 监听端口: 8050"
echo "📍 文档: http://localhost:8050/docs"
echo "📍 日志: server_langfuse.log"

# 启动服务器
python -m src.api.server > server_langfuse.log 2>&1 &
SERVER_PID=$!

echo "✅ 服务器已启动 (PID: $SERVER_PID)"
echo ""
echo "📋 管理命令:"
echo "  查看日志: tail -f server_langfuse.log"
echo "  停止服务: kill $SERVER_PID"
echo "  健康检查: curl http://localhost:8050/health"
echo ""
echo "🔍 测试命令:"
echo "  python test_quick_demo.py  # 快速测试两种模式"
echo "  python test_real_s3_scenarios.py  # 完整测试"

# 等待服务器启动
sleep 3

# 健康检查
echo "🔍 健康检查..."
if curl -s http://localhost:8050/health > /dev/null; then
    echo "✅ 服务器启动成功!"
    echo "🌐 访问: http://localhost:8050/docs"
else
    echo "❌ 服务器启动失败，请检查日志:"
    echo "tail -f server_langfuse.log"
fi