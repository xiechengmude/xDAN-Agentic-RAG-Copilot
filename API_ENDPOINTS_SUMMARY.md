# xDAN Rag Copilot API Service - Complete API Documentation

## Service Overview
- **Title**: xDAN Rag Copilot API Service
- **Description**: 统一的API服务，整合LiteLLM对话和RAGFlow知识库管理
- **Version**: 1.0.0
- **Base URL**: http://localhost:8050
- **Documentation URL**: http://localhost:8050/docs

## API Endpoints

### 1. Chat Management APIs

#### POST /api/v1/chats
- **Summary**: Create Chat (创建新的对话)
- **Operation ID**: `create_chat_api_v1_chats_post`
- **Request Body** (required):
  ```json
  {
    "name": "string",                    // 聊天名称 (required)
    "dataset_ids": ["string"],          // 关联的数据集ID列表 (default: [])
    "description": "string",            // 聊天描述 (optional)
    "llm_config": {                     // LLM配置 (optional)
      "model_name": "deepseek-chat",
      "temperature": 0.7,
      "max_tokens": 2000
    }
  }
  ```
- **Response**: 200 OK with JSON response

#### GET /api/v1/chats
- **Summary**: List Chats (获取对话列表)
- **Operation ID**: `list_chats_api_v1_chats_get`
- **Query Parameters**:
  - `page` (integer, default: 1)
  - `page_size` (integer, default: 20)
- **Response**: 200 OK with JSON response

#### DELETE /api/v1/chats/{chat_id}
- **Summary**: Delete Chat (删除对话)
- **Operation ID**: `delete_chat_api_v1_chats__chat_id__delete`
- **Path Parameters**:
  - `chat_id` (string, required)
- **Response**: 200 OK with JSON response

### 2. Chat Interaction APIs

#### POST /api/v1/chats/{chat_id}/completions
- **Summary**: Chat Completion (发送消息并获取AI回复（支持SSE流式响应）)
- **Operation ID**: `chat_completion_api_v1_chats__chat_id__completions_post`
- **Path Parameters**:
  - `chat_id` (string, required)
- **Request Body** (required):
  ```json
  {
    "content": "string",      // 消息内容 (required)
    "stream": false          // 是否流式返回 (default: false)
  }
  ```
- **Response**: 200 OK with JSON response (or SSE stream if stream=true)

#### GET /api/v1/chats/{chat_id}/messages
- **Summary**: Get Chat Messages (获取对话历史)
- **Operation ID**: `get_chat_messages_api_v1_chats__chat_id__messages_get`
- **Path Parameters**:
  - `chat_id` (string, required)
- **Query Parameters**:
  - `page` (integer, default: 1)
  - `page_size` (integer, default: 20)
- **Response**: 200 OK with JSON response

### 3. Knowledge Base (Dataset) APIs

#### GET /api/v1/datasets
- **Summary**: List Datasets (获取知识库列表 - 代理到RAGFlow)
- **Operation ID**: `list_datasets_api_v1_datasets_get`
- **Query Parameters**:
  - `page` (integer, default: 1)
  - `page_size` (integer, default: 12)
  - `name` (string, optional) - Filter by name
- **Response**: 200 OK with JSON response

#### POST /api/v1/datasets
- **Summary**: Create Dataset (创建知识库 - 代理到RAGFlow)
- **Operation ID**: `create_dataset_api_v1_datasets_post`
- **Request Body** (required):
  ```json
  {
    "name": "string",                              // 名称 (required)
    "description": "string",                       // 描述 (optional)
    "embedding_model": "BAAI/bge-m3@SILICONFLOW", // 嵌入模型 (default)
    "chunk_method": "naive",                       // 分块方法 (default)
    "parser_config": {                             // 解析配置 (default)
      "chunk_token_num": 512,
      "delimiter": "\n"
    }
  }
  ```
- **Response**: 200 OK with JSON response

