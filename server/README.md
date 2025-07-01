# FlashSearch Server 服务层

FlashSearch v2.5.0 的服务层实现，提供 REST API 和 MCP 协议接口。

## 架构概览

```
server/
├── api/                    # FastAPI REST API 服务器
│   └── flash_search_api.py
├── mcp/                    # FastMCP 服务器  
│   └── mira_flash_search.py
├── requirements.txt        # 服务层依赖
├── start_api_server.sh     # API服务器启动脚本
├── start_mcp_server.sh     # MCP服务器启动脚本
└── README.md              # 本文档
```

## 服务特性

### 🔍 FlashSearch v2.5.0 引擎
- **Google关键词优化**: 智能提取3-8个核心关键词，搜索结果提升128%
- **时间感知算子**: 深度理解相对时间词("最近"、"本季度"等)
- **多领域增强**: 新闻、财经、技术、学术、政策等专门优化
- **权威来源**: 整合中美英权威媒体和官方网站
- **Langfuse集成**: 完整的搜索链路追踪和分析

### 🌐 REST API 服务器 (FastAPI)
- **HTTP接口**: 标准RESTful API
- **异步支持**: 高并发处理能力
- **自动文档**: OpenAPI/Swagger文档
- **健康检查**: 服务状态监控
- **统计信息**: 实时性能统计
- **CORS支持**: 跨域请求支持

### 🔌 MCP 服务器 (FastMCP)
- **MCP协议**: Model Context Protocol标准
- **多传输**: STDIO/HTTP/SSE传输协议
- **工具集成**: 搜索工具和分析工具
- **资源暴露**: 服务器统计和配置信息
- **上下文感知**: 进度报告和日志记录

## 快速开始

### 1. 安装依赖

```bash
# 进入服务器目录
cd server

# 安装依赖 
pip install -r requirements.txt

# 安装FastMCP (如果未安装)
pip install fastmcp
```

### 2. 配置环境

确保项目根目录的 `.env` 文件包含必要的API密钥：

```env
# 必需的API密钥
BRIGHTDATA_API_KEY=your_brightdata_key
FIRECRAWL_API_KEY=your_firecrawl_key
DEEPSEEK_API_KEY=your_deepseek_key

# Langfuse配置 (可选)
LANGFUSE_SECRET_KEY=your_langfuse_secret
LANGFUSE_PUBLIC_KEY=your_langfuse_public
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 3. 启动服务

#### 启动 REST API 服务器

```bash
# 开发模式 (支持热重载)
RELOAD=true ./start_api_server.sh

# 生产模式
./start_api_server.sh

# 自定义端口
PORT=8080 ./start_api_server.sh
```

服务地址:
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **统计信息**: http://localhost:8000/stats

#### 启动 MCP 服务器

```bash
# STDIO模式 (适用于本地MCP客户端)
./start_mcp_server.sh

# HTTP模式 (适用于网络MCP客户端)  
TRANSPORT=http ./start_mcp_server.sh

# SSE模式 (服务器发送事件)
TRANSPORT=sse PORT=9001 ./start_mcp_server.sh
```

MCP服务地址:
- **HTTP**: http://localhost:9000/mcp/
- **SSE**: http://localhost:9000/sse/

## API 使用示例

### REST API 

#### 执行搜索

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "比亚迪2024年第三季度财报",
    "domain": "finance",
    "enable_langfuse": true
  }'
```

#### 查询验证

```bash
curl -X POST "http://localhost:8000/validate" \
  -H "Content-Type: application/json" \
  -d '{"query": "最新新能源汽车政策"}'
```

#### 异步搜索

```bash
curl -X POST "http://localhost:8000/search/async" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "人工智能最新突破",
    "domain": "tech"
  }'
```

### MCP 协议

使用支持MCP的客户端连接到服务器:

```python
from fastmcp import Client

# 连接到HTTP MCP服务器
client = Client("http://localhost:9000/mcp/")

# 执行搜索工具
result = await client.call_tool(
    "flash_search", 
    {
        "query": "最近比亚迪财报",
        "domain": "finance"
    }
)
```

## 服务配置

### API 服务器环境变量

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `HOST` | `0.0.0.0` | 服务器主机地址 |
| `PORT` | `8000` | 服务器端口 |
| `WORKERS` | `1` | 工作进程数 |
| `RELOAD` | `false` | 开发模式热重载 |
| `LOG_LEVEL` | `info` | 日志级别 |

### MCP 服务器环境变量

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `TRANSPORT` | `stdio` | 传输协议 (stdio/http/sse) |
| `HOST` | `127.0.0.1` | 服务器主机 (非stdio) |
| `PORT` | `9000` | 服务器端口 (非stdio) |
| `LOG_LEVEL` | `info` | 日志级别 |

## 监控和运维

### 健康检查

```bash
# API服务器健康检查
curl http://localhost:8000/health

# MCP服务器健康检查 (使用工具)
# 通过MCP客户端调用 health_check 工具
```

### 统计信息

```bash
# 获取API服务器统计
curl http://localhost:8000/stats

# 获取MCP服务器统计 (通过资源)
# 访问 mcp://server/stats 资源
```

### 日志

服务器日志通过标准输出输出，可以通过以下方式收集:

```bash
# 启动时重定向日志
./start_api_server.sh > api_server.log 2>&1 &

# 使用systemd (生产环境)
sudo systemctl start flashsearch-api
sudo journalctl -u flashsearch-api -f
```

## 部署建议

### 开发环境
- 使用 `RELOAD=true` 开启热重载
- 单进程运行便于调试
- 使用STDIO模式的MCP服务器

### 生产环境
- 使用反向代理 (Nginx/Apache)
- 多进程部署 (`WORKERS > 1`)
- 配置SSL/TLS
- 使用HTTP模式的MCP服务器
- 配置监控和日志收集

### Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY server/ .
COPY src/ ../src/
COPY .env ../.env

RUN pip install -r requirements.txt

EXPOSE 8000 9000

CMD ["./start_api_server.sh"]
```

## 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   lsof -i :8000  # 查看端口占用
   PORT=8080 ./start_api_server.sh  # 使用其他端口
   ```

2. **API密钥未配置**
   ```bash
   # 检查.env文件
   cat ../.env | grep -E "(BRIGHTDATA|FIRECRAWL|DEEPSEEK)"
   ```

3. **依赖缺失**
   ```bash
   pip install fastmcp  # 安装FastMCP
   pip install -r requirements.txt  # 安装所有依赖
   ```

4. **搜索失败**
   - 检查网络连接
   - 验证API密钥有效性
   - 查看服务器日志

### 性能调优

1. **增加工作进程** (API服务器)
   ```bash
   WORKERS=4 ./start_api_server.sh
   ```

2. **调整超时时间**
   - 在搜索请求中设置 `timeout` 参数
   - 默认超时为30分钟

3. **启用缓存** (需要Redis)
   - 配置Redis连接
   - 缓存搜索结果

## 扩展开发

### 添加新的搜索工具

在MCP服务器中添加新工具:

```python
@mcp.tool(
    name="custom_search",
    description="自定义搜索工具"
)
async def custom_search_tool(
    query: str,
    custom_param: str,
    ctx: Context = None
) -> ToolResult:
    # 实现自定义搜索逻辑
    pass
```

### 添加新的API端点

在API服务器中添加新端点:

```python
@app.post("/custom-endpoint")
async def custom_endpoint(request: CustomRequest):
    # 实现自定义API逻辑
    pass
```

## 许可证

MIT License - 详见项目根目录的 LICENSE 文件