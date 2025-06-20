#!/bin/bash

# RAGFlow API 客户端安装脚本

echo "=== RAGFlow API 客户端安装脚本 ==="
echo "该脚本将设置虚拟环境并安装所需依赖"

# 检查 Python 版本
python_version=$(python3 --version 2>&1)
echo "检测到 Python 版本: $python_version"

# 检查是否安装了 uv
if command -v uv &> /dev/null; then
    echo "检测到 uv 已安装"
    USE_UV=true
else
    echo "未检测到 uv，将使用 venv 和 pip"
    USE_UV=false
fi

# 创建虚拟环境
echo "创建虚拟环境..."
if [ "$USE_UV" = true ]; then
    uv venv
else
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装依赖..."
if [ "$USE_UV" = true ]; then
    uv pip install -r requirements.txt
else
    pip install -r requirements.txt
fi

# 检查是否存在 .env 文件
if [ ! -f .env ]; then
    echo "创建 .env 文件..."
    cp .env.example .env
    echo "请编辑 .env 文件，填入您的 RAGFlow API 密钥"
fi

# 给命令行工具添加执行权限
echo "给命令行工具添加执行权限..."
chmod +x ragflow_cli.py

echo "=== 安装完成 ==="
echo "您现在可以使用以下命令启动服务器:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "或者使用命令行工具:"
echo "  source venv/bin/activate"
echo "  ./ragflow_cli.py --help"
