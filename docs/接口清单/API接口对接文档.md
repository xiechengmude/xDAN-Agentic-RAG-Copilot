# xDAN Rag Copilot API Service 接口对接文档

## 📋 目录
- [基础配置](#基础配置)
- [认证方式](#认证方式)
- [响应格式](#响应格式)
- [知识库管理](#知识库管理)
- [文档管理](#文档管理)
- [对话管理](#对话管理)
- [检索接口](#检索接口)
- [引用文档查看](#引用文档查看)
- [SSE实时通信](#sse实时通信)
- [S3框架特性](#s3框架特性)
- [错误处理](#错误处理)
- [完整示例](#完整示例)

---

## 技术架构

### 系统架构图
```
┌─────────────┐     ┌──────────────────────────┐     ┌─────────────┐
│   前端应用   │────▶│ xDAN Unified API Server  │────▶│  RAGFlow    │
└─────────────┘     │      (Port 8050)         │     └─────────────┘
                    │                          │            ▲
                    │  ┌──────────────────┐   │            │
                    │  │ S3 Framework     │   │            │
                    │  │ - Search Agent   │   │────────────┘
                    │  │ - Select Agent   │   │
                    │  │ - Synthesize     │   │
                    │  └──────────────────┘   │
                    │                          │
                    │  ┌──────────────────┐   │     ┌─────────────┐
                    │  │ LiteLLM Router   │───┼────▶│ LLM Models  │
                    │  └──────────────────┘   │     └─────────────┘
                    │                          │
                    │  ┌──────────────────┐   │     ┌─────────────┐
                    │  │ PostgreSQL       │───┼────▶│  Database   │
                    │  │ Async Pool       │   │     └─────────────┘
                    │  └──────────────────┘   │
                    │                          │
                    │  ┌──────────────────┐   │     ┌─────────────┐
                    │  │ Langfuse Client  │───┼────▶│  Langfuse   │
                    │  │ (Observability)  │   │     │  Platform   │
                    │  └──────────────────┘   │     └─────────────┘
                    └──────────────────────────┘
```

### 核心组件说明

1. **xDAN Unified API Server**
   - 统一的API入口，提供标准化的RESTful接口
   - 集成Bearer Token认证
   - 统一响应格式处理

2. **S3 Framework (Search-Select-Synthesize)**
   - **Search Agent**: 智能搜索查询生成
   - **Select Agent**: 信息充分性判断（使用专用模型）
   - **Synthesize**: 基于筛选文档生成答案

3. **LiteLLM Router**
   - 统一的LLM调用接口
   - 支持多模型路由（DeepSeek、Qwen等）
   - 成本优化和负载均衡

4. **PostgreSQL存储层**
   - 高并发异步连接池（10-50连接）
   - 存储对话历史和元数据
   - 支持事务和ACID特性

5. **Langfuse可观察性**
   - 实时追踪S3工作流
   - LLM调用监控
   - 性能分析和成本追踪

---

## 基础配置

### API基础信息
- **本地开发**:
  - 统一API服务 Base URL: `http://localhost:8050` (xDAN Unified API Server)
  - 前端开发服务: `http://localhost:5173`
- **远程部署**:
  - 统一API服务 Base URL: `http://150.109.16.195:8050`
  - 前端应用: `http://150.109.16.195` (需配置nginx)
- **RAGFlow服务 Base URL**: `http://150.109.16.195:7080` (后端知识库服务)
- **API版本**: `v1`
- **协议**: `HTTP/HTTPS`
- **数据格式**: `JSON` / `FormData` (文件上传)

### 服务说明
xDAN Rag Copilot API Service 是一个完整的API代理服务，提供了标准化的接口访问。建议使用代理服务地址进行开发和集成。

### Swagger文档
- **本地访问**: http://localhost:8050/docs
- **远程访问**: http://150.109.16.195:8050/docs
- **OpenAPI规范**: `/openapi.json`
- 可通过Swagger UI直接测试所有接口

### 端口配置说明
| 服务 | 本地端口 | 远程端口 | 说明 |
|------|----------|----------|------|
| 前端应用 | 5173 | 80/443 | Vite开发服务器 / Nginx |
| API代理服务 | 8050 | 8050 | xDAN Rag Copilot API Service |
| RAGFlow服务 | - | 7080 | 原始RAGFlow API |
| 搜索演示 | 8051 | 8051 | 可选的搜索可视化服务 |
| PostgreSQL | 5432 | 5432 | 数据库服务 |
| Redis | 6379 | 6379 | 缓存服务（可选） |

### 配置文件说明

#### config.yaml结构
```yaml
# 服务配置
service:
  name: "xDAN Rag Copilot API Service"
  version: "2.0.0"
  host: "0.0.0.0"
  port: 8050

# 数据库配置
database:
  type: postgresql
  postgresql:
    host: ${DB_HOST:localhost}
    port: ${DB_PORT:5432}
    database: ${DB_NAME:xdan_rag_service}
    username: ${DB_USER:postgres}
    password: ${DB_PASSWORD:postgres}
    pool:
      min_connections: 10
      max_connections: 50

# RAGFlow配置
ragflow:
  base_url: ${RAGFLOW_BASE_URL:http://150.109.16.195:7080}
  api_key: ${RAGFLOW_API_KEY:ragflow-xxx}
  dataset_id: ${RAGFLOW_DATASET_ID:xxx}
  timeout: 30

# LiteLLM配置
litellm:
  config_path: "litellm_ragflow_config.yaml"
  default_model: "deepseek-ai/DeepSeek-V3@SILICONFLOW"

# 可观察性配置
observability:
  langfuse:
    enabled: true
    host: ${LANGFUSE_HOST:https://agentops.xdan.ai}
    public_key: ${LANGFUSE_PUBLIC_KEY:pk-lf-xxx}
    secret_key: ${LANGFUSE_SECRET_KEY:sk-lf-xxx}
```

#### 环境变量配置
```bash
# .env文件示例
DB_HOST=localhost
DB_PORT=5432
DB_NAME=xdan_rag_service
DB_USER=postgres
DB_PASSWORD=postgres

RAGFLOW_BASE_URL=http://150.109.16.195:7080
RAGFLOW_API_KEY=ragflow-g4ZWE3OTNhNDUxYTExZjA8MTljMDI0Mm
RAGFLOW_DATASET_ID=7e8d9e924cde11f0afc90242ac140006

LANGFUSE_HOST=https://agentops.xdan.ai
LANGFUSE_PUBLIC_KEY=pk-lf-aab86f14-addb-4f26-a755-9ba672359e85
LANGFUSE_SECRET_KEY=sk-lf-dbfde2d7-c80a-456a-8078-279958763214
```

### 请求头配置
```http
Content-Type: application/json
Authorization: Bearer {token}
Accept: application/json
```

---

## 认证方式

### Bearer Token认证
所有API请求需要在请求头中携带Bearer Token：

```http
Authorization: Bearer xDAN-RAG-Service-Demo-Key
```

**默认API Key**: `xDAN-RAG-Service-Demo-Key`

**注意**: 
- 所有接口都需要Bearer Token认证
- 无认证或错误Token将返回401/403错误
- 建议在生产环境中更换为自定义密钥

---

## 响应格式

### 统一响应结构
```json
{
  "code": 0,                    // 0表示成功，非0表示错误
  "message": "Success",         // 响应消息
  "data": {                     // 响应数据（可选）
    // 具体数据内容
  },
  "meta": {                     // 元数据（分页时使用）
    "page": 1,
    "size": 20,
    "total": 100,
    "has_next": true,
    "has_prev": false
  }
}
```

### 错误响应格式
```json
{
  "code": 400,
  "message": "参数错误",
  "data": null
}
```

---

## 系统管理接口

### 健康检查
```http
GET /health
```

**响应示例**:
```json
{
  "code": 0,
  "message": "Success",
  "data": {
    "status": "healthy",
    "version": "2.0.0",
    "components": {
      "database": {
        "status": "healthy",
        "type": "postgresql",
        "pool_size": 10
      },
      "ragflow": {
        "status": "healthy",
        "base_url": "http://150.109.16.195:7080"
      },
      "langfuse": {
        "status": "healthy",
        "enabled": true
      },
      "s3_framework": {
        "status": "healthy",
        "agent_model": "xDAN-R2-Qwen3-14b-RagRL-step450-0618"
      }
    },
    "timestamp": "2025-06-26T12:00:00Z"
  }
}
```

---

## 知识库管理

### 1. 获取知识库列表
```http
GET /api/v1/datasets?page=1&page_size=12&name=keyword
```

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认12 |
| name | string | 否 | 名称模糊搜索（在客户端进行过滤） |

**注意**: `name` 参数的搜索是在客户端实现的，因为 RAGFlow API 会将 name 参数误认为是数据集 ID 进行权限检查。

**响应示例**:
```json
{
  "code": 0,
  "data": [
    {
      "id": "7e8d9e924cde11f0afc90242ac140006",
      "name": "360test00000",
      "description": "as",
      "document_count": 3,
      "chunk_count": 201,
      "token_num": 46759,
      "embedding_model": "BAAI/bge-m3@SILICONFLOW",
      "chunk_method": "naive",
      "status": "1",
      "create_date": "Thu, 19 Jun 2025 15:24:53 GMT",
      "update_date": "Mon, 23 Jun 2025 09:18:35 GMT",
      "parser_config": {
        "chunk_token_num": 512,
        "delimiter": "\n",
        "auto_keywords": 0,
        "auto_questions": 0
      }
    }
  ]
}
```

### 2. 创建知识库
```http
POST /api/v1/datasets
```

**请求体**:
```json
{
  "name": "测试知识库",
  "description": "用于测试的知识库",
  "embedding_model": "BAAI/bge-m3@SILICONFLOW",
  "chunk_method": "naive",
  "parser_config": {
    "chunk_token_num": 512,
    "delimiter": "\n",
    "auto_keywords": 0,
    "auto_questions": 0
  }
}
```

**重要说明**:
- `embedding_model` 必须使用格式：`模型名@提供商`
- 不能包含 `language` 字段
- `chunk_method` 可选值：`naive`

**响应示例**:
```json
{
  "code": 0,
  "data": {
    "id": "b66e12c44fea11f0bc4e0242ac140006",
    "name": "测试知识库",
    "status": "1"
  }
}
```

### 3. 更新知识库
```http
PUT /api/v1/datasets/{dataset_id}
```

**请求体**:
```json
{
  "name": "更新后的名称",
  "description": "更新后的描述"
}
```

### 4. 删除知识库
```http
DELETE /api/v1/datasets/{dataset_id}
```

**注意**: 内部实现使用批量删除接口，即使是删除单个数据集。

**响应示例**:
```json
{
  "code": 0,
  "message": "删除成功"
}
```

---

## 文档管理

### 1. 上传文档
```http
POST /api/v1/datasets/{dataset_id}/documents
Content-Type: multipart/form-data
```

**请求体** (FormData):
- `file`: 文件对象（单个文件使用 `file` 字段，不是 `files[]`）

**注意**: 不要手动设置 Content-Type 头，让浏览器自动设置以确保正确的 boundary 参数。

**响应示例** (重要：返回数组格式):
```json
{
  "code": 0,
  "data": [
    {
      "id": "4cae901c4fda11f0a76c0242ac140006",
      "name": "debug_upload.txt",
      "size": 78,
      "type": "doc",
      "location": "debug_upload.txt",
      "dataset_id": "7e9fe1de4ce211f09cf90242ac140006",
      "run": "UNSTART",
      "parser_config": {
        "chunk_token_num": 512,
        "delimiter": "\n"
      }
    }
  ]
}
```

### 2. 获取文档列表
```http
GET /api/v1/datasets/{dataset_id}/documents?page=1&page_size=20
```

**响应示例**:
```json
{
  "code": 0,
  "data": {
    "docs": [
      {
        "id": "doc123",
        "name": "test.pdf",
        "size": 1024,
        "run": "DONE",
        "type": "pdf",
        "dataset_id": "dataset123"
      }
    ],
    "total": 1
  }
}
```

### 3. 获取文档内容
```http
GET /api/v1/datasets/{dataset_id}/documents/{doc_id}
```

**响应**: 返回文档的文本内容（非JSON格式）

### 4. 删除文档
```http
DELETE /api/v1/datasets/{dataset_id}/documents/{doc_id}
```

**注意**: 内部实现统一使用批量删除接口。

### 5. 批量删除文档
```http
DELETE /api/v1/datasets/{dataset_id}/documents
```

**请求体**:
```json
{
  "ids": ["doc_id1", "doc_id2"]
}
```

**注意**: 所有文档删除操作都使用此批量接口，即使删除单个文档也需要传递数组格式。

### 6. 下载文档
```http
GET /api/v1/datasets/{dataset_id}/documents/{doc_id}/download
```

**响应**: 文件流

### 7. 解析文档
```http
POST /api/v1/datasets/{dataset_id}/documents/parse
```

**请求体**:
```json
{
  "document_ids": ["doc_id1", "doc_id2"]
}
```

**说明**: RAGFlow 通常在上传后自动解析文档，此接口主要用于触发重新解析。

---

## 对话管理

**注意**: `GET /api/v1/chats/{chat_id}` 和 `PUT /api/v1/chats/{chat_id}` 这两个接口未实现。

### 1. 创建对话
```http
POST /api/v1/chats
```

**请求体**:
```json
{
  "name": "测试对话",
  "dataset_ids": ["7e8d9e924cde11f0afc90242ac140006"],
  "description": "用于测试的对话"
}
```

**注意**: 只有包含已解析文档的知识库才能创建对话。

**响应示例**:
```json
{
  "code": 0,
  "data": {
    "id": "2d0215664feb11f09be10242ac140006",
    "name": "测试对话",
    "dataset_ids": ["7e8d9e924cde11f0afc90242ac140006"],
    "llm": {
      "model_name": "deepseek-ai/DeepSeek-V3@SILICONFLOW",
      "temperature": 0.1,
      "max_tokens": 512
    },
    "create_date": "Mon, 23 Jun 2025 12:33:12 GMT"
  }
}
```

### 2. 发送消息（SSE流式响应）
```http
POST /api/v1/chats/{chat_id}/completions
Content-Type: application/json
```

**请求体**:
```json
{
  "content": "你好，请介绍一下RAGFlow"
}
```

**响应格式** (SSE):
```
data:{"code": 0, "message": "", "data": {"answer": "Hi! I'm your assistant, what can I do for you?", "reference": {}, "audio_binary": null, "id": null, "session_id": "fa6c17504fea11f0b6cc0242ac140006"}}

data:{"code": 0, "message": "", "data": true}
```

### 3. 获取对话历史
```http
GET /api/v1/chats/{chat_id}/messages?page=1&page_size=20
```

### 4. 删除对话
```http
DELETE /api/v1/chats/{chat_id}
```

---

## 检索接口

### 知识库检索
```http
POST /api/v1/retrieve
```

**请求体**:
```json
{
  "question": "什么是权益申请？",
  "dataset_ids": ["7e8d9e924cde11f0afc90242ac140006"],
  "page": 1,
  "page_size": 5
}
```

**响应示例**:
```json
{
  "code": 0,
  "data": {
    "chunks": [
      {
        "id": "chunk123",
        "content_ltks": "权益申请业务是指...",
        "similarity": 0.694,
        "document_name": "业务手册.pdf",
        "dataset_id": "7e8d9e924cde11f0afc90242ac140006"
      }
    ]
  }
}
```

---

## 引用文档查看

### 1. 获取引用文档详情
```http
GET /api/v1/documents/reference/{document_id}?dataset_id={dataset_id}
```

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| document_id | string | 是 | 文档ID（从对话响应的reference中获取） |
| dataset_id | string | 是 | 数据集ID |

**响应示例**:
```json
{
  "code": 0,
  "message": "Success",
  "data": {
    "document_id": "5adf66a24d0011f0853d0242ac140006",
    "document_name": "业务手册.pdf",
    "dataset_id": "7e8d9e924cde11f0afc90242ac140006",
    "content": "权益申请业务是指客户向银行申请各类权益服务的流程...",
    "metadata": {
      "size": 15420,
      "pages": 25,
      "upload_time": "2024-06-19T15:24:53Z"
    }
  }
}
```

### 2. 批量获取引用文档
```http
POST /api/v1/documents/reference/batch
```

**请求体**:
```json
{
  "references": [
    {
      "document_id": "doc1",
      "dataset_id": "dataset1"
    },
    {
      "document_id": "doc2", 
      "dataset_id": "dataset1"
    }
  ]
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "Success",
  "data": {
    "documents": [
      {
        "document_id": "doc1",
        "document_name": "文档1.pdf",
        "content": "文档1的内容...",
        "similarity": 0.95
      },
      {
        "document_id": "doc2",
        "document_name": "文档2.pdf", 
        "content": "文档2的内容...",
        "similarity": 0.88
      }
    ],
    "total_found": 2
  }
}
```

### 使用场景
- **验证回答合理性**: 用户可以查看模型引用的原始文档内容
- **追溯信息来源**: 了解答案基于哪些具体文档
- **质量评估**: 检查引用文档与问题的相关性
- **Langfuse追踪**: 所有文档查看请求都会记录在Langfuse平台

---

## SSE实时通信

### 1. 对话流式响应
**端点**: `POST /api/v1/chats/{chat_id}/completions`

**SSE数据格式**:
```javascript
// 初始响应 - 包含完整的搜索元数据和S3框架执行过程
data:{"code": 0, "message": "Success", "data": {
  "answer": "根据业务手册，权益申请是指...",
  "reference": {
    "total": 3,
    "chunks": [
      {
        "id": "chunk_id_1",
        "content": "权益申请业务是指...",
        "document_name": "业务手册.pdf",
        "document_id": "5adf66a24d0011f0853d0242ac140006",
        "dataset_id": "7e8d9e924cde11f0afc90242ac140006",
        "similarity": 0.95,
        "position": "p12-15"  // 文档位置信息
      }
    ],
    "search_rounds": 2,
    "search_process": [
      {
        "round": 1,
        "query": "权益申请流程",
        "documents_found": 5,
        "agent_decision": "信息不足，需要更多关于具体操作步骤的信息",
        "agent_confidence": 0.3,
        "time_ms": 245
      },
      {
        "round": 2,
        "query": "权益申请操作步骤详细流程",
        "documents_found": 3,
        "agent_decision": "信息充足，可以生成答案",
        "agent_confidence": 0.85,
        "time_ms": 198
      }
    ],
    "s3_trace_id": "trace_12345",  // Langfuse追踪ID
    "total_time_ms": 1234
  },
  "session_id": "xxx",
  "message_id": "msg_12345"
}}

// 增量消息 - 流式传输答案内容（真正的增量）
data:{"code": 0, "message": "Success", "data": {
  "answer_delta": "具",  // 每次只返回新增的字符
  "accumulated_answer": "根据业务手册，权益申请是指...具"  // 服务端累加的完整内容（可选）
}}

data:{"code": 0, "message": "Success", "data": {
  "answer_delta": "体",  // 下一个字符
  "accumulated_answer": "根据业务手册，权益申请是指...具体"
}}

// 注意：answer_delta 是真正的增量内容，每次只包含新增的字符，实现逐字流式效果

// 结束标志
data:{"code": 0, "message": "", "data": true}
```

### 2. 前端处理示例
```javascript
const response = await fetch('http://localhost:8050/api/v1/chats/chat_id/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer xDAN-RAG-Service-Demo-Key'
  },
  body: JSON.stringify({ content: '你好' })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();
let buffer = '';

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split('\n');
  buffer = lines.pop() || '';
  
  for (const line of lines) {
    if (line.startsWith('data:')) {
      const jsonData = line.slice(5).trim();
      if (jsonData) {
        const data = JSON.parse(jsonData);
        if (data.code === 0 && data.data.answer) {
          console.log('AI回答:', data.data.answer);
        }
      }
    }
  }
}
```

---

## S3框架特性

### Search-Select-Synthesize智能工作流

**核心特性**:
- **智能搜索**: 基于用户问题自动生成搜索查询
- **智能选择**: 使用专用智能体模型判断信息充分性
- **多轮搜索**: 最多5轮智能搜索，直到信息充足
- **精准合成**: 基于筛选文档生成准确答案

### 1. S3框架工作流程
```
用户问题 → S3-Search → S3-Select → S3-Synthesize → 最终答案
                ↑         ↓
              多轮搜索 ← 信息不足？
```

### 2. 智能体决策展示
对话响应中包含完整的搜索过程：

```json
{
  "reference": {
    "search_rounds": 2,
    "search_process": [
      {
        "round": 1,
        "query": "权益申请流程",
        "documents_found": 5,
        "agent_decision": "信息不足，需要更多关于具体操作步骤的信息"
      },
      {
        "round": 2, 
        "query": "权益申请操作步骤详细流程",
        "documents_found": 3,
        "agent_decision": "信息充足，可以生成答案"
      }
    ]
  }
}
```

### 3. 专用模型配置
- **智能体模型**: `xDAN-R2-Qwen3-14b-RagRL-step450-0618` (决策专用)
  - 用途：判断信息充分性，生成搜索查询
  - 特点：专门训练的强化学习模型
- **生成模型**: `deepseek-ai/DeepSeek-V3` (成本优化)
  - 用途：基于检索文档生成最终答案
  - 特点：高质量生成，成本效益好
- **路由策略**: LiteLLM智能路由
  - 基于成本优化
  - 支持降级和故障转移
  - 实时监控和调整

### 4. 可观测性特性

#### Langfuse集成
- **追踪粒度**: 
  - S3框架完整工作流追踪
  - 每轮搜索独立追踪
  - LLM调用详细记录
- **关键指标**:
  - 搜索轮数和耗时
  - 智能体决策置信度
  - 文档相关性分数
  - Token使用量和成本
- **用户反馈**: 
  - 支持用户对答案质量的反馈
  - 反馈数据自动同步到Langfuse

#### 实时监控
- **S3执行过程**: 完整的Search-Select-Synthesize流程
- **决策透明**: 智能体每轮决策理由和置信度
- **性能分析**: 
  - P50/P95/P99延迟
  - 成功率和错误率
  - 资源使用情况

#### 数据持久化
- **PostgreSQL存储**:
  - 对话历史完整保存
  - S3工作流元数据
  - 用户反馈记录
  - 性能指标汇总

---

## 错误处理

### 常见错误码
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 0 | 成功 | - |
| 100 | 通用错误 | 检查请求参数和格式 |
| 101 | 文件相关错误 | "No file part!" - 检查文件上传格式 |
| 400 | 请求参数错误 | 检查必填参数和参数格式 |
| 401 | 未授权 | 检查token是否有效 |
| 403 | 禁止访问 | 检查资源权限 |
| 404 | 资源不存在 | 确认资源ID是否正确 |
| 500 | 服务器内部错误 | 稍后重试或联系技术支持 |
| 502 | RAGFlow服务不可用 | 检查后端服务状态 |
| 503 | S3框架暂时不可用 | 系统将自动降级到直接生成 |

### 错误响应示例
```json
{
  "code": 100,
  "data": null,
  "message": "The dataset b66e12c44fea11f0bc4e0242ac140006 doesn't own parsed file"
}
```

### 异常处理机制

#### S3框架降级
当S3框架不可用时，系统自动降级：
1. 跳过智能搜索，直接使用简单检索
2. 使用备用LLM模型生成答案
3. 在响应中标记降级状态

#### 数据库故障处理
- 对话历史暂存在内存
- 异步重试写入
- 不影响核心问答功能

#### Langfuse不可用
- 继续正常服务
- 本地记录关键指标
- 恢复后批量上传

---

## 完整示例

### 完整的知识库问答流程

#### 1. 创建知识库
```bash
curl -X POST "http://localhost:8050/api/v1/datasets" \
  -H "Authorization: Bearer xDAN-RAG-Service-Demo-Key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "API测试知识库",
    "description": "通过API创建的测试知识库",
    "embedding_model": "BAAI/bge-m3@SILICONFLOW",
    "chunk_method": "naive"
  }'
```

#### 2. 上传文档
```bash
curl -X POST "http://localhost:8050/api/v1/datasets/{dataset_id}/documents" \
  -H "Authorization: Bearer xDAN-RAG-Service-Demo-Key" \
  -F "file=@test_document.txt"
```

#### 3. 等待文档解析
```bash
# 检查文档状态
curl -X GET "http://localhost:8050/api/v1/datasets/{dataset_id}/documents/{doc_id}" \
  -H "Authorization: Bearer xDAN-RAG-Service-Demo-Key"
```

#### 4. 创建对话
```bash
curl -X POST "http://localhost:8050/api/v1/chats" \
  -H "Authorization: Bearer xDAN-RAG-Service-Demo-Key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试对话",
    "dataset_ids": ["{dataset_id}"]
  }'
```

#### 5. 发送消息
```bash
curl -X POST "http://localhost:8050/api/v1/chats/{chat_id}/completions" \
  -H "Authorization: Bearer xDAN-RAG-Service-Demo-Key" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "请介绍一下文档的主要内容"
  }'
```

#### 6. 检索测试
```bash
curl -X POST "http://localhost:8050/api/v1/retrieve" \
  -H "Authorization: Bearer xDAN-RAG-Service-Demo-Key" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "文档中的关键信息",
    "dataset_ids": ["{dataset_id}"],
    "page": 1,
    "page_size": 5
  }'
```

---

## 重要提醒

### 1. 文档上传注意事项
- 使用 `file` 字段，不是 `files[]`
- 响应是数组格式，需要取 `data[0]`
- 文档上传后会自动解析

### 2. 对话创建前提
- 知识库必须包含已解析完成的文档
- 文档状态必须是 `DONE`

### 3. SSE响应处理
- 流式响应包含多条 `data:` 消息
- 第一条包含答案内容
- 最后一条 `data: true` 表示结束

### 4. embedding模型格式
- 必须使用 `模型名@提供商` 格式
- 推荐：`BAAI/bge-m3@SILICONFLOW`

### 5. API测试建议
- 先用现有知识库测试功能
- 使用ID：`7e8d9e924cde11f0afc90242ac140006`
- 该知识库包含3个已解析文档，可直接测试对话

---

---

## 部署指南

### Docker Compose部署
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: xdan_rag_service
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  api-server:
    build: .
    ports:
      - "8050:8050"
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
    depends_on:
      - postgres
    volumes:
      - ./config.yaml:/app/config.yaml
      - ./.env:/app/.env

volumes:
  postgres_data:
```

### 生产环境配置建议
1. **API密钥**: 替换默认的 `xDAN-RAG-Service-Demo-Key`
2. **数据库**: 使用独立的PostgreSQL实例，配置SSL
3. **连接池**: 根据负载调整连接池大小（10-100）
4. **监控**: 配置Prometheus + Grafana监控
5. **日志**: 使用ELK或类似方案收集日志

---

**文档版本**: v2.2  
**最后更新**: 2025-06-27  
**测试状态**: ✅ 已验证所有接口  
**服务名称**: xDAN Rag Copilot API Service  
**主要更新**: 
- 添加技术架构说明
- 补充PostgreSQL和Langfuse集成
- 完善S3框架工作流程
- 增加健康检查接口
- 更新SSE响应格式
- 添加部署指南
- 更新删除接口和名称搜索说明
- 明确流式响应为真正的逐字增量
- 添加解析文档接口
- 修正检索接口路径（/api/v1/retrieve）
- 标注未实现的对话管理接口