#!/bin/bash
# FlashSearch API Server 启动脚本

set -e

echo "🚀 启动 FlashSearch API Server v2.5.0"

# 切换到服务器目录
cd "$(dirname "$0")"

# 检查环境变量
if [ ! -f "../.env" ]; then
    echo "❌ 未找到 .env 文件，请确保环境变量已配置"
    exit 1
fi

# 激活虚拟环境 (如果存在)
if [ -d "../.venv" ]; then
    echo "📦 激活虚拟环境"
    source ../.venv/bin/activate
fi

# 设置默认参数
HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-"8000"}
WORKERS=${WORKERS:-"1"}
RELOAD=${RELOAD:-"false"}
LOG_LEVEL=${LOG_LEVEL:-"info"}

# 检查端口是否被占用
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  端口 $PORT 已被占用，请检查或更改端口"
    exit 1
fi

echo "📡 服务器配置:"
echo "   - 主机: $HOST"
echo "   - 端口: $PORT"
echo "   - 工作进程: $WORKERS"
echo "   - 重载模式: $RELOAD"
echo "   - 日志级别: $LOG_LEVEL"

# 启动服务器
if [ "$RELOAD" = "true" ]; then
    echo "🔄 开发模式 (支持热重载)"
    python api/flash_search_api.py --host $HOST --port $PORT --reload --log-level $LOG_LEVEL
else
    echo "🏭 生产模式"
    uvicorn api.flash_search_api:app \
        --host $HOST \
        --port $PORT \
        --workers $WORKERS \
        --log-level $LOG_LEVEL \
        --access-log \
        --loop uvloop
fi