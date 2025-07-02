#!/bin/bash

# FlashSearch 本地快速启动脚本
# 直接使用 Python 启动 API 和 MCP 服务

echo "🚀 启动 FlashSearch 本地服务..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装"
    exit 1
fi

# 检查并安装依赖
echo "📦 检查依赖..."

# 检查是否使用 uv
if command -v uv &> /dev/null; then
    echo "🚀 使用 uv 安装依赖..."
    # 安装根目录依赖
    if [ -f "requirements.txt" ]; then
        uv pip install -r requirements.txt
    fi
    # 安装服务器特定依赖
    if [ -f "server/requirements.txt" ]; then
        uv pip install -r server/requirements.txt
    fi
    # 安装额外需要的包
    uv pip install beautifulsoup4 lxml
else
    echo "📦 使用 pip 安装依赖..."
    # 安装根目录依赖
    if [ -f "requirements.txt" ]; then
        pip3 install -q -r requirements.txt
    fi
    # 安装服务器特定依赖
    if [ -f "server/requirements.txt" ]; then
        pip3 install -q -r server/requirements.txt
    fi
    # 安装额外需要的包
    pip3 install -q beautifulsoup4 lxml
fi

# 停止可能存在的旧进程
echo "🛑 清理旧进程..."
pkill -f "uvicorn api.flash_search_api:app" 2>/dev/null || true
pkill -f "mira_flash_search.py" 2>/dev/null || true

# 启动 API 服务
echo "🌐 启动 API 服务 (端口 8060)..."
cd server
nohup python3 -m uvicorn api.flash_search_api:app \
    --host 0.0.0.0 \
    --port 8060 \
    --reload \
    --log-level info \
    > ../api_server.log 2>&1 &
API_PID=$!
cd ..

# 启动 MCP 服务
echo "🔌 启动 MCP 服务 (端口 9060)..."
cd server
nohup python3 mcp/mira_flash_search.py \
    --transport sse \
    --host 0.0.0.0 \
    --port 9060 \
    > ../mcp_server.log 2>&1 &
MCP_PID=$!
cd ..

# 保存 PID
echo $API_PID > .api.pid
echo $MCP_PID > .mcp.pid

echo ""
echo "✅ 服务启动完成!"
echo ""
echo "📝 进程信息:"
echo "  - API PID: $API_PID"
echo "  - MCP PID: $MCP_PID"
echo ""
echo "🔗 访问地址:"
echo "  - API 文档: http://localhost:8060/docs"
echo "  - API 健康: http://localhost:8060/health"
echo "  - MCP SSE: http://localhost:9060/sse/"
echo ""
echo "📋 查看日志:"
echo "  - API: tail -f api_server.log"
echo "  - MCP: tail -f mcp_server.log"
echo ""
echo "🛑 停止服务: ./stop-local.sh"