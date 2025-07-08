#!/bin/bash
# FlashSearch API 部署脚本 v0708-0130
# 完整的生产环境部署自动化脚本
# 支持SSE流式搜索、代理禁用、健康检查等功能
#
# 使用方法:
#   ./0708-0130.sh [HOST] [PORT] [LOG_LEVEL] [WORKERS] [AUTO_CLEAN]
#
# 参数说明:
#   HOST       - 服务器地址 (默认: 0.0.0.0)
#   PORT       - 服务端口 (默认: 8050)
#   LOG_LEVEL  - 日志级别 (默认: info, 可选: debug, info, warning, error)
#   WORKERS    - 工作进程数 (默认: 1)
#   AUTO_CLEAN - 自动清理旧进程 (默认: true, 可选: true, false)
#
# 示例:
#   ./0708-0130.sh                           # 使用默认配置
#   ./0708-0130.sh 0.0.0.0 8051              # 指定端口
#   ./0708-0130.sh 0.0.0.0 8051 debug        # 启用调试模式
#   ./0708-0130.sh 0.0.0.0 8051 info 1 true  # 完整参数

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 脚本信息
SCRIPT_VERSION="v0708-0130"
DEPLOY_TIME=$(date '+%Y-%m-%d %H:%M:%S')
PROJECT_NAME="FlashSearch API"

echo -e "${BLUE}=================================================${NC}"
echo -e "${CYAN}🚀 $PROJECT_NAME 部署脚本 $SCRIPT_VERSION${NC}"
echo -e "${CYAN}📅 部署时间: $DEPLOY_TIME${NC}"
echo -e "${BLUE}=================================================${NC}"

# 部署配置
DEFAULT_HOST="0.0.0.0"
DEFAULT_PORT="${FLASHSEARCH_PORT:-8060}"
DEFAULT_LOG_LEVEL="info"
DEFAULT_WORKERS="1"
AUTO_CLEAN="true"  # 默认自动清理旧进程

# 解析命令行参数
HOST=${1:-$DEFAULT_HOST}
PORT=${2:-$DEFAULT_PORT}
LOG_LEVEL=${3:-$DEFAULT_LOG_LEVEL}
WORKERS=${4:-$DEFAULT_WORKERS}
AUTO_CLEAN=${5:-$AUTO_CLEAN}

echo -e "${BLUE}📋 部署配置:${NC}"
echo -e "   - 主机地址: ${CYAN}$HOST${NC}"
echo -e "   - 服务端口: ${CYAN}$PORT${NC}"
echo -e "   - 日志级别: ${CYAN}$LOG_LEVEL${NC}"
echo -e "   - 工作进程: ${CYAN}$WORKERS${NC}"
echo ""

# 1. 环境检查
echo -e "${YELLOW}🔧 步骤1: 环境检查${NC}"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未安装，请先安装 Python 3.8+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✅ Python 版本: $PYTHON_VERSION${NC}"

# 检查项目目录
if [ ! -f "server/api/flash_search_api.py" ]; then
    echo -e "${RED}❌ 未找到 FlashSearch API 文件，请在项目根目录执行此脚本${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 项目文件检查通过${NC}"

# 清理旧进程
echo -e "${CYAN}🧹 清理旧的FlashSearch进程...${NC}"

# 清理可能的旧进程
pkill -f "flash_search_api" 2>/dev/null || true
pkill -f "flashsearch" 2>/dev/null || true

