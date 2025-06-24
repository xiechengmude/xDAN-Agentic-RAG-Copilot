#!/bin/bash

# 搜索可视化服务启动脚本（包含API和前端）

# 设置颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查API服务是否已在运行
check_api_running() {
    if pgrep -f "ragflow_search_server.py" > /dev/null || pgrep -f "xdan_rag_server.py" > /dev/null; then
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

# 停止API服务
stop_api_service() {
    echo "正在停止API服务..."
    pkill -f "ragflow_search_server.py"
    pkill -f "xdan_rag_server.py"
    sleep 2
    if check_api_running; then
        echo -e "${RED}API服务停止失败，尝试强制停止...${NC}"
        pkill -9 -f "ragflow_search_server.py"
        pkill -9 -f "xdan_rag_server.py"
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

# 启动API服务
start_api_service() {
    echo -e "${BLUE}正在启动搜索可视化API服务...${NC}"
    
    # 确保日志目录存在
    mkdir -p logs
    
    # 检查是否有参数指定使用新版
    if [ "$1" = "--new" ] || [ "$USE_NEW_API" = "true" ]; then
        echo -e "${BLUE}使用xDAN RAG主服务器${NC}"
        nohup uv run python xdan_rag_server.py > logs/xdan_rag_server_$(date +%Y%m%d_%H%M%S).log 2>&1 &
    else
        echo -e "${BLUE}使用RAGFlow搜索服务器${NC}"
        nohup uv run python ragflow_search_server.py > logs/ragflow_search_server_$(date +%Y%m%d_%H%M%S).log 2>&1 &
    fi
    
    # 等待服务启动
    sleep 3
    
    # 检查服务是否成功启动
    if check_api_running; then
        echo -e "${GREEN}✅ API服务启动成功！${NC}"
        echo -e "${GREEN}API访问地址: http://localhost:8050${NC}"
        echo -e "${GREEN}API文档: http://localhost:8050/docs${NC}"
    else
        echo -e "${RED}❌ API服务启动失败，请检查日志文件${NC}"
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
        # 检查API服务
        if check_api_running; then
            echo -e "${RED}API服务已在运行中${NC}"
        else
            start_api_service
        fi
        
        # 检查前端服务
        if check_frontend_running; then
            echo -e "${RED}前端服务已在运行中${NC}"
        else
            start_frontend_service
        fi
        ;;
    stop)
        # 停止两个服务
        stop_api_service
        stop_frontend_service
        echo -e "${GREEN}所有服务已停止${NC}"
        ;;
    restart)
        # 重启两个服务
        stop_api_service
        stop_frontend_service
        start_api_service
        start_frontend_service
        ;;
    status)
        echo -e "${BLUE}=== 服务状态 ===${NC}"
        
        # API服务状态
        if check_api_running; then
            echo -e "${GREEN}✅ API服务正在运行${NC}"
            ps aux | grep -E "(ragflow_search_server|xdan_rag_server).py" | grep -v grep | head -1
        else
            echo -e "${RED}❌ API服务未运行${NC}"
        fi
        
        echo ""
        
        # 前端服务状态
        if check_frontend_running; then
            echo -e "${GREEN}✅ 前端服务正在运行${NC}"
            # 显示前端服务端口信息
            lsof -i:5173,5174 | grep LISTEN | head -1
        else
            echo -e "${RED}❌ 前端服务未运行${NC}"
        fi
        ;;
    api)
        # 仅管理API服务
        case "$2" in
            start)
                if check_api_running; then
                    echo -e "${RED}API服务已在运行中${NC}"
                else
                    start_api_service "$3"
                fi
                ;;
            stop)
                stop_api_service
                ;;
            restart)
                stop_api_service
                start_api_service
                ;;
            *)
                echo "使用方法: $0 api {start|stop|restart}"
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
        echo "使用方法: $0 {start|stop|restart|status|api|frontend}"
        echo "  start    - 启动所有服务（API和前端）"
        echo "  stop     - 停止所有服务"
        echo "  restart  - 重启所有服务"
        echo "  status   - 查看所有服务状态"
        echo "  api      - 管理API服务 (start|stop|restart)"
        echo "  frontend - 管理前端服务 (start|stop|restart)"
        echo ""
        echo "选项:"
        echo "  --new    - 使用xDAN RAG主服务器（默认使用RAGFlow搜索服务器）"
        echo ""
        echo "示例:"
        echo "  $0 start              # 启动所有服务"
        echo "  $0 api start --new    # 启动新版API服务"
        echo "  $0 api stop           # 仅停止API服务"
        echo "  $0 frontend restart   # 仅重启前端服务"
        exit 1
        ;;
esac