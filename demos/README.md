# 演示脚本目录

本目录包含各种演示脚本，展示系统的不同功能和使用场景。

## 目录结构

### `/deepsearch` - DeepSearch功能演示
展示S3框架的搜索、选择、合成能力。

- **`demo_single_complex_question.py`**
  - 展示单个复杂问题的完整处理流程
  - 演示多跳推理过程
  - 包含完整的推理链构建

- **`test_challenging_questions.py`**
  - 批量测试10个挑战性问题
  - 包含持续优化机制
  - 生成详细的测试报告

- **`demo_deepsearch_complete.py`**
  - 使用真实数据的完整演示
  - 展示BrightData搜索和FireCrawl爬取
  - 端到端的DeepSearch流程

- **`test_brightdata_demo.py`**
  - BrightData SERP API功能演示
  - 展示搜索结果解析
  - 批量搜索和优化搜索示例

- **`test_real_search.py`**
  - 真实搜索和爬取测试
  - 完整的搜索+爬取流程
  - 错误处理和重试机制

### `/api` - API功能演示
展示各种API端点的使用方法。

- **`demo_chat_api.py`**
  - 基础对话API使用
  - S3搜索功能演示
  - 流式响应处理
  - 多轮对话管理

### `/integration` - 集成测试演示
展示不同组件之间的集成。

- **`demo_rag_integration.py`**
  - RAGFlow + LiteLLM + S3完整集成
  - 端到端的RAG流程演示
  - 性能统计和优势展示

## 使用方法

### 运行DeepSearch演示

```bash
# 单个复杂问题演示
python demos/deepsearch/demo_single_complex_question.py

# 批量测试挑战性问题
python demos/deepsearch/test_challenging_questions.py

# 完整的DeepSearch流程
python demos/deepsearch/demo_deepsearch_complete.py
```

### 查看结果

演示脚本会生成各种输出文件：
- JSON格式的结果报告
- 调试日志文件
- 搜索和爬取的原始数据

## 配置要求

运行演示前，请确保：
1. 配置文件 `config.yaml` 已正确设置
2. API密钥在 `.env` 文件中配置
3. 安装了所有依赖包

## 注意事项

- 某些演示使用模拟数据来展示流程
- 真实API调用需要有效的API密钥
- 大规模测试可能产生API费用