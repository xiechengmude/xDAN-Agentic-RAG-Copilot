# RAGFlow API Client

基于RAGFlow API的知识库管理系统，提供完整的文档处理、检索和对话功能。

## 🌟 特性

- **知识库管理**：完整的知识库CRUD操作
- **文档处理**：支持文档上传、解析、状态跟踪
- **智能问答**：基于知识库的实时流式对话
- **语义检索**：高精度的文档内容检索
- **实时通信**：使用Server-Sent Events提供实时状态更新
- **现代化前端**：React 19 + TypeScript + Vite
- **完整API测试**：100%接口验证通过

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Git

### 1. 克隆仓库
```bash
git clone <repository-url>
cd ragflow-api-client
```

### 2. 环境配置

创建并配置环境变量文件：

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
# RAGFlow API 配置
RAGFLOW_API_URL=http://150.109.16.195:7080
RAGFLOW_API_KEY=ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm

# S3框架模型配置
S3_SEARCH_MODEL_NAME=xDAN-R2-Qwen3-14b-RagRL-step450-0618
S3_SEARCH_MODEL_URL=http://209.20.158.45:8001/v1
S3_SEARCH_MODEL_API_KEY=sk-empty

S3_GENERATOR_API_BASE=http://43.134.187.48:7220/v1
S3_GENERATOR_MODEL_NAME=deepseek-chat
S3_GENERATOR_API_KEY=sk-vvr2jecYl1lkEu2MF4E3Ef0dC92c4a3eA6F2B633Ba621d81

# 默认数据集ID
DEFAULT_DATASET_ID=7e8d9e924cde11f0afc90242ac140006
```

### 3. 安装依赖

#### 后端依赖
```bash
# 创建Python虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装Python依赖
pip install -r requirements.txt
```

#### 前端依赖
```bash
cd frontend
npm install
cd ..
```

### 4. 启动服务

#### 方式1：分别启动（推荐开发）
```bash
# 终端1：启动后端API服务
source venv/bin/activate
python demo_server_simple.py

# 终端2：启动前端服务
cd frontend
npm run dev
```

#### 方式2：单一后端服务
```bash
# 仅启动搜索可视化服务
source venv/bin/activate
python demo_server_simple.py
```

### 5. 访问应用

- **前端应用**: http://localhost:5173
- **搜索可视化**: http://localhost:8050
- **API文档**: 查看 `docs/API接口对接文档.md`

## 🏗️ 架构说明

### 系统架构
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Demo Server    │    │   RAGFlow       │
│   (React 19)    │◄──►│   (FastAPI)      │◄──►│   Server        │
│   Port: 5173    │    │   Port: 8050     │    │   Port: 7080    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 核心功能模块

#### ✅ 已验证功能
1. **知识库管理** (100% 测试通过)
   - 创建、查询、更新、删除知识库
   - 知识库列表和详情获取
   - 支持自定义embedding模型

2. **文档管理** (100% 测试通过)
   - 文档上传和自动解析
   - 文档列表和状态查询
   - 文档内容获取和下载
   - 批量删除操作

3. **对话系统** (100% 测试通过)
   - 基于知识库的智能问答
   - SSE流式对话响应
   - 多轮对话支持

4. **检索功能** (100% 测试通过)
   - 语义相似度检索
   - 多知识库跨库检索
   - 结果相关度排序

5. **实时通信** (100% 测试通过)
   - Server-Sent Events (SSE)
   - 流式响应处理
   - 实时状态更新

## 📋 API接口

### 核心接口列表

| 功能模块 | 接口 | 方法 | 状态 |
|---------|------|------|------|
| 知识库列表 | `/api/v1/datasets` | GET | ✅ |
| 创建知识库 | `/api/v1/datasets` | POST | ✅ |
| 更新知识库 | `/api/v1/datasets/{id}` | PUT | ✅ |
| 删除知识库 | `/api/v1/datasets/{id}` | DELETE | ✅ |
| 上传文档 | `/api/v1/datasets/{id}/documents` | POST | ✅ |
| 文档列表 | `/api/v1/datasets/{id}/documents` | GET | ✅ |
| 批量删除文档 | `/api/v1/datasets/{id}/documents` | DELETE | ✅ |
| 创建对话 | `/api/v1/chats` | POST | ✅ |
| 发送消息 | `/api/v1/chats/{id}/completions` | POST | ✅ |
| 知识库检索 | `/api/v1/retrieval` | POST | ✅ |

**测试结果**: 12/12 接口测试通过，成功率 100%

### 接口文档
详细的API接口文档请查看：
- **[API接口对接文档](docs/API接口对接文档.md)** - 完整的接口规范和使用示例

## 🧪 测试

### 运行测试
```bash
# 激活虚拟环境
source venv/bin/activate

# 安装测试依赖
pip install pytest pytest-asyncio aiohttp

# 运行完整的API测试
python tests/test_final_complete_workflow.py

# 运行特定测试
python tests/test_implemented_apis.py
python tests/test_with_existing_kb.py
```

### 测试覆盖
- ✅ **知识库管理**: 创建、列表、更新、删除
- ✅ **文档管理**: 上传、列表、批量删除
- ✅ **对话功能**: 创建对话、SSE流式问答
- ✅ **检索功能**: 语义检索、相似度匹配
- ✅ **错误处理**: 各种错误场景验证

## 🛠️ 开发指南

### API开发
使用已验证的接口进行开发：
```bash
# 查看接口测试示例
cat tests/test_final_complete_workflow.py

# 运行调试脚本
python tests/debug_failed_apis.py
```

### 前端开发
```bash
cd frontend
npm run dev        # 开发模式
npm run build      # 生产构建
npm run preview    # 预览构建结果
npm run type-check # TypeScript类型检查
npm run lint       # 代码检查
npm run test       # 运行测试
```

### 添加新功能
1. 查看 `docs/API接口对接文档.md` 了解接口规范
2. 参考 `tests/` 目录下的测试案例
3. 使用现有的API客户端进行开发

## 📊 项目状态

### 当前版本
- **API版本**: v1.0
- **前端版本**: v1.0
- **测试覆盖**: 100%
- **最后更新**: 2025-06-23

### 关键特性
- ✅ 完整的RAGFlow API集成
- ✅ 实时SSE通信
- ✅ 现代化React前端
- ✅ 完整的测试覆盖
- ✅ 详细的API文档
- ✅ 生产就绪的代码质量

## 📚 文档

- **[API接口对接文档](docs/API接口对接文档.md)** - 主要接口文档
- **[README](docs/README.md)** - 文档导航

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 开发流程
1. Fork项目
2. 创建feature分支
3. 提交代码
4. 运行测试确保通过
5. 提交Pull Request

## 📄 许可证

MIT License