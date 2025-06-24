#!/bin/bash
set -e

# xDAN RAG Copilot Frontend 前端部署脚本
# 支持 React/Vue/Angular 等现代前端框架

echo "🚀 xDAN RAG Copilot Frontend 部署脚本"
echo "====================================="

# 配置参数
PROJECT_NAME="xdan-rag-frontend"
PROJECT_DIR="/var/www/${PROJECT_NAME}"
SERVICE_USER="www-data"
NODE_VERSION="18"
BUILD_DIR="dist"
ENVIRONMENT="${ENVIRONMENT:-production}"
DOMAIN="${DOMAIN:-localhost}"
SSL_ENABLED="${SSL_ENABLED:-false}"

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

# 安装Node.js和npm
install_nodejs() {
    print_info "安装Node.js $NODE_VERSION..."
    
    # 检查是否已安装正确版本的Node.js
    if command -v node &> /dev/null; then
        CURRENT_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
        if [[ "$CURRENT_VERSION" -ge "$NODE_VERSION" ]]; then
            print_success "Node.js已安装，版本: $(node -v)"
            return
        fi
    fi
    
    case $OS in
        "linux")
            # 使用NodeSource仓库安装Node.js
            curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash -
            case $DISTRO in
                "ubuntu")
                    apt-get install -y nodejs
                    ;;
                "centos")
                    yum install -y nodejs npm
                    ;;
            esac
            ;;
        "macos")
            if command -v brew &> /dev/null; then
                brew install node@${NODE_VERSION}
            else
                print_error "请先安装 Homebrew 或手动安装 Node.js"
                exit 1
            fi
            ;;
    esac
    
    # 安装yarn (可选)
    npm install -g yarn
    
    print_success "Node.js安装完成: $(node -v)"
    print_success "npm版本: $(npm -v)"
}

# 安装系统依赖
install_system_dependencies() {
    print_info "安装系统依赖..."
    
    case $OS in
        "linux")
            case $DISTRO in
                "ubuntu")
                    apt-get update
                    apt-get install -y nginx git curl build-essential
                    ;;
                "centos")
                    yum update -y
                    yum install -y nginx git curl gcc-c++ make
                    ;;
            esac
            ;;
        "macos")
            if command -v brew &> /dev/null; then
                brew install nginx git
            fi
            ;;
    esac
    
    print_success "系统依赖安装完成"
}

# 设置项目目录
setup_project_directory() {
    print_info "设置项目目录: $PROJECT_DIR"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        mkdir -p $PROJECT_DIR
        mkdir -p $PROJECT_DIR/src
        mkdir -p $PROJECT_DIR/build
        
        if [[ "$OS" == "linux" ]]; then
            chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR
        fi
    else
        PROJECT_DIR="$(pwd)/frontend"
        mkdir -p $PROJECT_DIR
    fi
    
    print_success "项目目录设置完成"
}