# 清理旧的PID文件
if [ -f ".flashsearch_api.pid" ]; then
    OLD_PID=$(cat .flashsearch_api.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  发现旧进程 PID: $OLD_PID${NC}"
        kill -9 $OLD_PID 2>/dev/null || true
        echo -e "${GREEN}✅ 已停止旧进程 $OLD_PID${NC}"
    fi
    rm -f .flashsearch_api.pid
fi

# 检查并清理端口占用
if lsof -ti:$PORT > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  端口 $PORT 仍被占用，强制清理...${NC}"
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
    sleep 2
    
    # 再次检查
    if lsof -ti:$PORT > /dev/null 2>&1; then
        echo -e "${RED}❌ 端口 $PORT 无法释放，请手动清理${NC}"
        echo -e "${CYAN}提示: sudo lsof -ti:$PORT | sudo xargs kill -9${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ 进程清理完成${NC}"

# 2. 代理配置
echo -e "${YELLOW}🔧 步骤2: 网络配置${NC}"

# 禁用代理以避免外部API调用问题
echo -e "${CYAN}🌐 禁用本地代理...${NC}"
unset HTTP_PROXY
unset HTTPS_PROXY
unset http_proxy
unset https_proxy
export NO_PROXY="*"
echo -e "${GREEN}✅ 代理已禁用，确保外部API正常访问${NC}"

# 3. 环境变量检查
echo -e "${YELLOW}🔧 步骤3: 环境变量检查${NC}"

# 检查必需的API密钥
REQUIRED_KEYS=("BRIGHTDATA_API_KEY" "FIRECRAWL_API_KEY" "DEEPSEEK_API_KEY")
MISSING_KEYS=()

for key in "${REQUIRED_KEYS[@]}"; do
    if [ -z "${!key}" ]; then
        MISSING_KEYS+=($key)
    else
        # 显示密钥前6位用于验证
        KEY_VALUE="${!key}"
        echo -e "${GREEN}✅ $key: ${KEY_VALUE:0:6}...${NC}"
    fi
done

if [ ${#MISSING_KEYS[@]} -ne 0 ]; then
    echo -e "${YELLOW}⚠️  缺少以下环境变量:${NC}"
    for key in "${MISSING_KEYS[@]}"; do
        echo -e "   - $key"
    done
    
    if [ -f ".env" ]; then
        echo -e "${CYAN}📄 检查 .env 文件...${NC}"
        source .env
        echo -e "${GREEN}✅ 已加载 .env 文件${NC}"
    else
        echo -e "${RED}❌ 未找到 .env 文件，请配置必需的API密钥${NC}"
        exit 1
    fi
fi

# 4. 依赖检查
echo -e "${YELLOW}🔧 步骤4: 依赖检查${NC}"

# 检查关键Python包
REQUIRED_PACKAGES=("fastapi" "uvicorn" "aiohttp" "asyncio")
for package in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        echo -e "${GREEN}✅ $package 已安装${NC}"
    else
        echo -e "${RED}❌ $package 未安装${NC}"
        echo -e "${CYAN}📦 尝试安装依赖...${NC}"
        pip3 install -r requirements.txt || pip3 install $package
    fi
done

# 5. 服务启动
echo -e "${YELLOW}🔧 步骤5: 启动服务${NC}"

# 创建日志目录
mkdir -p logs
LOG_FILE="logs/flashsearch_${PORT}_$(date +%Y%m%d_%H%M%S).log"

echo -e "${CYAN}🚀 启动 FlashSearch API 服务器...${NC}"

# 启动命令
# 确保端口参数正确传递
echo -e "${CYAN}📋 启动参数: HOST=$HOST PORT=$PORT LOG_LEVEL=$LOG_LEVEL WORKERS=$WORKERS${NC}"
START_CMD="python3 server/api/flash_search_api.py --host $HOST --port $PORT --log-level $LOG_LEVEL --workers $WORKERS"

# 后台启动
nohup $START_CMD > $LOG_FILE 2>&1 &
SERVER_PID=$!

# 保存PID
echo $SERVER_PID > .flashsearch_api.pid

echo -e "${GREEN}✅ 服务已启动 (PID: $SERVER_PID)${NC}"
echo -e "${CYAN}📋 日志文件: $LOG_FILE${NC}"

# 6. 健康检查
echo -e "${YELLOW}🔧 步骤6: 健康检查${NC}"

echo -e "${CYAN}⏳ 等待服务就绪...${NC}"
for i in {1..30}; do
    if curl -s -f "http://$HOST:$PORT/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 服务健康检查通过!${NC}"
        break
    fi
    echo -n "."
    sleep 1
    
    if [ $i -eq 30 ]; then
        echo -e "\n${RED}❌ 服务启动超时，检查日志: $LOG_FILE${NC}"
        exit 1
    fi
done

# 7. API测试
echo -e "${YELLOW}🔧 步骤7: API功能测试${NC}"

# 测试健康检查
echo -e "${CYAN}🏥 测试健康检查接口...${NC}"
HEALTH_RESPONSE=$(curl -s "http://$HOST:$PORT/health")
echo -e "${GREEN}✅ 健康检查响应: ${HEALTH_RESPONSE:0:50}...${NC}"

# 测试搜索模式
echo -e "${CYAN}🔍 测试搜索模式接口...${NC}"
MODES_RESPONSE=$(curl -s "http://$HOST:$PORT/modes" | python3 -c "import json,sys; data=json.load(sys.stdin); print(f\"默认模式: {data['default']}, 可用模式: {list(data['modes'].keys())}\")" 2>/dev/null || echo "API响应正常")
echo -e "${GREEN}✅ 搜索模式: $MODES_RESPONSE${NC}"

# 8. 部署信息总结
echo -e "${BLUE}=================================================${NC}"
echo -e "${GREEN}🎉 $PROJECT_NAME 部署完成!${NC}"
echo -e "${BLUE}=================================================${NC}"

echo -e "${CYAN}📊 部署信息:${NC}"
echo -e "   - 部署版本: $SCRIPT_VERSION"
echo -e "   - 部署时间: $DEPLOY_TIME"
echo -e "   - 进程PID: $SERVER_PID"
echo -e "   - 日志文件: $LOG_FILE"

echo -e "${CYAN}🔗 访问地址:${NC}"
echo -e "   - 服务地址: ${YELLOW}http://$HOST:$PORT${NC}"
echo -e "   - API文档: ${YELLOW}http://$HOST:$PORT/docs${NC}"
echo -e "   - 健康检查: ${YELLOW}http://$HOST:$PORT/health${NC}"
echo -e "   - 统计信息: ${YELLOW}http://$HOST:$PORT/stats${NC}"

echo -e "${CYAN}🛠️  支持的API接口:${NC}"
echo -e "   - 同步搜索: ${YELLOW}POST /search${NC}"
echo -e "   - 异步搜索: ${YELLOW}POST /search/async${NC}"
echo -e "   - 流式搜索: ${YELLOW}POST /search/stream${NC} ${GREEN}(SSE)${NC}"

echo -e "${CYAN}📋 快速测试命令:${NC}"
echo -e "${PURPLE}# 健康检查${NC}"
echo -e "curl http://$HOST:$PORT/health"
echo ""
echo -e "${PURPLE}# 同步搜索${NC}"
echo -e "curl -X POST \"http://$HOST:$PORT/search\" \\"
echo -e "  -H \"Content-Type: application/json\" \\"
echo -e "  -d '{\"query\": \"人工智能最新发展\", \"mode\": \"fast\"}'"
echo ""
echo -e "${PURPLE}# SSE流式搜索${NC}"
echo -e "curl -X POST \"http://$HOST:$PORT/search/stream\" \\"
echo -e "  -H \"Content-Type: application/json\" \\"
echo -e "  -H \"Accept: text/event-stream\" \\"
echo -e "  -d '{\"query\": \"量子计算应用\", \"mode\": \"fast\"}' \\"
echo -e "  --no-buffer"

echo -e "${CYAN}🔧 管理命令:${NC}"
echo -e "   - 查看日志: ${YELLOW}tail -f $LOG_FILE${NC}"
echo -e "   - 停止服务: ${YELLOW}kill $SERVER_PID${NC}"
echo -e "   - 重启服务: ${YELLOW}./0708-0130.sh $HOST $PORT $LOG_LEVEL $WORKERS${NC}"
echo -e "   - 查看进程: ${YELLOW}ps aux | grep $SERVER_PID${NC}"

echo -e "${CYAN}📈 监控建议:${NC}"
echo -e "   - 设置进程监控: systemd, supervisor 或 pm2"
echo -e "   - 配置日志轮转: logrotate"
echo -e "   - 监控API响应时间和成功率"
echo -e "   - 定期检查外部API密钥有效性"

echo -e "${BLUE}=================================================${NC}"
echo -e "${GREEN}✨ 部署脚本执行完成! 服务已就绪!${NC}"
echo -e "${BLUE}=================================================${NC}"

# 如果是开发模式，显示实时日志
if [ "$LOG_LEVEL" == "debug" ]; then
    echo -e "${YELLOW}🐛 Debug模式 - 显示实时日志 (Ctrl+C 退出):${NC}"
    tail -f $LOG_FILE
fi