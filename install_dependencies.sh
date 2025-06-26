#!/bin/bash

# xDAN RAG Copilot 依赖安装脚本
# 确保所有必要的Python包都被正确安装

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo -e "${BLUE}=== xDAN RAG Copilot 依赖安装 ===${NC}"
echo

# 检查Python版本
python_version=$(python3 --version 2>&1)
if [[ $? -eq 0 ]]; then
    log_info "Python版本: $python_version"
else
    log_error "Python3 未安装或不可用"
    exit 1
fi

# 检查并激活虚拟环境
if [ -d ".venv" ]; then
    log_info "激活 .venv 虚拟环境"
    source .venv/bin/activate
elif [ -d "venv" ]; then
    log_info "激活 venv 虚拟环境"
    source venv/bin/activate
else
    log_warning "未找到虚拟环境，使用系统Python"
fi

# 检查并安装uv包管理器
if command -v uv &> /dev/null; then
    log_info "使用 uv 安装依赖..."
    uv pip install -r requirements.txt
    
    # 确保关键依赖已安装
    log_info "验证关键依赖..."
    uv pip install PyYAML>=6.0.0
    uv pip install asyncpg>=0.29.0
    uv pip install redis>=5.0.0
    uv pip install litellm>=1.0.0
    uv pip install python-multipart>=0.0.9
    uv pip install httpx>=0.27.0
    
else
    log_info "使用 pip 安装依赖..."
    pip install -r requirements.txt
    
    # 确保关键依赖已安装
    log_info "验证关键依赖..."
    pip install PyYAML>=6.0.0
    pip install asyncpg>=0.29.0
    pip install redis>=5.0.0
    pip install litellm>=1.0.0
    pip install python-multipart>=0.0.9
    pip install httpx>=0.27.0
fi

# 验证关键模块导入
log_info "验证模块导入..."

python3 -c "
import sys
modules_to_check = [
    'yaml',
    'asyncpg', 
    'redis',
    'fastapi',
    'uvicorn',
    'pydantic',
    'requests',
    'httpx',
    'multipart'
]

failed_modules = []
for module in modules_to_check:
    try:
        __import__(module)
        print(f'✓ {module}')
    except ImportError:
        failed_modules.append(module)
        print(f'✗ {module}')

if failed_modules:
    print(f'\n❌ 以下模块导入失败: {failed_modules}')
    sys.exit(1)
else:
    print('\n✅ 所有关键模块导入成功')
"

if [ $? -eq 0 ]; then
    log_success "依赖安装完成，所有模块可正常导入"
    echo
    echo "🚀 现在可以启动服务:"
    echo "   ./start_server.sh start"
else
    log_error "部分依赖安装失败，请检查错误信息"
    exit 1
fi