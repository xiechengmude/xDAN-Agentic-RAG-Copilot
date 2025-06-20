# RAGFlow API Client 测试套件

本目录包含了RAGFlow API Client的完整测试套件，基于原生ragflow_sdk编写。

## 目录结构

```
tests/
├── unit/                          # 单元测试
│   ├── test_ragflow_sdk_wrapper.py    # SDK封装测试
│   ├── test_enhanced_s3_rag_service.py # 增强S3服务测试
│   └── test_retrieve_functionality.py  # 检索功能测试
├── integration/                   # 集成测试
│   └── test_s3_framework_integration.py # S3框架集成测试
├── fixtures/                      # 测试夹具
│   ├── __init__.py
│   └── mock_data.py              # Mock数据定义
├── conftest.py                   # pytest配置和共享fixtures
├── test_config.py                # 测试配置
└── README.md                     # 本文档
```

## 测试覆盖

### 单元测试

1. **RAGFlowSDKWrapper测试** (`test_ragflow_sdk_wrapper.py`)
   - SDK初始化和配置
   - 数据集管理功能
   - 检索功能
   - Agent管理
   - Session管理
   - 错误处理

2. **Enhanced S3 RAG Service测试** (`test_enhanced_s3_rag_service.py`)
   - S3框架核心方法
   - Agent与S3集成
   - 搜索流程控制
   - 答案合成
   - SDK/HTTP模式切换

3. **检索功能测试** (`test_retrieve_functionality.py`)
   - 基础查询检索
   - 多数据集检索
   - 相似度阈值过滤
   - 文档级别检索
   - 特殊字符处理
   - 大数据集处理

### 集成测试

1. **S3框架集成测试** (`test_s3_framework_integration.py`)
   - 完整S3流程（单轮/多轮）
   - Agent对话集成
   - Session管理集成
   - 错误处理和回退机制
   - 端到端测试

## 运行测试

### 安装依赖

```bash
pip install pytest pytest-asyncio pytest-mock
```

### 运行所有测试

```bash
pytest tests/
```

### 运行特定类型的测试

```bash
# 只运行单元测试
pytest tests/unit/

# 只运行集成测试
pytest tests/integration/

# 运行特定文件的测试
pytest tests/unit/test_ragflow_sdk_wrapper.py
```

### 使用标记运行测试

```bash
# 跳过慢速测试
pytest -m "not slow"

# 只运行单元测试
pytest -m unit

# 只运行需要SDK的测试
pytest -m requires_sdk
```

### 查看测试覆盖率

```bash
# 安装coverage
pip install pytest-cov

# 运行测试并生成覆盖率报告
pytest --cov=. --cov-report=html tests/
```

## 测试配置

### 环境变量

测试需要以下环境变量（可在`.env`文件中设置）：

```bash
# RAGFlow配置
RAGFLOW_API_URL=http://test.ragflow.com:7080
RAGFLOW_API_KEY=test-api-key

# LLM配置
LLM_API_URL=http://test.llm.com/v1
LLM_MODEL_NAME=test-model

# 默认数据集
DEFAULT_DATASET_ID=test-dataset-id

# 测试环境
TEST_ENV=test  # 可选: test, integration
```

### 测试参数

在`test_config.py`中可以配置：
- S3框架参数（搜索轮数、top_k等）
- Agent测试参数
- Mock响应延迟
- 错误率模拟
- 性能基准

## Mock数据

`fixtures/mock_data.py`提供了丰富的测试数据：
- 文档和Chunk数据
- Agent响应模板
- LLM响应模板
- 错误场景
- Session对话历史

## 编写新测试

### 单元测试示例

```python
def test_new_feature(mock_ragflow_sdk):
    """测试新功能"""
    # 设置mock返回值
    mock_ragflow_sdk.new_method.return_value = {'code': 0, 'data': {}}
    
    # 执行测试
    result = some_function()
    
    # 验证结果
    assert result['code'] == 0
    mock_ragflow_sdk.new_method.assert_called_once()
```

### 使用fixtures

```python
def test_with_fixtures(mock_chunks, create_mock_agent_response):
    """使用测试fixtures"""
    # 使用预定义的mock数据
    chunks = mock_chunks
    
    # 使用工厂函数创建响应
    agent_response = create_mock_agent_response(
        query="new search",
        important_docs=[1, 2],
        search_complete=False
    )
```

## 持续集成

测试套件已准备好集成到CI/CD流程中：

```yaml
# GitHub Actions示例
- name: Run tests
  run: |
    pytest tests/ --junit-xml=test-results.xml
    
- name: Upload test results
  uses: actions/upload-artifact@v2
  with:
    name: test-results
    path: test-results.xml
```

## 故障排除

### 常见问题

1. **ImportError: No module named 'ragflow_sdk'**
   - 确保已安装ragflow_sdk: `pip install ragflow-sdk`

2. **测试超时**
   - 检查`TEST_TIMEOUTS`配置
   - 使用`-m "not slow"`跳过慢速测试

3. **Mock数据不匹配**
   - 检查`mock_data.py`中的数据格式
   - 确保mock返回值与实际API响应一致

## 贡献指南

1. 新功能必须包含相应的测试
2. 保持测试覆盖率在80%以上
3. 遵循现有的测试命名和组织约定
4. 在PR中包含测试结果截图或日志