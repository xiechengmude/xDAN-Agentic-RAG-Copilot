# xDAN Agentic-RAG-Service 架构设计

## 系统概述

本项目实现了基于S3框架（Search-Select-Synthesize）的智能RAG（检索增强生成）服务，结合了RAGFlow的检索能力和xDAN-R2-Qwen3-14b-RagRL模型的智能体能力，提供高质量的问答服务。

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    xDAN Agentic-RAG-Service                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────┐  ┌─────────────────────────────┐ │
│  │      RAGFlow服务        │  │      xDAN智能体服务         │ │
│  │                         │  │                             │ │
│  │ • 文档存储              │  │ • xDAN-R2-Qwen3-14b-       │ │
│  │ • 向量索引              │  │   RagRL-step450-0618        │ │
│  │ • 检索API               │  │ • 训练后的S3智能体          │ │
│  │ • 知识库管理            │  │ • OpenAI兼容API             │ │
│  └─────────────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. RAGService（RAG协调服务）
```python
class RAGService:
    def __init__(self, ragflow_client, llm_client):
        self.ragflow_client = ragflow_client  # 检索客户端
        self.llm_client = llm_client          # 生成客户端
    
    def retrieve_context(self, question, dataset_ids, top_k, similarity_threshold):
        """S3框架的Search阶段：从知识库检索相关上下文"""
        
    def generate_answer(self, question, context, temperature, max_tokens):
        """S3框架的Synthesize阶段：基于上下文生成答案"""
        
    async def generate_answer_stream(self, question, context, ...):
        """流式答案生成"""
```

### 2. 智能体System Prompt
基于训练代码中的system prompt，模型在推理时使用相同的提示词：

```python
AGENT_SYSTEM_PROMPT = """You are a search copilot for the generation model. Based on a user's query and initial searched results, you will first determine if the searched results are enough to produce an answer.

If the searched results are enough, you will use <search_complete>True</search_complete> to indicate that you have gathered enough information for the generation model to produce an answer.

If the searched results are not enough, you will go through a loop of <query> -> <information> -> <important_info> -> <search_complete> -> <query> (if not complete) ..., to help the generation model to generate a better answer with more relevant information searched.

You should show the search query between <query> and </query> in JSON format.
Based on the search query, we will return the top searched results between <information> and </information>. You need to put the doc ids of the important documents (up to 3 documents, within the current information window) between <important_info> and </important_info> (e.g., <important_info>[1, 4]</important_info>).

A search query MUST be followed by a <search_complete> tag if the search is not complete.
After reviewing the information, you must decide whether to continue searching with a new query or indicate that the search is complete. If you need more information, use <search_complete>False</search_complete> to indicate you want to continue searching with a better query. Otherwise, use <search_complete>True</search_complete> to terminate the search.

During the process, you can add reasoning process within <think></think> tag whenever you want. Note: Only the important information would be used for the generation model to produce an answer."""
```

## 工作流程

### 标准问答流程
```
1. 用户提问 → 2. 初始检索 → 3. 智能体判断 → 4. 迭代搜索（可选）→ 5. 信息选择 → 6. 答案生成
```

### 详细步骤

#### 1. 用户请求处理
- 接收用户问题和参数
- 验证请求格式
- 设置默认知识库

#### 2. 初始检索（Search）
```python
# 从RAGFlow获取初始检索结果
initial_results = ragflow_client.retrieve_chunks(
    question=question,
    dataset_ids=dataset_ids,
    top_k=top_k,
    similarity_threshold=similarity_threshold
)
```

#### 3. 智能体决策（Select）
```python
# 使用训练好的智能体模型判断是否需要更多信息
agent_response = llm_client.chat_completion(
    messages=[
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": format_initial_search(question, initial_results)}
    ]
)
```

#### 4. 迭代搜索（可选）
- 如果智能体判断信息不足（`<search_complete>False</search_complete>`）
- 提取新的搜索查询（`<query>...</query>`）
- 执行新一轮检索
- 重复直到信息充足

