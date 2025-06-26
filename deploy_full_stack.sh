#!/bin/bash

# xDAN RAG Copilot 全栈一键部署脚本
# 自动安装 PostgreSQL, Redis 并部署应用程序

set -e  # 遇到错误立即退出

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# 检测操作系统
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            OS="debian"
            log_info "检测到 Debian/Ubuntu 系统"
        elif [ -f /etc/redhat-release ]; then
            OS="redhat"
            log_info "检测到 RedHat/CentOS 系统"
        else
            OS="linux"
            log_info "检测到 Linux 系统"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        log_info "检测到 macOS 系统"
    else
        log_error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
}

# 检查是否为 root 用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "检测到 root 用户，建议使用普通用户运行此脚本"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 安装系统依赖
install_system_dependencies() {
    log_step "安装系统依赖..."
    
    case $OS in
        "debian")
            sudo apt-get update
            sudo apt-get install -y curl wget gnupg2 software-properties-common apt-transport-https ca-certificates
            ;;
        "redhat")
            sudo yum update -y
            sudo yum install -y curl wget gnupg2
            ;;
        "macos")
            if ! command -v brew &> /dev/null; then
                log_info "安装 Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            ;;
    esac
    
    log_success "系统依赖安装完成"
}

# 安装 PostgreSQL (使用Docker避免冲突)
install_postgresql() {
    log_step "安装 PostgreSQL (Docker容器: postgres-rag)..."
    
    # 检查Docker是否安装
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 停止并删除现有的postgres-rag容器（如果存在）
    docker stop postgres-rag 2>/dev/null || true
    docker rm postgres-rag 2>/dev/null || true
    
    # 创建PostgreSQL数据目录
    sudo mkdir -p /opt/ragflow-rag/postgres-data
    sudo chown $USER:$USER /opt/ragflow-rag/postgres-data
    
    # 启动PostgreSQL容器
    docker run -d \
        --name postgres-rag \
        --restart unless-stopped \
        -p 5433:5432 \
        -v /opt/ragflow-rag/postgres-data:/var/lib/postgresql/data \
        -e POSTGRES_DB=xdan_rag_service \
        -e POSTGRES_USER=ragflow_user \
        -e POSTGRES_PASSWORD=ragflow123 \
        -e POSTGRES_INITDB_ARGS="--encoding=UTF-8 --lc-collate=C --lc-ctype=C" \
        postgres:15-alpine
    
    log_success "PostgreSQL容器 (postgres-rag) 安装完成，端口: 5433"
}

# 配置 PostgreSQL
configure_postgresql() {
    log_step "配置 PostgreSQL 容器..."
    
    # 等待PostgreSQL容器启动
    log_info "等待PostgreSQL容器启动..."
    sleep 10
    
    # 测试数据库连接
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker exec postgres-rag pg_isready -U ragflow_user -d xdan_rag_service &> /dev/null; then
            log_success "PostgreSQL 容器启动成功"
            break
        fi
        
        log_info "等待PostgreSQL启动... ($attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "PostgreSQL 容器启动超时"
        return 1
    fi
    
    log_success "PostgreSQL 配置完成"
}

# 安装 Redis (使用Docker避免冲突)
install_redis() {
    log_step "安装 Redis (Docker容器: redis-rag)..."
    
    # 检查Docker是否安装
    if ! command -v docker &> /dev/null; then
        log_info "安装 Docker..."
        case $OS in
            "debian")
                sudo apt-get update
                sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
                curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
                echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
                sudo apt-get update
                sudo apt-get install -y docker-ce docker-ce-cli containerd.io
                sudo systemctl start docker
                sudo systemctl enable docker
                sudo usermod -aG docker $USER
                ;;
            "redhat")
                sudo yum install -y yum-utils
                sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
                sudo yum install -y docker-ce docker-ce-cli containerd.io
                sudo systemctl start docker
                sudo systemctl enable docker
                sudo usermod -aG docker $USER
                ;;
            "macos")
                log_error "请手动安装 Docker Desktop for Mac"
                exit 1
                ;;
        esac
        
        log_warning "Docker已安装，请重新登录以使用户组生效，然后重新运行脚本"
        exit 0
    fi
    
    # 停止并删除现有的redis-rag容器（如果存在）
    docker stop redis-rag 2>/dev/null || true
    docker rm redis-rag 2>/dev/null || true
    
    # 创建Redis数据目录
    sudo mkdir -p /opt/ragflow-rag/redis-data
    sudo chown $USER:$USER /opt/ragflow-rag/redis-data
    
    # 启动Redis容器
    docker run -d \
        --name redis-rag \
        --restart unless-stopped \
        -p 6380:6379 \
        -v /opt/ragflow-rag/redis-data:/data \
        -e REDIS_PASSWORD=ragflow123 \
        redis:7-alpine \
        redis-server --requirepass ragflow123 --appendonly yes
    
    log_success "Redis容器 (redis-rag) 安装完成，端口: 6380"
}

# 配置 Redis
configure_redis() {
    log_step "配置 Redis 容器..."
    
    # 等待Redis容器启动
    sleep 5
    
    # 测试Redis连接
    if docker exec redis-rag redis-cli -a ragflow123 ping &> /dev/null; then
        log_success "Redis 容器配置完成，连接测试成功"
    else
        log_error "Redis 容器配置失败"
        return 1
    fi
}

# 安装 Python 和 uv
install_python_tools() {
    log_step "安装 Python 和 uv 工具..."
    
    # 检查 Python 3.9+
    if ! command -v python3 &> /dev/null; then
        case $OS in
            "debian")
                sudo apt-get install -y python3 python3-pip python3-venv
                ;;
            "redhat")
                sudo yum install -y python3 python3-pip
                ;;
            "macos")
                brew install python@3.11
                ;;
        esac
    fi
    
    # 安装 uv
    if ! command -v uv &> /dev/null; then
        log_info "安装 uv 包管理工具..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.cargo/env 2>/dev/null || true
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
    
    log_success "Python 工具安装完成"
}

