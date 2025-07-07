# FlashSearch API 部署文档

## 概述

FlashSearch API 是基于 S3 架构（Search-Select-Synthesize）的智能搜索系统，提供高质量的在线搜索和知识问答能力。

## 快速开始

### 1. 环境要求

- Python 3.8+
- 无需数据库（可选配置）
- 外部API密钥：BrightData、FireCrawl、DeepSeek

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制环境变量模板并编辑：

```bash
cp .env.example .env
```

必需的配置项：
- `BRIGHTDATA_API_KEY`: BrightData SERP API密钥
- `FIRECRAWL_API_KEY`: FireCrawl网页爬取API密钥
- `DEEPSEEK_API_KEY`: DeepSeek LLM API密钥

### 4. 启动API服务器

#### 方法1: 使用测试服务器（推荐用于开发和测试）

```bash
cd tests/v1.0
python3 test_api_server_real.py
```

服务器将在 `http://localhost:8000` 启动。

#### 方法2: 使用启动脚本（推荐用于生产环境）

```bash
./start-flash-api-no-db.sh
```

服务器将在 `http://localhost:8060` 启动。

## API 使用说明

### 健康检查

```bash
curl http://localhost:8000/health
```

### 搜索API

```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "什么是人工智能？",
    "mode": "flash",
    "max_rounds": 1
  }'
```

支持的搜索模式：
- `flash`: 快速搜索（约30-60秒）
- `standard`: 标准搜索（约60-120秒）
- `deep`: 深度搜索（约120-180秒）

## 架构说明

### S3 架构流程

1. **Search（搜索）**: 使用 BrightData SERP API 进行在线搜索
2. **Select（选择）**: 智能筛选最相关的搜索结果
3. **Synthesize（综合）**: 使用 DeepSeek LLM 生成高质量答案

### 核心特性

- **无数据库依赖**: 轻量级部署，专注搜索功能
- **真实时响应**: Flash模式约45秒，Standard模式约90秒
- **高质量答案**: 结构化输出，包含来源引用
- **灵活配置**: 支持多种搜索模式和参数调整

## 性能优化

### 1. 禁用本地代理

如果遇到网络问题，请确保禁用本地代理：

```bash
unset http_proxy
unset https_proxy
export NO_PROXY="*"
```

### 2. 并发配置

修改 `config.yaml` 中的并发设置：

```yaml
search:
  max_concurrent_requests: 3
  request_timeout: 60
```

### 3. 缓存优化

启用搜索结果缓存（开发中）：

```yaml
cache:
  enabled: true
  ttl: 3600
```

## 故障排查

### 常见问题

1. **API调用失败**
   - 检查API密钥是否正确
   - 确认网络连接正常
   - 查看是否有代理干扰

2. **响应时间过长**
   - 这是正常的，真实搜索需要时间
   - Flash模式通常需要30-60秒
   - 可以调整搜索轮数减少时间

3. **服务器启动失败**
   - 检查端口是否被占用
   - 确认Python环境正确
   - 查看日志文件获取详细错误

### 日志位置

- API日志：`logs/api.log`
- 搜索日志：`logs/search.log`
- 错误日志：`logs/error.log`

## 生产部署建议

1. **使用进程管理器**

```bash
# 使用 systemd
sudo systemctl start flashsearch-api

# 使用 supervisor
supervisorctl start flashsearch-api
```

2. **配置反向代理**

使用 Nginx 配置：

```nginx
server {
    listen 80;
    server_name api.flashsearch.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. **监控和告警**

- 使用 Prometheus + Grafana 监控
- 设置响应时间和错误率告警
- 定期检查API密钥使用量

## 更新历史

### v1.0.0 (2025-07-07)

- 初始版本发布
- 实现真实的S3架构搜索
- 支持三种搜索模式
- 解决代理冲突问题
- 优化测试框架

## 联系支持

如有问题，请提交 Issue 到：[GitHub仓库](https://github.com/xiechengmude/xDAN-Agentic-RAG-Copilot)