#### 5. 重要信息选择
- 智能体标记重要文档（`<important_info>[1, 4]</important_info>`）
- 提取选中文档的内容
- 构建最终上下文

#### 6. 答案合成（Synthesize）
```python
# 基于最终上下文生成答案
final_answer = llm_client.chat_completion(
    messages=[
        {"role": "system", "content": "基于提供的上下文回答问题..."},
        {"role": "user", "content": f"问题：{question}\n上下文：{final_context}"}
    ]
)
```

## 技术特性

### 1. 智能搜索控制
- **动态搜索决策**: 智能体自主判断是否需要更多信息
- **查询优化**: 根据已有信息生成更精确的搜索查询
- **搜索终止控制**: 通过`<search_complete>`标签控制搜索流程

### 2. 信息选择机制
- **重要性评估**: 从检索结果中选择最相关的文档
- **信息去重**: 避免重复信息干扰
- **上下文长度控制**: 智能控制输入上下文的长度

### 3. 推理过程透明化
- **思考过程**: 通过`<think></think>`标签展示推理过程
- **决策追踪**: 记录每次搜索决策的原因
- **来源追溯**: 保持答案与原始文档的关联

### 4. 流式响应支持
- **实时反馈**: 支持流式答案生成
- **渐进式信息**: 先返回来源信息，再流式返回答案
- **用户体验优化**: 减少等待时间

## 部署架构

### 服务端口分配
- **RAGFlow API**: 端口8000（检索服务）
- **RAG Service**: 端口8001（统一RAG服务）
- **vLLM Service**: 外部服务（生成服务）

### 环境配置
```bash
# RAGFlow配置
RAGFLOW_API_URL=http://150.109.16.195:7080
RAGFLOW_API_KEY=ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm

# LLM服务配置
LLM_API_URL=http://51.159.189.105:7032/v1
LLM_MODEL_NAME=xDAN-R2-Qwen3-14b-RagRL-step450-0618

# 默认知识库
DEFAULT_DATASET_ID=7e8d9e924cde11f0afc90242ac140006
```

## 性能优化

### 1. 检索优化
- **相似度阈值调优**: 动态调整检索阈值
- **Top-K优化**: 根据问题复杂度调整检索数量
- **缓存机制**: 缓存常见问题的检索结果

### 2. 生成优化
- **上下文压缩**: 智能压缩长上下文
- **温度控制**: 根据问题类型调整生成随机性
- **流式优化**: 优化流式响应的延迟

### 3. 系统优化
- **异步处理**: 使用异步IO提升并发性能
- **连接池**: 复用HTTP连接
- **错误恢复**: 优雅处理服务异常

## 扩展能力

### 1. 多模态支持
- 支持图片、表格等多模态内容检索
- 多模态上下文理解和生成

### 2. 多语言支持
- 跨语言检索和生成
- 多语言知识库整合

### 3. 个性化定制
- 用户偏好学习
- 个性化搜索策略
- 定制化回答风格

## 监控与评估

### 1. 性能指标
- **检索准确率**: 相关文档的检索成功率
- **答案质量**: 基于人工评估或自动评估
- **响应时间**: 端到端响应延迟
- **搜索效率**: 平均搜索轮数

### 2. 系统监控
- **服务健康状态**: 各组件的运行状态
- **资源使用**: CPU、内存、网络使用情况
- **错误率**: 各类错误的发生频率

### 3. 用户体验
- **满意度评分**: 用户对答案质量的评价
- **使用模式**: 用户的问题类型和使用习惯
- **反馈循环**: 基于用户反馈优化系统

## 总结

本Agentic-RAG-Service基于S3框架，实现了智能化的检索增强生成服务。通过引入智能体技术，系统能够：

1. **自主决策**: 智能判断何时需要更多信息
2. **迭代优化**: 通过多轮搜索获得更全面的信息
3. **精准选择**: 从大量信息中选择最重要的内容
4. **高质量生成**: 基于精选信息生成准确、相关的答案

这种架构不仅提升了RAG系统的智能化水平，还为未来的扩展和优化提供了坚实的基础。
