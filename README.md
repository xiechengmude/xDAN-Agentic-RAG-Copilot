# RAGFlow API 客户端

这个项目是 RAGFlow API 的客户端封装，提供了简单易用的接口来访问 RAGFlow 的各种功能，包括知识库管理、聊天、搜索和 Agent 等功能。项目实现了增强的 S3（Search-Select-Synthesize）框架，集成了官方 RAGFlow SDK 和 Agent 功能。

## 功能特性

- **S3 RAG 框架**：实现 Search-Select-Synthesize 智能检索框架
- **官方 SDK 集成**：支持 RAGFlow 官方 Python SDK
- **Agent 和 Session 支持**：集成 Agent 对话和会话管理
- **OpenAI 兼容 API**：提供与 OpenAI API 兼容的接口
- **数据集管理**：创建、删除、更新、列表数据集
- **文档管理**：列表、删除、解析文档
- **智能检索**：支持向量和关键词混合检索

## 安装

### 前提条件

- Python 3.10+
- RAGFlow API 访问权限和 API Key

### 安装步骤

1. 克隆仓库或下载代码

2. 创建并激活虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # 在 Windows 上使用 venv\Scripts\activate
```

3. 安装依赖

```bash
pip install -r requirements.txt
```

4. 配置环境变量

复制 `.env.example` 文件为 `.env`，并填写你的 RAGFlow API URL 和 API Key：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```
# RAGFlow API 配置
RAGFLOW_API_URL=http://your-ragflow-api-url
RAGFLOW_API_KEY=your_api_key_here

# S3框架模型配置
# Search Model - 用于S3框架中的搜索决策
S3_SEARCH_MODEL_NAME=your-search-model-name
S3_SEARCH_MODEL_URL=http://your-search-llm-server:8000/v1

# Generator Model - 用于最终答案生成
S3_GENERATOR_MODEL_NAME=your-generator-model-name  
S3_GENERATOR_MODEL_URL=http://your-generator-llm-server:8000/v1

# 服务器配置
HOST=0.0.0.0
PORT=8000
```

## 使用方法

### 启动服务器

```bash
python main.py
```

服务器将在 `http://localhost:8000` 启动。你可以通过浏览器访问 `http://localhost:8000/docs` 查看 API 文档。

### API 端点

#### OpenAI 兼容 API

- `POST /v1/chats/{chat_id}/chat/completions` - 创建聊天完成
- `POST /v1/agents/{agent_id}/chat/completions` - 创建 Agent 完成

#### 数据集管理

- `POST /v1/datasets` - 创建数据集
- `DELETE /v1/datasets` - 删除数据集
- `PUT /v1/datasets/{dataset_id}` - 更新数据集
- `GET /v1/datasets` - 列出数据集

#### 文档管理

- `GET /v1/datasets/{dataset_id}/documents` - 列出数据集中的文档
- `DELETE /v1/datasets/{dataset_id}/documents` - 删除数据集中的文档
- `POST /v1/datasets/{dataset_id}/chunks` - 解析文档

#### 检索

- `POST /v1/retrieval` - 检索文本块

### 使用 Python 客户端

你也可以直接在 Python 代码中使用 `RAGFlowClient` 类：

```python
from ragflow_client import RAGFlowClient

# 创建客户端实例
client = RAGFlowClient(
    api_url="http://your-ragflow-api-url",
    api_key="your_api_key_here"
)

# 列出数据集
datasets = client.list_datasets()
print(datasets)

# 创建聊天完成
response = client.create_chat_completion(
    chat_id="your_chat_id",
    model="model_name",
    messages=[
        {"role": "user", "content": "你好，请介绍一下 RAGFlow"}
    ],
    stream=False
)
print(response)
```

### 使用命令行工具

项目提供了一个命令行工具 `ragflow_cli.py`，可以直接从命令行与 RAGFlow API 交互：

```bash
# 给脚本添加执行权限
chmod +x ragflow_cli.py

# 查看帮助信息
./ragflow_cli.py --help

# 列出数据集
./ragflow_cli.py list-datasets

# 创建数据集
./ragflow_cli.py create-dataset --name "测试数据集"

# 检索
./ragflow_cli.py retrieve --dataset-id "your_dataset_id" --question "什么是 RAGFlow?" --highlight
```

#### 可用命令

- **数据集管理**
  - `list-datasets` - 列出数据集
  - `create-dataset` - 创建数据集
  - `delete-dataset` - 删除数据集

