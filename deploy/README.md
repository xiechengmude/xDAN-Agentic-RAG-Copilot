# 🚀 xDAN RAG Copilot 部署指南

## 📋 目录结构

```
deploy/
├── backend/                 # 后端部署
│   └── deploy_api_server.sh # API服务部署脚本
├── frontend/                # 前端部署
│   └── deploy_frontend.sh   # 前端应用部署脚本
├── docker/                  # Docker部署
│   ├── docker-compose.yml   # Docker Compose配置
│   ├── Dockerfile.backend   # 后端Docker镜像
│   ├── Dockerfile.frontend  # 前端Docker镜像
│   ├── nginx.conf          # Nginx配置
│   └── .env.docker         # Docker环境变量
├── scripts/                 # 部署脚本
│   └── deploy.sh           # 一键部署脚本
├── config/                  # 配置文件
└── README.md               # 本文档
```

## 🎯 快速开始

### 方式一：一键部署（推荐）

```bash
# Docker部署（生产环境推荐）
./deploy/scripts/deploy.sh --type docker --env production --domain your-domain.com

# 传统部署
./deploy/scripts/deploy.sh --type native --env production --domain your-domain.com

# 开发环境
./deploy/scripts/deploy.sh --type dev
```

### 方式二：分步部署

#### 1. Docker部署

```bash
cd deploy/docker
docker-compose up -d
```

#### 2. 传统部署

```bash
# 后端部署
./deploy/backend/deploy_api_server.sh

# 前端部署  
./deploy/frontend/deploy_frontend.sh
```

## 🐳 Docker部署（推荐）

### 系统要求

- Docker 20.10+
- Docker Compose 2.0+
- 最少 2GB RAM
- 最少 10GB 磁盘空间

### 快速启动

```bash
# 克隆项目
git clone <repository-url>
cd ragflow-api-client

# 启动所有服务
cd deploy/docker
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 服务访问

- **前端应用**: http://localhost
- **API服务**: http://localhost:8050
- **Swagger文档**: http://localhost/docs
- **Grafana监控**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090

### Docker管理命令

```bash
# 停止所有服务
docker-compose down

# 重启服务
docker-compose restart

# 更新服务
docker-compose pull
docker-compose up -d

# 查看资源使用
docker-compose top

# 清理未使用的资源
docker system prune -a
```

## 🖥️ 传统部署

### 系统要求

- Ubuntu 20.04+ / CentOS 8+ / macOS
- Python 3.11+
- Node.js 18+
- Nginx
- 最少 2GB RAM

### 后端部署

```bash
# 设置环境变量
export ENVIRONMENT=production
export PORT=8050

# 运行部署脚本
sudo ./deploy/backend/deploy_api_server.sh
```

### 前端部署

```bash
# 设置环境变量
export ENVIRONMENT=production
export DOMAIN=your-domain.com
export NODE_VERSION=18

# 运行部署脚本
sudo ./deploy/frontend/deploy_frontend.sh
```

### 服务管理

```bash
# 后端服务
sudo systemctl start xdan-rag-api
sudo systemctl stop xdan-rag-api
sudo systemctl restart xdan-rag-api
sudo systemctl status xdan-rag-api

# Nginx服务
sudo systemctl start nginx
sudo systemctl reload nginx
sudo systemctl status nginx

# 查看日志
sudo journalctl -u xdan-rag-api -f
sudo tail -f /var/log/nginx/access.log
```

## 🔧 开发环境

### 系统要求

- Python 3.11+
- Node.js 18+ (如果有前端开发)

### 后端开发

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install fastapi uvicorn python-multipart requests pydantic

# 启动开发服务器
python xdan_api_proxy_server_fixed.py
```

### 前端开发（如果有）

```bash
cd frontend
npm install
npm run dev
```

## ⚙️ 配置说明

### 环境变量

#### 后端配置

```bash
# 基础配置
ENVIRONMENT=production          # 环境: production/staging/development
PORT=8050                      # 服务端口
HOST=0.0.0.0                   # 绑定地址
LOG_LEVEL=info                 # 日志级别

# RAGFlow API配置
RAGFLOW_API_URL=http://150.109.16.195:7080
RAGFLOW_API_KEY=ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm

# 数据库配置（可选）
DATABASE_URL=postgresql://user:pass@localhost:5432/xdan_rag
REDIS_URL=redis://localhost:6379/0

# 安全配置
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost,http://localhost:3000
```

