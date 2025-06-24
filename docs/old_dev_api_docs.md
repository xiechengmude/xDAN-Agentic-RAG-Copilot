# RAGFlow API 客户端

**版本**: 0.1.0

**生成时间**: 2025-06-24 16:01:09

---

## 接口列表

### GET /api/v1/datasets/{dataset_id}/documents/{document_id}/status/stream

**摘要**: Stream Document Status

**描述**: 使用 SSE 流式推送文档处理状态

返回格式:
data: {"type": "status", "doc_id": "xxx", "status": "parsing", "progress": 0.5}

**标签**: SSE

#### 请求参数
| 参数名 | 位置 | 类型 | 必需 | 描述 |
|--------|------|------|------|------|
| dataset_id | path | string | 是 |  |
| document_id | path | string | 是 |  |

#### 响应

**200**: Successful Response

**Content-Type**: application/json

**422**: Validation Error

**Content-Type**: application/json

---

### POST /api/v1/chats/{chat_id}/stream

**摘要**: Stream Chat Response

**描述**: 使用 SSE 流式返回对话响应

请求体:
{
    "messages": [{"role": "user", "content": "你好"}],
    "dataset_id": "xxx"  # 可选，指定知识库
}

返回格式:
data: {"type": "message", "content": "你好", "done": false}

**标签**: SSE

#### 请求参数
| 参数名 | 位置 | 类型 | 必需 | 描述 |
|--------|------|------|------|------|
| chat_id | path | string | 是 |  |

#### 请求体

**Content-Type**: application/json

#### 响应

**200**: Successful Response

**Content-Type**: application/json

**422**: Validation Error

**Content-Type**: application/json

---

### GET /api/v1/datasets/{dataset_id}/documents/status/stream

**摘要**: Stream Multiple Documents Status

**描述**: 批量监控多个文档的处理状态

参数:
- doc_ids: 逗号分隔的文档ID列表，如 "id1,id2,id3"

**标签**: SSE

#### 请求参数
| 参数名 | 位置 | 类型 | 必需 | 描述 |
|--------|------|------|------|------|
| dataset_id | path | string | 是 |  |
| doc_ids | query | string | 是 |  |

#### 响应

**200**: Successful Response

**Content-Type**: application/json

**422**: Validation Error

**Content-Type**: application/json

---

### POST /v1/chats/{chat_id}/chat/completions

**摘要**: Create Chat Completion

**描述**: 创建聊天完成

#### 请求参数
| 参数名 | 位置 | 类型 | 必需 | 描述 |
|--------|------|------|------|------|
| chat_id | path | string | 是 |  |

#### 请求体

**Content-Type**: application/json

| 字段名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| model | string | 是 | Model |
| messages | array[N/A] | 是 | Messages |
| stream | boolean | 否 | Stream |

#### 响应

**200**: Successful Response

**Content-Type**: application/json

**422**: Validation Error

**Content-Type**: application/json

---

### POST /v1/agents/{agent_id}/chat/completions

**摘要**: Create Agent Completion

**描述**: 创建 Agent 完成

#### 请求参数
| 参数名 | 位置 | 类型 | 必需 | 描述 |
|--------|------|------|------|------|
| agent_id | path | string | 是 |  |

#### 请求体

**Content-Type**: application/json

| 字段名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| model | string | 是 | Model |
| messages | array[N/A] | 是 | Messages |
| stream | boolean | 否 | Stream |

#### 响应

**200**: Successful Response

**Content-Type**: application/json

**422**: Validation Error

**Content-Type**: application/json

---

### POST /v1/datasets

**摘要**: Create Dataset

**描述**: 创建数据集

#### 请求体

**Content-Type**: application/json

| 字段名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| name | string | 是 | Name |
| avatar | N/A | 否 | Avatar |
| description | N/A | 否 | Description |
| embedding_model | N/A | 否 | Embedding Model |
| permission | N/A | 否 | Permission (默认: me) |
| chunk_method | N/A | 否 | Chunk Method (默认: naive) |
| pagerank | N/A | 否 | Pagerank |
| parser_config | N/A | 否 | Parser Config |

