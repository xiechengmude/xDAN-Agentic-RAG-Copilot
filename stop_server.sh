#!/bin/bash

# xDAN Rag Copilot 服务停止脚本

# 设置颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 停止指定进程
stop_process() {
    local process_name=$1
    local display_name=$2
    
    echo -e "${BLUE}正在停止 ${display_name}...${NC}"
    
    # 查找进程
    local pids=$(pgrep -f "$process_name")
    
    if [ -z "$pids" ]; then
        echo -e "${YELLOW}${display_name} 未运行${NC}"
        return
    fi
    
    # 尝试优雅停止
    kill $pids 2>/dev/null
    sleep 2
    
    # 检查是否仍在运行
    if pgrep -f "$process_name" > /dev/null; then
        echo -e "${YELLOW}正在强制停止 ${display_name}...${NC}"
        kill -9 $(pgrep -f "$process_name") 2>/dev/null
        sleep 1
    fi
    
    if ! pgrep -f "$process_name" > /dev/null; then
        echo -e "${GREEN}✅ ${display_name} 已停止${NC}"
    else
        echo -e "${RED}❌ 无法停止 ${display_name}${NC}"
    fi
}

# 停止前端服务
stop_frontend() {
    echo -e "${BLUE}正在停止前端服务...${NC}"
    
    # 查找占用5173或5174端口的进程
    local pids=$(lsof -ti:5173,5174 2>/dev/null)
    
    if [ -z "$pids" ]; then
        echo -e "${YELLOW}前端服务未运行${NC}"
        return
    fi
    
    # 停止进程
    echo $pids | xargs kill 2>/dev/null
    sleep 2
    
    # 检查是否仍在运行
    if [ -n "$(lsof -ti:5173,5174 2>/dev/null)" ]; then
        echo -e "${YELLOW}正在强制停止前端服务...${NC}"
        lsof -ti:5173,5174 | xargs kill -9 2>/dev/null
        sleep 1
    fi
    
    if [ -z "$(lsof -ti:5173,5174 2>/dev/null)" ]; then
        echo -e "${GREEN}✅ 前端服务已停止${NC}"
    else
        echo -e "${RED}❌ 无法停止前端服务${NC}"
    fi
}

# 主函数
main() {
    echo -e "${BLUE}=== 停止 xDAN Rag Copilot 服务 ===${NC}"
    echo
    
    # 停止所有服务
    stop_process "api_proxy.py" "API代理服务"
    stop_process "demo_server_simple.py" "搜索演示服务"
    stop_frontend
    
    echo
    echo -e "${GREEN}所有服务停止完成${NC}"
    
    # 清理PID文件（如果存在）
    rm -f .api_proxy.pid .demo_server.pid 2>/dev/null
}

# 执行主函数
main