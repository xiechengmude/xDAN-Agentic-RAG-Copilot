#!/bin/bash
# FlashSearch API 部署脚本 v0708-0130
# 简化版 - 遵循 KISS 和 DRY 原则
#
# 使用方法:
#   ./0708-0130.sh [HOST] [PORT] [LOG_LEVEL] [WORKERS]
#
# 示例:
#   ./0708-0130.sh                    # 默认: 0.0.0.0 8060
#   ./0708-0130.sh 0.0.0.0 8062       # 指定端口 8062
#   ./0708-0130.sh 0.0.0.0 8062 debug # 调试模式

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 解析参数 - 确保端口参数正确传递
HOST="${1:-0.0.0.0}"
PORT="${2:-${FLASHSEARCH_PORT:-8060}}"  # 优先使用命令行参数
LOG_LEVEL="${3:-info}"
WORKERS="${4:-1}"

echo -e "${BLUE}=================================================${NC}"
echo -e "${CYAN}🚀 FlashSearch API 部署脚本${NC}"
echo -e "${BLUE}=================================================${NC}"

# 显示配置
echo -e "${CYAN}📋 部署配置:${NC}"
echo -e "   - 主机地址: $HOST"
echo -e "   - 服务端口: $PORT"
echo -e "   - 日志级别: $LOG_LEVEL"
echo -e "   - 工作进程: $WORKERS"
echo ""

# 1. 环境检查
echo -e "${YELLOW}🔧 步骤1: 环境检查${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未安装${NC}"
    exit 1
fi

if [ ! -f "server/api/flash_search_api.py" ]; then
    echo -e "${RED}❌ 未找到 API 文件${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 环境检查通过${NC}"

# 2. 清理旧进程和端口
echo -e "${YELLOW}🔧 步骤2: 清理旧进程${NC}"

# 清理指定端口
if lsof -ti:$PORT > /dev/null 2>&1; then
    echo -e "${YELLOW}清理端口 $PORT...${NC}"
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# 清理 FlashSearch 进程
pkill -f "flash_search_api" 2>/dev/null || true

echo -e "${GREEN}✅ 清理完成${NC}"

# 3. 加载环境变量
echo -e "${YELLOW}🔧 步骤3: 配置环境${NC}"

# 禁用代理
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
export NO_PROXY="*"

# 加载 .env
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
    echo -e "${GREEN}✅ 已加载 .env${NC}"
fi

# 4. 启动服务
echo -e "${YELLOW}🔧 步骤4: 启动服务${NC}"

mkdir -p logs
LOG_FILE="logs/flashsearch_${PORT}_$(date +%Y%m%d_%H%M%S).log"

# 启动命令 - 明确传递端口参数
CMD="python3 server/api/flash_search_api.py --host $HOST --port $PORT --log-level $LOG_LEVEL --workers $WORKERS"

echo -e "${CYAN}执行命令: $CMD${NC}"

# 启动服务
nohup $CMD > "$LOG_FILE" 2>&1 &
PID=$!

echo $PID > .flashsearch_api.pid
echo -e "${GREEN}✅ 服务已启动 (PID: $PID)${NC}"

# 5. 健康检查
echo -e "${YELLOW}🔧 步骤5: 健康检查${NC}"

echo -n "等待服务就绪"
for i in {1..30}; do
    if curl -s -f "http://$HOST:$PORT/health" > /dev/null 2>&1; then
        echo -e "\n${GREEN}✅ 服务已就绪！${NC}"
        break
    fi
    echo -n "."
    sleep 1
    
    if [ $i -eq 30 ]; then
        echo -e "\n${RED}❌ 启动超时${NC}"
        echo -e "${YELLOW}查看日志: tail -f $LOG_FILE${NC}"
        exit 1
    fi
done

# 6. 显示结果
echo -e "${BLUE}=================================================${NC}"
echo -e "${GREEN}🎉 部署完成!${NC}"
echo -e "${BLUE}=================================================${NC}"

echo -e "${CYAN}📊 部署信息:${NC}"
echo -e "   - PID: $PID"
echo -e "   - 端口: $PORT"
echo -e "   - 日志: $LOG_FILE"

echo -e "${CYAN}🔗 访问地址:${NC}"
echo -e "   - API文档: http://$HOST:$PORT/docs"
echo -e "   - 健康检查: http://$HOST:$PORT/health"

echo -e "${CYAN}📋 测试命令:${NC}"
echo "curl http://$HOST:$PORT/health"
echo "curl -X POST \"http://$HOST:$PORT/search\" -H \"Content-Type: application/json\" -d '{\"query\": \"测试\", \"mode\": \"fast\"}'"

echo -e "${CYAN}🔧 管理命令:${NC}"
echo -e "   - 查看日志: tail -f $LOG_FILE"
echo -e "   - 停止服务: kill $PID"

# 调试模式显示日志
if [ "$LOG_LEVEL" == "debug" ]; then
    echo -e "${YELLOW}🐛 Debug模式 - 显示日志:${NC}"
    tail -20 "$LOG_FILE"
fi