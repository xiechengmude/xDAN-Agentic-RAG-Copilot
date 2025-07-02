#!/bin/bash
# FlashSearch API Server 停止脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🛑 停止 FlashSearch API Server${NC}"

# 读取PID文件
if [ -f ".api.pid" ]; then
    API_PID=$(cat .api.pid)
    if kill -0 $API_PID 2>/dev/null; then
        kill -9 $API_PID
        echo -e "${GREEN}✅ API服务已停止 (PID: $API_PID)${NC}"
    else
        echo -e "${YELLOW}⚠️  API进程不存在 (PID: $API_PID)${NC}"
    fi
    rm -f .api.pid
else
    echo -e "${YELLOW}⚠️  未找到API PID文件${NC}"
fi

# 额外检查端口8060
if lsof -ti:8060 > /dev/null 2>&1; then
    echo "🔍 发现8060端口仍被占用，清理中..."
    kill -9 $(lsof -ti:8060) 2>/dev/null || true
    echo -e "${GREEN}✅ 已清理8060端口${NC}"
fi

# 清理uvicorn进程
if pgrep -f "uvicorn api.flash_search_api:app" > /dev/null; then
    pkill -f "uvicorn api.flash_search_api:app"
    echo -e "${GREEN}✅ 已清理uvicorn进程${NC}"
fi

echo -e "${GREEN}✅ API服务停止完成${NC}"