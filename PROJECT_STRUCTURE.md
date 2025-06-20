# 项目结构说明

## 目录结构

```
ragflow-api-client/
├── src/                      # 源代码目录
│   ├── __init__.py
│   ├── clients/             # 客户端模块
│   │   ├── __init__.py
│   │   ├── ragflow_client.py     # RAGFlow HTTP客户端
│   │   ├── ragflow_sdk_wrapper.py # RAGFlow SDK封装
│   │   └── llm_client.py         # LLM客户端
│   ├── services/            # 服务模块
│   │   ├── __init__.py
│   │   ├── rag_service.py        # 基础RAG服务
│   │   ├── s3_rag_service.py     # S3框架RAG服务
│   │   └── enhanced_s3_rag_service.py # 增强版S3 RAG服务
│   ├── core/                # 核心模块
│   │   ├── __init__.py
│   │   └── models.py            # 数据模型定义
│   └── utils/               # 工具模块
│       └── __init__.py
├── tests/                   # 测试目录
│   ├── __init__.py
│   ├── conftest.py         # pytest配置
│   ├── test_config.py      # 测试配置
│   ├── unit/               # 单元测试
│   │   ├── __init__.py
│   │   ├── test_ragflow_sdk_wrapper.py
│   │   ├── test_enhanced_s3_rag_service.py
│   │   └── test_retrieve_functionality.py
│   ├── integration/        # 集成测试
│   │   ├── __init__.py
│   │   └── test_s3_framework_integration.py
│   └── fixtures/           # 测试固件
│       ├── __init__.py
│       └── mock_data.py
├── scripts/                # 脚本目录
│   ├── test_zhixin_questions.py  # 智信问题测试脚本
│   ├── test_debug_s3.py         # S3调试脚本
│   ├── test_direct_retrieve.py  # 直接检索测试
│   └── ...                      # 其他测试脚本
├── examples/               # 示例代码
│   ├── basic_usage.py     # 基础使用示例
│   └── chat_example.py    # 聊天示例
├── config/                 # 配置文件
│   └── settings.py        # 项目配置
├── docs/                   # 文档目录
│   ├── ARCHITECTURE.md    # 架构说明
│   ├── ARCHITECTURE_UPDATE_ANALYSIS.md
│   ├── API_ANALYSIS_REPORT.md
│   └── ragflow_half.md   # RAGFlow文档
├── questions/              # 测试问题和知识库
│   ├── 阶段一-测试文档/
│   ├── 阶段二-接口文档/
│   └── 阶段三-补充知识/
├── results/                # 测试结果目录
│   └── test_results_*.json
├── prompts/                # 提示词模板
├── .env                    # 环境变量配置
├── requirements.txt        # 项目依赖
├── requirements-test.txt   # 测试依赖
├── pytest.ini             # pytest配置
├── README.md              # 项目说明
└── setup.sh               # 安装脚本
```

## 模块说明

### src/clients/
- **ragflow_client.py**: 基于HTTP API的RAGFlow客户端实现
- **ragflow_sdk_wrapper.py**: 官方RAGFlow SDK的封装，提供统一接口
- **llm_client.py**: 通用的LLM客户端，支持OpenAI兼容的API

### src/services/
- **rag_service.py**: 基础的RAG服务实现
- **s3_rag_service.py**: 实现S3（Search-Select-Synthesize）框架的RAG服务
- **enhanced_s3_rag_service.py**: 增强版S3服务，集成Agent和Session功能

### src/core/
- **models.py**: Pydantic模型定义，包含请求和响应模型

### tests/
- **unit/**: 单元测试，测试各个模块的独立功能
- **integration/**: 集成测试，测试模块间的交互
- **fixtures/**: 测试数据和mock对象

### scripts/
包含各种独立的测试脚本，用于功能验证和调试

### config/
统一的配置管理，从环境变量读取配置

## 使用方法

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
cp .env.example .env
# 编辑.env文件，设置必要的配置
```

3. 运行测试：
```bash
pytest tests/
```

4. 运行示例：
```bash
python examples/basic_usage.py
```

5. 启动API服务：
```bash
python api.py
```