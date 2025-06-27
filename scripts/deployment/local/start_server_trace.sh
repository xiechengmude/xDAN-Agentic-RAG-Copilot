#!/bin/bash
# 启动API服务器脚本

echo "启动xDAN统一API服务器..."
echo "================================"
echo "服务器端口: 9099"
echo "查看日志中的[S3_TRACE]标记"
echo "================================"

source venv/bin/activate
python src/api/server.py