#!/bin/bash

# 部署检查脚本
# 检查所有组件是否正确配置和可访问

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=== xDAN Rag Copilot 部署检查 ===${NC}"
echo

ISSUES=0

# 1. 检查Python版本
echo -e "${BLUE}1. 检查Python环境${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo -e "   ${GREEN}✅ $PYTHON_VERSION${NC}"
else
    echo -e "   ${RED}❌ Python未安装${NC}"
    ((ISSUES++))
fi

# 2. 检查虚拟环境
echo -e "${BLUE}2. 检查虚拟环境${NC}"
if [ -d ".venv" ] || [ -d "venv" ]; then
    echo -e "   ${GREEN}✅ 虚拟环境已创建${NC}"
else
    echo -e "   ${YELLOW}⚠️  虚拟环境未创建${NC}"
    ((ISSUES++))
fi

# 3. 检查配置文件
echo -e "${BLUE}3. 检查配置文件${NC}"
if [ -f "config.yaml" ]; then
    echo -e "   ${GREEN}✅ config.yaml 存在${NC}"
else
    echo -e "   ${RED}❌ config.yaml 不存在${NC}"
    ((ISSUES++))
fi

if [ -f ".env" ]; then
    echo -e "   ${GREEN}✅ .env 存在${NC}"
else
    echo -e "   ${YELLOW}⚠️  .env 不存在（可选）${NC}"
fi

# 4. 检查必要目录
echo -e "${BLUE}4. 检查目录结构${NC}"
REQUIRED_DIRS=("src" "src/api" "src/core" "src/clients" "src/services" "logs" "data")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "   ${GREEN}✅ $dir/${NC}"
    else
        echo -e "   ${RED}❌ $dir/ 不存在${NC}"
        ((ISSUES++))
    fi
done

# 5. 检查关键文件
echo -e "${BLUE}5. 检查关键文件${NC}"
KEY_FILES=(
    "src/api/server.py"
    "src/core/s3_framework.py"
    "src/services/s3_service.py"
    "src/clients/litellm_client.py"
    "src/clients/ragflow_client.py"
)
for file in "${KEY_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "   ${GREEN}✅ $file${NC}"
    else
        echo -e "   ${RED}❌ $file 不存在${NC}"
        ((ISSUES++))
    fi
done

# 6. 检查服务连接
echo -e "${BLUE}6. 检查外部服务连接${NC}"

# 检查RAGFlow
if [ -f "config.yaml" ]; then
    RAGFLOW_URL=$(grep -A2 "ragflow:" config.yaml | grep "api_url:" | awk '{print $2}' | tr -d '"' | sed 's/${.*://' | sed 's/}$//')
    if [ -z "$RAGFLOW_URL" ] && [ -f ".env" ]; then
        RAGFLOW_URL=$(grep "RAGFLOW_API_URL=" .env | cut -d'=' -f2)
    fi
    
    if [ -n "$RAGFLOW_URL" ]; then
        echo -n "   检查RAGFlow ($RAGFLOW_URL)... "
        if curl -s --max-time 5 "$RAGFLOW_URL" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 可访问${NC}"
        else
            echo -e "${RED}❌ 无法访问${NC}"
            ((ISSUES++))
        fi
    else
        echo -e "   ${YELLOW}⚠️  未配置RAGFlow URL${NC}"
    fi
fi

# 检查本地API服务
echo -n "   检查本地API服务 (localhost:8050)... "
if curl -s --max-time 2 http://localhost:8050/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 运行中${NC}"
else
    echo -e "${YELLOW}⚠️  未运行${NC}"
fi

# 7. 检查Python依赖
echo -e "${BLUE}7. 检查Python依赖${NC}"
if [ -f "requirements.txt" ]; then
    echo -e "   ${GREEN}✅ requirements.txt 存在${NC}"
    
    # 激活虚拟环境并检查关键包
    if [ -d ".venv" ]; then
        source .venv/bin/activate 2>/dev/null
    elif [ -d "venv" ]; then
        source venv/bin/activate 2>/dev/null
    fi
    
    # 检查关键包
    PACKAGES=("fastapi" "uvicorn" "httpx" "litellm")
    for pkg in "${PACKAGES[@]}"; do
        if python -c "import $pkg" 2>/dev/null; then
            echo -e "   ${GREEN}✅ $pkg 已安装${NC}"
        else
            echo -e "   ${RED}❌ $pkg 未安装${NC}"
            ((ISSUES++))
        fi
    done
else
    echo -e "   ${RED}❌ requirements.txt 不存在${NC}"
    ((ISSUES++))
fi

# 8. 总结
echo
echo -e "${BLUE}=== 检查结果 ===${NC}"
if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✅ 所有检查通过！系统已准备就绪。${NC}"
    echo
    echo "启动服务："
    echo "  ./start_api_server.sh start"
    echo "或"
    echo "  uv run python -m src.api.server"
else
    echo -e "${RED}❌ 发现 $ISSUES 个问题需要解决${NC}"
    echo
    echo "建议操作："
    if [ ! -f "config.yaml" ]; then
        echo "  1. 复制配置文件: cp config.example.yaml config.yaml"
    fi
    if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
        echo "  2. 创建虚拟环境: python3 -m venv venv"
    fi
    echo "  3. 安装依赖: pip install -r requirements.txt"
    echo "  4. 检查外部服务连接"
fi

echo
echo -e "${BLUE}查看详细文档: DEPLOYMENT_GUIDE_V2.md${NC}"