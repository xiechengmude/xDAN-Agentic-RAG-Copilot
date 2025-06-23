#!/bin/bash

# xDAN Rag Copilot 诊断脚本
# 用于快速诊断部署和运行问题

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== xDAN Rag Copilot 诊断工具 ===${NC}"
echo

# 1. 检查Python环境
echo -e "${BLUE}[1] Python环境检查${NC}"
echo -n "Python3: "
if command -v python3 &> /dev/null; then
    python3 --version
else
    echo -e "${RED}未找到${NC}"
fi

echo -n "Pip: "
if command -v pip3 &> /dev/null; then
    pip3 --version
elif command -v pip &> /dev/null; then
    pip --version
else
    echo -e "${RED}未找到${NC}"
fi

# 2. 检查虚拟环境
echo
echo -e "${BLUE}[2] 虚拟环境检查${NC}"
if [ -d ".venv" ]; then
    echo -e "${GREEN}✓ 找到 .venv 目录${NC}"
    if [ -f ".venv/bin/activate" ]; then
        echo -e "${GREEN}✓ 虚拟环境可用${NC}"
    else
        echo -e "${RED}✗ 虚拟环境损坏${NC}"
    fi
elif [ -d "venv" ]; then
    echo -e "${GREEN}✓ 找到 venv 目录${NC}"
    if [ -f "venv/bin/activate" ]; then
        echo -e "${GREEN}✓ 虚拟环境可用${NC}"
    else
        echo -e "${RED}✗ 虚拟环境损坏${NC}"
    fi
else
    echo -e "${RED}✗ 未找到虚拟环境${NC}"
fi

# 3. 检查依赖
echo
echo -e "${BLUE}[3] 依赖检查${NC}"

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate 2>/dev/null
elif [ -d "venv" ]; then
    source venv/bin/activate 2>/dev/null
fi

# 检查关键包
for package in fastapi uvicorn httpx python-multipart python-dotenv aiohttp requests; do
    if python3 -c "import $package" 2>/dev/null; then
        echo -e "${GREEN}✓ $package${NC}"
    else
        echo -e "${RED}✗ $package 未安装${NC}"
    fi
done

# 4. 检查配置文件
echo
echo -e "${BLUE}[4] 配置文件检查${NC}"
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env 文件存在${NC}"
    # 检查关键配置（不显示值）
    if grep -q "RAGFLOW_API_URL" .env; then
        echo -e "${GREEN}✓ RAGFLOW_API_URL 已配置${NC}"
    else
        echo -e "${YELLOW}! RAGFLOW_API_URL 未配置${NC}"
    fi
    if grep -q "RAGFLOW_API_KEY" .env; then
        echo -e "${GREEN}✓ RAGFLOW_API_KEY 已配置${NC}"
    else
        echo -e "${YELLOW}! RAGFLOW_API_KEY 未配置${NC}"
    fi
else
    echo -e "${RED}✗ .env 文件不存在${NC}"
fi

# 5. 检查端口
echo
echo -e "${BLUE}[5] 端口检查${NC}"
for port in 8001 8050 5173; do
    if lsof -i:$port &>/dev/null; then
        echo -e "${YELLOW}! 端口 $port 已被占用${NC}"
        lsof -i:$port | grep LISTEN | head -1
    else
        echo -e "${GREEN}✓ 端口 $port 可用${NC}"
    fi
done

# 6. 检查文件权限
echo
echo -e "${BLUE}[6] 文件权限检查${NC}"
for file in api_proxy.py start_server.sh stop_server.sh; do
    if [ -f "$file" ]; then
        if [ -r "$file" ]; then
            echo -e "${GREEN}✓ $file 可读${NC}"
        else
            echo -e "${RED}✗ $file 不可读${NC}"
        fi
    else
        echo -e "${RED}✗ $file 不存在${NC}"
    fi
done

# 7. 检查日志
echo
echo -e "${BLUE}[7] 最新日志${NC}"
if [ -d "logs" ]; then
    latest_log=$(ls -t logs/api_proxy_*.log 2>/dev/null | head -1)
    if [ -n "$latest_log" ]; then
        echo "最新日志文件: $latest_log"
        echo "最后10行内容:"
        echo "---"
        tail -10 "$latest_log" 2>/dev/null || echo "无法读取日志"
        echo "---"
    else
        echo -e "${YELLOW}没有找到日志文件${NC}"
    fi
else
    echo -e "${YELLOW}logs 目录不存在${NC}"
fi

# 8. 测试导入
echo
echo -e "${BLUE}[8] 模块导入测试${NC}"
python3 -c "
try:
    import api_proxy
    print('✓ api_proxy.py 可以导入')
except Exception as e:
    print(f'✗ 导入失败: {e}')
" 2>&1

# 9. 建议
echo
echo -e "${BLUE}=== 诊断建议 ===${NC}"
echo "如果看到错误，请尝试："
echo "1. 运行 ./deploy_remote.sh 重新安装依赖"
echo "2. 检查 .env 文件配置"
echo "3. 确保所有依赖都已安装"
echo "4. 检查端口是否被占用"