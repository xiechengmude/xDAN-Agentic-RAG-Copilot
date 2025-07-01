# FlashSearch Docker 部署指南

## 快速开始

### 1. 使用管理脚本（推荐）

```bash
# 启动本地服务（非Docker）
./manage-services.sh start-local

# 使用Docker启动服务
./manage-services.sh start-docker

# 查看服务状态
./manage-services.sh status

# 停止所有服务
./manage-services.sh stop
```

### 2. 直接使用 Docker Compose

#### 开发环境（推荐用于本地开发）
```bash
# 启动API和MCP服务
docker-compose -f docker-compose-dev.yml up -d api mcp

# 启动所有服务（包括Langfuse）
docker-compose -f docker-compose-dev.yml up -d

# 查看日志
docker-compose -f docker-compose-dev.yml logs -f

# 停止服务
docker-compose -f docker-compose-dev.yml down
```

#### 生产环境
```bash
cd server
# 构建并启动
docker-compose -f docker-compose-flashsearch.yml up -d --build

# 查看日志
docker-compose -f docker-compose-flashsearch.yml logs -f

# 停止服务
docker-compose -f docker-compose-flashsearch.yml down
```

## 服务端点

- **API服务**: http://localhost:8060
  - 健康检查: http://localhost:8060/health
  - API文档: http://localhost:8060/docs
  - 搜索接口: POST http://localhost:8060/search

- **MCP服务**: http://localhost:9060
  - SSE端点: http://localhost:9060/sse/
  - 工具列表: 通过MCP客户端访问

- **Langfuse** (可选): http://localhost:3000
  - 默认凭据需要在首次访问时设置

## 配置说明

### 环境变量
确保根目录下有 `.env` 文件，包含以下配置：
```bash
# API Keys
OPENAI_API_KEY=your_key
BRIGHTDATA_API_KEY=your_key
FIRECRAWL_API_KEY=your_key

# Langfuse (可选)
LANGFUSE_PUBLIC_KEY=your_key
LANGFUSE_SECRET_KEY=your_key
LANGFUSE_HOST=http://localhost:3000
```

### Docker Compose 文件说明

1. **docker-compose-dev.yml** (根目录)
   - 用于本地开发
   - 直接挂载源代码，支持热重载
   - 包含Langfuse服务（可选）

2. **docker-compose-flashsearch.yml** (server目录)
   - 用于生产部署
   - 构建独立的Docker镜像
   - 更严格的资源限制和健康检查

## 故障排查

### 端口占用
```bash
# 检查端口占用
lsof -i :8060
lsof -i :9060

# 强制停止占用端口的进程
kill -9 $(lsof -ti:8060)
kill -9 $(lsof -ti:9060)
```

### Docker相关
```bash
# 查看容器状态
docker ps -a

# 查看容器日志
docker logs flashsearch-api-dev
docker logs flashsearch-mcp-dev

# 进入容器调试
docker exec -it flashsearch-api-dev bash
```

### 网络问题
```bash
# 检查Docker网络
docker network ls
docker network inspect flashsearch-dev-net

# 重建网络
docker-compose -f docker-compose-dev.yml down
docker network prune
docker-compose -f docker-compose-dev.yml up -d
```

## 性能优化

### 1. 资源限制
在生产环境中，可以添加资源限制：
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### 2. 缓存配置
启用Redis缓存（在docker-compose中已包含）：
```yaml
environment:
  - REDIS_URL=redis://redis:6379
```

### 3. 日志管理
限制日志大小：
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 部署检查清单

- [ ] 确认 `.env` 文件包含所有必需的API密钥
- [ ] 确认端口 8060 和 9060 未被占用
- [ ] 确认 Docker 已安装并运行
- [ ] 确认有足够的系统资源（至少4GB内存）
- [ ] 运行健康检查确认服务正常