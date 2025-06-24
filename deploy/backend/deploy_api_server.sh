#!/bin/bash
set -e

# xDAN RAG Copilot API Server 后端部署脚本
# 支持开发环境和生产环境部署

echo "🚀 xDAN RAG Copilot API Server 部署脚本"
echo "======================================"

# 配置参数
PROJECT_NAME="xdan-rag-api"
PROJECT_DIR="/opt/${PROJECT_NAME}"
SERVICE_NAME="xdan-rag-api"
SERVICE_USER="xdan"
PYTHON_VERSION="3.11"
PORT="${PORT:-8050}"
ENVIRONMENT="${ENVIRONMENT:-production}"

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

# 检查运行权限
check_permissions() {
    if [[ $EUID -ne 0 ]] && [[ "$ENVIRONMENT" == "production" ]]; then
        print_error "生产环境部署需要root权限，请使用 sudo 运行此脚本"
        exit 1
    fi
}

# 检查系统环境
check_system() {
    print_info "检查系统环境..."
    
    # 检查操作系统
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if command -v apt-get &> /dev/null; then
            DISTRO="ubuntu"
        elif command -v yum &> /dev/null; then
            DISTRO="centos"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        print_error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
    
    print_success "操作系统: $OS"
}

# 安装系统依赖
install_system_dependencies() {
    print_info "安装系统依赖..."
    
    case $OS in
        "linux")
            case $DISTRO in
                "ubuntu")
                    apt-get update
                    apt-get install -y python3 python3-pip python3-venv nginx supervisor git curl
                    ;;
                "centos")
                    yum update -y
                    yum install -y python3 python3-pip nginx supervisor git curl
                    ;;
            esac
            ;;
        "macos")
            if ! command -v brew &> /dev/null; then
                print_error "请先安装 Homebrew: https://brew.sh/"
                exit 1
            fi
            brew install python@${PYTHON_VERSION} nginx
            ;;
    esac
    
    print_success "系统依赖安装完成"
}

# 创建服务用户
create_service_user() {
    if [[ "$ENVIRONMENT" == "production" && "$OS" == "linux" ]]; then
        print_info "创建服务用户: $SERVICE_USER"
        
        if ! id "$SERVICE_USER" &>/dev/null; then
            useradd -r -m -s /bin/bash $SERVICE_USER
            print_success "服务用户创建完成"
        else
            print_info "服务用户已存在"
        fi
    fi
}

# 创建项目目录
setup_project_directory() {
    print_info "设置项目目录: $PROJECT_DIR"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        mkdir -p $PROJECT_DIR
        chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR
    else
        PROJECT_DIR="$(pwd)"
    fi
    
    print_success "项目目录设置完成"
}

# 部署应用代码
deploy_application() {
    print_info "部署应用代码..."
    
    # 复制代码到目标目录
    if [[ "$ENVIRONMENT" == "production" ]]; then
        cp -r ../xdan_api_proxy_server_fixed.py $PROJECT_DIR/
        cp -r ../requirements.txt $PROJECT_DIR/ 2>/dev/null || echo "requirements.txt not found, creating..."
        
        # 创建requirements.txt如果不存在
        if [[ ! -f "$PROJECT_DIR/requirements.txt" ]]; then
            cat > $PROJECT_DIR/requirements.txt << EOF
fastapi==0.115.13
uvicorn==0.34.3
python-multipart==0.0.20
requests==2.32.4
pydantic==2.11.7
EOF
        fi
        
        chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR
    fi
    
    print_success "应用代码部署完成"
}

# 设置Python虚拟环境
setup_virtual_environment() {
    print_info "设置Python虚拟环境..."
    
    cd $PROJECT_DIR
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        sudo -u $SERVICE_USER python3 -m venv venv
        sudo -u $SERVICE_USER ./venv/bin/pip install --upgrade pip
        sudo -u $SERVICE_USER ./venv/bin/pip install -r requirements.txt
    else
        if [[ ! -d "venv" ]]; then
            python3 -m venv venv
        fi
        ./venv/bin/pip install --upgrade pip
        ./venv/bin/pip install -r requirements.txt 2>/dev/null || {
            print_warning "requirements.txt not found, installing basic dependencies..."
            ./venv/bin/pip install fastapi uvicorn python-multipart requests pydantic
        }
    fi
    
    print_success "Python虚拟环境设置完成"
}

# 创建配置文件
create_config_files() {
    print_info "创建配置文件..."
    
    # 创建环境配置文件
    cat > $PROJECT_DIR/.env << EOF
# xDAN RAG Copilot API Server Configuration
ENVIRONMENT=$ENVIRONMENT
PORT=$PORT
HOST=0.0.0.0
LOG_LEVEL=info
RAGFLOW_API_URL=http://150.109.16.195:7080
RAGFLOW_API_KEY=ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm
EOF
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        chown $SERVICE_USER:$SERVICE_USER $PROJECT_DIR/.env
        chmod 600 $PROJECT_DIR/.env
    fi
    
    print_success "配置文件创建完成"
}

