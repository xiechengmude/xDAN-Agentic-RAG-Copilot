#!/bin/bash
set -e

# xDAN RAG Copilot 一键部署脚本
# 支持多种部署方式：Docker、传统部署、开发环境

echo "🚀 xDAN RAG Copilot 一键部署脚本"
echo "================================="

# 默认配置
DEPLOYMENT_TYPE="${DEPLOYMENT_TYPE:-docker}"
ENVIRONMENT="${ENVIRONMENT:-production}"
DOMAIN="${DOMAIN:-localhost}"
SSL_ENABLED="${SSL_ENABLED:-false}"
BACKUP_ENABLED="${BACKUP_ENABLED:-true}"

# 颜色输出函数
print_info() {
    echo -e "\033[34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

print_warning() {
    echo -e "\033[33m[WARNING]\033[0m $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
xDAN RAG Copilot 部署脚本

用法: $0 [选项]

选项:
  -t, --type TYPE          部署类型 (docker|native|dev) [默认: docker]
  -e, --env ENV           环境 (production|staging|development) [默认: production]
  -d, --domain DOMAIN     域名 [默认: localhost]
  -s, --ssl               启用SSL
  -b, --backup            启用备份 [默认: 启用]
  -h, --help              显示帮助信息

部署类型:
  docker    使用Docker Compose部署 (推荐)
  native    传统方式部署到服务器
  dev       开发环境部署

示例:
  $0 --type docker --env production --domain example.com --ssl
  $0 --type native --env staging
  $0 --type dev

EOF
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--type)
                DEPLOYMENT_TYPE="$2"
                shift 2
                ;;
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -d|--domain)
                DOMAIN="$2"
                shift 2
                ;;
            -s|--ssl)
                SSL_ENABLED="true"
                shift
                ;;
            -b|--backup)
                BACKUP_ENABLED="true"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                print_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 检查依赖
check_dependencies() {
    print_info "检查系统依赖..."
    
    case $DEPLOYMENT_TYPE in
        "docker")
            if ! command -v docker &> /dev/null; then
                print_error "Docker未安装，请先安装Docker"
                exit 1
            fi
            
            if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
                print_error "Docker Compose未安装，请先安装Docker Compose"
                exit 1
            fi
            ;;
        "native")
            if ! command -v python3 &> /dev/null; then
                print_error "Python3未安装"
                exit 1
            fi
            
            if ! command -v node &> /dev/null; then
                print_error "Node.js未安装"
                exit 1
            fi
            ;;
        "dev")
            if ! command -v python3 &> /dev/null; then
                print_error "Python3未安装"
                exit 1
            fi
            ;;
    esac
    
    print_success "依赖检查通过"
}

# 准备部署环境
prepare_environment() {
    print_info "准备部署环境..."
    
    # 创建必要的目录
    mkdir -p logs
    mkdir -p data/postgres
    mkdir -p data/redis
    mkdir -p ssl
    
    # 设置环境变量
    export DEPLOYMENT_TYPE ENVIRONMENT DOMAIN SSL_ENABLED
    
    print_success "环境准备完成"
}

# Docker部署
deploy_docker() {
    print_info "开始Docker部署..."
    
    cd deploy/docker
    
    # 检查docker-compose文件
    if [[ ! -f "docker-compose.yml" ]]; then
        print_error "docker-compose.yml文件不存在"
        exit 1
    fi
    
    # 停止现有服务
    docker-compose down 2>/dev/null || true
    
    # 拉取最新镜像
    print_info "拉取基础镜像..."
    docker-compose pull
    
    # 构建应用镜像
    print_info "构建应用镜像..."
    docker-compose build
    
    # 启动服务
    print_info "启动服务..."
    docker-compose up -d
    
    # 等待服务就绪
    print_info "等待服务启动..."
    sleep 30
    
    # 健康检查
    if docker-compose ps | grep -q "Up"; then
        print_success "Docker服务启动成功"
    else
        print_error "Docker服务启动失败"
        docker-compose logs
        exit 1
    fi
    
    cd ../..
}

# 传统部署
deploy_native() {
    print_info "开始传统部署..."
    
    # 部署后端
    print_info "部署后端API服务..."
    if ! bash deploy/backend/deploy_api_server.sh; then
        print_error "后端部署失败"
        exit 1
    fi
    
    # 部署前端
    print_info "部署前端应用..."
    if ! bash deploy/frontend/deploy_frontend.sh; then
        print_error "前端部署失败"
        exit 1
    fi
    
    print_success "传统部署完成"
}

# 开发环境部署
deploy_dev() {
    print_info "设置开发环境..."
    
    # 设置Python虚拟环境
    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    
    # 安装后端依赖
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
    else
        pip install fastapi uvicorn python-multipart requests pydantic
    fi
    
    print_success "开发环境设置完成"
    
    print_info "启动开发服务器..."
    print_info "后端: python xdan_api_proxy_server_fixed.py"
    print_info "前端: cd frontend && npm run dev (如果有前端项目)"
}

