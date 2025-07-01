#!/bin/bash

# FlashSearch 服务管理脚本 V2
# 兼容 docker compose (V2) 和 docker-compose (V1)

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函数：打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 检测Docker Compose命令
if command -v "docker compose" &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
    print_info "使用 Docker Compose V2"
elif command -v "docker-compose" &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    print_info "使用 Docker Compose V1"
else
    echo -e "${RED}[ERROR]${NC} 未找到 Docker Compose"
    echo "请安装 Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# 函数：检查服务健康状态
check_health() {
    local service=$1
    local url=$2
    local max_attempts=10
    local attempt=1
    
    print_info "检查 $service 服务健康状态..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            print_success "$service 服务已就绪!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    print_error "$service 服务启动失败或未响应"
    return 1
}

# 函数：启动本地服务（非Docker）
start_local() {
    print_info "启动本地服务..."
    
    # 检查Python环境
    if ! command -v python3 &> /dev/null; then
        print_error "未找到 Python3，请先安装"
        exit 1
    fi
    
    # 检查是否已有服务在运行
    if lsof -ti:8060 > /dev/null 2>&1; then
        print_warning "端口 8060 已被占用，可能API服务已在运行"
    else
        print_info "启动 API 服务 (端口 8060)..."
        cd server && nohup bash start_api_server.sh > ../api_server.log 2>&1 &
        cd ..
    fi
    
    if lsof -ti:9060 > /dev/null 2>&1; then
        print_warning "端口 9060 已被占用，可能MCP服务已在运行"
    else
        print_info "启动 MCP 服务 (端口 9060)..."
        cd server && nohup bash start_mcp_server.sh > ../mcp_server.log 2>&1 &
        cd ..
    fi
    
    sleep 3
    
    # 检查服务健康状态
    check_health "API" "http://localhost:8060/health"
    check_health "MCP" "http://localhost:9060/sse/"
    
    print_success "本地服务启动完成!"
    echo ""
    echo "访问地址:"
    echo "  - API文档: http://localhost:8060/docs"
    echo "  - API健康检查: http://localhost:8060/health"
    echo "  - MCP SSE: http://localhost:9060/sse/"
}

# 函数：启动Docker服务
start_docker() {
    print_info "启动Docker服务..."
    
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker未运行，请先启动Docker"
        exit 1
    fi
    
    print_info "使用命令: $DOCKER_COMPOSE"
    
    # 检查docker-compose文件是否存在
    if [ ! -f "docker-compose-dev.yml" ]; then
        print_error "未找到 docker-compose-dev.yml 文件"
        exit 1
    fi
    
    # 启动服务
    $DOCKER_COMPOSE -f docker-compose-dev.yml up -d api mcp
    
    sleep 5
    
    # 检查服务健康状态
    check_health "API" "http://localhost:8060/health"
    check_health "MCP" "http://localhost:9060/sse/"
    
    print_success "Docker服务启动完成!"
}

# 函数：使用Python直接启动（备选方案）
start_python() {
    print_info "使用Python直接启动服务..."
    
    # 检查依赖
    if [ ! -f "requirements.txt" ]; then
        print_error "未找到 requirements.txt"
        exit 1
    fi
    
    # 安装依赖
    print_info "检查Python依赖..."
    pip3 install -q -r requirements.txt
    
    # 启动API服务
    print_info "启动 API 服务..."
    cd server
    python3 -m uvicorn api.flash_search_api:app --host 0.0.0.0 --port 8060 --reload &
    API_PID=$!
    cd ..
    
    # 启动MCP服务
    print_info "启动 MCP 服务..."
    cd server
    python3 mcp/mira_flash_search.py --transport sse --host 0.0.0.0 --port 9060 &
    MCP_PID=$!
    cd ..
    
    print_success "服务已启动"
    echo "API PID: $API_PID"
    echo "MCP PID: $MCP_PID"
    
    # 保存PID以便后续停止
    echo $API_PID > .api.pid
    echo $MCP_PID > .mcp.pid
    
    sleep 3
    check_health "API" "http://localhost:8060/health"
    check_health "MCP" "http://localhost:9060/sse/"
}

