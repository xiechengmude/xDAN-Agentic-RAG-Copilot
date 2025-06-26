#!/bin/bash

# xDAN Rag Copilot 服务启动脚本
# 支持启动API代理服务、搜索演示服务和前端服务

# 设置颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查RAG API服务是否已在运行
check_api_running() {
    if pgrep -f "src/api/server.py" > /dev/null || pgrep -f "uvicorn.*main:app" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# 检查搜索演示服务是否已在运行
check_demo_running() {
    if pgrep -f "demo_server_simple.py" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# 检查前端服务是否已在运行
check_frontend_running() {
    if lsof -i:5173 > /dev/null 2>&1 || lsof -i:5174 > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 停止RAG API服务
stop_api_service() {
    echo "正在停止RAG API服务..."
    pkill -f "src/api/server.py"
    pkill -f "uvicorn.*main:app"
    sleep 2
    if check_api_running; then
        echo -e "${RED}RAG API服务停止失败，尝试强制停止...${NC}"
        pkill -9 -f "src/api/server.py"
        pkill -9 -f "uvicorn.*main:app"
        sleep 1
    fi
}

# 停止搜索演示服务
stop_demo_service() {
    echo "正在停止搜索演示服务..."
    pkill -f "demo_server_simple.py"
    sleep 2
    if check_demo_running; then
        echo -e "${RED}搜索演示服务停止失败，尝试强制停止...${NC}"
        pkill -9 -f "demo_server_simple.py"
        sleep 1
    fi
}

# 停止前端服务
stop_frontend_service() {
    echo "正在停止前端服务..."
    # 查找并停止占用5173或5174端口的进程
    lsof -ti:5173 | xargs kill 2>/dev/null
    lsof -ti:5174 | xargs kill 2>/dev/null
    sleep 2
}

# 启动RAG API服务
start_api_service() {
    echo -e "${BLUE}正在启动xDAN RAG Copilot API Service v2.0...${NC}"
    
    # 确保日志目录存在
    mkdir -p logs
    
    # 检查并激活虚拟环境
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    elif [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo -e "${YELLOW}未找到虚拟环境，使用系统Python${NC}"
    fi
    
    # 检查Python模块路径
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    
    # 启动新架构的API服务
    nohup uvicorn src.api.server:app --host 0.0.0.0 --port 8050 --log-level info > logs/api_server_$(date +%Y%m%d_%H%M%S).log 2>&1 &
    
    # 等待服务启动
    sleep 5
    
    # 检查服务是否成功启动
    if check_api_running; then
        echo -e "${GREEN}✅ RAG API服务启动成功！${NC}"
        echo -e "${GREEN}API访问地址: http://localhost:8050${NC}"
        echo -e "${GREEN}API文档: http://localhost:8050/docs${NC}"
        echo -e "${GREEN}健康检查: http://localhost:8050/health${NC}"
    else
        echo -e "${RED}❌ RAG API服务启动失败，请检查日志文件${NC}"
        echo -e "${YELLOW}最新日志：${NC}"
        tail -10 logs/api_server_*.log 2>/dev/null || echo "无法读取日志文件"
        return 1
    fi
}

# 启动搜索演示服务
start_demo_service() {
    echo -e "${BLUE}正在启动搜索演示服务...${NC}"
    
    # 确保日志目录存在
    mkdir -p logs
    
    # 检查并激活虚拟环境
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    elif [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo -e "${YELLOW}未找到虚拟环境，使用系统Python${NC}"
    fi
    
    nohup python3 demo_server_simple.py > logs/demo_server_$(date +%Y%m%d_%H%M%S).log 2>&1 &
    
    # 等待服务启动
    sleep 3
    
    # 检查服务是否成功启动
    if check_demo_running; then
        echo -e "${GREEN}✅ 搜索演示服务启动成功！${NC}"
        echo -e "${GREEN}演示访问地址: http://localhost:8051${NC}"
    else
        echo -e "${RED}❌ 搜索演示服务启动失败，请检查日志文件${NC}"
        return 1
    fi
}

# 启动前端服务
start_frontend_service() {
    echo -e "${BLUE}正在启动前端服务...${NC}"
    
    # 确保日志目录存在
    mkdir -p logs
    
    # 进入前端目录并启动
    cd frontend
    
    # 检查是否需要安装依赖
    if [ ! -d "node_modules" ]; then
        echo "正在安装前端依赖..."
        npm install
    fi
    
    # 启动前端服务
    nohup npm run dev > ../logs/frontend_$(date +%Y%m%d_%H%M%S).log 2>&1 &
    cd ..
    
    # 等待服务启动
    sleep 3
    
    # 检查服务是否成功启动
    if check_frontend_running; then
        echo -e "${GREEN}✅ 前端服务启动成功！${NC}"
        # 从日志中获取实际端口
        FRONTEND_PORT=$(grep -h "Local:" logs/frontend_*.log | tail -1 | grep -o ":[0-9]*" | grep -o "[0-9]*" | head -1)
        echo -e "${GREEN}前端访问地址: http://localhost:${FRONTEND_PORT}/app/${NC}"
    else
        echo -e "${RED}❌ 前端服务启动失败，请检查日志文件${NC}"
        return 1
    fi
}

# 主逻辑
case "$1" in
    start)
        echo -e "${BLUE}=== 启动 xDAN Rag Copilot 服务 ===${NC}"
        
        # 检查RAG API服务
        if check_api_running; then
            echo -e "${YELLOW}RAG API服务已在运行中${NC}"
        else
            start_api_service
        fi
        
        # 询问是否启动搜索演示
        read -p "是否启动搜索演示服务？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if check_demo_running; then
                echo -e "${YELLOW}搜索演示服务已在运行中${NC}"
            else
                start_demo_service
            fi
        fi
        
        # 询问是否启动前端
        read -p "是否启动前端开发服务？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if check_frontend_running; then
                echo -e "${YELLOW}前端服务已在运行中${NC}"
            else
                start_frontend_service
            fi
        fi
        ;;
    stop)
        # 停止所有服务
        stop_api_service
        stop_demo_service
        stop_frontend_service
        echo -e "${GREEN}所有服务已停止${NC}"
        ;;
    restart)
        # 重启所有服务
        stop_api_service
        stop_demo_service
        stop_frontend_service
        sleep 2
        start_api_service
        
        read -p "是否重启搜索演示服务？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            start_demo_service
        fi
        
        read -p "是否重启前端服务？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            start_frontend_service
        fi
        ;;
    status)
        echo -e "${BLUE}=== 服务状态 ===${NC}"
        echo
        
        # RAG API服务状态
        echo -e "${BLUE}[RAG API服务]${NC}"
        if check_api_running; then
            echo -e "${GREEN}✅ 运行中${NC} - http://localhost:8050"
            ps aux | grep -E "(src/api/server.py|uvicorn.*main:app)" | grep -v grep | head -1
        else
            echo -e "${RED}❌ 未运行${NC}"
        fi
        
        echo
        
        # 搜索演示服务状态
        echo -e "${BLUE}[搜索演示服务]${NC}"
        if check_demo_running; then
            echo -e "${GREEN}✅ 运行中${NC} - http://localhost:8051"
            ps aux | grep demo_server_simple.py | grep -v grep | head -1
        else
            echo -e "${RED}❌ 未运行${NC}"
        fi
        
        echo
        
        # 前端服务状态
        echo -e "${BLUE}[前端服务]${NC}"
        if check_frontend_running; then
            echo -e "${GREEN}✅ 运行中${NC}"
            # 显示前端服务端口信息
            lsof -i:5173,5174 | grep LISTEN | head -1
        else
            echo -e "${RED}❌ 未运行${NC}"
        fi
        ;;
    api)
        # 仅管理RAG API服务
        case "$2" in
            start)
                if check_api_running; then
                    echo -e "${RED}RAG API服务已在运行中${NC}"
                else
                    start_api_service
                fi
                ;;
            stop)
                stop_api_service
                ;;
            restart)
                stop_api_service
                sleep 2
                start_api_service
                ;;
            *)
                echo "使用方法: $0 api {start|stop|restart}"
                ;;
        esac
        ;;
    demo)
        # 仅管理搜索演示服务
        case "$2" in
            start)
                if check_demo_running; then
                    echo -e "${RED}搜索演示服务已在运行中${NC}"
                else
                    start_demo_service
                fi
                ;;
            stop)
                stop_demo_service
                ;;
            restart)
                stop_demo_service
                sleep 2
                start_demo_service
                ;;
            *)
                echo "使用方法: $0 demo {start|stop|restart}"
                ;;
        esac
        ;;
    frontend)
        # 仅管理前端服务
        case "$2" in
            start)
                if check_frontend_running; then
                    echo -e "${RED}前端服务已在运行中${NC}"
                else
                    start_frontend_service
                fi
                ;;
            stop)
                stop_frontend_service
                ;;
            restart)
                stop_frontend_service
                start_frontend_service
                ;;
            *)
                echo "使用方法: $0 frontend {start|stop|restart}"
                ;;
        esac
        ;;
    *)
        echo -e "${BLUE}=== xDAN RAG Copilot 服务管理脚本 v2.0 ===${NC}"
        echo "使用方法: $0 {start|stop|restart|status|api|demo|frontend}"
        echo ""
        echo "命令说明:"
        echo "  start      - 启动所有服务（会询问是否启动可选服务）"
        echo "  stop       - 停止所有服务"
        echo "  restart    - 重启所有服务"
        echo "  status     - 查看所有服务状态"
        echo "  api        - 管理RAG API服务 (start|stop|restart)"
        echo "  demo       - 管理搜索演示服务 (start|stop|restart)"
        echo "  frontend   - 管理前端服务 (start|stop|restart)"
        echo ""
        echo "示例:"
        echo "  $0 start                  # 启动服务（交互式）"
        echo "  $0 api start              # 仅启动RAG API服务"
        echo "  $0 demo stop              # 仅停止搜索演示服务"
        echo "  $0 frontend restart       # 仅重启前端服务"
        echo "  $0 status                 # 查看所有服务状态"
        exit 1
        ;;
esac