# 健康检查
health_check() {
    print_info "运行健康检查..."
    
    case $DEPLOYMENT_TYPE in
        "docker")
            CHECK_URL="http://localhost/health"
            ;;
        "native")
            CHECK_URL="http://${DOMAIN}/health"
            ;;
        "dev")
            CHECK_URL="http://localhost:8050/health"
            ;;
    esac
    
    # 等待服务就绪
    for i in {1..10}; do
        if curl -f -s $CHECK_URL > /dev/null; then
            print_success "健康检查通过: $CHECK_URL"
            return 0
        fi
        print_info "等待服务就绪... ($i/10)"
        sleep 5
    done
    
    print_warning "健康检查超时，请检查服务状态"
    return 1
}

# 设置监控
setup_monitoring() {
    if [[ "$ENVIRONMENT" == "production" && "$DEPLOYMENT_TYPE" == "docker" ]]; then
        print_info "设置监控服务..."
        
        # Prometheus配置
        cat > deploy/docker/prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'xdan-rag-api'
    static_configs:
      - targets: ['xdan-rag-api:9000']
    scrape_interval: 5s
    metrics_path: '/metrics'

  - job_name: 'nginx'
    static_configs:
      - targets: ['xdan-rag-frontend:80']
EOF
        
        print_success "监控服务配置完成"
    fi
}

# 设置备份
setup_backup() {
    if [[ "$BACKUP_ENABLED" == "true" && "$ENVIRONMENT" == "production" ]]; then
        print_info "设置自动备份..."
        
        # 创建备份脚本
        cat > deploy/scripts/backup.sh << 'EOF'
#!/bin/bash
# 自动备份脚本

BACKUP_DIR="/opt/backups/xdan-rag"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
if docker ps | grep -q xdan-postgres; then
    docker exec xdan-postgres pg_dump -U xdan_user xdan_rag | gzip > $BACKUP_DIR/db_$DATE.sql.gz
fi

# 备份配置文件
tar -czf $BACKUP_DIR/config_$DATE.tar.gz deploy/

# 清理旧备份 (保留30天)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "备份完成: $DATE"
EOF
        
        chmod +x deploy/scripts/backup.sh
        
        # 添加到crontab (每天凌晨2点备份)
        if command -v crontab &> /dev/null; then
            (crontab -l 2>/dev/null; echo "0 2 * * * $(pwd)/deploy/scripts/backup.sh") | crontab -
            print_success "自动备份设置完成"
        fi
    fi
}

# 显示部署信息
show_deployment_info() {
    print_success "部署完成！"
    echo ""
    echo "======================================"
    echo "🎉 xDAN RAG Copilot 部署信息"
    echo "======================================"
    echo "部署类型: $DEPLOYMENT_TYPE"
    echo "环境: $ENVIRONMENT"
    echo "域名: $DOMAIN"
    echo "SSL: $SSL_ENABLED"
    echo ""
    
    case $DEPLOYMENT_TYPE in
        "docker")
            echo "🐳 Docker 服务:"
            echo "  API服务: http://localhost:8050"
            echo "  前端应用: http://localhost"
            echo "  Swagger文档: http://localhost/docs"
            echo "  Grafana监控: http://localhost:3000 (admin/admin123)"
            echo ""
            echo "管理命令:"
            echo "  查看状态: docker-compose ps"
            echo "  查看日志: docker-compose logs -f"
            echo "  重启服务: docker-compose restart"
            echo "  停止服务: docker-compose down"
            ;;
        "native")
            echo "🖥️  传统部署:"
            echo "  API服务: http://${DOMAIN}:8050"
            echo "  前端应用: http://${DOMAIN}"
            echo "  Swagger文档: http://${DOMAIN}/docs"
            echo ""
            echo "管理命令:"
            echo "  重启API: sudo systemctl restart xdan-rag-api"
            echo "  重启Nginx: sudo systemctl restart nginx"
            echo "  查看日志: sudo journalctl -u xdan-rag-api -f"
            ;;
        "dev")
            echo "🔧 开发环境:"
            echo "  API服务: http://localhost:8050"
            echo "  Swagger文档: http://localhost:8050/docs"
            echo ""
            echo "启动命令:"
            echo "  source venv/bin/activate"
            echo "  python xdan_api_proxy_server_fixed.py"
            ;;
    esac
    
    echo "======================================"
}

# 主函数
main() {
    parse_args "$@"
    
    print_info "开始部署 xDAN RAG Copilot..."
    print_info "部署类型: $DEPLOYMENT_TYPE"
    print_info "环境: $ENVIRONMENT"
    print_info "域名: $DOMAIN"
    echo ""
    
    check_dependencies
    prepare_environment
    
    case $DEPLOYMENT_TYPE in
        "docker")
            setup_monitoring
            deploy_docker
            ;;
        "native")
            deploy_native
            ;;
        "dev")
            deploy_dev
            ;;
        *)
            print_error "不支持的部署类型: $DEPLOYMENT_TYPE"
            exit 1
            ;;
    esac
    
    if [[ "$DEPLOYMENT_TYPE" != "dev" ]]; then
        health_check
        setup_backup
    fi
    
    show_deployment_info
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi