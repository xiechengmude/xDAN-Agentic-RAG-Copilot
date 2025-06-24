# API 版本对比分析报告

生成时间：2025-01-24

## 概述

本报告对比了当前运行的API（demo_server_simple.py）与新版xDAN-RAG-Copilot-API的差异，并提供详细的迁移指南。

## 主要变化总结

1. **所有API路径增加 `/api` 前缀**
2. **统一的响应格式（包含code、message、data字段）**
3. **简化的对话请求格式**
4. **删除了Agent和SSE状态流相关接口**
5. **新增了对话管理功能**

## 接口对比表

### 数据集（知识库）相关接口

| 功能 | 旧版路径 | 新版路径 | 变化说明 |
|------|----------|----------|----------|
| 获取数据集列表 | `GET /v1/datasets` | `GET /api/v1/datasets` | 增加 `/api` 前缀 |
| 创建数据集 | `POST /v1/datasets` | `POST /api/v1/datasets` | 增加 `/api` 前缀，embedding_model必填 |
| 更新数据集 | `PUT /v1/datasets/{dataset_id}` | `PUT /api/v1/datasets/{dataset_id}` | 增加 `/api` 前缀 |
| 删除数据集 | `DELETE /v1/datasets` | `DELETE /api/v1/datasets/{dataset_id}` | 改为单个删除操作 |

### 文档相关接口

| 功能 | 旧版路径 | 新版路径 | 变化说明 |
|------|----------|----------|----------|
| 获取文档列表 | `GET /v1/datasets/{dataset_id}/documents` | `GET /api/v1/datasets/{dataset_id}/documents` | 增加 `/api` 前缀 |
| 上传文档 | 无 | `POST /api/v1/datasets/{dataset_id}/documents` | 新增接口 |
| 删除文档 | `DELETE /v1/datasets/{dataset_id}/documents` | `DELETE /api/v1/datasets/{dataset_id}/documents/{doc_id}` | 支持单个删除 |
| 文档解析 | `POST /v1/datasets/{dataset_id}/chunks` | - | 删除（上传后自动解析） |

### 对话相关接口

| 功能 | 旧版路径 | 新版路径 | 变化说明 |
|------|----------|----------|----------|
| 创建对话 | 无 | `POST /api/v1/chats` | 新增接口 |
| 发送消息 | `POST /v1/chats/{chat_id}/chat/completions` | `POST /api/v1/chats/{chat_id}/completions` | 路径简化，请求格式变化 |
| 获取历史 | 无 | `GET /api/v1/chats/{chat_id}/messages` | 新增接口 |
| Agent对话 | `POST /v1/agents/{agent_id}/chat/completions` | - | 删除 |

### 检索接口

| 功能 | 旧版路径 | 新版路径 | 变化说明 |
|------|----------|----------|----------|
| 知识库检索 | `POST /v1/retrieval` | `POST /api/v1/retrieval` | 增加 `/api` 前缀，参数简化 |

## 请求/响应格式变化

### 统一响应格式

**新版采用统一格式：**
```json
{
  "code": 0,          // 0表示成功
  "message": "Success",
  "data": {},         // 实际数据
  "meta": {}          // 分页元数据（可选）
}
```

### 创建数据集请求

**旧版：**
```json
{
  "name": "string",
  "embedding_model": null,  // 可选
  "chunk_method": "naive"
}
```

**新版：**
```json
{
  "name": "测试知识库",
  "description": "用于测试的知识库",
  "embedding_model": "BAAI/bge-m3@SILICONFLOW",  // 必填，格式固定
  "chunk_method": "naive",
  "parser_config": {
    "chunk_token_num": 512
  }
}
```

### 对话请求格式

**旧版：**
```json
{
  "model": "string",
  "messages": [{"role": "user", "content": "string"}],
  "stream": false
}
```

**新版：**
```json
{
  "content": "你好，请介绍一下RAGFlow"  // 大幅简化
}
```

## 代码修改建议

### 1. 更新基础配置

```python
# 旧代码
BASE_URL = "http://localhost:8001/v1"

# 新代码
BASE_URL = "http://localhost:8050/api/v1"
```

### 2. 统一响应处理

```python
def handle_response(response):
    data = response.json()
    if data['code'] == 0:
        return data['data']
    else:
        raise APIError(f"Error {data['code']}: {data['message']}")
```

### 3. 修改数据集创建

```python
def create_dataset(name, description):
    payload = {
        "name": name,
        "description": description,
        "embedding_model": "BAAI/bge-m3@SILICONFLOW",  # 必须指定
        "chunk_method": "naive"
    }
    return requests.post(f"{BASE_URL}/datasets", json=payload)
```

### 4. 简化对话接口

```python
# 创建对话
def create_chat(name, dataset_ids):
    payload = {"name": name, "dataset_ids": dataset_ids}
    return requests.post(f"{BASE_URL}/chats", json=payload)

# 发送消息
def send_message(chat_id, content):
    payload = {"content": content}
    return requests.post(f"{BASE_URL}/chats/{chat_id}/completions", json=payload)
```

### 5. 处理文档上传

```python
def upload_document(dataset_id, file_path):
    with open(file_path, 'rb') as f:
        files = {'file': f}  # 注意：使用 'file' 而不是 'files[]'
        response = requests.post(
            f"{BASE_URL}/datasets/{dataset_id}/documents",
            files=files
        )
    # 响应是数组格式
    return response.json()['data'][0]
```

## 注意事项

1. **服务端口变更**：从8001改为8050
2. **文档自动解析**：上传后无需手动调用解析接口
3. **必须先创建对话**：在发送消息前需要先创建对话
4. **embedding_model格式**：必须使用"模型名@提供商"格式
5. **SSE流式响应**：对话接口自动支持流式响应

## 迁移步骤建议

1. 更新所有API路径，添加`/api`前缀
2. 实现统一的响应处理函数
3. 更新数据集创建逻辑，确保包含必填字段
4. 移除Agent相关代码
5. 实现新的对话管理功能
6. 更新文档上传逻辑，移除解析步骤
7. 测试所有功能确保正常工作

## 错误代码参考

- 0: 成功
- 100: 通用错误
- 101: 文件相关错误
- 400: 请求参数错误
- 401: 未授权
- 404: 资源不存在
- 500: 服务器内部错误