#### 响应

**200**: Successful Response

**Content-Type**: application/json

**422**: Validation Error

**Content-Type**: application/json

---

### DELETE /v1/datasets

**摘要**: Delete Datasets

**描述**: 删除数据集

#### 请求体

**Content-Type**: application/json

#### 响应

**200**: Successful Response

**Content-Type**: application/json

**422**: Validation Error

**Content-Type**: application/json

---

### GET /v1/datasets

**摘要**: List Datasets

**描述**: 列出数据集

#### 请求参数
| 参数名 | 位置 | 类型 | 必需 | 描述 |
|--------|------|------|------|------|
| page | query | integer | 否 |  |
| page_size | query | integer | 否 |  |
| orderby | query | string | 否 |  |
| desc | query | boolean | 否 |  |
| name | query | N/A | 否 |  |
| id | query | N/A | 否 |  |

#### 响应

**200**: Successful Response

**Content-Type**: application/json

**422**: Validation Error

**Content-Type**: application/json

---

### PUT /v1/datasets/{dataset_id}

**摘要**: Update Dataset

**描述**: 更新数据集

#### 请求参数
| 参数名 | 位置 | 类型 | 必需 | 描述 |
|--------|------|------|------|------|
| dataset_id | path | string | 是 |  |

#### 请求体

**Content-Type**: application/json

#### 响应

**200**: Successful Response

**Content-Type**: application/json

**422**: Validation Error

**Content-Type**: application/json

---

### GET /v1/datasets/{dataset_id}/documents

**摘要**: List Documents

**描述**: 列出数据集中的文档

#### 请求参数
| 参数名 | 位置 | 类型 | 必需 | 描述 |
|--------|------|------|------|------|
| dataset_id | path | string | 是 |  |
| page | query | N/A | 否 |  |
| page_size | query | N/A | 否 |  |
| orderby | query | N/A | 否 |  |
| desc | query | N/A | 否 |  |
| keywords | query | N/A | 否 |  |
| id | query | N/A | 否 |  |
| name | query | N/A | 否 |  |

#### 响应

**200**: Successful Response

**Content-Type**: application/json

**422**: Validation Error

**Content-Type**: application/json

---

### DELETE /v1/datasets/{dataset_id}/documents

**摘要**: Delete Documents

**描述**: 删除数据集中的文档

#### 请求参数
| 参数名 | 位置 | 类型 | 必需 | 描述 |
|--------|------|------|------|------|
| dataset_id | path | string | 是 |  |

#### 请求体

**Content-Type**: application/json

#### 响应

**200**: Successful Response

**Content-Type**: application/json

**422**: Validation Error

**Content-Type**: application/json

---

### POST /v1/datasets/{dataset_id}/chunks

**摘要**: Parse Documents

**描述**: 解析文档

#### 请求参数
| 参数名 | 位置 | 类型 | 必需 | 描述 |
|--------|------|------|------|------|
| dataset_id | path | string | 是 |  |

#### 请求体

**Content-Type**: application/json

#### 响应

**200**: Successful Response

**Content-Type**: application/json

**422**: Validation Error

**Content-Type**: application/json

---

### GET /v1/datasets/{dataset_id}/documents/{document_id}/download

**摘要**: Download Document

**描述**: 下载文档原始文件

#### 请求参数
| 参数名 | 位置 | 类型 | 必需 | 描述 |
|--------|------|------|------|------|
| dataset_id | path | string | 是 |  |
| document_id | path | string | 是 |  |

#### 响应

**200**: Successful Response

**Content-Type**: application/json

**422**: Validation Error

**Content-Type**: application/json

---

### GET /v1/datasets/{dataset_id}/documents/{document_id}/status

**摘要**: Get Document Status

**描述**: 获取文档状态信息

#### 请求参数
| 参数名 | 位置 | 类型 | 必需 | 描述 |
|--------|------|------|------|------|
| dataset_id | path | string | 是 |  |
| document_id | path | string | 是 |  |

#### 响应

**200**: Successful Response

**Content-Type**: application/json

**422**: Validation Error

**Content-Type**: application/json

---

### POST /v1/retrieval

**摘要**: Retrieve Chunks

**描述**: 检索文本块

#### 请求体

**Content-Type**: application/json

| 字段名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| question | string | 是 | Question |
| dataset_ids | N/A | 否 | Dataset Ids |
| document_ids | N/A | 否 | Document Ids |
| page | N/A | 否 | Page (默认: 1) |
| page_size | N/A | 否 | Page Size (默认: 30) |
| similarity_threshold | N/A | 否 | Similarity Threshold (默认: 0.2) |
| vector_similarity_weight | N/A | 否 | Vector Similarity Weight (默认: 0.3) |
| top_k | N/A | 否 | Top K (默认: 1024) |
| rerank_id | N/A | 否 | Rerank Id |
| keyword | N/A | 否 | Keyword |
| highlight | N/A | 否 | Highlight |

#### 响应

**200**: Successful Response

**Content-Type**: application/json

**422**: Validation Error

**Content-Type**: application/json

---

## 数据模型

### ChatCompletionChoice

ChatCompletionChoice

| 字段名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| index | integer | 否 | Index |
| message | N/A | 否 |  |
| delta | N/A | 否 | Delta |
| finish_reason | N/A | 否 | Finish Reason |
| logprobs | N/A | 否 | Logprobs |


### ChatCompletionRequest

ChatCompletionRequest

| 字段名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| model | string | 是 | Model |
| messages | array[N/A] | 是 | Messages |
| stream | boolean | 否 | Stream |


### ChatCompletionResponse

ChatCompletionResponse

| 字段名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| id | string | 是 | Id |
| object | string | 是 | Object |
| created | integer | 是 | Created |
| model | string | 是 | Model |
| choices | array[N/A] | 是 | Choices |
| usage | N/A | 否 |  |


### ChatCompletionUsage

ChatCompletionUsage

| 字段名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| prompt_tokens | integer | 是 | Prompt Tokens |
| completion_tokens | integer | 是 | Completion Tokens |
| total_tokens | integer | 是 | Total Tokens |


### DatasetCreateRequest

DatasetCreateRequest

| 字段名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| name | string | 是 | Name |
| avatar | N/A | 否 | Avatar |
| description | N/A | 否 | Description |
| embedding_model | N/A | 否 | Embedding Model |
| permission | N/A | 否 | Permission (默认: me) |
| chunk_method | N/A | 否 | Chunk Method (默认: naive) |
| pagerank | N/A | 否 | Pagerank |
| parser_config | N/A | 否 | Parser Config |


### DatasetResponse

DatasetResponse

| 字段名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| code | integer | 是 | Code |
| data | N/A | 否 | Data |
| message | N/A | 否 | Message |


### HTTPValidationError

HTTPValidationError

| 字段名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| detail | array[N/A] | 否 | Detail |


### Message

Message

| 字段名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| role | string | 是 | Role |
| content | string | 是 | Content |


### RetrievalRequest

RetrievalRequest

| 字段名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| question | string | 是 | Question |
| dataset_ids | N/A | 否 | Dataset Ids |
| document_ids | N/A | 否 | Document Ids |
| page | N/A | 否 | Page (默认: 1) |
| page_size | N/A | 否 | Page Size (默认: 30) |
| similarity_threshold | N/A | 否 | Similarity Threshold (默认: 0.2) |
| vector_similarity_weight | N/A | 否 | Vector Similarity Weight (默认: 0.3) |
| top_k | N/A | 否 | Top K (默认: 1024) |
| rerank_id | N/A | 否 | Rerank Id |
| keyword | N/A | 否 | Keyword |
| highlight | N/A | 否 | Highlight |


### ValidationError

ValidationError

| 字段名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| loc | array[N/A] | 是 | Location |
| msg | string | 是 | Message |
| type | string | 是 | Error Type |

