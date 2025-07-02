#!/bin/bash
# Mira FlashSearch MCP Server 停止脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🛑 停止 Mira FlashSearch MCP Server${NC}"

# 读取PID文件
if [ -f ".mcp.pid" ]; then
    MCP_PID=$(cat .mcp.pid)
    if kill -0 $MCP_PID 2>/dev/null; then
        kill -9 $MCP_PID
        echo -e "${GREEN}✅ MCP服务已停止 (PID: $MCP_PID)${NC}"
    else
        echo -e "${YELLOW}⚠️  MCP进程不存在 (PID: $MCP_PID)${NC}"
    fi
    rm -f .mcp.pid
else
    echo -e "${YELLOW}⚠️  未找到MCP PID文件${NC}"
fi

# 额外检查端口9060
if lsof -ti:9060 > /dev/null 2>&1; then
    echo "🔍 发现9060端口仍被占用，清理中..."
    kill -9 $(lsof -ti:9060) 2>/dev/null || true
    echo -e "${GREEN}✅ 已清理9060端口${NC}"
fi

# 清理mcp进程
if pgrep -f "mira_flash_search.py" > /dev/null; then
    pkill -f "mira_flash_search.py"
    echo -e "${GREEN}✅ 已清理MCP进程${NC}"
fi

echo -e "${GREEN}✅ MCP服务停止完成${NC}"