# 创建示例前端应用
create_sample_frontend() {
    print_info "创建示例前端应用..."
    
    cd $PROJECT_DIR
    
    # 检查是否已存在前端项目
    if [[ -f "package.json" ]]; then
        print_info "发现现有前端项目，跳过初始化"
        return
    fi
    
    # 创建package.json
    cat > package.json << EOF
{
  "name": "xdan-rag-frontend",
  "version": "1.0.0",
  "description": "xDAN RAG Copilot Frontend Application",
  "main": "index.js",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "serve": "http-server dist -p 3000"
  },
  "dependencies": {
    "axios": "^1.6.0",
    "vue": "^3.3.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.5.0",
    "vite": "^5.0.0",
    "http-server": "^14.1.1"
  }
}
EOF
    
    # 创建vite配置
    cat > vite.config.js << EOF
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8050',
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets'
  }
})
EOF
    
    # 创建index.html
    cat > index.html << EOF
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>xDAN RAG Copilot</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .chat-container { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .message { margin-bottom: 15px; padding: 10px; border-radius: 8px; }
        .user { background: #007bff; color: white; margin-left: 20%; }
        .assistant { background: #f1f1f1; margin-right: 20%; }
        .input-area { display: flex; gap: 10px; margin-top: 20px; }
        .input-area input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 4px; }
        .input-area button { padding: 12px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .input-area button:hover { background: #0056b3; }
        .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .status.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <div id="app">
        <div class="container">
            <div class="header">
                <h1>🤖 xDAN RAG Copilot</h1>
                <p>智能对话助手 - 基于知识库的问答系统</p>
                <div v-if="status" :class="['status', status.type]">{{ status.message }}</div>
            </div>
            
            <div class="chat-container">
                <div class="messages">
                    <div v-for="message in messages" :key="message.id" :class="['message', message.role]">
                        <strong>{{ message.role === 'user' ? '用户' : 'AI助手' }}:</strong>
                        {{ message.content }}
                    </div>
                </div>
                
                <div class="input-area">
                    <input 
                        v-model="inputMessage" 
                        @keyup.enter="sendMessage"
                        placeholder="请输入您的问题..."
                        :disabled="loading"
                    />
                    <button @click="sendMessage" :disabled="loading">
                        {{ loading ? '发送中...' : '发送' }}
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script type="module" src="/src/main.js"></script>
</body>
</html>
EOF
    
    # 创建src目录和主要文件
    mkdir -p src
    
    cat > src/main.js << EOF
import { createApp } from 'vue'
import App from './App.vue'

createApp(App).mount('#app')
EOF
    
    cat > src/App.vue << EOF
<template>
  <div class="container">
    <div class="header">
      <h1>🤖 xDAN RAG Copilot</h1>
      <p>智能对话助手 - 基于知识库的问答系统</p>
      <div v-if="status" :class="['status', status.type]">{{ status.message }}</div>
    </div>
    
    <div class="chat-container">
      <div class="messages">
        <div v-for="message in messages" :key="message.id" :class="['message', message.role]">
          <strong>{{ message.role === 'user' ? '用户' : 'AI助手' }}:</strong>
          {{ message.content }}
        </div>
      </div>
      
      <div class="input-area">
        <input 
          v-model="inputMessage" 
          @keyup.enter="sendMessage"
          placeholder="请输入您的问题..."
          :disabled="loading"
        />
        <button @click="sendMessage" :disabled="loading">
          {{ loading ? '发送中...' : '发送' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'App',
  setup() {
    const messages = ref([])
    const inputMessage = ref('')
    const loading = ref(false)
    const status = ref(null)
    
    // 检查API健康状态
    const checkHealth = async () => {
      try {
        const response = await axios.get('/api/health')
        if (response.data.code === 0) {
          status.value = { type: 'success', message: 'API服务连接正常' }
        }
      } catch (error) {
        status.value = { type: 'error', message: 'API服务连接失败' }
      }
    }
    
    // 发送消息
    const sendMessage = async () => {
      if (!inputMessage.value.trim() || loading.value) return
      
      const userMessage = {
        id: Date.now(),
        role: 'user',
        content: inputMessage.value
      }
      
      messages.value.push(userMessage)
      loading.value = true
      
      try {
        // 这里可以接入实际的API调用
        // const response = await axios.post('/api/v1/chat', {
        //   question: inputMessage.value
        // })
        
        // 模拟AI响应
        setTimeout(() => {
          const aiMessage = {
            id: Date.now() + 1,
            role: 'assistant',
            content: \`您好！您问的是："\${inputMessage.value}"。这是一个示例回答，实际部署时会连接到真实的xDAN RAG API。\`
          }
          messages.value.push(aiMessage)
          loading.value = false
        }, 1000)
        
      } catch (error) {
        status.value = { type: 'error', message: '发送消息失败' }
        loading.value = false
      }
      
      inputMessage.value = ''
    }
    
    onMounted(() => {
      checkHealth()
    })
    
    return {
      messages,
      inputMessage,
      loading,
      status,
      sendMessage
    }
  }
}
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
.container { max-width: 1200px; margin: 0 auto; padding: 20px; }
.header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.chat-container { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.message { margin-bottom: 15px; padding: 10px; border-radius: 8px; }
.user { background: #007bff; color: white; margin-left: 20%; }
.assistant { background: #f1f1f1; margin-right: 20%; }
.input-area { display: flex; gap: 10px; margin-top: 20px; }
.input-area input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 4px; }
.input-area button { padding: 12px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
.input-area button:hover { background: #0056b3; }
.status { padding: 10px; margin: 10px 0; border-radius: 4px; }
.status.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
.status.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
</style>
EOF
    
    print_success "示例前端应用创建完成"
}

# 安装依赖
install_dependencies() {
    print_info "安装前端依赖..."
    
    cd $PROJECT_DIR
    
    if [[ "$ENVIRONMENT" == "production" && "$OS" == "linux" ]]; then
        sudo -u $SERVICE_USER npm install
    else
        npm install
    fi
    
    print_success "前端依赖安装完成"
}

# 构建应用
build_application() {
    print_info "构建前端应用..."
    
    cd $PROJECT_DIR
    
    if [[ "$ENVIRONMENT" == "production" && "$OS" == "linux" ]]; then
        sudo -u $SERVICE_USER npm run build
    else
        npm run build
    fi
    
    if [[ -d "$BUILD_DIR" ]]; then
        print_success "应用构建完成: $BUILD_DIR"
    else
        print_error "应用构建失败"
        exit 1
    fi
}

# 配置Nginx
configure_nginx() {
    if [[ "$ENVIRONMENT" == "production" ]]; then
        print_info "配置Nginx..."
        
        # 创建Nginx配置文件
        cat > /etc/nginx/sites-available/${PROJECT_NAME} << EOF
server {
    listen 80;
    server_name ${DOMAIN};
    root ${PROJECT_DIR}/${BUILD_DIR};
    index index.html;
    
    # 启用gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API代理到后端
    location /api/ {
        proxy_pass http://127.0.0.1:8050;
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
        proxy_pass http://127.0.0.1:8050;
    }
    
    # SPA路由支持
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
EOF
        
        # SSL配置 (如果启用)
        if [[ "$SSL_ENABLED" == "true" ]]; then
            cat >> /etc/nginx/sites-available/${PROJECT_NAME} << EOF

server {
    listen 443 ssl http2;
    server_name ${DOMAIN};
    root ${PROJECT_DIR}/${BUILD_DIR};
    index index.html;
    
    # SSL配置
    ssl_certificate /etc/ssl/certs/${DOMAIN}.crt;
    ssl_certificate_key /etc/ssl/private/${DOMAIN}.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # 重复HTTP配置...
    # (这里省略，实际部署时会包含完整配置)
}
EOF
        fi
        
        # 启用站点
        if [[ "$OS" == "linux" ]]; then
            ln -sf /etc/nginx/sites-available/${PROJECT_NAME} /etc/nginx/sites-enabled/
            rm -f /etc/nginx/sites-enabled/default
        fi
        
        # 测试配置
        nginx -t
        
        print_success "Nginx配置完成"
    fi
}

# 设置文件权限
set_permissions() {
    if [[ "$ENVIRONMENT" == "production" && "$OS" == "linux" ]]; then
        print_info "设置文件权限..."
        
        chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR
        chmod -R 755 $PROJECT_DIR
        
        print_success "文件权限设置完成"
    fi
}

# 启动服务
start_services() {
    print_info "启动服务..."
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        systemctl reload nginx
        
        if systemctl is-active --quiet nginx; then
            print_success "Nginx服务运行正常"
        else
            print_error "Nginx服务启动失败"
            systemctl status nginx
            exit 1
        fi
    else
        print_info "开发环境启动命令:"
        print_info "cd $PROJECT_DIR && npm run dev"
    fi
}

# 健康检查
health_check() {
    print_info "运行健康检查..."
    
    sleep 2
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        CHECK_URL="http://${DOMAIN}"
    else
        CHECK_URL="http://localhost:5173"
    fi
    
    if curl -f -s $CHECK_URL > /dev/null; then
        print_success "前端应用健康检查通过: $CHECK_URL"
    else
        print_warning "前端应用健康检查失败，请检查配置"
    fi
}

# 显示部署信息
show_deployment_info() {
    print_success "前端部署完成！"
    echo ""
    echo "======================================"
    echo "🎉 xDAN RAG Copilot Frontend 部署信息"
    echo "======================================"
    echo "环境: $ENVIRONMENT"
    echo "项目目录: $PROJECT_DIR"
    echo "构建目录: $PROJECT_DIR/$BUILD_DIR"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        echo "访问地址: http://${DOMAIN}"
        if [[ "$SSL_ENABLED" == "true" ]]; then
            echo "HTTPS地址: https://${DOMAIN}"
        fi
        echo ""
        echo "Nginx配置: /etc/nginx/sites-available/${PROJECT_NAME}"
        echo "重启Nginx: sudo systemctl reload nginx"
    else
        echo "开发服务器: http://localhost:5173"
        echo ""
        echo "启动命令:"
        echo "  cd $PROJECT_DIR && npm run dev"
        echo "构建命令:"
        echo "  cd $PROJECT_DIR && npm run build"
    fi
    
    echo "======================================"
}

# 主函数
main() {
    echo "开始部署 xDAN RAG Copilot Frontend..."
    echo "环境: $ENVIRONMENT"
    echo "域名: $DOMAIN"
    echo ""
    
    check_permissions
    check_system
    install_nodejs
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        install_system_dependencies
    fi
    
    setup_project_directory
    create_sample_frontend
    install_dependencies
    build_application
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        configure_nginx
        set_permissions
    fi
    
    start_services
    health_check
    show_deployment_info
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi