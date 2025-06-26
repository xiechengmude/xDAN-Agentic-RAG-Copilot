# 部署指南 V2 - 重构后架构

## 📋 目录
- [系统架构概览](#系统架构概览)
- [环境要求](#环境要求)
- [本地部署](#本地部署)
- [生产部署](#生产部署)
- [Docker部署](#docker部署)
- [配置说明](#配置说明)
- [监控和维护](#监控和维护)

## 🏗️ 系统架构概览

### 重构后的架构
```
┌─────────────────────────────────────────────────────────────────┐
│                        客户端层 (Frontend)                        │
│                    React + TypeScript + Vite                     │
│                        Port: 5173                                │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API服务层 (API Server)                       │
│                   FastAPI + SQLite + SSE                         │
│                        Port: 8050                                │
│                   src/api/server.py                              │
└─────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
┌───────────────────────────┐    ┌───────────────────────────────┐
│      S3 Service           │    │       Direct Proxy            │
│  (智能问答，使用S3框架)    │    │    (知识库管理接口)           │
│  src/services/s3_service  │    │    直接代理到RAGFlow          │
└───────────────────────────┘    └───────────────────────────────┘
            │                                  │
            ▼                                  ▼
┌───────────────────────────┐    ┌───────────────────────────────┐
│    S3 Framework Core      │    │                               │
│ src/core/s3_framework.py  │    │                               │
└───────────────────────────┘    │                               │
            │                     │                               │
    ┌───────┴────────┐           │                               │
    ▼                ▼           ▼                               ▼
┌─────────┐    ┌─────────────────────────────────────────────────┐
│LiteLLM  │    │              RAGFlow Server                      │
│统一LLM  │    │            知识库存储和检索                        │
│路由管理 │    │           http://150.109.16.195:7080             │
└─────────┘    └─────────────────────────────────────────────────┘
     │
     ├─→ xDAN-R2 (Agent模型)
     ├─→ DeepSeek (生成模型)
     └─→ OpenAI兼容接口
```

### 核心组件说明
1. **API Server** (`src/api/server.py`)
   - 统一的API入口
   - 管理聊天会话和消息历史
   - 集成S3框架进行智能问答
   - 代理RAGFlow知识库操作

2. **S3 Framework** (`src/core/s3_framework.py`)
   - Search-Select-Synthesize智能编排
   - 多轮迭代搜索
   - 智能文档筛选

3. **LiteLLM** (`src/clients/litellm_client.py`)
   - 统一的LLM路由
   - 成本优化
   - 故障转移

4. **RAGFlow Client** (`src/clients/ragflow_client.py`)
   - 知识库检索
   - 文档管理

## 💻 环境要求

### 基础环境
- Python 3.11+
- Node.js 18+ (前端)
- Git

### Python依赖
```txt
# requirements.txt 核心依赖
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
httpx>=0.27.0
litellm>=1.0.0
pydantic>=2.0.0
python-multipart>=0.0.5
sse-starlette>=2.0.0
```

## 🚀 本地部署

### 1. 克隆代码
```bash
git clone <repository-url>
cd ragflow-api-client
```

### 2. 配置文件

#### 创建config.yaml
```bash
cp config.example.yaml config.yaml
```

编辑配置文件：
```yaml
# config.yaml
# RAGFlow配置
ragflow:
  api_url: ${RAGFLOW_API_URL:http://150.109.16.195:7080}
  api_key: ${RAGFLOW_API_KEY}
  default_dataset_id: ${DEFAULT_DATASET_ID}

# LiteLLM配置
litellm:
  # 代理配置（可选）
  proxy:
    http: ${HTTP_PROXY:}
    https: ${HTTPS_PROXY:}
  
  # 模型提供商配置
  providers:
    - provider: xdan_search
      api_key: ${XDAN_API_KEY:sk-empty}
      base_url: ${XDAN_BASE_URL:http://209.20.158.204:8001/v1}
      models:
        - name: xDAN-R2-Qwen3-14b-RagRL-step450-0618
          max_tokens: 4096
          temperature: 0.1
    
    - provider: deepseek
      api_key: ${DEEPSEEK_API_KEY}
      base_url: https://api.deepseek.com/v1
      models:
        - name: deepseek-chat
          max_tokens: 4096
          temperature: 0.7
    
    - provider: openai
      api_key: ${OPENAI_API_KEY}
      base_url: ${OPENAI_BASE_URL:http://43.134.187.48:7220/v1}
      models:
        - name: gpt-4o-mini
          max_tokens: 4096

# S3框架配置
s3_framework:
  agent_model: xDAN-R2-Qwen3-14b-RagRL-step450-0618
  generation_model: deepseek-chat
  max_search_rounds: 3
  search_top_k: 10
```

#### 创建.env文件
```bash
cp .env.example .env
```

编辑环境变量：
```bash
# RAGFlow配置
RAGFLOW_API_URL=http://150.109.16.195:7080
RAGFLOW_API_KEY=your_ragflow_api_key
DEFAULT_DATASET_ID=your_default_dataset_id

# LLM配置
XDAN_API_KEY=sk-empty
XDAN_BASE_URL=http://209.20.158.204:8001/v1
DEEPSEEK_API_KEY=your_deepseek_api_key
OPENAI_API_KEY=your_openai_api_key

# 代理配置（可选）
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

### 3. 安装依赖

#### 使用uv（推荐）
```bash
# 安装uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境并安装依赖
uv venv
source .venv/bin/activate  # Linux/macOS
uv pip install -r requirements.txt
```

#### 使用pip
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

### 4. 启动服务
```bash
# 方式1：使用uv运行
uv run python -m src.api.server

# 方式2：直接运行
python -m src.api.server

# 方式3：使用uvicorn
uvicorn src.api.server:app --host 0.0.0.0 --port 8050 --reload
```

### 5. 验证部署
- API文档：http://localhost:8050/docs
- 健康检查：http://localhost:8050/health

## 🌐 生产部署

### 1. 系统要求
- Ubuntu 20.04+ / CentOS 8+
- Python 3.11+
- Nginx (反向代理)
- Supervisor (进程管理)
- PostgreSQL 15+ (可选，替代SQLite)

### 2. 安装依赖
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

# 安装系统依赖
sudo apt install nginx supervisor postgresql git
```

### 3. 创建应用用户
```bash
sudo useradd -m -s /bin/bash xdan
sudo su - xdan
```

### 4. 部署应用
```bash
# 克隆代码
git clone <repository-url> /home/xdan/ragflow-api-client
cd /home/xdan/ragflow-api-client

# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install gunicorn
```

### 5. 配置Gunicorn
创建 `gunicorn_config.py`:
```python
bind = "127.0.0.1:8050"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 60
keepalive = 5
accesslog = "/home/xdan/ragflow-api-client/logs/access.log"
errorlog = "/home/xdan/ragflow-api-client/logs/error.log"
loglevel = "info"
```

### 6. 配置Supervisor
创建 `/etc/supervisor/conf.d/xdan-api.conf`:
```ini
[program:xdan-api]
command=/home/xdan/ragflow-api-client/venv/bin/gunicorn src.api.server:app -c /home/xdan/ragflow-api-client/gunicorn_config.py
directory=/home/xdan/ragflow-api-client
user=xdan
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/xdan/ragflow-api-client/logs/supervisor.log
environment=PATH="/home/xdan/ragflow-api-client/venv/bin",HOME="/home/xdan"
```

### 7. 配置Nginx
创建 `/etc/nginx/sites-available/xdan-api`:
```nginx
upstream xdan_api {
    server 127.0.0.1:8050;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL配置
    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # 代理配置
    location / {
        proxy_pass http://xdan_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE支持
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
    
    # 静态文件
    location /static {
        alias /home/xdan/ragflow-api-client/static;
    }
}
```

### 8. 启动服务
```bash
# 启用Nginx配置
sudo ln -s /etc/nginx/sites-available/xdan-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 启动Supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start xdan-api
```

## 🐳 Docker部署

### 1. 创建Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p logs data

# 暴露端口
EXPOSE 8050

# 启动命令
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8050"]
```

### 2. 创建docker-compose.yml
```yaml
version: '3.8'

services:
  api:
    build: .
    container_name: xdan-api
    ports:
      - "8050:8050"
    environment:
      - RAGFLOW_API_URL=${RAGFLOW_API_URL}
      - RAGFLOW_API_KEY=${RAGFLOW_API_KEY}
      - DEFAULT_DATASET_ID=${DEFAULT_DATASET_ID}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - HTTP_PROXY=${HTTP_PROXY}
      - HTTPS_PROXY=${HTTPS_PROXY}
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8050/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 3. 构建和运行
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## ⚙️ 配置说明

### 环境变量优先级
1. 系统环境变量
2. .env文件
3. config.yaml中的默认值

### 数据库配置
默认使用SQLite，生产环境建议切换到PostgreSQL：

1. 安装PostgreSQL
2. 创建数据库和用户
3. 修改连接字符串：
```python
# src/api/server.py
DATABASE_URL = "postgresql://user:password@localhost/dbname"
```

### 日志配置
```python
# 日志级别
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 日志格式
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
```

## 📊 监控和维护

### 健康检查
```bash
# 检查服务状态
curl http://localhost:8050/health

# 预期响应
{
  "status": "healthy",
  "ragflow": true,
  "litellm": true,
  "s3_framework": true,
  "database": true
}
```

### 日志监控
```bash
# 查看应用日志
tail -f logs/app.log

# 查看访问日志
tail -f logs/access.log

# 查看错误日志
tail -f logs/error.log
```

### 性能监控
1. **API响应时间**：通过Nginx日志分析
2. **内存使用**：`ps aux | grep python`
3. **CPU使用**：`top -p $(pgrep -f "src.api.server")`

### 备份策略
```bash
# 备份数据库（SQLite）
cp data/chat.db data/chat.db.backup.$(date +%Y%m%d)

# 备份配置
tar -czf config_backup_$(date +%Y%m%d).tar.gz config.yaml .env

# 定期清理日志
find logs/ -name "*.log" -mtime +30 -delete
```

### 故障排查
1. **服务无法启动**
   - 检查端口占用：`lsof -i :8050`
   - 检查配置文件
   - 查看错误日志

2. **API调用失败**
   - 检查RAGFlow连接
   - 验证API密钥
   - 查看代理设置

3. **性能问题**
   - 增加worker数量
   - 优化数据库查询
   - 启用缓存

## 🔐 安全建议

1. **使用HTTPS**：生产环境必须启用SSL
2. **API密钥管理**：使用环境变量，不要硬编码
3. **访问控制**：配置防火墙规则
4. **定期更新**：及时更新依赖包
5. **日志脱敏**：不要记录敏感信息

## 📝 更新日志

- **2025-06-26**: 重构后的部署文档
  - 简化部署流程
  - 统一配置管理
  - 优化生产部署