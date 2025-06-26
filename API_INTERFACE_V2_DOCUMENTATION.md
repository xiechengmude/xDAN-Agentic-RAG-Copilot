# xDAN Rag Copilot API Service V2.0 接口文档

## 📋 版本更新说明

### V2.0 主要变更：
1. **统一响应格式**：所有接口返回 `{code, message, data, meta}` 格式
2. **Bearer Token认证**：所有API接口需要认证
3. **S3框架深度集成**：智能问答基于Search-Select-Synthesize框架
4. **增强的错误处理**：统一的错误响应格式

---

## 🔐 认证方式

### API Key认证
所有API请求需要在请求头中携带认证token：

```http
Authorization: Bearer xDAN-RAG-Service-Demo-Key
```

**默认API Key**: `xDAN-RAG-Service-Demo-Key`

### 认证错误响应
```json
{
  "code": 401,
  "message": "Invalid API key",
  "data": null
}
```

---

## 📝 统一响应格式

### 成功响应结构
```json
{
  "code": 0,                    // 0表示成功
  "message": "Success",         // 响应消息
  "data": {                     // 响应数据
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

### 错误响应结构
```json
{
  "code": 400,                  // HTTP状态码
  "message": "Error message",   // 错误描述
  "data": null                  // 错误详情（可选）
}
```

---

## 🔍 API接口列表

### 1. 系统接口

#### GET /health
- **描述**: 健康检查（无需认证）
- **响应示例**:
```json
{
  "code": 0,
  "message": "Success",
  "data": {
    "status": "healthy",
    "service": "xDAN Rag Copilot API Service",
    "version": "2.0.0",
    "components": {
      "s3_framework": true,
      "ragflow": true,
      "litellm": true
    },
    "timestamp": "2025-06-26T20:30:00"
  }
}
```

#### GET /
- **描述**: 根路径信息（无需认证）
- **响应示例**:
```json
{
  "code": 0,
  "message": "Success",
  "data": {
    "service": "xDAN Rag Copilot API Service",
    "version": "2.0.0",
    "description": "统一的API服务，整合S3框架和RAGFlow知识库管理",
    "features": [
      "S3智能问答框架",
      "知识库管理",
      "实时流式对话",
      "统一LLM路由"
    ],
    "endpoints": {
      "docs": "/docs",
      "health": "/health",
      "api": "/api/v1"
    }
  }
}
```

### 2. 聊天管理接口

#### POST /api/v1/chats
- **描述**: 创建新的对话
- **认证**: 需要Bearer Token
- **请求体**:
```json
{
  "name": "测试对话",
  "dataset_ids": ["dataset_id_1", "dataset_id_2"],
  "description": "对话描述",
  "llm_config": {
    "model_name": "deepseek-chat",
    "temperature": 0.7,
    "max_tokens": 2000
  }
}
```
- **响应示例**:
```json
{
  "code": 0,
  "message": "Success",
  "data": {
    "id": "chat_id_123",
    "name": "测试对话",
    "description": "对话描述",
    "dataset_ids": ["dataset_id_1"],
    "llm": {
      "model_name": "deepseek-chat",
      "temperature": 0.7,
      "max_tokens": 2000
    },
    "create_date": "2025-06-26T20:30:00"
  }
}
```

#### GET /api/v1/chats
- **描述**: 获取对话列表
- **认证**: 需要Bearer Token
- **查询参数**:
  - `page`: 页码（默认1）
  - `page_size`: 每页数量（默认20）
- **响应示例**:
```json
{
  "code": 0,
  "message": "Success",
  "data": [
    {
      "id": "chat_id_123",
      "name": "测试对话",
      "description": "对话描述",
      "created_at": "2025-06-26T20:30:00"
    }
  ],
  "meta": {
    "page": 1,
    "size": 20,
    "total": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

#### POST /api/v1/chats/{chat_id}/completions
- **描述**: 发送消息并获取AI回复（集成S3框架）
- **认证**: 需要Bearer Token
- **请求体**:
```json
{
  "content": "什么是S3框架？",
  "stream": false
}
```
- **响应示例**:
```json
{
  "code": 0,
  "message": "Success",
  "data": {
    "answer": "S3框架是Search-Select-Synthesize的缩写...",
    "reference": {
      "total": 3,
      "chunks": [
        {
          "content": "相关文档内容",
          "similarity": 0.95,
          "document_name": "S3架构文档.pdf"
        }
      ],
      "search_rounds": 2,
      "search_process": [
        {
          "round": 1,
          "query": "S3框架",
          "results_count": 5
        }
      ]
    },
    "session_id": "chat_id_123"
  }
}
```

#### GET /api/v1/chats/{chat_id}/messages
- **描述**: 获取对话历史
- **认证**: 需要Bearer Token
- **查询参数**:
  - `page`: 页码（默认1）
  - `page_size`: 每页数量（默认20）

#### DELETE /api/v1/chats/{chat_id}
- **描述**: 删除对话
- **认证**: 需要Bearer Token
- **响应示例**:
```json
{
  "code": 0,
  "message": "Chat deleted successfully",
  "data": null
}
```

### 3. 知识库管理接口

#### GET /api/v1/datasets
- **描述**: 获取知识库列表
- **认证**: 需要Bearer Token
- **查询参数**:
  - `page`: 页码（默认1）
  - `page_size`: 每页数量（默认12）
  - `name`: 名称筛选（可选）

#### POST /api/v1/datasets
- **描述**: 创建知识库
- **认证**: 需要Bearer Token
- **请求体**:
```json
{
  "name": "测试知识库",
  "description": "用于测试的知识库",
  "embedding_model": "BAAI/bge-m3@SILICONFLOW",
  "chunk_method": "naive",
  "parser_config": {
    "chunk_token_num": 512,
    "delimiter": "\\n"
  }
}
```

#### PUT /api/v1/datasets/{dataset_id}
- **描述**: 更新知识库
- **认证**: 需要Bearer Token

#### DELETE /api/v1/datasets/{dataset_id}
- **描述**: 删除知识库
- **认证**: 需要Bearer Token

### 4. 文档管理接口

#### POST /api/v1/datasets/{dataset_id}/documents
- **描述**: 上传文档到知识库
- **认证**: 需要Bearer Token
- **请求体**: multipart/form-data
  - `file`: 文件对象

#### GET /api/v1/datasets/{dataset_id}/documents
- **描述**: 获取文档列表
- **认证**: 需要Bearer Token

#### DELETE /api/v1/datasets/{dataset_id}/documents/{document_id}
- **描述**: 删除文档
- **认证**: 需要Bearer Token

### 5. 知识检索接口

#### POST /api/v1/retrieval
- **描述**: 知识库检索
- **认证**: 需要Bearer Token
- **请求体**:
```json
{
  "question": "什么是S3框架？",
  "dataset_ids": ["dataset_id_1"],
  "page": 1,
  "page_size": 5,
  "similarity_threshold": 0.1
}
```

---

## 🔄 SSE流式响应

对于聊天完成接口，当`stream: true`时，返回SSE格式：

```
Content-Type: text/event-stream

data: {"type": "chunk", "content": "部分回答内容"}

data: {"type": "workflow", "workflow_info": {"search_rounds": 2, "selected_documents": []}}

data: {"type": "done"}
```

---

## 🚨 错误处理

### 常见错误码
- `401`: 未授权（API Key无效或缺失）
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误
- `503`: 服务不可用

### 错误响应示例
```json
{
  "code": 401,
  "message": "Invalid API key",
  "data": null
}
```

---

## 📚 测试示例

### cURL示例
```bash
# 健康检查（无需认证）
curl -X GET "http://localhost:8050/health"

# 获取知识库列表（需要认证）
curl -X GET "http://localhost:8050/api/v1/datasets" \
  -H "Authorization: Bearer xDAN-RAG-Service-Demo-Key"

# 创建聊天
curl -X POST "http://localhost:8050/api/v1/chats" \
  -H "Authorization: Bearer xDAN-RAG-Service-Demo-Key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试聊天",
    "dataset_ids": ["dataset_id"]
  }'
```

### Python示例
```python
import requests

headers = {
    "Authorization": "Bearer xDAN-RAG-Service-Demo-Key",
    "Content-Type": "application/json"
}

# 获取知识库列表
response = requests.get(
    "http://localhost:8050/api/v1/datasets",
    headers=headers
)

if response.status_code == 200:
    result = response.json()
    if result["code"] == 0:
        datasets = result["data"]
        print(f"找到 {len(datasets)} 个知识库")
```

---

## 🎯 S3框架特性

### 智能问答流程
1. **Search阶段**: 从RAGFlow检索相关文档
2. **Select阶段**: 使用xDAN-R2模型智能筛选重要文档
3. **Synthesize阶段**: 使用DeepSeek模型生成精准答案

### 配置选项
- 最大搜索轮数：3轮
- 检索数量：每轮10个文档
- 智能筛选：自动选择最相关的3个文档

---

**文档版本**: V2.0  
**最后更新**: 2025-06-26  
**服务版本**: 2.0.0