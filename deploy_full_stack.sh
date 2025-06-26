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

# 检查现有安装状态
check_existing_installation() {
    log_step "检查现有安装状态..."
    
    POSTGRES_EXISTS=false
    REDIS_EXISTS=false
    DOCKER_INSTALLED=false
    
    # 检查Docker是否安装
    if command -v docker &> /dev/null; then
        DOCKER_INSTALLED=true
        log_info "✓ Docker 已安装"
        
        # 检查PostgreSQL容器
        if docker ps -a --format "table {{.Names}}" | grep -q "postgres-rag"; then
            POSTGRES_EXISTS=true
            if docker ps --format "table {{.Names}}" | grep -q "postgres-rag"; then
                log_info "✓ PostgreSQL 容器 (postgres-rag) 已存在且运行中"
            else
                log_warning "! PostgreSQL 容器 (postgres-rag) 已存在但未运行"
            fi
        fi
        
        # 检查Redis容器
        if docker ps -a --format "table {{.Names}}" | grep -q "redis-rag"; then
            REDIS_EXISTS=true
            if docker ps --format "table {{.Names}}" | grep -q "redis-rag"; then
                log_info "✓ Redis 容器 (redis-rag) 已存在且运行中"
            else
                log_warning "! Redis 容器 (redis-rag) 已存在但未运行"
            fi
        fi
    else
        log_info "○ Docker 未安装"
    fi
    
    # 检查Python虚拟环境
    if [ -d ".venv" ] || [ -d "venv" ]; then
        log_info "✓ Python 虚拟环境已存在"
    else
        log_info "○ Python 虚拟环境不存在"
    fi
    
    # 检查配置文件
    if [ -f ".env" ]; then
        log_info "✓ .env 配置文件已存在"
    else
        log_info "○ .env 配置文件不存在"
    fi
}

# 安装系统依赖
install_system_dependencies() {
    log_step "安装系统依赖..."
    
    case $OS in
        "debian")
            sudo apt-get update
            sudo apt-get install -y curl wget gnupg2 software-properties-common apt-transport-https ca-certificates postgresql-client
            ;;
        "redhat")
            sudo yum update -y
            sudo yum install -y curl wget gnupg2 postgresql
            ;;
        "macos")
            if ! command -v brew &> /dev/null; then
                log_info "安装 Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            # macOS通过Homebrew安装PostgreSQL客户端
            if ! command -v psql &> /dev/null; then
                brew install postgresql
            fi
            ;;
    esac
    
    log_success "系统依赖安装完成"
}

