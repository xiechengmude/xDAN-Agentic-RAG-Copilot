#!/bin/bash

# xDAN RAG Copilot 部署恢复脚本
# 用于从中断的部署过程恢复

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

# 检查部署状态
check_deployment_status() {
    echo -e "${PURPLE}=== 检查部署状态 ===${NC}"
    echo
    
    # 检查Docker
    if command -v docker &> /dev/null; then
        log_success "Docker 已安装"
    else
        log_error "Docker 未安装"
        return 1
    fi
    
    # 检查PostgreSQL容器
    if docker ps -a --format "table {{.Names}}" | grep -q "postgres-rag"; then
        if docker ps --format "table {{.Names}}" | grep -q "postgres-rag"; then
            log_success "PostgreSQL 容器运行中"
            
            # 检查数据库初始化
            local table_count=$(docker exec postgres-rag psql -U ragflow_user -d xdan_rag_service -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('chats', 'messages', 's3_workflow_traces', 'langfuse_sessions');" 2>/dev/null | tr -d ' ' || echo "0")
            
            if [ "$table_count" -eq 4 ]; then
                log_success "数据库已完全初始化"
            else
                log_warning "数据库需要初始化 (表数量: $table_count/4)"
            fi
        else
            log_warning "PostgreSQL 容器已存在但未运行"
        fi
    else
        log_error "PostgreSQL 容器不存在"
    fi
    
    # 检查Redis容器
    if docker ps -a --format "table {{.Names}}" | grep -q "redis-rag"; then
        if docker ps --format "table {{.Names}}" | grep -q "redis-rag"; then
            log_success "Redis 容器运行中"
        else
            log_warning "Redis 容器已存在但未运行"
        fi
    else
        log_error "Redis 容器不存在"
    fi
    
    # 检查Python虚拟环境
    if [ -d ".venv" ] || [ -d "venv" ]; then
        log_success "Python 虚拟环境已存在"
    else
        log_warning "Python 虚拟环境不存在"
    fi
    
    # 检查配置文件
    if [ -f ".env" ]; then
        log_success ".env 配置文件已存在"
    else
        log_warning ".env 配置文件不存在"
    fi
    
    # 检查管理脚本
    if [ -f "check_services.sh" ] && [ -f "restart_services.sh" ]; then
        log_success "管理脚本已存在"
    else
        log_warning "管理脚本不存在"
    fi
}

# 修复常见问题
fix_common_issues() {
    echo
    echo -e "${PURPLE}=== 修复常见问题 ===${NC}"
    
    # 检查并处理运行中的应用程序
    if pgrep -f "uvicorn.*main:app" > /dev/null; then
        log_warning "检测到RAG服务正在运行"
        echo "当前运行的进程："
        ps aux | grep -E "(uvicorn.*main:app|python.*main\.py)" | grep -v grep
        echo
        
        read -p "是否重启服务以应用最新配置? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "重启RAG服务..."
            
            # 尝试优雅关闭
            if [ -f "stop_server.sh" ]; then
                ./stop_server.sh 2>/dev/null || true
            fi
            
            # 强制关闭剩余进程
            pkill -f "uvicorn.*main:app" 2>/dev/null || true
            pkill -f "python.*main\.py" 2>/dev/null || true
            
            sleep 3
            
            # 重新启动
            if [ -f "start_server.sh" ]; then
                ./start_server.sh start
                sleep 3
                if pgrep -f "uvicorn.*main:app" > /dev/null; then
                    log_success "RAG服务重启成功"
                else
                    log_warning "RAG服务重启可能失败，请检查日志"
                fi
            fi
        fi
    fi
    
    # 启动停止的容器
    if docker ps -a --format "table {{.Names}}" | grep -q "postgres-rag"; then
        if ! docker ps --format "table {{.Names}}" | grep -q "postgres-rag"; then
            log_info "启动 PostgreSQL 容器..."
            docker start postgres-rag
        fi
    fi
    
    if docker ps -a --format "table {{.Names}}" | grep -q "redis-rag"; then
        if ! docker ps --format "table {{.Names}}" | grep -q "redis-rag"; then
            log_info "启动 Redis 容器..."
            docker start redis-rag
        fi
    fi
    
    # 等待容器启动
    sleep 5
    
    # 初始化数据库（如果需要）
    local table_count=$(docker exec postgres-rag psql -U ragflow_user -d xdan_rag_service -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('chats', 'messages', 's3_workflow_traces', 'langfuse_sessions');" 2>/dev/null | tr -d ' ' || echo "0")
    
    if [ "$table_count" -lt 4 ]; then
        log_info "初始化数据库表结构..."
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
        
        if [ $? -eq 0 ]; then
            log_success "数据库初始化完成"
        else
            log_error "数据库初始化失败"
        fi
    fi
    
    # 创建.env文件（如果不存在）
    if [ ! -f ".env" ]; then
        log_info "创建 .env 配置文件..."
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
        log_success ".env 文件已创建"
    fi
    
    # 创建管理脚本（如果不存在）
    if [ ! -f "check_services.sh" ]; then
        log_info "创建服务检查脚本..."
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
        log_success "check_services.sh 已创建"
    fi
    
    if [ ! -f "restart_services.sh" ]; then
        log_info "创建服务重启脚本..."
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
        log_success "restart_services.sh 已创建"
    fi
}

# 提供下一步指导
show_next_steps() {
    echo
    echo -e "${GREEN}=== 恢复完成 ===${NC}"
    echo
    echo "📋 下一步操作："
    echo "1. 编辑 .env 文件配置 API 密钥"
    echo "2. 运行 ./check_services.sh 检查服务状态"
    echo "3. 运行 ./start_server.sh start 启动应用"
    echo
    echo "🔗 服务地址："
    echo "   - API 文档: http://localhost:8001/docs"
    echo "   - 健康检查: http://localhost:8001/health"
    echo
}

# 主函数
main() {
    echo -e "${BLUE}=== xDAN RAG Copilot 部署恢复 ===${NC}"
    echo
    
    check_deployment_status
    
    echo
    read -p "是否尝试修复发现的问题? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        fix_common_issues
        echo
        log_info "重新检查部署状态..."
        check_deployment_status
    fi
    
    show_next_steps
}

# 运行主函数
main "$@"