- **文档管理**
  - `list-documents` - 列出文档
  - `upload-document` - 上传文档
  - `delete-document` - 删除文档
  - `parse-document` - 解析文档

- **检索**
  - `retrieve` - 检索文本块

- **聊天**
  - `chat` - 与聊天助手交互
  - `agent` - 与 Agent 交互

### 示例脚本

在 `examples` 目录下提供了一些示例脚本：

- `basic_usage.py` - 基本使用示例
- `chat_example.py` - 聊天应用示例

运行示例：

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行基本使用示例
python examples/basic_usage.py

# 运行聊天示例
python examples/chat_example.py
```

## 开发

### 添加新功能

1. 在 `ragflow_client.py` 中添加新的方法
2. 在 `api.py` 中添加对应的 API 端点
3. 在 `models.py` 中添加必要的数据模型

### 运行测试

```bash
pytest
```

## 许可证

MIT

## RAG知识服务

我们提供了一个统一的RAG（检索增强生成）服务，整合了RAGFlow检索和外部LLM生成功能。

### 启动RAG服务

```bash
# 激活虚拟环境
source .venv/bin/activate

# 启动RAG服务（端口8001）
python rag_service.py
```

### RAG服务API端点

#### 1. 健康检查
```bash
curl http://localhost:8001/health
```

#### 2. 列出数据集
```bash
curl http://localhost:8001/v1/rag/datasets
```

#### 3. RAG问答
```bash
curl -X POST http://localhost:8001/v1/rag/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "什么是人工智能？",
    "top_k": 5,
    "similarity_threshold": 0.1,
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

#### 4. RAG流式问答
```bash
curl -X POST http://localhost:8001/v1/rag/ask-stream \
  -H "Content-Type: application/json" \
  -d '{
    "question": "请介绍机器学习的基本概念",
    "top_k": 3,
    "temperature": 0.7
  }'
```

### 测试RAG服务

运行测试脚本验证RAG服务功能：

```bash
python test_rag_service.py
```

### RAG服务特性

- **智能检索**: 使用RAGFlow从知识库检索相关文档
- **高质量生成**: 基于检索到的上下文使用训练好的RAG模型生成答案
- **流式响应**: 支持实时流式答案生成
- **默认知识库**: 自动使用配置的默认知识库（360test）
- **来源追踪**: 提供答案来源的详细信息
- **灵活配置**: 支持自定义检索参数和生成参数

### 环境变量配置

RAG服务需要以下环境变量：

```bash
# RAGFlow API配置
RAGFLOW_API_URL=http://150.109.16.195:7080
RAGFLOW_API_KEY=ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm

# LLM模型服务配置
LLM_API_URL=http://51.159.189.105:7032/v1
LLM_MODEL_NAME=xDAN-R2-Qwen3-14b-RagRL-step450-0618

# 默认知识库
DEFAULT_DATASET_ID=7e8d9e924cde11f0afc90242ac140006
```

### 服务架构

RAG服务采用解耦的架构设计：

1. **检索层**: 使用RAGFlow API进行语义检索
2. **生成层**: 使用外部vLLM服务进行答案生成
3. **整合层**: 统一的API接口整合检索和生成流程

这种设计确保了系统的模块化、可扩展性和高性能。

### S3框架模型配置

S3（Search-Select-Synthesize）框架支持独立配置搜索决策模型和答案生成模型：

- **Search Model**: 用于搜索决策，决定是否需要继续搜索、提取重要文档等
- **Generator Model**: 用于最终答案生成，基于选中的文档生成高质量答案

这种设计允许您：
1. 使用轻量级模型进行快速搜索决策
2. 使用更强大的模型进行最终答案生成
3. 根据需求灵活切换不同的模型组合

### 项目结构

  1. src/ - 源代码目录
    - clients/ - 客户端模块（RAGFlow客户端、SDK封装、LLM客户端）
    - services/ - 服务模块（RAG服务、S3服务、增强版S3服务）
    - core/ - 核心模块（数据模型）
    - utils/ - 工具模块
  2. config/ - 配置文件目录
    - 统一的配置管理（settings.py）
  3. scripts/ - 独立脚本目录
    - 各种测试和调试脚本
  4. tests/ - 正式测试目录
    - 单元测试、集成测试、测试固件
  5. examples/ - 示例代码目录
    - 使用示例和演示
  6. docs/ - 文档目录
    - 架构文档、API分析、RAGFlow文档
  7. results/ - 测试结果目录
    - 测试报告和日志文件