#!/bin/bash
# FlashSearch API Server 启动脚本 (增强版)

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 启动 FlashSearch API Server v2.5.0${NC}"

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
else
    echo "📦 使用 pip 安装依赖..."
    pip3 install -q -r requirements.txt
    pip3 install -q -r server/requirements.txt
fi

# 设置默认参数
HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-"8060"}
WORKERS=${WORKERS:-"1"}
RELOAD=${RELOAD:-"true"}
LOG_LEVEL=${LOG_LEVEL:-"info"}

# 清理旧进程
echo -e "${BLUE}🛑 清理旧进程...${NC}"
if lsof -ti:$PORT > /dev/null 2>&1; then
    OLD_PID=$(lsof -ti:$PORT)
    kill -9 $OLD_PID 2>/dev/null || true
    echo -e "${GREEN}✅ 已停止旧的API进程 (PID: $OLD_PID)${NC}"
fi

# 清理可能的uvicorn进程
pkill -f "uvicorn api.flash_search_api:app" 2>/dev/null || true

echo -e "${BLUE}📡 服务器配置:${NC}"
echo "   - 主机: $HOST"
echo "   - 端口: $PORT"
echo "   - 工作进程: $WORKERS"
echo "   - 重载模式: $RELOAD"
echo "   - 日志级别: $LOG_LEVEL"

# 启动服务器
cd server
if [ "$RELOAD" = "true" ]; then
    echo -e "${YELLOW}🔄 开发模式 (支持热重载)${NC}"
    nohup python3 -m uvicorn api.flash_search_api:app \
        --host $HOST \
        --port $PORT \
        --reload \
        --log-level $LOG_LEVEL \
        > ../api_server.log 2>&1 &
else
    echo -e "${GREEN}🏭 生产模式${NC}"
    nohup uvicorn api.flash_search_api:app \
        --host $HOST \
        --port $PORT \
        --workers $WORKERS \
        --log-level $LOG_LEVEL \
        --access-log \
        --loop uvloop \
        > ../api_server.log 2>&1 &
fi
API_PID=$!
cd ..

# 保存PID
echo $API_PID > .api.pid
echo -e "${GREEN}✅ API服务已启动 (PID: $API_PID)${NC}"

# 等待服务启动
echo -n "⏳ 等待服务就绪"
for i in {1..10}; do
    if curl -s -f "http://localhost:$PORT/health" > /dev/null 2>&1; then
        echo -e "\n${GREEN}✅ API服务已就绪!${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# 输出信息
echo ""
echo -e "${BLUE}🔗 访问地址:${NC}"
echo "   - API文档: http://localhost:$PORT/docs"
echo "   - 健康检查: http://localhost:$PORT/health"
echo "   - 统计信息: http://localhost:$PORT/stats"
echo ""
echo -e "${BLUE}📋 管理命令:${NC}"
echo "   - 查看日志: tail -f api_server.log"
echo "   - 停止服务: ./stop-api-server.sh"
echo "   - 查看进程: ps aux | grep $API_PID"