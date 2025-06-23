#!/bin/bash

# xDAN Rag Copilot 安装脚本
# 用于初始化环境和安装依赖

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 检查Python版本
check_python() {
    log_info "检查Python环境..."
    
    # 检查python3
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        log_info "找到Python: $PYTHON_VERSION"
    else
        log_error "未找到Python3，请先安装Python 3.8+"
        exit 1
    fi
    
    # 检查pip
    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
    elif command -v pip &> /dev/null; then
        PIP_CMD="pip"
    else
        log_error "未找到pip，请先安装pip"
        exit 1
    fi
    
    log_info "使用pip: $PIP_CMD"
}

# 创建虚拟环境
create_venv() {
    log_info "创建Python虚拟环境..."
    
    if [ -d "venv" ]; then
        log_warning "虚拟环境已存在"
        read -p "是否重新创建？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv
            $PYTHON_CMD -m venv venv
        fi
    else
        $PYTHON_CMD -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    log_info "虚拟环境创建成功"
}

# 安装Python依赖
install_python_deps() {
    log_info "安装Python依赖..."
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装requirements.txt中的依赖
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        log_error "未找到requirements.txt文件"
        exit 1
    fi
    
    # 安装额外需要的包
    log_info "安装额外依赖..."
    pip install httpx python-multipart
    
    log_info "Python依赖安装完成"
}

# 检查Node.js环境（可选）
check_nodejs() {
    log_info "检查Node.js环境（前端开发可选）..."
    
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        log_info "找到Node.js: $NODE_VERSION"
        
        if command -v npm &> /dev/null; then
            NPM_VERSION=$(npm --version)
            log_info "找到npm: $NPM_VERSION"
            return 0
        fi
    else
        log_warning "未找到Node.js，如需前端开发请安装Node.js 18+"
        return 1
    fi
}

# 安装前端依赖（可选）
install_frontend_deps() {
    if [ -d "frontend" ]; then
        read -p "是否安装前端依赖？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "安装前端依赖..."
            cd frontend
            npm install
            cd ..
            log_info "前端依赖安装完成"
        fi
    fi
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    mkdir -p logs
    mkdir -p data
    log_info "目录创建完成"
}

# 配置环境变量
setup_env() {
    log_info "配置环境变量..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_info "已从.env.example创建.env文件"
            log_warning "请编辑.env文件，配置必要的API密钥和URL"
        else
            log_warning "未找到.env.example文件，请手动创建.env文件"
        fi
    else
        log_info ".env文件已存在"
    fi
}

# 显示安装摘要
show_summary() {
    echo
    echo -e "${BLUE}=== 安装完成 ===${NC}"
    echo
    echo "环境配置摘要："
    echo "  Python版本: $PYTHON_VERSION"
    echo "  虚拟环境: venv/"
    echo "  日志目录: logs/"
    echo
    echo "下一步操作："
    echo "1. 编辑 .env 文件，配置必要的API密钥"
    echo "2. 运行 ./start_server.sh start 启动服务"
    echo "3. 访问 http://localhost:8001/docs 查看API文档"
    echo
    echo -e "${GREEN}安装成功！${NC}"
}

# 主函数
main() {
    echo -e "${BLUE}=== xDAN Rag Copilot 安装脚本 ===${NC}"
    echo
    
    # 检查Python
    check_python
    
    # 创建虚拟环境
    create_venv
    
    # 安装Python依赖
    install_python_deps
    
    # 检查Node.js（可选）
    check_nodejs
    
    # 安装前端依赖（可选）
    if [ $? -eq 0 ]; then
        install_frontend_deps
    fi
    
    # 创建目录
    create_directories
    
    # 配置环境变量
    setup_env
    
    # 显示摘要
    show_summary
}

# 执行主函数
main