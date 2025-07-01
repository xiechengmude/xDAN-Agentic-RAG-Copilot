#!/bin/bash
# Mira FlashSearch MCP Server 启动脚本

set -e

echo "🚀 启动 Mira FlashSearch MCP Server v2.5.0"

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
TRANSPORT=${TRANSPORT:-"stdio"}
HOST=${HOST:-"127.0.0.1"}
PORT=${PORT:-"9000"}
LOG_LEVEL=${LOG_LEVEL:-"info"}

echo "📡 MCP服务器配置:"
echo "   - 传输协议: $TRANSPORT"
if [ "$TRANSPORT" != "stdio" ]; then
    echo "   - 主机: $HOST"
    echo "   - 端口: $PORT"
fi
echo "   - 日志级别: $LOG_LEVEL"

# 检查端口 (非stdio模式)
if [ "$TRANSPORT" != "stdio" ] && lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  端口 $PORT 已被占用，请检查或更改端口"
    exit 1
fi

# 启动MCP服务器
echo "🔌 启动MCP服务器..."

if [ "$TRANSPORT" = "http" ]; then
    echo "🌐 HTTP模式: http://$HOST:$PORT/mcp/"
    python mcp/mira_flash_search.py --transport http --host $HOST --port $PORT --log-level $LOG_LEVEL
elif [ "$TRANSPORT" = "sse" ]; then
    echo "📡 SSE模式: http://$HOST:$PORT/sse/"
    python mcp/mira_flash_search.py --transport sse --host $HOST --port $PORT --log-level $LOG_LEVEL
else
    echo "📟 STDIO模式 (适用于本地MCP客户端)"
    python mcp/mira_flash_search.py --transport stdio --log-level $LOG_LEVEL
fi