# RAGFlow API Client

基于RAGFlow API的知识库管理系统，提供完整的文档处理、检索和对话功能。

## 🌟 特性

- **知识库管理**：完整的知识库CRUD操作
- **文档处理**：支持文档上传、解析、状态跟踪
- **实时通信**：使用Server-Sent Events提供实时状态更新
- **对话功能**：基于知识库的智能问答
- **现代化前端**：Vue 3 + TypeScript + Vite
- **完整API文档**：FastAPI自动生成的交互式文档

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- uv (Python包管理器)

### 1. 克隆仓库
```bash
git clone <repository-url>
cd ragflow-api-client
```

### 2. 环境管理

本项目使用 **uv** 进行Python环境和依赖管理：

```bash
# 安装uv (如果尚未安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境并安装依赖
uv venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 安装Python依赖
uv pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
cd ..
```

### 3. 配置环境

项目使用 `.env` 文件进行环境配置：

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置RAGFlow服务器信息
RAGFLOW_API_URL=http://your-ragflow-server:9380
RAGFLOW_API_KEY=your-api-key

# S3框架模型配置（可选）
S3_SEARCH_MODEL_NAME=your-search-model
S3_SEARCH_MODEL_URL=http://your-search-model-url/v1
S3_SEARCH_MODEL_API_KEY=your-search-api-key

S3_GENERATOR_MODEL_NAME=your-generator-model
S3_GENERATOR_MODEL_URL=http://your-generator-model-url/v1
S3_GENERATOR_API_KEY=your-generator-api-key

# 默认数据集ID（可选）
DEFAULT_DATASET_ID=your-default-dataset-id
```

### 4. 启动服务

```bash
# 激活虚拟环境
source .venv/bin/activate

# 启动后端API服务
uvicorn api:app --host 0.0.0.0 --port 8001 --reload

# 新终端启动前端服务
cd frontend
npm run dev
```

### 5. 测试和开发

```bash
# 运行SSE单元测试
uv pip install pytest pytest-asyncio httpx requests psutil vitest
python3 run_sse_tests.py

# 前端测试
cd frontend
npm run test

# 类型检查
npm run type-check

# 代码格式化
npm run lint
```

## 📍 访问地址

- **前端应用**: http://localhost:5173
- **后端API**: http://localhost:8001
- **API文档**: http://localhost:8001/docs
- **演示服务**: http://localhost:8050 (如果运行)

## 🏗️ 架构说明

### 系统架构
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API    │    │   RAGFlow       │
│   (Vue 3)       │◄──►│   (FastAPI)      │◄──►│   Server        │
│   Port: 5173    │    │   Port: 8001     │    │   Port: 9380    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 核心功能模块

1. **知识库管理**
   - 创建、查询、更新、删除知识库
   - 知识库列表和详情获取

2. **文档管理** 
   - 文档上传和解析
   - 文档状态实时跟踪
   - 文档下载和删除

3. **对话系统**
   - 基于知识库的智能问答
   - 流式对话响应
   - 聊天历史管理

4. **实时通信**
   - Server-Sent Events (SSE)
   - 文档处理进度推送
   - 批量状态监控

### 核心组件

- `api.py`: FastAPI主服务，提供RESTful API
- `src/api/sse_endpoints.py`: SSE实时通信端点
- `src/clients/ragflow_client.py`: RAGFlow API客户端封装
- `frontend/`: Vue 3前端应用
- `tests/`: 完整的单元测试和集成测试

## 🛠️ 开发指南

### API开发

查看接口文档：
- [知识库管理系统接口清单](docs/知识库管理系统接口清单.md)
- [RAGFlow API文档](docs/ragflow_half2.md)

### 前端开发

```bash
cd frontend
npm run dev        # 开发模式
npm run build      # 生产构建
npm run preview    # 预览构建结果
npm run type-check # TypeScript类型检查
npm run lint       # 代码检查
```

### 测试开发

```bash
# 后端测试
python3 run_sse_tests.py

# 前端测试  
cd frontend && npm run test

# 特定测试标记
uv run pytest -m sse        # 仅SSE测试
uv run pytest -m integration # 仅集成测试
```

## 📚 文档

- [知识库管理系统接口清单](docs/知识库管理系统接口清单.md)
- [RAGFlow API参考](docs/ragflow_half2.md)
- [知识库接口页面需求](docs/知识库接口页面需求.md)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License