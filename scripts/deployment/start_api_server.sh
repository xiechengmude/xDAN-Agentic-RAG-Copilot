#!/bin/bash

# xDAN Rag Copilot API服务管理脚本
# 适配重构后的新架构

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 服务信息
SERVICE_NAME="xDAN Rag Copilot API Service"
SERVICE_PORT=8050
SERVICE_MODULE="src.api.server"
PID_FILE="data/api_server.pid"

# 创建必要目录
mkdir -p logs data

# 检查服务是否运行
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
        fi
    fi
    
    # 检查端口
    if lsof -i:$SERVICE_PORT > /dev/null 2>&1; then
        return 0
    fi
    
    return 1
}

# 获取Python命令
get_python_cmd() {
    if command -v uv &> /dev/null && [ -d ".venv" ]; then
        echo "uv run python"
    elif [ -f "venv/bin/python" ]; then
        echo "venv/bin/python"
    elif [ -f ".venv/bin/python" ]; then
        echo ".venv/bin/python"
    else
        echo "python"
    fi
}

# 启动服务
start_service() {
    if is_running; then
        echo -e "${YELLOW}$SERVICE_NAME 已经在运行${NC}"
        return 1
    fi
    
    echo -e "${BLUE}启动 $SERVICE_NAME...${NC}"
    
    PYTHON_CMD=$(get_python_cmd)
    
    # 后台启动服务
    nohup $PYTHON_CMD -m $SERVICE_MODULE > logs/api_server.log 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"
    
    # 等待服务启动
    echo -n "等待服务启动"
    for i in {1..10}; do
        sleep 1
        echo -n "."
        if curl -s http://localhost:$SERVICE_PORT/health > /dev/null 2>&1; then
            echo
            echo -e "${GREEN}✅ $SERVICE_NAME 启动成功${NC}"
            echo -e "${GREEN}API文档: http://localhost:$SERVICE_PORT/docs${NC}"
            echo -e "${GREEN}健康检查: http://localhost:$SERVICE_PORT/health${NC}"
            return 0
        fi
    done
    
    echo
    echo -e "${RED}❌ 服务启动失败，请查看日志: logs/api_server.log${NC}"
    return 1
}

# 停止服务
stop_service() {
    if ! is_running; then
        echo -e "${YELLOW}$SERVICE_NAME 未在运行${NC}"
        return 1
    fi
    
    echo -e "${BLUE}停止 $SERVICE_NAME...${NC}"
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        kill $PID 2>/dev/null
        
        # 等待进程结束
        for i in {1..5}; do
            if ! ps -p "$PID" > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done
        
        # 强制结束
        if ps -p "$PID" > /dev/null 2>&1; then
            kill -9 $PID 2>/dev/null
        fi
        
        rm -f "$PID_FILE"
    fi
    
    # 清理端口占用
    PID=$(lsof -ti:$SERVICE_PORT)
    if [ -n "$PID" ]; then
        kill -9 $PID 2>/dev/null
    fi
    
    echo -e "${GREEN}✅ $SERVICE_NAME 已停止${NC}"
}

# 查看状态
show_status() {
    if is_running; then
        echo -e "${GREEN}● $SERVICE_NAME 正在运行${NC}"
        
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            echo "  PID: $PID"
        fi
        
        echo "  端口: $SERVICE_PORT"
        echo "  API文档: http://localhost:$SERVICE_PORT/docs"
        
        # 检查健康状态
        if curl -s http://localhost:$SERVICE_PORT/health > /dev/null 2>&1; then
            HEALTH=$(curl -s http://localhost:$SERVICE_PORT/health)
            echo "  健康状态: ✅ 正常"
        else
            echo "  健康状态: ⚠️  无法连接"
        fi
    else
        echo -e "${RED}● $SERVICE_NAME 未运行${NC}"
    fi
}

# 查看日志
show_logs() {
    if [ -f "logs/api_server.log" ]; then
        echo -e "${BLUE}=== 最近的日志 ===${NC}"
        tail -n 50 logs/api_server.log
        echo
        echo -e "${YELLOW}提示: 使用 'tail -f logs/api_server.log' 实时查看日志${NC}"
    else
        echo -e "${YELLOW}日志文件不存在${NC}"
    fi
}

# 重启服务
restart_service() {
    stop_service
    sleep 2
    start_service
}

# 主函数
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "使用方法: $0 {start|stop|restart|status|logs}"
        echo
        echo "命令说明:"
        echo "  start   - 启动API服务"
        echo "  stop    - 停止API服务"
        echo "  restart - 重启API服务"
        echo "  status  - 查看服务状态"
        echo "  logs    - 查看服务日志"
        exit 1
        ;;
esac