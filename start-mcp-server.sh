#!/bin/bash
# Mira FlashSearch MCP Server 启动脚本 (增强版)

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 启动 Mira FlashSearch MCP Server v2.5.0${NC}"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未找到 Python3，请先安装${NC}"
    exit 1
fi

# 检查环境变量
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  未找到 .env 文件${NC}"
    if [ -f ".env.example" ]; then
        echo "📝 从 .env.example 创建 .env"
        cp .env.example .env
        echo -e "${YELLOW}请编辑 .env 文件配置必要的API密钥${NC}"
    else
        echo -e "${RED}❌ 未找到 .env.example 文件${NC}"
        exit 1
    fi
fi

# 检查并安装依赖
echo -e "${BLUE}📦 检查依赖...${NC}"
if command -v uv &> /dev/null; then
    echo "🚀 使用 uv 安装依赖..."
    uv pip install -r requirements.txt
    uv pip install -r server/requirements.txt
    uv pip install fastmcp
else
    echo "📦 使用 pip 安装依赖..."
    pip3 install -q -r requirements.txt
    pip3 install -q -r server/requirements.txt
    pip3 install -q fastmcp
fi

# 设置默认参数
TRANSPORT=${TRANSPORT:-"sse"}
HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-"9060"}
LOG_LEVEL=${LOG_LEVEL:-"info"}

# 清理旧进程
echo -e "${BLUE}🛑 清理旧进程...${NC}"
if [ "$TRANSPORT" != "stdio" ]; then
    if lsof -ti:$PORT > /dev/null 2>&1; then
        OLD_PID=$(lsof -ti:$PORT)
        kill -9 $OLD_PID 2>/dev/null || true
        echo -e "${GREEN}✅ 已停止旧的MCP进程 (PID: $OLD_PID)${NC}"
    fi
fi

# 清理可能的mcp进程
pkill -f "mira_flash_search.py" 2>/dev/null || true

echo -e "${BLUE}📡 MCP服务器配置:${NC}"
echo "   - 传输协议: $TRANSPORT"
if [ "$TRANSPORT" != "stdio" ]; then
    echo "   - 主机: $HOST"
    echo "   - 端口: $PORT"
fi
echo "   - 日志级别: $LOG_LEVEL"

# 启动MCP服务器
echo -e "${BLUE}🔌 启动MCP服务器...${NC}"

cd server
if [ "$TRANSPORT" = "http" ]; then
    echo -e "${GREEN}🌐 HTTP模式: http://$HOST:$PORT/mcp/${NC}"
    nohup python3 mcp/mira_flash_search.py \
        --transport http \
        --host $HOST \
        --port $PORT \
        --log-level $LOG_LEVEL \
        > ../mcp_server.log 2>&1 &
elif [ "$TRANSPORT" = "sse" ]; then
    echo -e "${GREEN}📡 SSE模式: http://$HOST:$PORT/sse/${NC}"
    nohup python3 mcp/mira_flash_search.py \
        --transport sse \
        --host $HOST \
        --port $PORT \
        --log-level $LOG_LEVEL \
        > ../mcp_server.log 2>&1 &
else
    echo -e "${GREEN}📟 STDIO模式 (适用于本地MCP客户端)${NC}"
    python3 mcp/mira_flash_search.py \
        --transport stdio \
        --log-level $LOG_LEVEL
    exit 0
fi
MCP_PID=$!
cd ..

# 保存PID
echo $MCP_PID > .mcp.pid
echo -e "${GREEN}✅ MCP服务已启动 (PID: $MCP_PID)${NC}"

# 等待服务启动
if [ "$TRANSPORT" != "stdio" ]; then
    echo -n "⏳ 等待服务就绪"
    for i in {1..10}; do
        if [ "$TRANSPORT" = "sse" ] && curl -s -f "http://localhost:$PORT/sse/" > /dev/null 2>&1; then
            echo -e "\n${GREEN}✅ MCP服务已就绪!${NC}"
            break
        elif [ "$TRANSPORT" = "http" ] && curl -s -f "http://localhost:$PORT/mcp/" > /dev/null 2>&1; then
            echo -e "\n${GREEN}✅ MCP服务已就绪!${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done
fi

# 输出信息
echo ""
echo -e "${BLUE}🔗 访问地址:${NC}"
if [ "$TRANSPORT" = "sse" ]; then
    echo "   - SSE端点: http://localhost:$PORT/sse/"
    echo "   - 使用FastMCP客户端连接"
elif [ "$TRANSPORT" = "http" ]; then
    echo "   - HTTP端点: http://localhost:$PORT/mcp/"
    echo "   - 工具列表: http://localhost:$PORT/mcp/tools"
fi
echo ""
echo -e "${BLUE}📋 管理命令:${NC}"
echo "   - 查看日志: tail -f mcp_server.log"
echo "   - 停止服务: ./stop-mcp-server.sh"
echo "   - 查看进程: ps aux | grep $MCP_PID"