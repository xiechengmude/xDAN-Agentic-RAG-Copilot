#!/bin/bash

# FlashSearch 本地服务停止脚本

echo "🛑 停止 FlashSearch 本地服务..."

# 读取 PID 文件
if [ -f ".api.pid" ]; then
    API_PID=$(cat .api.pid)
    if kill -0 $API_PID 2>/dev/null; then
        kill -9 $API_PID
        echo "✅ API 服务已停止 (PID: $API_PID)"
    else
        echo "⚠️  API 进程不存在 (PID: $API_PID)"
    fi
    rm -f .api.pid
else
    echo "⚠️  未找到 API PID 文件"
fi

if [ -f ".mcp.pid" ]; then
    MCP_PID=$(cat .mcp.pid)
    if kill -0 $MCP_PID 2>/dev/null; then
        kill -9 $MCP_PID
        echo "✅ MCP 服务已停止 (PID: $MCP_PID)"
    else
        echo "⚠️  MCP 进程不存在 (PID: $MCP_PID)"
    fi
    rm -f .mcp.pid
else
    echo "⚠️  未找到 MCP PID 文件"
fi

# 额外检查并清理可能的遗留进程
echo ""
echo "🔍 检查遗留进程..."

# 检查 uvicorn 进程
if pgrep -f "uvicorn api.flash_search_api:app" > /dev/null; then
    pkill -f "uvicorn api.flash_search_api:app"
    echo "✅ 清理了遗留的 API 进程"
fi

# 检查 MCP 进程
if pgrep -f "mira_flash_search.py" > /dev/null; then
    pkill -f "mira_flash_search.py"
    echo "✅ 清理了遗留的 MCP 进程"
fi

# 检查端口占用
if lsof -ti:8060 > /dev/null 2>&1; then
    kill -9 $(lsof -ti:8060) 2>/dev/null || true
    echo "✅ 清理了 8060 端口"
fi

if lsof -ti:9060 > /dev/null 2>&1; then
    kill -9 $(lsof -ti:9060) 2>/dev/null || true
    echo "✅ 清理了 9060 端口"
fi

echo ""
echo "✅ 所有服务已停止!"