# 函数：停止所有服务
stop_all() {
    print_info "停止所有服务..."
    
    # 停止本地服务
    if lsof -ti:8060 > /dev/null 2>&1; then
        print_info "停止API服务..."
        kill -9 $(lsof -ti:8060) 2>/dev/null || true
    fi
    
    if lsof -ti:9060 > /dev/null 2>&1; then
        print_info "停止MCP服务..."
        kill -9 $(lsof -ti:9060) 2>/dev/null || true
    fi
    
    # 清理PID文件
    rm -f .api.pid .mcp.pid
    
    # 停止Docker服务
    if [ -f "docker-compose-dev.yml" ] && docker ps -q 2>/dev/null | grep -q .; then
        print_info "停止Docker服务..."
        $DOCKER_COMPOSE -f docker-compose-dev.yml down || true
    fi
    
    print_success "所有服务已停止!"
}

# 函数：查看服务状态
status() {
    print_info "服务状态:"
    echo ""
    
    # 检查API服务
    if lsof -ti:8060 > /dev/null 2>&1; then
        echo -e "  API服务 (8060): ${GREEN}运行中${NC}"
        if curl -s -f "http://localhost:8060/health" > /dev/null 2>&1; then
            echo -e "    健康状态: ${GREEN}正常${NC}"
        else
            echo -e "    健康状态: ${RED}异常${NC}"
        fi
    else
        echo -e "  API服务 (8060): ${RED}未运行${NC}"
    fi
    
    # 检查MCP服务
    if lsof -ti:9060 > /dev/null 2>&1; then
        echo -e "  MCP服务 (9060): ${GREEN}运行中${NC}"
    else
        echo -e "  MCP服务 (9060): ${RED}未运行${NC}"
    fi
    
    # 检查Docker服务
    if [ -f "docker-compose-dev.yml" ]; then
        echo ""
        echo "Docker 容器状态:"
        $DOCKER_COMPOSE -f docker-compose-dev.yml ps 2>/dev/null || echo "  无运行中的容器"
    fi
    
    echo ""
}

# 函数：查看日志
logs() {
    local service=$1
    
    case $service in
        api)
            if [ -f api_server.log ]; then
                tail -f api_server.log
            elif [ -f "docker-compose-dev.yml" ]; then
                $DOCKER_COMPOSE -f docker-compose-dev.yml logs -f api
            else
                print_error "未找到API日志"
            fi
            ;;
        mcp)
            if [ -f mcp_server.log ]; then
                tail -f mcp_server.log
            elif [ -f "docker-compose-dev.yml" ]; then
                $DOCKER_COMPOSE -f docker-compose-dev.yml logs -f mcp
            else
                print_error "未找到MCP日志"
            fi
            ;;
        all|docker)
            if [ -f "docker-compose-dev.yml" ]; then
                $DOCKER_COMPOSE -f docker-compose-dev.yml logs -f
            else
                print_error "未找到Docker配置"
            fi
            ;;
        *)
            print_error "未知服务: $service"
            echo "可用选项: api, mcp, all"
            ;;
    esac
}

# 主菜单
case "${1:-help}" in
    start-local)
        start_local
        ;;
    start-docker)
        start_docker
        ;;
    start-python)
        start_python
        ;;
    stop)
        stop_all
        ;;
    status)
        status
        ;;
    logs)
        logs "${2:-all}"
        ;;
    help|*)
        echo "FlashSearch 服务管理工具 V2"
        echo ""
        echo "用法: $0 [命令] [选项]"
        echo ""
        echo "命令:"
        echo "  start-local  - 启动本地服务（使用shell脚本）"
        echo "  start-docker - 使用Docker启动服务"
        echo "  start-python - 直接使用Python启动（备选）"
        echo "  stop         - 停止所有服务"
        echo "  status       - 查看服务状态"
        echo "  logs [服务]  - 查看日志 (api/mcp/all)"
        echo "  help         - 显示此帮助信息"
        echo ""
        echo "示例:"
        echo "  $0 start-local     # 启动本地服务"
        echo "  $0 start-docker    # 使用Docker启动"
        echo "  $0 start-python    # Python直接启动"
        echo "  $0 status          # 查看状态"
        echo "  $0 logs api        # 查看API日志"
        echo ""
        echo "Docker Compose版本: $DOCKER_COMPOSE"
        ;;
esac