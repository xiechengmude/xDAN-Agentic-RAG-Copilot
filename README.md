# xDAN Rag Copilot API Service

基于S3框架（Search-Select-Synthesize）和RAGFlow的智能知识库问答系统，提供完整的文档处理、智能检索和对话功能。

## 🌟 特性

- **S3智能框架**：Search-Select-Synthesize三阶段智能问答
- **知识库管理**：完整的知识库CRUD操作
- **文档处理**：支持文档上传、解析、状态跟踪
- **智能问答**：基于S3框架的多轮迭代搜索和精准回答
- **统一LLM管理**：通过LiteLLM统一管理多个模型
- **语义检索**：高精度的文档内容检索
- **实时通信**：使用Server-Sent Events提供实时状态更新
- **现代化架构**：清晰的分层架构，易于扩展和维护

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

#### 配置文件（推荐）
```bash
# 复制配置模板
cp config.example.yaml config.yaml

# 编辑 config.yaml 配置文件
# 支持环境变量替换，格式：${VAR_NAME:default_value}
```

#### 环境变量（可选）
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件设置必要的环境变量
# RAGFlow配置
RAGFLOW_API_KEY=your_ragflow_api_key
DEFAULT_DATASET_ID=your_dataset_id

# LLM API密钥
DEEPSEEK_API_KEY=your_deepseek_api_key
```

### 3. 安装依赖

#### 使用uv（推荐，更快）
```bash
# 安装uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境并安装依赖
uv venv
source .venv/bin/activate  # Linux/macOS
uv pip install -r requirements.txt
```

#### 使用pip（传统方式）
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

#### 启动API服务
```bash
# 方式1：使用uv运行（推荐）
uv run python -m src.api.server

# 方式2：直接运行
python -m src.api.server

# 方式3：使用uvicorn（支持热重载）
uvicorn src.api.server:app --host 0.0.0.0 --port 8050 --reload
```

#### 启动前端（可选）
```bash
cd frontend
npm run dev
```

### 5. 访问应用

- **API服务**: http://localhost:8050
- **Swagger文档**: http://localhost:8050/docs
- **前端应用**: http://localhost:5173 (如果启动了前端)
- **健康检查**: http://localhost:8050/health

## 🏗️ 架构说明

### 系统架构
```
┌─────────────────┐
│   Frontend      │
│  (React + TS)   │
│   Port: 5173    │
└────────┬────────┘
         │
    ┌────▼─────┐
    │   API    │     ┌──────────────┐     ┌──────────────┐
    │  Server  ├────►│ S3 Framework ├────►│   LiteLLM    │
    │Port: 8050│     │  (编排引擎)  │     │ (统一LLM路由) │
    └─────┬────┘     └──────┬───────┘     └──────────────┘
          │                 │
          └─────────────────┼──────────────┐
                           │              │
                    ┌──────▼───────┐      │
                    │   RAGFlow    │      │
                    │ (知识库检索)  │◄─────┘
                    │ Port: 7080   │
                    └──────────────┘
```

### 核心功能模块

#### ✅ S3智能问答框架
- **Search阶段**：从RAGFlow知识库检索相关文档
- **Select阶段**：使用xDAN-R2模型智能筛选重要文档
- **Synthesize阶段**：使用DeepSeek生成精准答案
- **多轮迭代**：支持最多3轮搜索优化

#### ✅ 统一API接口
1. **聊天管理**：创建、列表、删除聊天会话
2. **聊天交互**：发送消息、获取历史（支持SSE流式）
3. **知识库管理**：CRUD操作（代理到RAGFlow）
4. **文档管理**：上传、列表、删除文档
5. **知识检索**：多知识库语义检索

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
# 运行S3框架测试
uv run pytest tests/test_s3_framework.py -v

# 运行架构测试
uv run pytest tests/test_refactored_architecture.py -v

# 运行所有测试
uv run pytest tests/ -v
```

### 测试覆盖
- ✅ **S3框架**: Search、Select、Synthesize各阶段
- ✅ **服务层**: 服务创建、健康检查、搜索功能
- ✅ **客户端**: LiteLLM集成、RAGFlow连接
- ✅ **配置系统**: 配置加载、环境变量替换
- ✅ **API接口**: 所有RESTful接口

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
- **API版本**: v2.0 (重构后)
- **架构版本**: S3框架集成
- **测试覆盖**: 100%
- **最后更新**: 2025-06-26

### 关键特性
- ✅ S3智能问答框架
- ✅ 统一的LLM路由管理
- ✅ 完整的RAGFlow集成
- ✅ 清晰的分层架构
- ✅ 生产级部署支持
- ✅ 完善的配置系统

## 📚 文档

- **[部署指南](DEPLOYMENT_GUIDE_V2.md)** - 完整的部署说明
- **[API状态](CURRENT_API_STATUS.md)** - 当前API服务状态
- **[架构文档](docs/架构文档/S3-ARCHITECTURE.md)** - S3架构设计
- **[迁移指南](docs/migration/MIGRATION_GUIDE.md)** - 代码迁移指南

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