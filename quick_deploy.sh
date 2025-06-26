#!/bin/bash

# 快速部署脚本 - 适用于重构后的架构
# 支持本地和远程部署

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=== xDAN Rag Copilot 快速部署脚本 ===${NC}"
echo

# 检查命令是否存在
command_exists() {
    command -v "$1" &> /dev/null
}

# 1. 检查Python版本
echo -e "${BLUE}检查Python环境...${NC}"
if command_exists python3.11; then
    PYTHON_CMD="python3.11"
elif command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ $(echo "$PYTHON_VERSION >= 3.11" | bc) -eq 1 ]]; then
        PYTHON_CMD="python3"
    else
        echo -e "${RED}❌ 需要Python 3.11或更高版本${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ 未找到Python 3${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python版本: $($PYTHON_CMD --version)${NC}"

# 2. 检查并安装uv（如果需要）
if command_exists uv; then
    echo -e "${GREEN}✅ 检测到uv工具${NC}"
    USE_UV=true
else
    echo -e "${YELLOW}未检测到uv工具...${NC}"
    read -p "是否安装uv（推荐）？[Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        echo -e "${BLUE}安装uv...${NC}"
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.cargo/env
        USE_UV=true
    else
        USE_UV=false
    fi
fi

# 3. 创建配置文件
echo -e "${BLUE}检查配置文件...${NC}"
if [ ! -f "config.yaml" ]; then
    if [ -f "config.example.yaml" ]; then
        cp config.example.yaml config.yaml
        echo -e "${YELLOW}已创建config.yaml，请编辑配置${NC}"
        CONFIG_CREATED=true
    else
        echo -e "${RED}❌ 未找到config.example.yaml${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ config.yaml已存在${NC}"
fi

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}已创建.env，请设置必要的环境变量${NC}"
        ENV_CREATED=true
    fi
fi

# 4. 安装依赖
echo -e "${BLUE}安装Python依赖...${NC}"
if [ "$USE_UV" = true ]; then
    # 使用uv
    if [ ! -d ".venv" ]; then
        uv venv
    fi
    source .venv/bin/activate
    uv pip install -r requirements.txt
else
    # 使用pip
    if [ ! -d "venv" ]; then
        $PYTHON_CMD -m venv venv
    fi
    source venv/bin/activate
    pip install -r requirements.txt
fi

# 5. 创建必要目录
echo -e "${BLUE}创建必要目录...${NC}"
mkdir -p logs data

# 6. 数据库初始化（如果需要）
if [ ! -f "data/chat.db" ]; then
    echo -e "${BLUE}初始化数据库...${NC}"
    # 数据库会在首次启动时自动创建
fi

# 7. 提示配置
if [ "$CONFIG_CREATED" = true ] || [ "$ENV_CREATED" = true ]; then
    echo
    echo -e "${YELLOW}=== 配置提醒 ===${NC}"
    echo "请编辑以下文件设置必要的配置："
    [ "$CONFIG_CREATED" = true ] && echo "  - config.yaml: RAGFlow和LLM配置"
    [ "$ENV_CREATED" = true ] && echo "  - .env: API密钥等敏感信息"
    echo
    echo "配置完成后，运行以下命令启动服务："
    if [ "$USE_UV" = true ]; then
        echo -e "${GREEN}uv run python -m src.api.server${NC}"
    else
        echo -e "${GREEN}python -m src.api.server${NC}"
    fi
else
    # 8. 可选：立即启动服务
    echo
    read -p "是否立即启动API服务？[Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        echo -e "${BLUE}启动API服务...${NC}"
        if [ "$USE_UV" = true ]; then
            echo -e "${GREEN}运行命令: uv run python -m src.api.server${NC}"
            echo
            echo "服务启动中..."
            echo "API文档: http://localhost:8050/docs"
            echo "健康检查: http://localhost:8050/health"
            echo
            echo "按 Ctrl+C 停止服务"
            uv run python -m src.api.server
        else
            echo -e "${GREEN}运行命令: python -m src.api.server${NC}"
            echo
            echo "服务启动中..."
            echo "API文档: http://localhost:8050/docs"
            echo "健康检查: http://localhost:8050/health"
            echo
            echo "按 Ctrl+C 停止服务"
            python -m src.api.server
        fi
    else
        echo
        echo -e "${GREEN}=== 部署完成 ===${NC}"
        echo
        echo "启动服务命令："
        if [ "$USE_UV" = true ]; then
            echo "  uv run python -m src.api.server"
        else
            echo "  python -m src.api.server"
        fi
        echo
        echo "服务地址："
        echo "  API文档: http://localhost:8050/docs"
        echo "  健康检查: http://localhost:8050/health"
    fi
fi