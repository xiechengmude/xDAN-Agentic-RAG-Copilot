#!/bin/bash

# 远程服务器快速部署脚本
# 适用于使用 uv 工具的环境

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=== xDAN Rag Copilot 远程部署脚本 ===${NC}"
echo

# 1. 检查是否已安装 uv
if command -v uv &> /dev/null; then
    echo -e "${GREEN}✅ 检测到 uv 工具${NC}"
else
    echo -e "${YELLOW}未检测到 uv，尝试使用 pip...${NC}"
    USE_PIP=true
fi

# 2. 创建虚拟环境
if [ -z "$USE_PIP" ]; then
    # 使用 uv
    if [ ! -d ".venv" ]; then
        echo -e "${BLUE}创建虚拟环境...${NC}"
        uv venv
    fi
    
    # 激活虚拟环境
    source .venv/bin/activate
    
    # 安装依赖
    echo -e "${BLUE}安装依赖...${NC}"
    uv pip install -r requirements.txt
    uv pip install httpx python-multipart
else
    # 使用传统 pip
    if [ ! -d "venv" ]; then
        echo -e "${BLUE}创建虚拟环境...${NC}"
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 安装依赖
    echo -e "${BLUE}安装依赖...${NC}"
    pip install -r requirements.txt
    pip install httpx python-multipart
fi

# 3. 创建必要目录
echo -e "${BLUE}创建必要目录...${NC}"
mkdir -p logs
mkdir -p data

# 4. 检查配置文件
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}已创建 .env 文件，请编辑配置${NC}"
    else
        echo -e "${RED}警告：未找到 .env 文件${NC}"
    fi
fi

# 5. 设置权限
echo -e "${BLUE}设置执行权限...${NC}"
chmod +x start_server.sh stop_server.sh

echo
echo -e "${GREEN}=== 部署完成 ===${NC}"
echo
echo "下一步操作："
echo "1. 编辑 .env 文件配置 API 密钥"
echo "2. 运行 ./start_server.sh start 启动服务"
echo "3. 使用 ./start_server.sh status 查看状态"
echo
echo "API文档地址: http://$(hostname -I | awk '{print $1}'):8001/docs"