#### 前端配置

```bash
# 开发配置
NODE_ENV=development
API_BASE_URL=http://localhost:8050

# 生产配置
NODE_ENV=production
API_BASE_URL=https://your-domain.com
```

### Nginx配置

主要配置文件位于：
- Docker: `deploy/docker/nginx.conf`
- 传统部署: `/etc/nginx/sites-available/xdan-rag-frontend`

关键配置点：
- API代理到后端服务
- 静态资源缓存
- SSE流式支持
- 安全头设置

## 📊 监控和日志

### Docker环境

```bash
# 查看所有服务状态
docker-compose ps

# 查看实时日志
docker-compose logs -f [service-name]

# 查看资源使用
docker stats

# 进入容器调试
docker exec -it xdan-rag-api bash
```

### 传统部署

```bash
# 系统服务状态
sudo systemctl status xdan-rag-api nginx

# 应用日志
sudo journalctl -u xdan-rag-api -f
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# 系统资源
htop
df -h
free -h
```

### 监控面板

Grafana监控面板（仅Docker部署）：
- URL: http://localhost:3000
- 用户名: admin
- 密码: admin123

## 🔒 安全配置

### SSL/HTTPS配置

#### 使用Let's Encrypt（推荐）

```bash
# 安装certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### 使用自签名证书（开发环境）

```bash
# 生成证书
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/server.key \
  -out /etc/ssl/certs/server.crt
```

### 防火墙配置

```bash
# Ubuntu (UFW)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# CentOS (firewalld)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## 💾 备份和恢复

### 自动备份

备份脚本会自动创建（生产环境）：
```bash
# 手动执行备份
./deploy/scripts/backup.sh

# 查看备份文件
ls -la /opt/backups/xdan-rag/
```

### 数据库备份

```bash
# Docker环境
docker exec xdan-postgres pg_dump -U xdan_user xdan_rag > backup.sql

# 传统部署
pg_dump -U xdan_user -h localhost xdan_rag > backup.sql
```

### 恢复数据

```bash
# Docker环境
docker exec -i xdan-postgres psql -U xdan_user xdan_rag < backup.sql

# 传统部署
psql -U xdan_user -h localhost xdan_rag < backup.sql
```

## 🚨 故障排除

### 常见问题

#### 1. 服务无法启动

```bash
# 检查端口占用
sudo netstat -tlnp | grep :8050
sudo lsof -i :8050

# 检查日志
docker-compose logs xdan-rag-api
sudo journalctl -u xdan-rag-api -n 100
```

#### 2. API连接失败

```bash
# 检查健康状态
curl -f http://localhost:8050/health

# 检查网络连接
docker network ls
docker network inspect docker_xdan-network
```

#### 3. 前端无法访问后端

```bash
# 检查Nginx配置
sudo nginx -t
sudo nginx -s reload

# 检查代理设置
curl -I http://localhost/api/v1/datasets
```

#### 4. Docker容器问题

```bash
# 重建容器
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 清理Docker资源
docker system prune -a
docker volume prune
```

### 性能优化

#### 1. 后端优化

```bash
# 增加worker进程数
export WORKERS=4

# 调整内存限制
docker update --memory=2g xdan-rag-api
```

#### 2. 前端优化

```bash
# 启用Nginx缓存
# 编辑nginx.conf，添加缓存配置

# 压缩静态资源
# 确保gzip压缩已启用
```

#### 3. 数据库优化

```bash
# PostgreSQL性能调优
# 编辑postgresql.conf
shared_buffers = 256MB
max_connections = 200
```

## 📞 技术支持

### 日志收集

发生问题时，请收集以下日志：

```bash
# Docker环境
docker-compose logs > deployment-logs.txt
docker ps -a >> deployment-logs.txt
docker images >> deployment-logs.txt

# 传统部署
sudo journalctl -u xdan-rag-api -n 1000 > api-logs.txt
sudo tail -n 1000 /var/log/nginx/error.log > nginx-logs.txt
systemctl status xdan-rag-api nginx > service-status.txt
```

### 系统信息

```bash
# 收集系统信息
uname -a > system-info.txt
free -h >> system-info.txt
df -h >> system-info.txt
docker version >> system-info.txt
docker-compose version >> system-info.txt
```

---

**部署完成后，请访问 Swagger 文档验证 API 功能：`http://your-domain/docs`**