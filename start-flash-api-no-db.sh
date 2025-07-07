#!/bin/bash
# Flash Search API Server 启动脚本 (无数据库版本)
# 专门用于在线搜索，不需要本地存储

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 启动 Flash Search API Server (无数据库模式)${NC}"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未找到 Python3，请先安装${NC}"
    exit 1
fi

# 设置环境变量
export DISABLE_DATABASE=true
export API_MODE=flash_search
export ENABLE_TIME_AWARE=true

# 检查环境变量
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  未找到 .env 文件${NC}"
    if [ -f ".env.example" ]; then
        echo "📝 从 .env.example 创建 .env"
        cp .env.example .env
        echo -e "${YELLOW}请编辑 .env 文件配置必要的API密钥${NC}"
    fi
fi

# 加载环境变量
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 设置默认参数
HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-"8060"}
LOG_LEVEL=${LOG_LEVEL:-"info"}

# 清理旧进程
echo -e "${BLUE}🛑 清理旧进程...${NC}"
if lsof -ti:$PORT > /dev/null 2>&1; then
    OLD_PID=$(lsof -ti:$PORT)
    kill -9 $OLD_PID 2>/dev/null || true
    echo -e "${GREEN}✅ 已停止旧的API进程 (PID: $OLD_PID)${NC}"
fi

echo -e "${BLUE}📡 Flash Search 配置:${NC}"
echo "   - 主机: $HOST"
echo "   - 端口: $PORT"
echo "   - 日志级别: $LOG_LEVEL"
echo "   - 数据库: 已禁用"
echo "   - 模式: 在线搜索 (S3架构)"
echo ""
echo -e "${BLUE}🔧 外部服务配置:${NC}"
echo "   - BrightData: ${BRIGHTDATA_API_KEY:0:20}..."
echo "   - FireCrawl: ${FIRECRAWL_API_KEY:0:20}..."
echo ""

# 启动服务器
echo -e "${GREEN}🏃 启动 Flash Search API...${NC}"

# 如果在server目录下有专门的flash_search_api.py
if [ -f "server/api/flash_search_api.py" ]; then
    cd server
    python3 -m uvicorn api.flash_search_api:app \
        --host $HOST \
        --port $PORT \
        --log-level $LOG_LEVEL \
        --reload &
    API_PID=$!
    cd ..
else
    # 使用主API但禁用数据库
    python3 -m uvicorn api.main:app \
        --host $HOST \
        --port $PORT \
        --log-level $LOG_LEVEL \
        --reload &
    API_PID=$!
fi

# 保存PID
echo $API_PID > .flash_api.pid
echo -e "${GREEN}✅ Flash Search API已启动 (PID: $API_PID)${NC}"

# 等待服务启动
echo -n "⏳ 等待服务就绪"
for i in {1..10}; do
    if curl -s -f "http://localhost:$PORT/health" > /dev/null 2>&1; then
        echo -e "\n${GREEN}✅ Flash Search API服务已就绪!${NC}"
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
echo ""
echo -e "${BLUE}📋 快速测试:${NC}"
echo "# 健康检查"
echo "curl http://localhost:$PORT/health"
echo ""
echo "# Flash搜索测试"
echo 'curl -X POST "http://localhost:'$PORT'/api/v1/search" \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"question": "最新AI发展", "mode": "flash", "max_rounds": 1}'"'"
echo ""
echo -e "${BLUE}📋 管理命令:${NC}"
echo "   - 查看日志: tail -f flash_api.log"
echo "   - 停止服务: kill \$(cat .flash_api.pid)"
echo "   - 查看进程: ps aux | grep $API_PID"