# 创建systemd服务文件
create_systemd_service() {
    if [[ "$ENVIRONMENT" == "production" && "$OS" == "linux" ]]; then
        print_info "创建systemd服务文件..."
        
        cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=xDAN RAG Copilot API Server
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/python xdan_api_proxy_server_fixed.py
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        systemctl daemon-reload
        systemctl enable ${SERVICE_NAME}
        
        print_success "systemd服务文件创建完成"
    fi
}

# 配置Nginx反向代理
configure_nginx() {
    if [[ "$ENVIRONMENT" == "production" ]]; then
        print_info "配置Nginx反向代理..."
        
        cat > /etc/nginx/sites-available/${SERVICE_NAME} << EOF
server {
    listen 80;
    server_name _;
    
    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # SSE支持
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
    
    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
    
    # Swagger文档
    location /docs {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
    
    # 静态文件 (如果有前端)
    location / {
        root /var/www/html;
        try_files \$uri \$uri/ /index.html;
    }
}
EOF
        
        # 启用站点
        if [[ "$OS" == "linux" ]]; then
            ln -sf /etc/nginx/sites-available/${SERVICE_NAME} /etc/nginx/sites-enabled/
            rm -f /etc/nginx/sites-enabled/default
        fi
        
        # 测试Nginx配置
        nginx -t
        
        print_success "Nginx配置完成"
    fi
}

# 设置防火墙
setup_firewall() {
    if [[ "$ENVIRONMENT" == "production" && "$OS" == "linux" ]]; then
        print_info "配置防火墙..."
        
        if command -v ufw &> /dev/null; then
            ufw allow 80/tcp
            ufw allow 443/tcp
            ufw allow ssh
            print_success "UFW防火墙配置完成"
        elif command -v firewall-cmd &> /dev/null; then
            firewall-cmd --permanent --add-service=http
            firewall-cmd --permanent --add-service=https
            firewall-cmd --permanent --add-service=ssh
            firewall-cmd --reload
            print_success "firewalld防火墙配置完成"
        fi
    fi
}

# 启动服务
start_services() {
    print_info "启动服务..."
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        if [[ "$OS" == "linux" ]]; then
            systemctl start ${SERVICE_NAME}
            systemctl start nginx
            systemctl reload nginx
            
            print_success "服务启动完成"
            
            # 检查服务状态
            if systemctl is-active --quiet ${SERVICE_NAME}; then
                print_success "API服务运行正常"
            else
                print_error "API服务启动失败"
                systemctl status ${SERVICE_NAME}
                exit 1
            fi
            
            if systemctl is-active --quiet nginx; then
                print_success "Nginx服务运行正常"
            else
                print_error "Nginx服务启动失败"
                systemctl status nginx
                exit 1
            fi
        fi
    else
        print_info "开发环境启动命令:"
        print_info "cd $PROJECT_DIR && ./venv/bin/python xdan_api_proxy_server_fixed.py"
    fi
}

# 运行健康检查
health_check() {
    print_info "运行健康检查..."
    
    # 等待服务启动
    sleep 5
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        CHECK_URL="http://localhost/health"
    else
        CHECK_URL="http://localhost:$PORT/health"
    fi
    
    if curl -f -s $CHECK_URL > /dev/null; then
        print_success "健康检查通过: $CHECK_URL"
    else
        print_warning "健康检查失败，请检查服务状态"
    fi
}

# 显示部署信息
show_deployment_info() {
    print_success "部署完成！"
    echo ""
    echo "======================================"
    echo "🎉 xDAN RAG Copilot API Server 部署信息"
    echo "======================================"
    echo "环境: $ENVIRONMENT"
    echo "项目目录: $PROJECT_DIR"
    echo "服务端口: $PORT"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        echo "API地址: http://your-server/api/v1/"
        echo "健康检查: http://your-server/health"
        echo "Swagger文档: http://your-server/docs"
        echo ""
        echo "服务管理命令:"
        echo "  启动: sudo systemctl start $SERVICE_NAME"
        echo "  停止: sudo systemctl stop $SERVICE_NAME"
        echo "  重启: sudo systemctl restart $SERVICE_NAME"
        echo "  状态: sudo systemctl status $SERVICE_NAME"
        echo "  日志: sudo journalctl -u $SERVICE_NAME -f"
    else
        echo "API地址: http://localhost:$PORT/api/v1/"
        echo "健康检查: http://localhost:$PORT/health"
        echo "Swagger文档: http://localhost:$PORT/docs"
        echo ""
        echo "启动命令:"
        echo "  cd $PROJECT_DIR && ./venv/bin/python xdan_api_proxy_server_fixed.py"
    fi
    
    echo ""
    echo "配置文件: $PROJECT_DIR/.env"
    echo "======================================"
}

# 主函数
main() {
    echo "开始部署 xDAN RAG Copilot API Server..."
    echo "环境: $ENVIRONMENT"
    echo "端口: $PORT"
    echo ""
    
    check_permissions
    check_system
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        install_system_dependencies
        create_service_user
    fi
    
    setup_project_directory
    deploy_application
    setup_virtual_environment
    create_config_files
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        create_systemd_service
        configure_nginx
        setup_firewall
    fi
    
    start_services
    health_check
    show_deployment_info
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi