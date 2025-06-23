# xDAN Rag Copilot API Service 接口对接文档

## 📋 目录
- [基础配置](#基础配置)
- [认证方式](#认证方式)
- [响应格式](#响应格式)
- [知识库管理](#知识库管理)
- [文档管理](#文档管理)
- [对话管理](#对话管理)
- [检索接口](#检索接口)
- [SSE实时通信](#sse实时通信)
- [错误处理](#错误处理)
- [完整示例](#完整示例)

---

## 基础配置

### API基础信息
- **本地开发**:
  - 代理服务 Base URL: `http://localhost:8001` (xDAN Rag Copilot API Service)
  - 前端开发服务: `http://localhost:5173`
- **远程部署**:
  - 代理服务 Base URL: `http://150.109.16.195:8001`
  - 前端应用: `http://150.109.16.195` (需配置nginx)
- **RAGFlow服务 Base URL**: `http://150.109.16.195:7080` (后端实际服务)
- **API版本**: `v1`
- **协议**: `HTTP/HTTPS`
- **数据格式**: `JSON` / `FormData` (文件上传)

### 服务说明
xDAN Rag Copilot API Service 是一个完整的API代理服务，提供了标准化的接口访问。建议使用代理服务地址进行开发和集成。

### Swagger文档
- **本地访问**: http://localhost:8001/docs
- **远程访问**: http://150.109.16.195:8001/docs
- **OpenAPI规范**: `/openapi.json`
- 可通过Swagger UI直接测试所有接口

### 端口配置说明
| 服务 | 本地端口 | 远程端口 | 说明 |
|------|----------|----------|------|
| 前端应用 | 5173 | 80/443 | Vite开发服务器 / Nginx |
| API代理服务 | 8001 | 8001 | xDAN Rag Copilot API Service |
| RAGFlow服务 | - | 7080 | 原始RAGFlow API |
| 搜索演示 | 8050 | 8050 | 可选的搜索可视化服务 |

### 请求头配置
```http
Content-Type: application/json
Authorization: Bearer {token}
Accept: application/json
```

---

## 认证方式

### Token认证
所有API请求需要在请求头中携带认证token：

```http
Authorization: Bearer ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm
```

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
| name | string | 否 | 名称模糊搜索 |

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

### 6. 下载文档
```http
GET /api/v1/datasets/{dataset_id}/documents/{doc_id}/download
```

**响应**: 文件流

---

## 对话管理

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
POST /api/v1/retrieval
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

## SSE实时通信

### 1. 对话流式响应
**端点**: `POST /api/v1/chats/{chat_id}/completions`

**SSE数据格式**:
```javascript
// 第一条消息：包含回答内容
data:{"code": 0, "message": "", "data": {"answer": "回答内容", "reference": {"chunks": []}, "session_id": "xxx"}}

// 第二条消息：表示结束
data:{"code": 0, "message": "", "data": true}
```

### 2. 前端处理示例
```javascript
const response = await fetch('http://localhost:8001/api/v1/chats/chat_id/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm'
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

## 错误处理

### 常见错误码
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 0 | 成功 | - |
| 100 | 通用错误 | 检查请求参数和格式 |
| 101 | 文件相关错误 | "No file part!" - 检查文件上传格式 |
| 400 | 请求参数错误 | 检查必填参数和参数格式 |
| 401 | 未授权 | 检查token是否有效 |
| 404 | 资源不存在 | 确认资源ID是否正确 |
| 500 | 服务器内部错误 | 稍后重试或联系技术支持 |

### 错误响应示例
```json
{
  "code": 100,
  "data": null,
  "message": "The dataset b66e12c44fea11f0bc4e0242ac140006 doesn't own parsed file"
}
```

---

## 完整示例

### 完整的知识库问答流程

#### 1. 创建知识库
```bash
curl -X POST "http://localhost:8001/api/v1/datasets" \
  -H "Authorization: Bearer ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm" \
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
curl -X POST "http://localhost:8001/api/v1/datasets/{dataset_id}/documents" \
  -H "Authorization: Bearer ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm" \
  -F "file=@test_document.txt"
```

#### 3. 等待文档解析
```bash
# 检查文档状态
curl -X GET "http://localhost:8001/api/v1/datasets/{dataset_id}/documents/{doc_id}" \
  -H "Authorization: Bearer ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm"
```

#### 4. 创建对话
```bash
curl -X POST "http://localhost:8001/api/v1/chats" \
  -H "Authorization: Bearer ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试对话",
    "dataset_ids": ["{dataset_id}"]
  }'
```

#### 5. 发送消息
```bash
curl -X POST "http://localhost:8001/api/v1/chats/{chat_id}/completions" \
  -H "Authorization: Bearer ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "请介绍一下文档的主要内容"
  }'
```

#### 6. 检索测试
```bash
curl -X POST "http://localhost:8001/api/v1/retrieval" \
  -H "Authorization: Bearer ragflow-g4ZWE3OTNhNDUxYTExZjA8MTljMDI0Mm" \
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

**文档版本**: v1.1  
**最后更新**: 2025-06-23  
**测试状态**: ✅ 已验证所有接口  
**服务名称**: xDAN Rag Copilot API Service