# 测试指南

本项目包含多个层级的测试，确保各个组件正常工作。

## 环境配置

所有测试都依赖于 `.env` 文件中的配置。请确保在运行测试前正确配置环境变量。

### 查看当前配置

```bash
uv run python show_config.py
```

### 必需的环境变量

- `RAGFLOW_API_URL`: RAGFlow服务器地址
- `RAGFLOW_API_KEY`: RAGFlow API密钥
- `S3_SEARCH_MODEL_NAME`: 搜索模型名称
- `S3_SEARCH_MODEL_URL`: 搜索模型API地址
- `S3_SEARCH_MODEL_API_KEY`: 搜索模型API密钥
- `S3_GENERATOR_MODEL_NAME`: 生成模型名称
- `S3_GENERATOR_API_BASE`: 生成模型API地址
- `S3_GENERATOR_API_KEY`: 生成模型API密钥
- `DEFAULT_DATASET_ID`: 默认数据集ID

## 测试结构

```
tests/
├── ragflow_remote_service/   # RAGFlow远程服务测试
│   └── test_ragflow_api.py
├── llm_model/               # LLM模型测试
│   └── test_llm_client.py
├── local_backend_api/       # 本地后端API测试
│   └── test_local_server.py
└── rag_model/              # RAG模型测试
    └── test_s3_rag_service.py
```

## 快速测试

### 1. 快速连接测试

验证所有外部服务的连接状态：

```bash
uv run python quick_test.py
```

### 2. 运行所有测试

```bash
uv run python run_all_tests.py
```

### 3. 运行特定测试套件

```bash
# 测试RAGFlow远程服务
uv run python run_all_tests.py --suite ragflow

# 测试LLM模型
uv run python run_all_tests.py --suite llm

# 测试RAG模型
uv run python run_all_tests.py --suite rag

# 测试本地API服务
uv run python run_all_tests.py --suite local
```

## 各测试套件说明

### 1. RAGFlow远程服务测试 (`test_ragflow_api.py`)

测试与RAGFlow服务器的连接和基本API功能：
- API连接性
- 数据集管理（列表、创建、更新、删除）
- 知识库检索
- 对话管理（创建、发送消息、获取历史）
- 兼容性方法

### 2. LLM模型测试 (`test_llm_client.py`)

测试LLM客户端与模型服务的交互：
- Search模型和Generator模型连接
- 系统提示词功能
- 流式响应（同步和异步）
- 温度参数控制
- 最大令牌数控制
- 错误处理
- 模型切换

### 3. 本地后端API测试 (`test_local_server.py`)

测试本地服务器的所有接口：
- 主页访问
- 健康检查
- API文档
- S3智能搜索流式接口
- 对话流式接口
- 错误处理
- CORS配置

### 4. RAG模型测试 (`test_s3_rag_service.py`)

测试S3框架的核心功能：
- 搜索结果格式化
- 搜索决策提取
- 单步搜索
- 完整S3搜索流程
- 答案合成
- 空结果处理
- 多轮搜索
- 性能指标

## 服务器管理

### 启动服务器

```bash
# 启动xDAN RAG主服务器（使用新版API）
USE_NEW_API=true ./start_server.sh api start

# 或启动RAGFlow搜索服务器（旧版）
./start_server.sh api start
```

### 停止服务器

```bash
./start_server.sh stop
```

### 查看服务状态

```bash
./start_server.sh status
```

## 端口管理

本项目包含自动端口管理功能，如果默认端口（8050）被占用，会自动：
1. 尝试释放端口
2. 如果无法释放，寻找备用端口（8050-8100）

## 故障排查

### 1. 配置问题

如果测试失败，首先运行配置检查：

```bash
uv run python show_config.py
```

确保所有必需的环境变量都已设置。

### 2. 连接问题

运行快速测试检查各服务连接：

```bash
uv run python quick_test.py
```

### 3. 查看日志

服务器日志存储在 `logs/` 目录：

```bash
ls -la logs/
tail -f logs/xdan_rag_server_*.log
```

## 测试最佳实践

1. **环境隔离**：所有配置都应该从 `.env` 文件加载，不要硬编码
2. **原子测试**：每个测试应该独立运行，不依赖其他测试的状态
3. **清理资源**：测试创建的资源（如数据集、对话）应该在测试结束时清理
4. **错误处理**：测试应该优雅地处理服务不可用的情况
5. **性能考虑**：避免在测试中执行耗时操作，使用合理的超时设置