# 安装 PostgreSQL (使用Docker避免冲突)
install_postgresql() {
    if [ "$POSTGRES_EXISTS" = true ]; then
        log_info "PostgreSQL 容器已存在，跳过安装"
        
        # 如果容器存在但未运行，启动它
        if ! docker ps --format "table {{.Names}}" | grep -q "postgres-rag"; then
            log_info "启动现有的 PostgreSQL 容器..."
            docker start postgres-rag
        fi
        return 0
    fi
    
    log_step "安装 PostgreSQL (Docker容器: postgres-rag)..."
    
    # 检查Docker是否安装
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 创建PostgreSQL数据目录（幂等操作）
    sudo mkdir -p /opt/ragflow-rag/postgres-data
    sudo chown $USER:$USER /opt/ragflow-rag/postgres-data 2>/dev/null || true
    
    # 启动PostgreSQL容器
    if docker run -d \
        --name postgres-rag \
        --restart unless-stopped \
        -p 5433:5432 \
        -v /opt/ragflow-rag/postgres-data:/var/lib/postgresql/data \
        -e POSTGRES_DB=xdan_rag_service \
        -e POSTGRES_USER=ragflow_user \
        -e POSTGRES_PASSWORD=ragflow123 \
        -e POSTGRES_INITDB_ARGS="--encoding=UTF-8 --lc-collate=C --lc-ctype=C" \
        postgres:15-alpine; then
        
        log_success "PostgreSQL容器 (postgres-rag) 安装完成，端口: 5433"
        POSTGRES_EXISTS=true
    else
        log_error "PostgreSQL容器创建失败"
        exit 1
    fi
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
    if [ "$REDIS_EXISTS" = true ]; then
        log_info "Redis 容器已存在，跳过安装"
        
        # 如果容器存在但未运行，启动它
        if ! docker ps --format "table {{.Names}}" | grep -q "redis-rag"; then
            log_info "启动现有的 Redis 容器..."
            docker start redis-rag
        fi
        return 0
    fi
    
    log_step "安装 Redis (Docker容器: redis-rag)..."
    
    # 检查Docker是否安装
    if [ "$DOCKER_INSTALLED" = false ]; then
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
    
    # 创建Redis数据目录（幂等操作）
    sudo mkdir -p /opt/ragflow-rag/redis-data
    sudo chown $USER:$USER /opt/ragflow-rag/redis-data 2>/dev/null || true
    
    # 启动Redis容器
    if docker run -d \
        --name redis-rag \
        --restart unless-stopped \
        -p 6380:6379 \
        -v /opt/ragflow-rag/redis-data:/data \
        -e REDIS_PASSWORD=ragflow123 \
        redis:7-alpine \
        redis-server --requirepass ragflow123 --appendonly yes; then
        
        log_success "Redis容器 (redis-rag) 安装完成，端口: 6380"
        REDIS_EXISTS=true
    else
        log_error "Redis容器创建失败"
        exit 1
    fi
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

# 检查数据库是否已初始化
check_database_initialized() {
    # 检查是否已有表结构
    local table_count=$(docker exec postgres-rag psql -U ragflow_user -d xdan_rag_service -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('chats', 'messages', 's3_workflow_traces', 'langfuse_sessions');" 2>/dev/null | tr -d ' ' || echo "0")
    
    if [ "$table_count" -eq 4 ]; then
        log_info "数据库已初始化，跳过初始化步骤"
        return 0
    else
        return 1
    fi
}

# 初始化数据库
initialize_database() {
    log_step "初始化项目数据库..."
    
    # 检查是否已初始化
    if check_database_initialized; then
        return 0
    fi
    
    # 设置数据库连接环境变量（使用容器配置）
    export DB_HOST="localhost"
    export DB_PORT="5433"
    export DB_NAME="xdan_rag_service"
    export DB_USER="ragflow_user"
    export DB_PASSWORD="ragflow123"
    
    log_info "使用Docker容器执行数据库初始化..."
    
    # 直接使用Docker容器执行SQL，避免依赖外部psql
    if docker exec postgres-rag psql -U ragflow_user -d xdan_rag_service << 'EOF'
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
    then
        log_success "数据库初始化完成"
    else
        log_error "数据库初始化失败"
        return 1
    fi
}

# 检查并处理运行中的应用程序
check_running_application() {
    # 检查是否有RAG服务在运行
    if pgrep -f "uvicorn.*main:app" > /dev/null; then
        log_warning "检测到RAG服务正在运行"
        echo "当前运行的进程："
        ps aux | grep -E "(uvicorn.*main:app|python.*main\.py)" | grep -v grep
        echo
        
        read -p "是否停止当前运行的服务以继续部署? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "停止运行中的RAG服务..."
            
            # 尝试优雅关闭
            if [ -f "stop_server.sh" ]; then
                ./stop_server.sh 2>/dev/null || true
            fi
            
            # 强制关闭剩余进程
            pkill -f "uvicorn.*main:app" 2>/dev/null || true
            pkill -f "python.*main\.py" 2>/dev/null || true
            
            # 等待进程完全关闭
            sleep 3
            
            if pgrep -f "uvicorn.*main:app" > /dev/null; then
                log_error "无法停止运行中的服务，请手动关闭后重试"
                exit 1
            else
                log_success "服务已停止"
            fi
        else
            log_warning "用户选择保留运行中的服务，跳过应用程序部署"
            return 1
        fi
    fi
    return 0
}

# 部署应用程序
deploy_application() {
    log_step "部署应用程序..."
    
    # 检查运行中的应用程序
    if ! check_running_application; then
        log_info "跳过应用程序部署步骤"
        return 0
    fi
    
    # 检查是否已有虚拟环境
    if [ -d ".venv" ] || [ -d "venv" ]; then
        log_info "Python虚拟环境已存在"
        # 激活现有环境
        if [ -d ".venv" ]; then
            source .venv/bin/activate
        else
            source venv/bin/activate
        fi
        
        # 更新依赖（幂等操作）
        log_info "更新Python依赖..."
        if command -v uv &> /dev/null; then
            uv pip install -r requirements.txt --upgrade
            uv pip install httpx python-multipart asyncpg redis --upgrade
        else
            pip install -r requirements.txt --upgrade
            pip install httpx python-multipart asyncpg redis --upgrade
        fi
    else
        # 创建新的虚拟环境
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
    fi
    
    # 创建必要目录（幂等操作）
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
    
    # 询问是否立即启动服务
    echo
    read -p "是否立即启动RAG服务? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f "start_server.sh" ]; then
            log_info "启动RAG服务..."
            ./start_server.sh start
            sleep 3
            if pgrep -f "uvicorn.*main:app" > /dev/null; then
                log_success "RAG服务启动成功"
            else
                log_warning "RAG服务启动可能失败，请检查日志"
            fi
        else
            log_warning "start_server.sh 脚本不存在，请手动启动服务"
        fi
    else
        log_info "稍后可运行 ./start_server.sh start 启动服务"
    fi
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
    check_existing_installation
    
    # 询问是否继续
    echo
    echo "此脚本将安装以下组件："
    echo "- PostgreSQL 15 (Docker容器: postgres-rag, 端口: 5433)"
    echo "- Redis (Docker容器: redis-rag, 端口: 6380)"
    echo "- Python 虚拟环境"
    echo "- xDAN RAG Copilot 应用"
    echo
    if [ "$POSTGRES_EXISTS" = true ] || [ "$REDIS_EXISTS" = true ]; then
        echo "检测到现有安装，脚本将："
        echo "- 跳过已安装的组件"
        echo "- 启动已停止的容器"
        echo "- 更新应用程序代码"
        echo
    fi
    read -p "是否继续部署? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "部署已取消"
        exit 0
    fi
    
    # 执行部署步骤（支持断点续传）
    install_system_dependencies || { log_error "系统依赖安装失败"; exit 1; }
    install_postgresql || { log_error "PostgreSQL安装失败"; exit 1; }
    configure_postgresql || { log_error "PostgreSQL配置失败"; exit 1; }
    install_redis || { log_error "Redis安装失败"; exit 1; }
    configure_redis || { log_error "Redis配置失败"; exit 1; }
    install_python_tools || { log_error "Python工具安装失败"; exit 1; }
    initialize_database || { log_error "数据库初始化失败"; exit 1; }
    deploy_application || { log_error "应用程序部署失败"; exit 1; }
    create_service_scripts || { log_error "服务脚本创建失败"; exit 1; }
    health_check || { log_warning "健康检查发现问题，但部署已完成"; }
    
    # 显示结果
    show_deployment_summary
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查日志"; exit 1' ERR

# 运行主函数
main "$@"