#### PUT /api/v1/datasets/{dataset_id}
- **Summary**: Update Dataset (更新知识库 - 代理到RAGFlow)
- **Operation ID**: `update_dataset_api_v1_datasets__dataset_id__put`
- **Path Parameters**:
  - `dataset_id` (string, required)
- **Request Body** (required): Any JSON object with update fields
- **Response**: 200 OK with JSON response

#### DELETE /api/v1/datasets/{dataset_id}
- **Summary**: Delete Dataset (删除知识库 - 代理到RAGFlow)
- **Operation ID**: `delete_dataset_api_v1_datasets__dataset_id__delete`
- **Path Parameters**:
  - `dataset_id` (string, required)
- **Response**: 200 OK with JSON response

### 4. Document Management APIs

#### POST /api/v1/datasets/{dataset_id}/documents
- **Summary**: Upload Documents (上传文档到知识库 - 代理到RAGFlow)
- **Operation ID**: `upload_documents_api_v1_datasets__dataset_id__documents_post`
- **Path Parameters**:
  - `dataset_id` (string, required)
- **Request Body** (multipart/form-data):
  - `file` (binary, required) - The file to upload
- **Response**: 200 OK with JSON response

#### GET /api/v1/datasets/{dataset_id}/documents
- **Summary**: List Documents (获取文档列表 - 代理到RAGFlow)
- **Operation ID**: `list_documents_api_v1_datasets__dataset_id__documents_get`
- **Path Parameters**:
  - `dataset_id` (string, required)
- **Query Parameters**:
  - `page` (integer, default: 1)
  - `page_size` (integer, default: 20)
- **Response**: 200 OK with JSON response

#### DELETE /api/v1/datasets/{dataset_id}/documents/{document_id}
- **Summary**: Delete Document (删除文档 - 代理到RAGFlow)
- **Operation ID**: `delete_document_api_v1_datasets__dataset_id__documents__document_id__delete`
- **Path Parameters**:
  - `dataset_id` (string, required)
  - `document_id` (string, required)
- **Response**: 200 OK with JSON response

### 5. Knowledge Retrieval API

#### POST /api/v1/retrieval
- **Summary**: Retrieval (知识库检索 - 代理到RAGFlow)
- **Operation ID**: `retrieval_api_v1_retrieval_post`
- **Request Body** (required):
  ```json
  {
    "question": "string",           // 检索问题 (required)
    "dataset_ids": ["string"],      // 要检索的数据集ID列表 (required)
    "page": 1,                      // 页码 (default: 1, min: 1)
    "page_size": 5,                 // 每页数量 (default: 5, min: 1, max: 20)
    "similarity_threshold": 0.1     // 相似度阈值 (default: 0.1)
  }
  ```
- **Response**: 200 OK with JSON response

### 6. Utility APIs

#### GET /health
- **Summary**: Health Check (健康检查)
- **Operation ID**: `health_check_health_get`
- **Response**: 200 OK with JSON response

#### GET /
- **Summary**: Root (根路径)
- **Operation ID**: `root__get`
- **Response**: 200 OK with JSON response

## Error Responses

All endpoints may return the following error response:
- **422 Unprocessable Entity**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": ["string or integer"],  // Error location
        "msg": "string",                // Error message
        "type": "string"                // Error type
      }
    ]
  }
  ```

## Key Features

1. **Chat Management**: Complete CRUD operations for managing chat sessions
2. **Real-time Chat**: Support for both synchronous and streaming (SSE) responses
3. **Knowledge Base Integration**: Full integration with RAGFlow for knowledge base management
4. **Document Management**: Upload, list, and delete documents in knowledge bases
5. **Intelligent Retrieval**: Search across multiple knowledge bases with configurable parameters
6. **LLM Configuration**: Flexible LLM configuration per chat session

## Integration Notes

- The service acts as a unified gateway, integrating:
  - **LiteLLM**: For chat completions and LLM operations
  - **RAGFlow**: For knowledge base and document management
- Most knowledge base operations are proxied to RAGFlow
- Chat operations are handled locally with LiteLLM integration
- Supports both streaming and non-streaming responses for chat completions