# 初始化数据库
initialize_database() {
    log_step "初始化项目数据库..."
    
    # 设置数据库连接环境变量（使用容器配置）
    export DB_HOST="localhost"
    export DB_PORT="5433"
    export DB_NAME="xdan_rag_service"
    export DB_USER="ragflow_user"
    export DB_PASSWORD="ragflow123"
    
    # 检查初始化脚本是否存在
    if [ -f "scripts/init_postgresql.sh" ]; then
        chmod +x scripts/init_postgresql.sh
        
        log_info "运行数据库初始化脚本..."
        # 修改脚本使用Docker容器连接
        sed -i.bak "s/psql -h/docker exec postgres-rag psql -h localhost -p 5432 -U ragflow_user -d/g" scripts/init_postgresql.sh
        ./scripts/init_postgresql.sh
        # 恢复原脚本
        mv scripts/init_postgresql.sh.bak scripts/init_postgresql.sh
    else
        log_warning "数据库初始化脚本不存在，使用内置SQL创建表结构..."
        
        # 使用Docker容器执行SQL
        docker exec postgres-rag psql -U ragflow_user -d xdan_rag_service << 'EOF'
-- 创建chats表 - 存储对话会话信息
CREATE TABLE IF NOT EXISTS chats (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    dataset_ids JSONB DEFAULT '[]'::jsonb,
    llm_config JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建messages表 - 存储对话消息
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    chat_id VARCHAR(255) NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建s3_workflow_traces表 - 存储S3框架工作流追踪
CREATE TABLE IF NOT EXISTS s3_workflow_traces (
    id VARCHAR(255) PRIMARY KEY,
    chat_id VARCHAR(255) NOT NULL,
    user_question TEXT NOT NULL,
    search_rounds INTEGER DEFAULT 0,
    total_documents INTEGER DEFAULT 0,
    final_answer TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 创建langfuse_sessions表 - 存储Langfuse会话映射
CREATE TABLE IF NOT EXISTS langfuse_sessions (
    chat_id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    trace_id VARCHAR(255),
    user_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_chats_created_at ON chats(created_at);
CREATE INDEX IF NOT EXISTS idx_chats_dataset_ids ON chats USING GIN (dataset_ids);
CREATE INDEX IF NOT EXISTS idx_s3_workflow_traces_chat_id ON s3_workflow_traces(chat_id);
CREATE INDEX IF NOT EXISTS idx_s3_workflow_traces_created_at ON s3_workflow_traces(created_at);
CREATE INDEX IF NOT EXISTS idx_langfuse_sessions_session_id ON langfuse_sessions(session_id);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为chats表添加更新时间触发器
DROP TRIGGER IF EXISTS update_chats_updated_at ON chats;
CREATE TRIGGER update_chats_updated_at 
    BEFORE UPDATE ON chats 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
EOF
    fi
    
    log_success "数据库初始化完成"
}

# 部署应用程序
deploy_application() {
    log_step "部署应用程序..."
    
    # 创建虚拟环境
    if command -v uv &> /dev/null; then
        log_info "使用 uv 创建虚拟环境..."
        uv venv .venv
        source .venv/bin/activate
        uv pip install -r requirements.txt
        uv pip install httpx python-multipart asyncpg redis
    else
        log_info "使用 pip 创建虚拟环境..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        pip install httpx python-multipart asyncpg redis
    fi
    
    # 创建必要目录
    mkdir -p logs data
    
    # 配置环境文件
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_info "已创建 .env 文件"
        else
            log_info "创建基础 .env 文件..."
            cat > .env << 'EOF'
# 数据库配置 (Docker容器)
DB_HOST=localhost
DB_PORT=5433
DB_NAME=xdan_rag_service
DB_USER=ragflow_user
DB_PASSWORD=ragflow123

# Redis 配置 (Docker容器)
REDIS_HOST=localhost
REDIS_PORT=6380
REDIS_PASSWORD=ragflow123

# RAGFlow API 配置
RAGFLOW_API_URL=http://localhost:7080
RAGFLOW_API_KEY=your_api_key_here

# LLM API 配置
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# Langfuse 配置 (可选)
LANGFUSE_HOST=https://agentops.xdan.ai
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
EOF
        fi
        
        log_warning "请编辑 .env 文件配置 API 密钥"
    fi
    
    # 设置执行权限
    chmod +x start_server.sh stop_server.sh 2>/dev/null || true
    
    log_success "应用程序部署完成"
}

# 创建服务管理脚本
create_service_scripts() {
    log_step "创建服务管理脚本..."
    
    # 创建服务状态检查脚本
    cat > check_services.sh << 'EOF'
#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=== xDAN RAG Copilot 服务状态 ==="
echo

# 检查 PostgreSQL (Docker容器)
if docker ps | grep -q "postgres-rag"; then
    echo -e "PostgreSQL (postgres-rag): ${GREEN}运行中${NC}"
    
    # 检查数据库连接
    if docker exec postgres-rag pg_isready -U ragflow_user -d xdan_rag_service &> /dev/null; then
        echo -e "数据库连接: ${GREEN}正常${NC}"
    else
        echo -e "数据库连接: ${RED}失败${NC}"
    fi
else
    echo -e "PostgreSQL (postgres-rag): ${RED}未运行${NC}"
fi

# 检查 Redis (Docker容器)
if docker ps | grep -q "redis-rag"; then
    echo -e "Redis (redis-rag): ${GREEN}运行中${NC}"
    
    # 检查 Redis 连接
    if docker exec redis-rag redis-cli -a ragflow123 ping &> /dev/null; then
        echo -e "Redis 连接: ${GREEN}正常${NC}"
    else
        echo -e "Redis 连接: ${RED}失败${NC}"
    fi
else
    echo -e "Redis (redis-rag): ${RED}未运行${NC}"
fi

# 检查应用程序
if pgrep -f "uvicorn.*main:app" > /dev/null; then
    echo -e "RAG Service: ${GREEN}运行中${NC}"
    
    # 检查 API 响应
    if curl -s http://localhost:8001/health &> /dev/null; then
        echo -e "API 服务: ${GREEN}正常${NC}"
    else
        echo -e "API 服务: ${RED}无响应${NC}"
    fi
else
    echo -e "RAG Service: ${RED}未运行${NC}"
fi

echo
echo "服务端口："
echo "- RAG API: http://localhost:8001"
echo "- PostgreSQL (postgres-rag): localhost:5433"
echo "- Redis (redis-rag): localhost:6380"
EOF
    
    chmod +x check_services.sh
    
    # 创建服务重启脚本
    cat > restart_services.sh << 'EOF'
#!/bin/bash

echo "重启所有服务..."

# 重启 PostgreSQL 容器
docker restart postgres-rag 2>/dev/null || true

# 重启 Redis 容器
docker restart redis-rag 2>/dev/null || true

# 重启应用程序
./stop_server.sh 2>/dev/null || true
sleep 2
./start_server.sh start

echo "所有服务已重启"
EOF
    
    chmod +x restart_services.sh
    
    log_success "服务管理脚本创建完成"
}

# 健康检查
health_check() {
    log_step "执行健康检查..."
    
    # 等待服务启动
    sleep 3
    
    # 检查 PostgreSQL 容器
    if docker exec postgres-rag pg_isready -U ragflow_user -d xdan_rag_service &> /dev/null; then
        log_success "PostgreSQL 容器连接正常"
    else
        log_error "PostgreSQL 容器连接失败"
        return 1
    fi
    
    # 检查 Redis 容器
    if docker exec redis-rag redis-cli -a ragflow123 ping &> /dev/null; then
        log_success "Redis 容器连接正常"
    else
        log_warning "Redis 容器连接失败（可选服务）"
    fi
    
    log_success "健康检查完成"
}

# 显示部署结果
show_deployment_summary() {
    echo
    echo -e "${GREEN}=== 部署完成 ===${NC}"
    echo
    echo "✅ 已安装服务："
    echo "   - PostgreSQL 15 (Docker: postgres-rag)"
    echo "   - Redis (Docker: redis-rag)"
    echo "   - Python 虚拟环境"
    echo "   - xDAN RAG Copilot"
    echo
    echo "📋 下一步操作："
    echo "1. 编辑 .env 文件配置 API 密钥"
    echo "2. 运行 ./start_server.sh start 启动应用"
    echo "3. 使用 ./check_services.sh 检查服务状态"
    echo
    echo "🔗 服务地址："
    echo "   - API 文档: http://localhost:8001/docs"
    echo "   - 健康检查: http://localhost:8001/health"
    echo
    echo "🛠️  管理脚本："
    echo "   - ./check_services.sh    # 检查服务状态"
    echo "   - ./restart_services.sh  # 重启所有服务"
    echo "   - ./start_server.sh      # 启动应用"
    echo "   - ./stop_server.sh       # 停止应用"
    echo
}

# 主函数
main() {
    echo -e "${BLUE}=== xDAN RAG Copilot 全栈一键部署 ===${NC}"
    echo
    
    # 检查环境
    detect_os
    check_root
    
    # 询问是否继续
    echo "此脚本将安装以下组件："
    echo "- PostgreSQL 15 (Docker容器: postgres-rag, 端口: 5433)"
    echo "- Redis (Docker容器: redis-rag, 端口: 6380)"
    echo "- Python 虚拟环境"
    echo "- xDAN RAG Copilot 应用"
    echo
    read -p "是否继续部署? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "部署已取消"
        exit 0
    fi
    
    # 执行部署步骤
    install_system_dependencies
    install_postgresql
    configure_postgresql
    install_redis
    configure_redis
    install_python_tools
    initialize_database
    deploy_application
    create_service_scripts
    health_check
    
    # 显示结果
    show_deployment_summary
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查日志"; exit 1' ERR

# 运行主函数
main "$@"